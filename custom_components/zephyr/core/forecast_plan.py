"""From Home Assistant data to a plan and back (SPEC-planner §2, §4).

Pure functions around ``planner.plan``:

* **Prices** (§2.1): Nord Pool slots per start time (never per position), unit
  recognised (€/kWh, €/MWh, cents). The horizon runs per quarter from the running
  quarter to the end of tomorrow; hour prices count for all four quarters. While
  tomorrow is unknown, today's price at the same local time stands in
  (*indicative*: not in the totals). No price for the running quarter: no plan,
  state *No prices*, action N (never L or X).
* **Solar** (§2.2): Solcast half-hour detail (kW) per quarter; without a forecast
  the caller may pass yesterday's production per hour.
* **Consumption** (§2.3): a callback, normally ``LoadProfile.forecast``.
* **Output** (§4): action now, state, reason (NL/EN), blocks, key figures and a
  timeline per quarter.

Slots are counted in UTC, so days with 92 or 100 quarters come out right.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Any, Final

from .planner import Action, Battery, Plan, PlannerSettings, Slot, Step, plan, step
from .price_window import PriceSlot, parse_nordpool_raw
from .solar_history import ForecastPeriod

QUARTER: Final = timedelta(minutes=15)
MIN_BLOCK_KWH: Final = 0.1
"""Deliver blocks below this energy are left out of the block list (§4)."""
DEFAULT_LOAD_KWH_PER_HOUR: Final = 0.35
"""Consumption while nothing has been learned yet (≈ 3 000 kWh a year)."""
NEAR_LIMIT_PERCENT: Final = 0.5
"""SOC within this many %-points of min/max counts as empty/full (state only)."""


class PlanState:
    ACTIVE: Final = "active"
    NO_PRICES: Final = "no_prices"
    PRICE_RESERVE: Final = "price_reserve"
    BATTERY_EMPTY: Final = "battery_empty"
    BATTERY_FULL: Final = "battery_full"
    ALL: Final = (ACTIVE, NO_PRICES, PRICE_RESERVE, BATTERY_EMPTY, BATTERY_FULL)


ACTION_KEYS: Final[dict[Action, str]] = {
    Action.CHARGE: "charge",
    Action.HOLD: "hold",
    Action.DELIVER: "deliver",
    Action.EXPORT: "export",
}
"""Entity states for the actions (the letter stays available as attribute ``code``)."""


# --- prices -------------------------------------------------------------------------


def unit_factor(attributes: Mapping[str, Any]) -> float:
    """Factor from the sensor's price unit to €/kWh."""
    unit = str(attributes.get("unit") or attributes.get("unit_of_measurement") or "")
    factor = 0.001 if "MWh" in unit else 1.0
    if attributes.get("price_in_cents") is True or unit.lower().startswith(("ct", "cent", "c/")):
        factor /= 100
    return factor


def market_slots(attributes: Mapping[str, Any]) -> list[PriceSlot]:
    """Bare market prices (€/kWh) of a Nord Pool sensor (``raw_today`` + ``raw_tomorrow``), by start time."""
    factor = unit_factor(attributes)
    slots = parse_nordpool_raw(attributes.get("raw_today")) + parse_nordpool_raw(attributes.get("raw_tomorrow"))
    seen: dict[datetime, PriceSlot] = {}
    for s in slots:
        seen.setdefault(s.start, PriceSlot(s.start, s.end, s.price * factor))
    return sorted(seen.values(), key=lambda s: s.start)


def quarter_floor(moment: datetime) -> datetime:
    """Start of the quarter containing ``moment`` (aware)."""
    return moment.replace(minute=moment.minute - moment.minute % 15, second=0, microsecond=0)


def local_midnight(day_offset: int, now: datetime, tz: tzinfo) -> datetime:
    """Local midnight ``day_offset`` days after today (aware, in ``tz``)."""
    local = now.astimezone(tz)
    day = local.date() + timedelta(days=day_offset)
    return datetime(day.year, day.month, day.day, tzinfo=tz)


