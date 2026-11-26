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
    no_prices,
    solar_per_quarter,
)
from .core.load_profile import WEEKEND, WORKDAY, LoadProfile
from .core.planner import Action, PlannerSettings
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
"""First fill of the profile from the cost log (when the profile is empty)."""
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
        self.runtime = runtime
        self.price_entity: str | None = options.get(CONF_PRICE_ENTITY)
        self.solar_entities = solar_entities(options.get(CONF_SOLAR_FORECAST))
        self.settings = planner_settings(options)
        self.buffer = float(options.get(CONF_PLAN_BUFFER, 0.0))
        self.profile = LoadProfile()
        self.hour: dict[str, Any] = {}
        """The hour being collected for the profile: ``start`` (ISO local), ``kwh``, ``quarters``."""
        self.outcome: PlanOutcome | None = None
        self.inputs: dict[str, Any] = {}
        self.snapshots: deque[dict[str, Any]] = deque(maxlen=SNAPSHOTS)
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
        if self.profile.mean_count == 0:
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

    # --- triggers (§5) -------------------------------------------------------------

    @callback
    def _on_first(self, _now: datetime) -> None:
        self.async_request()

    @callback
    def _on_minute(self, now: datetime) -> None:
        waiting = self.outcome is None or self.outcome.state == PlanState.NO_PRICES
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

    async def async_calculate(self) -> PlanOutcome | None:
        assert self.price_entity is not None
        now = dt_util.utcnow()
        tz = dt_util.get_default_time_zone()
        state = self.hass.states.get(self.price_entity)
        prices = market_slots(state.attributes) if state is not None else []
        self._check_format(state, bool(prices))
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

        def buy(start: datetime, market: float) -> float:
            return tariffs.tariffs_for(dt_util.as_local(start).date()).buy(market)

        def sell(start: datetime, market: float, daylight: bool) -> float:
            return tariffs.tariffs_for(dt_util.as_local(start).date()).sell(market, start, daylight)[0]

        slots = build_horizon(markets, now, buy=buy, sell=sell, load=self._load, solar=solar_fn, daylight=lambda t: is_up(self.hass, t))
        prev_action = previous.action if previous is not None and previous.slots else Action.DELIVER
        began = time.perf_counter()
        outcome = await self.hass.async_add_executor_job(make_plan, slots, battery, now, self.settings, prev_action)
        outcome.duration_s = time.perf_counter() - began
        self._publish(
            outcome,
            {
                "price_entity": self.price_entity,
                "price_slots": len(prices),
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
            LOGGER.debug("Consumption profile filled from %s cost quarters", len(records))
            self._store.async_delay_save(self._data, 10)

    def _data(self) -> dict[str, Any]:
        return {"profile": self.profile.as_dict(), "hour": self.hour}

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
