"""Cost log: what electricity cost per quarter, and what it would have cost (B38, SPEC-kosten).

Per quarter ZEPHYR records grid import and export, battery charge and delivery,
solar and the market price. From that it computes the costs in three situations:

* **actual** (W): as measured;
* **without battery** (Z1): the battery's AC exchange removed, netted per quarter;
* **without battery and solar** (Z0): the whole house consumption from the grid
  (only with a solar counter).

Savings: solar = Z0 − Z1, battery = Z1 − W. The battery saving is split into
solar via the battery (two pools, solar and grid, on AC energy) and the rest,
the price difference (trade). Net metering (saldering, until 2027) is settled
per year: export above import loses the netting part.

Pure Python; the Home Assistant side feeds power samples and counter readings.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field, replace
from datetime import date, datetime
from typing import Any, Final

from . import plan_check

QUARTER_SECONDS: Final = 900.0
COMPLETE_SHARE: Final = 0.95
"""A quarter counts as complete when at least this share of its time was measured."""
MAX_SAMPLE_GAP: Final = 10.0
"""s; a longer gap between samples is not integrated (HA was busy or stopped)."""


# --- tariffs -------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Tariffs:
    """Own tariffs (B38); the tariff table of B28 fills the same fields later. €/kWh excl. VAT."""

    energy_tax: float = 0.09161
    """Energy tax (energiebelasting), Netherlands 2026, excl. VAT (€0.11085 incl.)."""
    vat: float = 21.0
    """%."""
    markup_import: float = 0.0
    """Supplier margin on import (opslag inkoop), excl. VAT."""
    markup_export: float = 0.0
    """Added to the market price for export (negative = a fee), excl. VAT."""
    solar_bonus: float = 0.0
    """% extra on (market + export margin) for export between sunrise and sunset, only when that
    amount is positive (Zonneplan's Zonnebonus: 10 %). Not part of net metering."""
    export_vat_after_saldering: bool = False
    """Without net metering: VAT on the export price too (some suppliers pay market incl. VAT)."""
    fixed_month: float = 0.0
    """Fixed costs per month incl. VAT (net: standing charges + grid operator − energy tax reduction)."""
    saldering_until: date = date(2027, 1, 1)
    """Net metering applies to quarters starting before this date."""
    source: str = "own"

    @property
    def vat_factor(self) -> float:
        return 1 + self.vat / 100

    def buy(self, market: float) -> float:
        """All-in import price."""
        return (market + self.markup_import + self.energy_tax) * self.vat_factor

    def bonus(self, market: float, daylight: bool) -> float:
        """Solar bonus per exported kWh (€): a share of market + export margin, by day, when positive."""
        base = market + self.markup_export
        return self.solar_bonus / 100 * base if daylight and base > 0 else 0.0

    def sell(self, market: float, start: datetime, daylight: bool = False) -> tuple[float, float]:
        """Export price and the part of it that exists only through net metering."""
        base = market + self.markup_export
        bonus = self.bonus(market, daylight)
        if start.date() < self.saldering_until:
            price = base * self.vat_factor + self.energy_tax * self.vat_factor
            return price + bonus, price - base
        return (base * self.vat_factor if self.export_vat_after_saldering else base) + bonus, 0.0

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["saldering_until"] = self.saldering_until.isoformat()
        return data


# --- measuring a quarter ---------------------------------------------------------


@dataclass(slots=True)
class QuarterMeter:
    """Integrates power samples (sample and hold) into energy for the running quarter."""

    import_kwh: float = 0.0
    export_kwh: float = 0.0
    charge_kwh: float = 0.0
    discharge_kwh: float = 0.0
    set_solar_kwh: float = 0.0
    grid_seconds: float = 0.0
    battery_seconds: float = 0.0
    _last_t: float | None = None
    _grid_w: float | None = None
    _charge_w: float | None = None
    _deliver_w: float = 0.0
    _solar_w: float = 0.0
    _battery_complete: bool = True

    def sample(
        self,
        now: float,
        grid_w: float | None,
        charge_w: float | None,
        deliver_w: float = 0.0,
        set_solar_w: float = 0.0,
        battery_complete: bool = True,
    ) -> None:
        """``grid_w``: + import, − export (None = no fresh P1).

        ``charge_w`` / ``deliver_w``: AC power into and out of the batteries, both ≥ 0
        (``charge_w`` None = no set counts). ``set_solar_w``: the sets' own PV. A sample
        counts towards the battery coverage only when ``battery_complete`` (all sets counted).
        """
        if self._last_t is not None:
            dt = now - self._last_t
            if 0 < dt <= MAX_SAMPLE_GAP:
                hours = dt / 3600
                if self._grid_w is not None:
                    self.grid_seconds += dt
                    self.import_kwh += max(self._grid_w, 0.0) / 1000 * hours
                    self.export_kwh += max(-self._grid_w, 0.0) / 1000 * hours
                if self._charge_w is not None:
                    if self._battery_complete:
                        self.battery_seconds += dt
                    self.charge_kwh += max(self._charge_w, 0.0) / 1000 * hours
                    self.discharge_kwh += max(self._deliver_w, 0.0) / 1000 * hours
                    self.set_solar_kwh += max(self._solar_w, 0.0) / 1000 * hours
        self._last_t = now
        self._grid_w, self._charge_w, self._deliver_w = grid_w, charge_w, deliver_w
        self._solar_w, self._battery_complete = set_solar_w, battery_complete

    def take(self, now: float) -> QuarterMeter:
        """Close the quarter at ``now``: return what was measured and start a new one (values held)."""
        self.sample(now, self._grid_w, self._charge_w, self._deliver_w, self._solar_w, self._battery_complete)
        done = replace(self)
        self.import_kwh = self.export_kwh = self.charge_kwh = self.discharge_kwh = self.set_solar_kwh = 0.0
        self.grid_seconds = self.battery_seconds = 0.0
        return done


def counter_delta(previous: float | None, current: float | None) -> float | None:
    """Energy between two counter readings. A drop (new meter, reset) counts from 0."""
    if previous is None or current is None:
        return None
    return current - previous if current >= previous else current


# --- one quarter -------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class QuarterInput:
    start: datetime
    """Start of the quarter (aware)."""
    minutes: float
    import_kwh: float
    export_kwh: float
    charge_kwh: float
    discharge_kwh: float
    solar_kwh: float | None
    """Total solar (counter + the sets' own PV); None = unknown."""
    market: float | None
    """Bare market price €/kWh; None = no price."""
    coverage: float = 1.0
    """Share of the quarter that was measured (0–1)."""
    stored_kwh: float | None = None
    """Energy in the battery at the end of the quarter (caps the pools)."""
    daylight: bool = False
    """Between sunrise and sunset (for the solar bonus)."""


@dataclass(slots=True)
class Pools:
    """Origin of the energy in the battery (AC side), for 'solar via the battery'."""

    solar_kwh: float = 0.0
    grid_kwh: float = 0.0
    solar_value: float = 0.0
    """Export revenue given up when the solar in the pool was charged (€)."""

    def as_dict(self) -> dict[str, float]:
        return {"solar_kwh": round(self.solar_kwh, 4), "grid_kwh": round(self.grid_kwh, 4), "solar_value": round(self.solar_value, 5)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> Pools:
        data = data or {}
        return cls(float(data.get("solar_kwh", 0.0)), float(data.get("grid_kwh", 0.0)), float(data.get("solar_value", 0.0)))


RECORD_FIELDS: Final = (
    "start",
    "minutes",
    "import_kwh",
    "export_kwh",
    "charge_kwh",
    "discharge_kwh",
    "solar_kwh",
    "house_kwh",
    "market",
    "buy",
    "sell",
    "complete",
    "cost",
    "cost_no_battery",
    "cost_no_solar",
    "saldering",
    "saldering_no_battery",
    "import_no_battery_kwh",
    "export_no_battery_kwh",
    "solar_direct_kwh",
    "solar_via_battery",
    "solar_direct_value",
    "solar_export_value",
    "solar_bonus_value",
    "fixed",
    "plan_action",
    "plan_cost",
    "soc",
    "excluded_kwh",
    "vacation",
    "ahead_load_kwh",
    "ahead_excluded_kwh",
    "ahead_solar_kwh",
    "ahead_import_kwh",
    "ahead_export_kwh",
    "ahead_cost",
    "ahead_soc",
    "battery_source",
    "estimated",
    "corrected_at",
    "status",
    "solar_ext_kwh",
    "measured_share",
    "price_source",
)
"""Fields of a stored quarter (and the CSV columns). ``plan_*``: the plan at the start of the quarter.
``soc``: state of charge at the end of the quarter (%, 0.8.2), for the panel's past.
``excluded_kwh`` (B41), ``vacation`` (B42). ``ahead_*``: the day-ahead plan (plan against reality, 0.8.21).
``battery_source``: ``counters`` (own energy counters) or ``meter``; ``estimated`` / ``corrected_at``: energy
of a filled counter gap was added afterwards (SPEC-tellers T3). ``status``: ``measured`` / ``estimated`` /
``missing`` (0.8.79); ``fill`` (method per flow), ``fill_kwh`` (kWh added per flow) and ``fill_causes``
(``p1``, ``set``, ``solar_counter``, ``ha_off``, ``price``) say how it was filled. Kept but not exported: ``pools`` (before the
quarter), ``stored_kwh``, ``daylight``, ``coverage``."""


def _r(value: float | None, digits: int = 4) -> float | None:
    return None if value is None else round(value, digits)


def evaluate(q: QuarterInput, tariffs: Tariffs, pools: Pools, days_in_month: int = 30) -> dict[str, Any]:
    """Costs of one quarter in the three situations. Updates ``pools`` in place."""
    imp, exp, chg, dis = q.import_kwh, q.export_kwh, q.charge_kwh, q.discharge_kwh
    n1 = imp - exp - chg + dis
    imp_nb, exp_nb = max(n1, 0.0), max(-n1, 0.0)
    house = None if q.solar_kwh is None else imp - exp + q.solar_kwh - chg + dis
    direct = None if q.solar_kwh is None else max(q.solar_kwh - exp_nb, 0.0)

    buy = sell = sal_part = None
    if q.market is not None:
        buy = tariffs.buy(q.market)
        sell, sal_part = tariffs.sell(q.market, q.start, q.daylight)

    # Pools: charged from solar = what would otherwise have been exported.
    from_solar_charge = min(chg, exp_nb)
    pools.solar_kwh += from_solar_charge
    pools.grid_kwh += chg - from_solar_charge
    if sell is not None:
        pools.solar_value += from_solar_charge * max(sell, 0.0)
    total = pools.solar_kwh + pools.grid_kwh
    from_solar = released = lost = 0.0
    if dis > 0 and total > 0:
        share = pools.solar_kwh / total
        from_solar = min(dis * share, pools.solar_kwh)
        released = pools.solar_value * (from_solar / pools.solar_kwh) if pools.solar_kwh > 0 else 0.0
        taken = min(dis, total)
        pools.solar_kwh -= from_solar
        pools.solar_value -= released
        pools.grid_kwh = max(pools.grid_kwh - (taken - from_solar), 0.0)
    if q.stored_kwh is not None:
        total = pools.solar_kwh + pools.grid_kwh
        if total > q.stored_kwh:
            scale = max(q.stored_kwh, 0.0) / total if total > 0 else 0.0
            lost = pools.solar_value * (1 - scale)  # conversion losses of stored solar
            pools.solar_kwh *= scale
            pools.grid_kwh *= scale
            pools.solar_value *= scale

    cost = cost_nb = cost_ns = sal = sal_nb = via = None
    sun_direct = sun_export = sun_bonus = None
    if buy is not None and sell is not None and sal_part is not None:
        cost = imp * buy - exp * sell
        cost_nb = imp_nb * buy - exp_nb * sell
        cost_ns = None if house is None else house * buy
        sal = exp * sal_part
        sal_nb = exp_nb * sal_part
        via = from_solar * buy - released - lost
        if direct is not None and q.market is not None:
            # OPDRACHT-besparing-zon: what the panels saved, split (Z0 − Z1 = direct + export).
            sun_direct = direct * buy
            sun_export = exp_nb * sell
            sun_bonus = exp_nb * tariffs.bonus(q.market, q.daylight)

    return {
        "start": q.start.isoformat(),
        "minutes": q.minutes,
        "import_kwh": _r(imp),
        "export_kwh": _r(exp),
        "charge_kwh": _r(chg),
        "discharge_kwh": _r(dis),
        "solar_kwh": _r(q.solar_kwh),
        "house_kwh": _r(house),
        "market": _r(q.market, 5),
        "buy": _r(buy, 5),
        "sell": _r(sell, 5),
        "complete": q.coverage >= COMPLETE_SHARE,
        "cost": _r(cost, 5),
        "cost_no_battery": _r(cost_nb, 5),
        "cost_no_solar": _r(cost_ns, 5),
        "saldering": _r(sal, 5),
        "saldering_no_battery": _r(sal_nb, 5),
        "import_no_battery_kwh": _r(imp_nb),
        "export_no_battery_kwh": _r(exp_nb),
        "solar_direct_kwh": _r(direct),
        "solar_via_battery": _r(via, 5),
        "solar_direct_value": _r(sun_direct, 5),
        "solar_export_value": _r(sun_export, 5),
        "solar_bonus_value": _r(sun_bonus, 5),
        "fixed": round(tariffs.fixed_month / days_in_month * q.minutes / 1440, 5),
        "plan_action": None,
        "plan_cost": None,
    }


# --- totals ---------------------------------------------------------------------------

SUM_FIELDS: Final = (
    "import_kwh",
    "export_kwh",
    "charge_kwh",
    "discharge_kwh",
    "import_no_battery_kwh",
    "export_no_battery_kwh",
    "fixed",
)
PRICED_FIELDS: Final = ("cost", "cost_no_battery", "saldering", "saldering_no_battery", "solar_via_battery", "buy")
SOLAR_FIELDS: Final = ("solar_kwh", "house_kwh", "solar_direct_kwh")
SOLAR_VALUE_FIELDS: Final = ("solar_direct_value", "solar_export_value", "solar_bonus_value")
"""€ per priced quarter with solar (OPDRACHT-besparing-zon); direct + export = Z0 − Z1."""


def add_to_day(day: dict[str, float], record: Mapping[str, Any]) -> None:
    """Add a quarter to a day total (a plain dict, as stored)."""
    day["quarters"] = day.get("quarters", 0) + 1
    status = quarter_status(record)
    if status == "missing":
        day["incomplete"] = day.get("incomplete", 0) + 1  # nothing to fill it with: the amounts are too low
    elif status == "estimated":
        day["estimated"] = day.get("estimated", 0) + 1
        for method in set((record.get("fill") or {}).values()):
            day[f"method_{method}"] = day.get(f"method_{method}", 0) + 1
        for cause in record.get("fill_causes") or ():
            day[f"cause_{cause}"] = day.get(f"cause_{cause}", 0) + 1
        for name, kwh in (record.get("fill_kwh") or {}).items():
            day[f"filled_{name}"] = day.get(f"filled_{name}", 0.0) + float(kwh or 0.0)
    if record.get("price_source") == "interpolated":
        day["price_interpolated"] = day.get("price_interpolated", 0) + 1
    for name in SUM_FIELDS:
        day[name] = day.get(name, 0.0) + float(record.get(name) or 0.0)
    if record.get("cost") is None:
        day["no_price"] = day.get("no_price", 0) + 1
    else:
        day["priced"] = day.get("priced", 0) + 1
        for name in PRICED_FIELDS:
            day[name] = day.get(name, 0.0) + float(record.get(name) or 0.0)
    if record.get("solar_kwh") is None:
        day["no_solar"] = day.get("no_solar", 0) + 1
    else:
        for name in SOLAR_FIELDS:
            day[name] = day.get(name, 0.0) + float(record.get(name) or 0.0)
        if record.get("cost_no_solar") is not None:
            day["cost_no_solar"] = day.get("cost_no_solar", 0.0) + float(record["cost_no_solar"])
            day["solar_priced"] = day.get("solar_priced", 0) + 1
            for name in SOLAR_VALUE_FIELDS:
                day[name] = day.get(name, 0.0) + float(record.get(name) or 0.0)
    plan_check.add_to_day(day, record)
    for key in list(day):
        if isinstance(day[key], float):
            day[key] = round(day[key], 5)


def quarter_status(record: Mapping[str, Any]) -> str:
    """``measured``, ``estimated`` (filled, OPDRACHT-onvolledige-kwartieren) or ``missing``.

    Quarters from before 0.8.79 have no status: incomplete ones count as missing, quarters with
    energy from a filled counter gap (T3) as estimated.
    """
    status = record.get("status")
    if isinstance(status, str):
        return status
    if not record.get("complete", True):
        return "missing"
    return "estimated" if record.get("estimated") else "measured"


@dataclass(slots=True)
class Summary:
    """Costs and savings over a period, derived from day totals."""

    days: int = 0
    totals: dict[str, float] = field(default_factory=dict)
    saldering_correction: float = 0.0
    saldering_correction_no_battery: float = 0.0

    @property
    def cost(self) -> float | None:
        if not self.totals.get("priced"):
            return None
        return self.totals.get("cost", 0.0) + self.saldering_correction

    @property
    def cost_no_battery(self) -> float | None:
        if not self.totals.get("priced"):
            return None
        return self.totals.get("cost_no_battery", 0.0) + self.saldering_correction_no_battery

    @property
    def solar_known(self) -> bool:
        """Every priced quarter has a solar value (the no-solar cost is complete)."""
        return bool(self.totals.get("priced")) and self.totals.get("solar_priced", 0) == self.totals.get("priced", 0)

    @property
    def savings_battery(self) -> float | None:
        cost, cost_nb = self.cost, self.cost_no_battery
        return None if cost is None or cost_nb is None else cost_nb - cost

    @property
    def savings_solar(self) -> float | None:
        cost_nb = self.cost_no_battery
        if cost_nb is None or not self.solar_known:
            return None
        return self.totals.get("cost_no_solar", 0.0) - cost_nb

    @property
    def self_consumption(self) -> float | None:
        """Share of the solar the house used itself (directly or later from the battery)."""
        solar = self.totals.get("solar_kwh")
        if not solar or solar <= 0 or self.totals.get("no_solar"):
            return None
        return max(min((solar - self.totals.get("export_kwh", 0.0)) / solar, 1.0), 0.0)

    @property
    def savings(self) -> float | None:
        """Solar + battery when solar is known; otherwise the battery alone."""
        battery = self.savings_battery
        if battery is None:
            return None
        solar = self.savings_solar
        return battery + (solar or 0.0)

    def as_dict(self) -> dict[str, Any]:
        t = self.totals
        battery = self.savings_battery
        via = t.get("solar_via_battery") if t.get("priced") else None
        house = t.get("house_kwh")
        cost = self.cost
        priced = t.get("priced", 0)

        def r(v: float | None, d: int = 2) -> float | None:
            return None if v is None else round(v, d)

        return {
            "cost": r(cost),
            "cost_no_battery": r(self.cost_no_battery),
            "cost_no_solar": r(t.get("cost_no_solar")) if self.solar_known else None,
            "savings": r(self.savings),
            "savings_solar": r(self.savings_solar),
            "savings_battery": r(battery),
            "savings_solar_via_battery": r(via),
            "savings_trade": r(None if battery is None or via is None else battery - via),
            "savings_total": r(self.savings if self.solar_known else None),
            "solar_direct_value": r(t.get("solar_direct_value")) if self.solar_known else None,
            "solar_export_value": r(t.get("solar_export_value")) if self.solar_known else None,
            "solar_bonus_value": r(t.get("solar_bonus_value")) if self.solar_known else None,
            "solar_direct_kwh": r(t.get("solar_direct_kwh"), 3),
            "self_consumption": r(self.self_consumption, 3),
            "includes_solar": self.solar_known,
            "fixed": r(t.get("fixed", 0.0)),
            "cost_incl_fixed": r(None if cost is None else cost + t.get("fixed", 0.0)),
            "saldering_correction": r(self.saldering_correction),
            "import_kwh": r(t.get("import_kwh", 0.0), 3),
            "export_kwh": r(t.get("export_kwh", 0.0), 3),
            "charge_kwh": r(t.get("charge_kwh", 0.0), 3),
            "discharge_kwh": r(t.get("discharge_kwh", 0.0), 3),
            "solar_kwh": r(t.get("solar_kwh"), 3),
            "house_kwh": r(house, 3),
            "effective_price": r(cost / house, 4) if cost is not None and house and self.solar_known else None,
            "mean_buy_price": r(t["buy"] / priced, 4) if priced and "buy" in t else None,
            "quarters": int(t.get("quarters", 0)),
            "incomplete_quarters": int(t.get("incomplete", 0)),
            "missing_quarters": int(t.get("incomplete", 0)),
            "estimated_quarters": int(t.get("estimated", 0)),
            "price_interpolated_quarters": int(t.get("price_interpolated", 0)),
            "quarters_without_price": int(t.get("no_price", 0)),
        }


def _sum(days: Iterable[Mapping[str, float]]) -> dict[str, float]:
    out: dict[str, float] = {}
    for day in days:
        for key, value in day.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                out[key] = out.get(key, 0) + value
    return out


def summarize(days: Mapping[str, Mapping[str, float]], first: date, last: date, tariffs: Tariffs) -> Summary:
    """Summary of the days ``first``..``last`` (inclusive, local dates as ISO keys).

    The yearly net-metering correction is applied for every calendar year whose
    whole range lies inside the period (in practice: the year summary).
    """
    selected = {k: v for k, v in days.items() if first.isoformat() <= k <= last.isoformat()}
    summary = Summary(days=len(selected), totals=_sum(selected.values()))
    if first.month == 1 and first.day == 1 and first.year == last.year and first < tariffs.saldering_until:
        summary.saldering_correction = saldering_correction(summary.totals, "")
        summary.saldering_correction_no_battery = saldering_correction(summary.totals, "_no_battery")
    return summary


def saldering_correction(totals: Mapping[str, float], suffix: str) -> float:
    """Extra cost because export above import is not netted (share of the netting part)."""
    imp = totals.get(f"import{suffix}_kwh", 0.0)
    exp = totals.get(f"export{suffix}_kwh", 0.0)
    part = totals.get(f"saldering{suffix}", 0.0)
    if exp <= imp or exp <= 0:
        return 0.0
    return (exp - imp) / exp * part


# --- export ---------------------------------------------------------------------------------


def to_csv(records: Iterable[Mapping[str, Any]]) -> str:
    """CSV (comma, decimal point) with the fields of RECORD_FIELDS."""
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(RECORD_FIELDS), extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for record in records:
        writer.writerow({k: ("" if record.get(k) is None else record.get(k)) for k in RECORD_FIELDS})
    return out.getvalue()