@dataclass(frozen=True, slots=True)
class HorizonSlot:
    start: datetime
    market: float
    buy: float
    sell: float
    load_kwh: float
    solar_kwh: float
    indicative: bool
    """Price taken from today's pattern (tomorrow not known yet)."""

    def planner_slot(self) -> Slot:
        return Slot(QUARTER.total_seconds() / 3600, self.buy, self.sell, self.load_kwh, self.solar_kwh)


def price_at(slots: Sequence[PriceSlot], moment: datetime) -> PriceSlot | None:
    return next((s for s in slots if s.start <= moment < s.end), None)


def horizon_markets(prices: Sequence[PriceSlot], now: datetime, tz: tzinfo) -> list[tuple[datetime, float, bool]]:
    """(quarter start, market price, indicative) from the running quarter to the end of tomorrow.

    Empty when there is no price for the running quarter (§2.1: never plan without a price for now).
    """
    # Steps in UTC: adding 15 minutes to a local time would skip or repeat an hour on DST days.
    first = quarter_floor(now.astimezone(UTC))
    if price_at(prices, first) is None:
        return []
    end = local_midnight(2, now, tz).astimezone(UTC)
    tomorrow = local_midnight(1, now, tz).astimezone(UTC)
    # Today's pattern by local clock time, for the quarters of tomorrow without a price.
    pattern: dict[tuple[int, int], float] = {}
    t = local_midnight(0, now, tz).astimezone(UTC)
    while t < tomorrow:
        slot = price_at(prices, t)
        if slot is not None:
            local = t.astimezone(tz)
            pattern.setdefault((local.hour, local.minute), slot.price)
        t += QUARTER
    out: list[tuple[datetime, float, bool]] = []
    t = first
    last_pattern: float | None = None
    while t < end:
        slot = price_at(prices, t)
        if slot is not None:
            out.append((t, slot.price, False))
        elif t >= tomorrow:
            local = t.astimezone(tz)
            value = pattern.get((local.hour, local.minute), last_pattern)
            if value is None:
                break
            last_pattern = value
            out.append((t, value, True))
        else:
            break  # a gap today: plan up to the gap
        t += QUARTER
    return out


# --- solar ----------------------------------------------------------------------------


def solar_per_quarter(periods: Iterable[ForecastPeriod]) -> dict[datetime, float]:
    """kWh per quarter start (UTC) from forecast periods (kW, usually half-hour periods)."""
    items = sorted(((datetime.fromisoformat(p.start), p.estimate) for p in periods), key=lambda item: item[0])
    out: dict[datetime, float] = {}
    for i, (start, kw) in enumerate(items):
        end = items[i + 1][0] if i + 1 < len(items) else start + timedelta(minutes=30)
        end = min(end, start + timedelta(hours=1))
        t = start
        while t < end:
            out[t] = max(kw, 0.0) * QUARTER.total_seconds() / 3600
            t += QUARTER
    return out


# --- the horizon ----------------------------------------------------------------------

BuyFn = Callable[[datetime, float], float]
SellFn = Callable[[datetime, float, bool], float]
LoadFn = Callable[[datetime, float], float]
"""(quarter start, hours ahead) → kWh in that quarter."""
SolarFn = Callable[[datetime], float]
DaylightFn = Callable[[datetime], bool]


def build_horizon(
    markets: Sequence[tuple[datetime, float, bool]],
    now: datetime,
    *,
    buy: BuyFn,
    sell: SellFn,
    load: LoadFn,
    solar: SolarFn,
    daylight: DaylightFn,
) -> list[HorizonSlot]:
    out: list[HorizonSlot] = []
    for start, market, indicative in markets:
        ahead = max((start - now).total_seconds() / 3600, 0.0)
        sun = max(solar(start), 0.0)
        out.append(
            HorizonSlot(
                start=start,
                market=market,
                buy=buy(start, market),
                sell=sell(start, market, daylight(start + QUARTER / 2)),
                load_kwh=max(load(start, ahead), 0.0),
                solar_kwh=sun,
                indicative=indicative,
            )
        )
    return out


