"""The planner in Home Assistant (SPEC-planner §2, §4, §5), shadow first.

Collects the inputs (Nord Pool prices with the tariffs, Solcast, the learned
consumption, the battery), runs the planner and keeps the outcome for the
entities and the diagnostics. In this version the plan is only calculated and
shown; the mode *Dynamic Forecasting* that carries it out follows.

* Recalculated every quarter at :10 s, when the prices change (tomorrow known),
  after a restart and, while there is no price for now, every minute (§5).
* Consumption is learned per hour from the cost log (house = import − export +
  solar − charged + delivered), in ZEPHYR's own storage (§2.3).
* The cost log gets the plan's action and expected cost per quarter (B38).
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_call_later, async_track_state_change_event, async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.sun import is_up
from homeassistant.util import dt as dt_util

from .const import (
    CONF_PLAN_ALLOW_EXPORT,
    CONF_PLAN_BUFFER,
    CONF_PLAN_LOAD_MARGIN,
    CONF_PLAN_WEAR_COST,
    CONF_PRICE_ENTITY,
    CONF_SOLAR_FORECAST,
    DEFAULT_PLAN_WEAR_COST,
    DOMAIN,
    LOGGER,
)
from .core.forecast_plan import (
    DEFAULT_LOAD_KWH_PER_HOUR,
    QUARTER,
    BatteryInput,
    PlanOutcome,
    PlanState,
    build_horizon,
    horizon_markets,
    make_plan,
    market_slots,
    merge_reserve,
    no_prices,
    price_at,
    quarter_floor,
    reason,
    remember,
    solar_per_quarter,
)
from .core.load_profile import WEEKEND, WORKDAY, HourEnergy, LoadProfile, profile_from_history
from .core.plan_view import plan_view
from .core.planner import Action, PlannerSettings
from .core.price_window import PriceSlot
from .core.solar_history import parse_detailed_forecast

if TYPE_CHECKING:
    from . import ZephyrRuntime

STORAGE_VERSION = 1
SNAPSHOT_EVERY = timedelta(minutes=15)
SNAPSHOTS = 120
"""≥ 24 hours of snapshots every 15 minutes (§4)."""
FIRST_RUN_DELAY = 5.0
"""s after startup, so the sets have reported."""
LEARN_FROM_DAYS = 28
"""First fill of the profile: this many days of the recorder's hourly statistics, else of the cost log."""
FILL_BELOW_HOURS = 48
"""Fill from the recorder while fewer hours than this have been learned."""
MIN_FILL_HOURS = 24
"""A fill from the recorder replaces the profile only with at least this many hours."""
ISSUE_PRICE_FORMAT = "price_format"


def planner_settings(options: Mapping[str, Any]) -> PlannerSettings:
    return PlannerSettings(
        wear_cost=float(options.get(CONF_PLAN_WEAR_COST, DEFAULT_PLAN_WEAR_COST)),
        allow_export=bool(options.get(CONF_PLAN_ALLOW_EXPORT, False)),
        load_margin=float(options.get(CONF_PLAN_LOAD_MARGIN, 0.0)) / 100,
    )


def day_type(local: datetime) -> str:
    return WEEKEND if local.weekday() >= 5 else WORKDAY


def solar_entities(entity: str | None) -> list[str]:
    """The chosen forecast sensor and its Solcast sibling (today ↔ tomorrow), so the horizon has both days."""
    if not entity:
        return []
    out = [entity]
    for a, b in (("forecast_tomorrow", "forecast_today"), ("forecast_today", "forecast_tomorrow")):
        if entity.endswith(a):
            out.append(entity[: -len(a)] + b)
    return out


def house_kwh(record: Mapping[str, Any], solar_known: bool) -> float | None:
    """House consumption of a closed cost quarter; without a solar counter only when there is no solar at all."""
    value = record.get("house_kwh")
    if value is not None:
        return float(value)
    if solar_known:
        return None
    try:
        return float(record["import_kwh"]) - float(record["export_kwh"]) - float(record["charge_kwh"]) + float(record["discharge_kwh"])
    except (KeyError, TypeError, ValueError):
        return None