# --- battery ----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BatteryInput:
    capacity_kwh: float
    """Nominal capacity of all sets."""
    soc: float
    """%."""
    min_soc: float
    max_soc: float
    charge_kw: float
    deliver_kw: float
    buffer: float = 0.0
    """%-points above min_SOC the planner keeps free (B37)."""
    eta_in: float = 0.93
    eta_out: float = 0.93

    @property
    def floor(self) -> float:
        return min(self.min_soc + self.buffer, self.max_soc)

    def battery(self) -> Battery:
        usable = self.capacity_kwh * max(self.max_soc - self.floor, 0.0) / 100
        return Battery(usable, self.charge_kw, self.deliver_kw, self.eta_in, self.eta_out)

    @property
    def energy_now(self) -> float:
        """kWh above the planning floor (min_SOC + buffer), bounded to the usable energy."""
        usable = self.capacity_kwh * max(self.max_soc - self.floor, 0.0) / 100
        return min(max(self.capacity_kwh * (self.soc - self.floor) / 100, 0.0), usable)


# --- the outcome --------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Block:
    action: Action
    start: datetime
    end: datetime
    kwh: float
    """L: from the grid into the battery; N/X: out of the battery; H: 0."""
    price: float
    """Mean all-in price (sell price for X)."""
    indicative: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "action": ACTION_KEYS[self.action],
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "kwh": round(self.kwh, 2),
            "price": round(self.price, 4),
            "indicative": self.indicative,
        }


@dataclass(slots=True)
class PlanOutcome:
    state: str
    action: Action
    """Action now (N when there is no plan)."""
    calculated_at: datetime
    slots: list[HorizonSlot] = field(default_factory=list)
    plan: Plan = field(default_factory=Plan)
    grid_kwh: list[float] = field(default_factory=list)
    """Per slot: kWh charged from the grid (L)."""
    export_kwh: list[float] = field(default_factory=list)
    """Per slot: kWh from the battery to the grid (X)."""
    energy: list[float] = field(default_factory=list)
    """Per slot: energy above the planning floor at the start (kWh)."""
    blocks: list[Block] = field(default_factory=list)
    battery: BatteryInput | None = None
    duration_s: float = 0.0
    no_prices_since: datetime | None = None

    # --- key figures (without indicative slots, §2.1) ---

    def _sum(self, values: list[float], price: Callable[[HorizonSlot], float] | None = None) -> float:
        return sum(v * (price(s) if price else 1.0) for v, s in zip(values, self.slots, strict=False) if not s.indicative)

    @property
    def planned_grid_charge_kwh(self) -> float:
        return self._sum(self.grid_kwh)

    @property
    def planned_grid_charge_cost(self) -> float:
        return self._sum(self.grid_kwh, lambda s: s.buy)

    @property
    def planned_export_kwh(self) -> float:
        return self._sum(self.export_kwh)

    @property
    def planned_export_revenue(self) -> float:
        return self._sum(self.export_kwh, lambda s: s.sell)

    @property
    def expected_cost(self) -> float:
        return sum(st.cost for st, s in zip(self.plan.steps, self.slots, strict=False) if not s.indicative)

    @property
    def indicative_from(self) -> datetime | None:
        return next((s.start for s in self.slots if s.indicative), None)

    @property
    def empty_at(self) -> datetime | None:
        """End of the first slot in which delivering empties the battery (to the planning floor)."""
        for slot, action, st in zip(self.slots, self.plan.actions, self.plan.steps, strict=False):
            if action in (Action.DELIVER, Action.EXPORT) and st.delivered > 0 and st.energy_after <= 0.01:
                return slot.start + QUARTER
        return None

    def step_at(self, start: datetime) -> tuple[Action, Step, HorizonSlot] | None:
        for slot, action, st in zip(self.slots, self.plan.actions, self.plan.steps, strict=False):
            if slot.start == start:
                return action, st, slot
        return None

    def timeline(self) -> list[dict[str, Any]]:
        """Per quarter: price, action, solar, consumption, battery (kW, + charging), SOC, grid (kW, + import)."""
        out: list[dict[str, Any]] = []
        bat = self.battery
        for slot, action, st, energy in zip(self.slots, self.plan.actions, self.plan.steps, self.energy, strict=False):
            soc = None
            if bat is not None and bat.capacity_kwh > 0:
                soc = round(bat.floor + st.energy_after / bat.capacity_kwh * 100, 1)
            hours = QUARTER.total_seconds() / 3600
            out.append(
                {
                    "start": slot.start.isoformat(),
                    "action": action.value,
                    "buy": round(slot.buy, 4),
                    "sell": round(slot.sell, 4),
                    "solar": round(slot.solar_kwh, 3),
                    "load": round(slot.load_kwh, 3),
                    "battery_kw": round((st.charged - st.delivered) / hours, 2),
                    "soc": soc,
                    "grid_kw": round((st.grid_import - st.grid_export) / hours, 2),
                    "energy": round(energy, 3),
                    "indicative": slot.indicative,
                }
            )
        return out

    def summary(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "action": self.action.value,
            "calculated_at": self.calculated_at.isoformat(),
            "duration_s": round(self.duration_s, 3),
            "slots": len(self.slots),
            "indicative_from": None if self.indicative_from is None else self.indicative_from.isoformat(),
            "grid_charge_kwh": round(self.planned_grid_charge_kwh, 3),
            "grid_charge_cost": round(self.planned_grid_charge_cost, 3),
            "export_kwh": round(self.planned_export_kwh, 3),
            "export_revenue": round(self.planned_export_revenue, 3),
            "expected_cost": round(self.expected_cost, 3),
            "empty_at": None if self.empty_at is None else self.empty_at.isoformat(),
            "no_prices_since": None if self.no_prices_since is None else self.no_prices_since.isoformat(),
        }


def no_prices(now: datetime, since: datetime | None) -> PlanOutcome:
    return PlanOutcome(PlanState.NO_PRICES, Action.DELIVER, now, no_prices_since=since or now)


def make_plan(
    slots: Sequence[HorizonSlot],
    bat: BatteryInput,
    now: datetime,
    settings: PlannerSettings,
    previous: Action = Action.DELIVER,
) -> PlanOutcome:
    """Plan over ``slots`` (the first is the running quarter) and derive the outcome (§4)."""
    if not slots:
        return no_prices(now, None)
    battery = bat.battery()
    result = plan([s.planner_slot() for s in slots], battery, bat.energy_now, settings, previous)
    outcome = PlanOutcome(PlanState.ACTIVE, result.actions[0], now, list(slots), result, battery=bat)
    energy = bat.energy_now
    for slot, action, st in zip(slots, result.actions, result.steps, strict=True):
        hold = step(slot.planner_slot(), battery, energy, Action.HOLD)
        outcome.energy.append(energy)
        outcome.grid_kwh.append(max(st.grid_import - hold.grid_import, 0.0) if action is Action.CHARGE else 0.0)
        outcome.export_kwh.append(max(st.grid_export - hold.grid_export, 0.0) if action is Action.EXPORT else 0.0)
        energy = st.energy_after
    outcome.blocks = blocks(outcome)
    if outcome.action is Action.DELIVER and bat.soc <= bat.min_soc + NEAR_LIMIT_PERCENT:
        outcome.state = PlanState.BATTERY_EMPTY
    elif outcome.action is Action.CHARGE and bat.soc >= bat.max_soc - NEAR_LIMIT_PERCENT:
        outcome.state = PlanState.BATTERY_FULL
    return outcome