class PlanRunner:
    def __init__(self, hass: HomeAssistant, entry_id: str, options: Mapping[str, Any], runtime: ZephyrRuntime) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.runtime = runtime
        self.profile_source = "none"
        self.price_entity: str | None = options.get(CONF_PRICE_ENTITY)
        self.solar_entities = solar_entities(options.get(CONF_SOLAR_FORECAST))
        self.settings = planner_settings(options)
        self.buffer = float(options.get(CONF_PLAN_BUFFER, 0.0))
        self.profile = LoadProfile()
        self.hour: dict[str, Any] = {}
        """The hour being collected for the profile: ``start`` (ISO local), ``kwh``, ``quarters``."""
        self.reserve: list[PriceSlot] = []
        """Saved prices (§2.1): used after midnight when the source has none for now yet."""
        self.outcome: PlanOutcome | None = None
        self.inputs: dict[str, Any] = {}
        self.snapshots: deque[dict[str, Any]] = deque(maxlen=SNAPSHOTS)
        self.known_at: dict[date, datetime] = {}
        """Day → when its prices were first seen (the panel shows "known since hh:mm")."""
        self.by_quarter: dict[str, tuple[str, float]] = {}
        """Quarter start (ISO UTC) → (action, expected cost) of the first plan in that quarter."""
        self._listeners: list[Callable[[], None]] = []
        self._task: asyncio.Task[None] | None = None
        self._again = False
        self._last_snapshot: datetime | None = None
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.planner")

    @property
    def enabled(self) -> bool:
        return bool(self.price_entity)

    # --- lifecycle --------------------------------------------------------------

    async def async_start(self) -> Callable[[], None]:
        stored = await self._store.async_load() or {}
        self.profile = LoadProfile.from_dict(stored.get("profile"))
        self.hour = dict(stored.get("hour") or {})
        self.reserve = _slots_from_store(stored.get("reserve"))
        self.profile_source = str(stored.get("profile_source") or ("stored" if self.profile.mean_count else "none"))
        if self.profile.mean_count < FILL_BELOW_HOURS:
            try:
                filled = await self._learn_from_recorder()
            except Exception:  # the recorder is a nice-to-have: never block the planner
                LOGGER.exception("Consumption profile from the recorder failed")
                filled = 0
            if filled < MIN_FILL_HOURS and self.profile.mean_count == 0:
                await self._learn_from_history()
        assert self.price_entity is not None
        unsubs: list[Callable[[], None]] = [
            async_track_time_change(self.hass, self._on_minute, second=10),
            async_track_state_change_event(self.hass, [self.price_entity], self._on_price_change),
            async_call_later(self.hass, FIRST_RUN_DELAY, self._on_first),
        ]

        def stop() -> None:
            for unsub in unsubs:
                unsub()
            if self._task is not None and not self._task.done():
                self._task.cancel()
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_PRICE_FORMAT)

        return stop

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def action_at(self, moment: datetime) -> Action | None:
        """The plan's action for ``moment``: N without prices, None without a plan for that quarter."""
        outcome = self.outcome
        if outcome is None:
            return None
        if outcome.state == PlanState.NO_PRICES:
            return Action.DELIVER
        for slot, action in zip(outcome.slots, outcome.plan.actions, strict=False):
            if slot.start <= moment < slot.start + QUARTER:
                return action
        return None

    # --- triggers (§5) -------------------------------------------------------------

    @callback
    def _on_first(self, _now: datetime) -> None:
        self.async_request()

    @callback
    def _on_minute(self, now: datetime) -> None:
        waiting = self.outcome is None or self.outcome.state in (PlanState.NO_PRICES, PlanState.PRICE_RESERVE)
        if waiting or dt_util.as_utc(now).minute % 15 == 0:
            self.async_request()

    @callback
    def _on_price_change(self, event: Event[EventStateChangedData]) -> None:
        old, new = event.data["old_state"], event.data["new_state"]
        if _price_key(old) != _price_key(new):
            self.async_request()

    @callback
    def async_request(self) -> None:
        """Recalculate now (once more after the running calculation if one is busy)."""
        if self._task is not None and not self._task.done():
            self._again = True
            return
        self._task = self.hass.async_create_task(self._run(), "zephyr: plan")

    async def _run(self) -> None:
        while True:
            self._again = False
            try:
                await self.async_calculate()
            except Exception:
                LOGGER.exception("Planner failed")
            if not self._again:
                return

    # --- calculating ---------------------------------------------------------------

    def _battery(self) -> BatteryInput | None:
        totals = self.runtime.totals()
        control = self.runtime.control
        if totals.capacity_kwh is None or totals.soc is None or control is None or totals.sets_online == 0:
            return None
        settings = control.engine.settings
        charge_kw, deliver_kw = control.power_limits_kw()
        return BatteryInput(
            capacity_kwh=totals.capacity_kwh,
            soc=totals.soc,
            min_soc=settings.min_soc,
            max_soc=settings.max_soc,
            charge_kw=charge_kw,
            deliver_kw=deliver_kw,
            buffer=self.buffer,
        )

    def _solar(self) -> tuple[Callable[[datetime], float], str]:
        periods = []
        for entity in self.solar_entities:
            state = self.hass.states.get(entity)
            if state is not None:
                periods += parse_detailed_forecast(state.attributes.get("detailedForecast"))
        forecast = solar_per_quarter(periods)
        if forecast:
            return lambda t: forecast.get(t, 0.0), "forecast"
        solar = self.runtime.solar
        if solar is not None and solar.energy_entity:
            yesterday: dict[date, dict[int, float]] = {}

            def from_yesterday(t: datetime) -> float:
                local = dt_util.as_local(t)
                day = local.date() - timedelta(days=1)
                if day not in yesterday:
                    yesterday[day] = solar.history.production_per_hour(day.isoformat())
                return yesterday[day].get(local.hour, 0.0) * QUARTER.total_seconds() / 3600

            return from_yesterday, "yesterday"
        return lambda t: 0.0, "none"

    def _load(self, start: datetime, ahead: float) -> float:
        hours = QUARTER.total_seconds() / 3600
        if self.profile.mean_count == 0:
            return DEFAULT_LOAD_KWH_PER_HOUR * hours
        local = dt_util.as_local(start)
        return self.profile.forecast(day_type(local), local.hour, ahead) * hours

    def _buy(self, start: datetime, market: float) -> float:
        tariffs = self.runtime.tariffs
        assert tariffs is not None
        return tariffs.tariffs_for(dt_util.as_local(start).date()).buy(market)

    def _sell(self, start: datetime, market: float, daylight: bool) -> float:
        tariffs = self.runtime.tariffs
        assert tariffs is not None
        return tariffs.tariffs_for(dt_util.as_local(start).date()).sell(market, start, daylight)[0]

    def _daylight(self, moment: datetime) -> bool:
        return is_up(self.hass, moment)

    def _note_known(self, source: list[PriceSlot], now: datetime) -> None:
        for day in {dt_util.as_local(s.start).date() for s in source}:
            self.known_at.setdefault(day, now)
        for day in sorted(self.known_at)[:-3]:
            del self.known_at[day]

    def view(self) -> dict[str, Any]:
        """Prices and plan of today and tomorrow for the panel (SPEC-ui §3.2)."""
        assert self.price_entity is not None
        now = dt_util.utcnow()
        tz = dt_util.get_default_time_zone()
        state = self.hass.states.get(self.price_entity)
        source = market_slots(state.attributes) if state is not None else []
        prices = merge_reserve(source, self.reserve)
        outcome = self.outcome
        tomorrow = dt_util.as_local(now).date() + timedelta(days=1)
        why = None
        if outcome is not None:
            why = {"nl": reason(outcome, "nl", tz), "en": reason(outcome, "en", tz)}
        return plan_view(
            outcome,
            prices,
            now,
            tz,
            buy=self._buy,
            sell=self._sell,
            daylight=self._daylight,
            tomorrow_known_at=self.known_at.get(tomorrow),
            reason=why,
        )

    async def async_calculate(self) -> PlanOutcome | None:
        assert self.price_entity is not None
        now = dt_util.utcnow()
        tz = dt_util.get_default_time_zone()
        state = self.hass.states.get(self.price_entity)
        source = market_slots(state.attributes) if state is not None else []
        self._check_format(state, bool(source))
        self._note_known(source, now)
        reserve = remember(self.reserve, source, now)
        if [(s.start, s.price) for s in reserve] != [(s.start, s.price) for s in self.reserve]:
            self.reserve = reserve
            self._store.async_delay_save(self._data, 10)
        prices = merge_reserve(source, self.reserve)
        from_reserve = price_at(source, quarter_floor(now)) is None and price_at(prices, quarter_floor(now)) is not None
        markets = horizon_markets(prices, now, tz)
        previous = self.outcome
        if not markets:
            since = previous.no_prices_since if previous is not None and previous.state == PlanState.NO_PRICES else None
            self._publish(no_prices(now, since), {"price_entity": self.price_entity, "price_slots": len(prices)})
            return self.outcome
        battery = self._battery()
        if battery is None:
            return previous  # no battery data yet: try again next minute
        tariffs = self.runtime.tariffs
        assert tariffs is not None
        solar_fn, solar_source = self._solar()
        slots = build_horizon(markets, now, buy=self._buy, sell=self._sell, load=self._load, solar=solar_fn, daylight=self._daylight)
        prev_action = previous.action if previous is not None and previous.slots else Action.DELIVER
        began = time.perf_counter()
        outcome = await self.hass.async_add_executor_job(make_plan, slots, battery, now, self.settings, prev_action)
        outcome.duration_s = time.perf_counter() - began
        if from_reserve:
            outcome.state = PlanState.PRICE_RESERVE
        self._publish(
            outcome,
            {
                "price_entity": self.price_entity,
                "price_slots": len(source),
                "reserve_slots": len(self.reserve),
                "price_source": "reserve" if from_reserve else "source",
                "solar_source": solar_source,
                "solar_entities": self.solar_entities,
                "tariffs": tariffs.tariffs_for(dt_util.as_local(now).date()).source,
                "battery": {
                    "capacity_kwh": battery.capacity_kwh,
                    "soc": battery.soc,
                    "min_soc": battery.min_soc,
                    "max_soc": battery.max_soc,
                    "buffer": battery.buffer,
                    "usable_kwh": round(battery.battery().capacity_kwh, 3),
                    "energy_now_kwh": round(battery.energy_now, 3),
                    "charge_kw": battery.charge_kw,
                    "deliver_kw": battery.deliver_kw,
                    "eta_in": battery.eta_in,
                    "eta_out": battery.eta_out,
                },
                "profile_hours_learned": self.profile.mean_count,
                "profile_source": self.profile_source,
                "previous_action": prev_action.value,
            },
        )
        return outcome

    def _check_format(self, state: State | None, parsed: bool) -> None:
        """A price sensor with a value but no readable slots is an error, not an empty list (§2.1, PT5)."""
        has_value = state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, "")
        if has_value and not parsed:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                ISSUE_PRICE_FORMAT,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_PRICE_FORMAT,
                translation_placeholders={"entity": str(self.price_entity)},
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_PRICE_FORMAT)

    def _publish(self, outcome: PlanOutcome, inputs: dict[str, Any]) -> None:
        self.outcome = outcome
        self.inputs = inputs
        if outcome.slots:
            first = outcome.slots[0].start.isoformat()
            if first not in self.by_quarter:
                self.by_quarter[first] = (outcome.action.value, round(outcome.plan.steps[0].cost, 5))
                for key in sorted(self.by_quarter)[:-8]:
                    del self.by_quarter[key]
        if self._last_snapshot is None or outcome.calculated_at - self._last_snapshot >= SNAPSHOT_EVERY:
            self._last_snapshot = outcome.calculated_at
            self.snapshots.append(
                {
                    "time": outcome.calculated_at.isoformat(timespec="seconds"),
                    "state": outcome.state,
                    "action": outcome.action.value,
                    "price_now": round(outcome.slots[0].buy, 4) if outcome.slots else None,
                    "soc": None if outcome.battery is None else outcome.battery.soc,
                    "grid_charging": outcome.action is Action.CHARGE,
                    "slots": len(outcome.slots),
                    "indicative_from": None if outcome.indicative_from is None else outcome.indicative_from.isoformat(),
                    "price_slots": inputs.get("price_slots"),
                }
            )
        for listener in list(self._listeners):
            listener()

    # --- the cost log and learning ------------------------------------------------------

    def quarter_closed(self, start: datetime, record: Mapping[str, Any], solar_known: bool) -> dict[str, Any]:
        """Learn from a closed cost quarter; return the plan fields for its record (B38)."""
        self._learn_quarter(start, record, solar_known)
        self._store.async_delay_save(self._data, 30)
        planned = self.by_quarter.get(dt_util.as_utc(start).isoformat())
        if planned is None:
            return {}
        return {"plan_action": planned[0], "plan_cost": planned[1]}

    def _learn_quarter(self, start: datetime, record: Mapping[str, Any], solar_known: bool) -> None:
        local = dt_util.as_local(start)
        hour_start = local.replace(minute=0, second=0, microsecond=0).isoformat()
        if self.hour.get("start") != hour_start:
            self.hour = {"start": hour_start, "kwh": 0.0, "quarters": 0}
        kwh = house_kwh(record, solar_known) if record.get("complete") else None
        if kwh is not None:
            self.hour["kwh"] += max(kwh, 0.0)
            self.hour["quarters"] += 1
        if local.minute == 45:
            if self.hour["quarters"] == 4:
                self.profile.learn(day_type(local), local.hour, self.hour["kwh"])
            self.hour = {}

    def _battery_entity(self) -> str:
        registry = er.async_get(self.hass)
        found = registry.async_get_entity_id("sensor", DOMAIN, f"{self.entry_id}_power")
        return found or "sensor.zephyr_power"

    async def _learn_from_recorder(self) -> int:
        """First fill from the recorder's hourly statistics (§2.3): house = import − export + solar − battery.

        Uses the cost log's DSMR counters, the solar counter and the mean of ZEPHYR's battery
        power. Only complete hours (every counter and the battery known) count. Returns the
        number of hours learned; the profile is replaced only from ``MIN_FILL_HOURS`` on.
        """
        costs = self.runtime.costs
        if costs is None or not costs.import_counters or "recorder" not in self.hass.config.components:
            return 0
        battery = self._battery_entity()
        solar = costs.solar_entity
        ids = [*costs.import_counters, *costs.export_counters, battery, *([solar] if solar else [])]
        end = dt_util.now().replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(days=LEARN_FROM_DAYS)
        stats = await hourly_statistics(self.hass, start, end, ids)

        def by_hour(entity: str, field: str) -> dict[float, float]:
            out: dict[float, float] = {}
            for row in stats.get(entity, []):
                value = row.get(field)
                begin = row.get("start")
                if value is None or begin is None:
                    continue
                key = begin.timestamp() if isinstance(begin, datetime) else float(begin)
                out[key] = float(value)
            return out

        imports = [by_hour(e, "change") for e in costs.import_counters]
        exports = [by_hour(e, "change") for e in costs.export_counters]
        solar_rows = by_hour(solar, "change") if solar else None
        battery_rows = by_hour(battery, "mean")
        hours: list[HourEnergy] = []
        for key, mean_w in battery_rows.items():
            parts = [rows.get(key) for rows in imports + exports]
            sun = solar_rows.get(key) if solar_rows is not None else 0.0
            if any(p is None for p in parts) or sun is None:
                continue
            n = len(imports)
            hours.append(
                HourEnergy(
                    start=dt_util.as_local(dt_util.utc_from_timestamp(key)),
                    import_kwh=sum(p for p in parts[:n] if p is not None),
                    export_kwh=sum(p for p in parts[n:] if p is not None),
                    solar_kwh=sun,
                    battery_kwh=mean_w / 1000,
                )
            )
        if len(hours) < MIN_FILL_HOURS:
            LOGGER.debug("Recorder gave %s complete hours for the consumption profile: too few", len(hours))
            return len(hours)
        self.profile = profile_from_history(hours)
        self.hour = {}
        self.profile_source = f"recorder ({len(hours)} h)"
        LOGGER.debug("Consumption profile filled from %s recorder hours", len(hours))
        self._store.async_delay_save(self._data, 10)
        return len(hours)

    async def _learn_from_history(self) -> None:
        costs = self.runtime.costs
        if costs is None:
            return
        today = dt_util.now().date()
        records = await costs.async_records(today - timedelta(days=LEARN_FROM_DAYS), today)
        solar_known = costs.solar_entity is not None
        for record in records:
            self._learn_quarter(datetime.fromisoformat(record["start"]), record, solar_known)
        if records:
            self.profile_source = "cost log"
            LOGGER.debug("Consumption profile filled from %s cost quarters", len(records))
            self._store.async_delay_save(self._data, 10)

    def _data(self) -> dict[str, Any]:
        return {
            "profile": self.profile.as_dict(),
            "hour": self.hour,
            "profile_source": self.profile_source,
            "reserve": [[s.start.isoformat(), s.end.isoformat(), s.price] for s in self.reserve],
        }

    def diagnostics(self) -> dict[str, Any]:
        outcome = self.outcome
        return {
            "settings": {
                "wear_cost": self.settings.wear_cost,
                "allow_export": self.settings.allow_export,
                "load_margin": self.settings.load_margin,
                "buffer": self.buffer,
                "steps": self.settings.steps,
            },
            "inputs": self.inputs,
            "outcome": None if outcome is None else outcome.summary(),
            "blocks": [] if outcome is None else [b.as_dict() for b in outcome.blocks],
            "timeline": [] if outcome is None else outcome.timeline(),
            "snapshots": list(self.snapshots),
            "profile": self.profile.as_dict(),
            "planned_quarters": self.by_quarter,
        }