def blocks(outcome: PlanOutcome) -> list[Block]:
    out: list[Block] = []
    rows = list(zip(outcome.slots, outcome.plan.actions, outcome.plan.steps, outcome.grid_kwh, outcome.export_kwh, strict=False))
    i = 0
    while i < len(rows):
        action = rows[i][1]
        j = i
        while j < len(rows) and rows[j][1] is action:
            j += 1
        part = rows[i:j]
        if action is Action.CHARGE:
            kwh = sum(r[3] for r in part)
        elif action in (Action.DELIVER, Action.EXPORT):
            kwh = sum(r[2].delivered for r in part)
        else:
            kwh = 0.0
        prices = [r[0].sell if action is Action.EXPORT else r[0].buy for r in part]
        indicative = any(r[0].indicative for r in part)
        block = Block(action, part[0][0].start, part[-1][0].start + QUARTER, kwh, sum(prices) / len(prices), indicative)
        if not (action is Action.DELIVER and kwh < MIN_BLOCK_KWH):
            out.append(block)
        i = j
    return out


# --- the reason (§4: one sentence in plain language) --------------------------------------

REASONS: Final[dict[str, tuple[str, str]]] = {
    "no_prices": (
        "No price for this quarter (since {since}): zero on the meter until there are prices again.",
        "Geen prijs voor dit kwartier (sinds {since}): Nul op de meter tot er weer prijzen zijn.",
    ),
    "charge_for": (
        "Charging from the grid is cheap now: {now}, the battery delivers from {time} at {later} on average.",
        "Laden uit het net is nu gunstig: {now}, de accu levert vanaf {time} bij gemiddeld {later}.",
    ),
    "charge": ("Charging from the grid: {now} now.", "Laden uit het net: {now} nu."),
    "deliver_then_charge": (
        "Delivering is worth it now: {now}, recharging at {time} costs {charge} including losses.",
        "Leveren is nu gunstig: {now}, bijladen om {time} kost {charge} inclusief verlies.",
    ),
    "deliver": ("Delivering: {now} now, no grid charging planned.", "Leveren: {now} nu, geen netladen gepland."),
    "hold_for": (
        "Holding: {now} now is too cheap to deliver; the battery delivers from {time} at {later} on average.",
        "Vasthouden: {now} nu is te goedkoop om te leveren; de accu levert vanaf {time} bij gemiddeld {later}.",
    ),
    "hold": ("Holding: {now} now; the battery waits for a better moment.", "Vasthouden: {now} nu; de accu wacht op een beter moment."),
    "export": ("Exporting from the battery pays now: {sell} per kWh.", "Terugleveren uit de accu loont nu: {sell} per kWh."),
}


def _euro(value: float, language: str) -> str:
    text = f"€{value:.2f}"
    return text.replace(".", ",") if language.startswith("nl") else text


def _clock(moment: datetime, tz: tzinfo) -> str:
    return moment.astimezone(tz).strftime("%H:%M")


def reason(outcome: PlanOutcome, language: str, tz: tzinfo) -> str:
    """One sentence that explains the action now (Dutch when ``language`` starts with nl)."""
    nl = language.startswith("nl")

    def text(key: str, **params: str) -> str:
        en_text, nl_text = REASONS[key]
        return (nl_text if nl else en_text).format(**params)

    if outcome.state == PlanState.NO_PRICES or not outcome.slots:
        since = outcome.no_prices_since or outcome.calculated_at
        return text("no_prices", since=_clock(since, tz))
    now_slot = outcome.slots[0]
    now = _euro(now_slot.buy, language)
    later_blocks = [b for b in outcome.blocks if b.start > now_slot.start]
    action = outcome.action
    if action is Action.EXPORT:
        return text("export", sell=_euro(now_slot.sell, language))
    if action in (Action.CHARGE, Action.HOLD):
        nxt = next((b for b in later_blocks if b.action in (Action.DELIVER, Action.EXPORT)), None)
        key = "charge" if action is Action.CHARGE else "hold"
        if nxt is None:
            return text(key, now=now)
        return text(f"{key}_for", now=now, time=_clock(nxt.start, tz), later=_euro(nxt.price, language))
    nxt = next((b for b in later_blocks if b.action is Action.CHARGE), None)
    if nxt is None:
        return text("deliver", now=now)
    bat = outcome.battery
    loss = (bat.eta_in * bat.eta_out) if bat is not None else 1.0
    return text("deliver_then_charge", now=now, time=_clock(nxt.start, tz), charge=_euro(nxt.price / loss, language))