def _price_key(state: State | None) -> tuple[Any, ...]:
    """What makes new prices: the number of slots and the first start of today and tomorrow."""
    if state is None:
        return ()
    key: list[Any] = [state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN)]
    for name in ("raw_today", "raw_tomorrow"):
        items = state.attributes.get(name) or []
        first = items[0].get("start") if items and isinstance(items[0], Mapping) else None
        key += [len(items), str(first)]
    return tuple(key)


async def hourly_statistics(hass: HomeAssistant, start: datetime, end: datetime, ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    """Hourly statistics (change for counters, mean for power) from the recorder."""
    from homeassistant.components.recorder.statistics import statistics_during_period
    from homeassistant.helpers.recorder import get_instance

    result = await get_instance(hass).async_add_executor_job(
        statistics_during_period,
        hass,
        start,
        end,
        set(ids),
        "hour",
        {"energy": "kWh", "power": "W"},
        {"change", "mean"},
    )
    return {key: [dict(row) for row in rows] for key, rows in result.items()}


def _slots_from_store(data: Any) -> list[PriceSlot]:
    out: list[PriceSlot] = []
    for item in data or []:
        try:
            start, end, price = item
            out.append(PriceSlot(datetime.fromisoformat(start), datetime.fromisoformat(end), float(price)))
        except (TypeError, ValueError):
            continue
    return out
