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
from functools import partial
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
    CONF_EXCLUDED_CLIMATE,
    CONF_EXCLUDED_ENERGY,
    CONF_EXCLUDED_MODES,
    CONF_PLAN_ALLOW_EXPORT,
    CONF_PLAN_BUFFER,
    CONF_PLAN_GRID_CHARGE_COST,
    CONF_PLAN_LOAD_MARGIN,
    CONF_PLAN_WEAR_COST,
    CONF_PRICE_ENTITY,
    CONF_SOLAR_FORECAST,
    DEFAULT_EXCLUDED_MODES,
    DEFAULT_PLAN_GRID_CHARGE_COST,
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
from .core.load_profile import WEEKEND, WORKDAY, HourEnergy, LoadProfile, blocked_share, profile_from_history
from .core.plan_view import local_midnight, plan_view
from .core.planner import Action, PlannerSettings
from .core.price_window import PriceSlot
from .core.solar_history import parse_detailed_forecast
from .core.vacation import base_load

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
MIN_VACATION_COUNT = 1
"""Hours of vacation use per day type and hour before the planner trusts them over the standby use."""
"""Fill from the recorder while fewer hours than this have been learned."""
MIN_FILL_HOURS = 24
"""A fill from the recorder replaces the profile only with at least this many hours."""
ISSUE_PRICE_FORMAT = "price_format"


def planner_settings(options: Mapping[str, Any]) -> PlannerSettings:
    return PlannerSettings(
        wear_cost=float(options.get(CONF_PLAN_WEAR_COST, DEFAULT_PLAN_WEAR_COST)),
        grid_charge_cost=float(options.get(CONF_PLAN_GRID_CHARGE_COST, DEFAULT_PLAN_GRID_CHARGE_COST)),
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
        self.excluded_entity: str | None = options.get(CONF_EXCLUDED_ENERGY)
        """B41: energy counter of the load the battery may not feed (the air conditioner)."""
        self.excluded_climate: str | None = options.get(CONF_EXCLUDED_CLIMATE) if self.excluded_entity else None
        self.excluded_modes: list[str] = list(options.get(CONF_EXCLUDED_MODES, DEFAULT_EXCLUDED_MODES))
        self.excluded_profile = LoadProfile()
        """That load's use per hour while excluded; the house profile is without it."""
        self.vacation_profile = LoadProfile()
        """B42: use per hour while on vacation (kept apart from the normal profile)."""
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

    def apply_options(self, options: Mapping[str, Any]) -> None:
        """Planner settings changed without a reload (UI-7): plan again with them."""
        self.settings = planner_settings(options)
        self.buffer = float(options.get(CONF_PLAN_BUFFER, 0.0))
        self.async_request()

    async def async_start(self) -> Callable[[], None]:
        stored = await self._store.async_load() or {}
        self.profile = LoadProfile.from_dict(stored.get("profile"))
        self.hour = dict(stored.get("hour") or {})
        self.reserve = _slots_from_store(stored.get("reserve"))
        self.profile_source = str(stored.get("profile_source") or ("stored" if self.profile.mean_count else "none"))
        self.excluded_profile = LoadProfile.from_dict(stored.get("excluded_profile"))
        self.vacation_profile = LoadProfile.from_dict(stored.get("vacation_profile"))
        # B41: a profile learned with another (or no) excluded load mixes it in: fill again.
        changed = stored.get("profile", None) is not None and stored.get("excluded_entity") != self.excluded_entity
        if changed:
            LOGGER.debug(
                "Excluded load changed (%s → %s): consumption profile filled again", stored.get("excluded_entity"), self.excluded_entity
            )
            self.excluded_profile = LoadProfile()
        if self.profile.mean_count < FILL_BELOW_HOURS or changed:
            await self._fill_profile()
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

    async def _fill_profile(self) -> None:
        """First fill (§2.3): the recorder, else the cost log if the profile is still empty."""
        try:
            filled = await self._learn_from_recorder()
        except Exception:  # the recorder is a nice-to-have: never block the planner
            LOGGER.exception("Consumption profile from the recorder failed")
            filled = 0
        # The cost log before B41 has no use of the excluded load: with a changed load the
        # old profile stays until the recorder (or the live hours) give a better one.
        if filled < MIN_FILL_HOURS and self.profile.mean_count == 0:
            await self._learn_from_history()
        self._store.async_delay_save(self._data, 10)

    async def async_reset_profile(self, refill: bool = True) -> dict[str, Any]:
        """Action ``zephyr.reset_profile`` (PT9): forget the learned consumption, optionally fill it again."""
        self.profile, self.excluded_profile, self.hour = LoadProfile(), LoadProfile(), {}
        self.profile_source = "none"
        if refill:
            await self._fill_profile()
        else:
            self._store.async_delay_save(self._data, 1)
        LOGGER.info("Consumption profile reset (%s, %s hours)", self.profile_source, self.profile.mean_count)
        self.async_request()
        return {"profile_source": self.profile_source, "hours": self.profile.mean_count}

    def plan_response(self) -> dict[str, Any]:
        """Action ``zephyr.get_plan``: the current plan for automations (blocks, quarters, figures)."""
        outcome = self.outcome
        if outcome is None:
            return {"state": None, "calculated_at": None, "blocks": [], "timeline": []}
        return {
            "state": str(outcome.state),
            "calculated_at": outcome.calculated_at.isoformat(),
            "summary": outcome.summary(),
            "blocks": [b.as_dict() for b in outcome.blocks],
            "timeline": outcome.timeline(),
        }

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

    def _on_vacation(self, moment: datetime) -> bool:
        vacation = self.runtime.vacation
        return vacation is not None and vacation.active_at(moment)

    def _vacation_load(self, local: datetime) -> float:
        """kWh per hour while away (B42): the learned vacation use, else the standby use of the normal profile."""
        kind, hour = day_type(local), local.hour
        if self.vacation_profile.counts[kind][hour] >= MIN_VACATION_COUNT:
            return self.vacation_profile.values[kind][hour]
        night = [self.profile.expected(k, h) for k in (WORKDAY, WEEKEND) for h in range(6)] if self.profile.mean_count else []
        return base_load(night, DEFAULT_LOAD_KWH_PER_HOUR)

    def _load(self, start: datetime, ahead: float) -> float:
        hours = QUARTER.total_seconds() / 3600
        if self._on_vacation(start):
            return self._vacation_load(dt_util.as_local(start)) * hours
        if self.profile.mean_count == 0:
            return DEFAULT_LOAD_KWH_PER_HOUR * hours
        local = dt_util.as_local(start)
        return self.profile.forecast(day_type(local), local.hour, ahead) * hours

    def _excluded(self, start: datetime, ahead: float) -> float:
        """Expected use of the excluded load (B41) in this quarter."""
        if self.excluded_profile.mean_count == 0 or self._on_vacation(start):
            return 0.0  # B42: the air conditioner is off while away
        local = dt_util.as_local(start)
        return self.excluded_profile.forecast(day_type(local), local.hour, ahead) * QUARTER.total_seconds() / 3600

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
        costs = self.runtime.costs
        history = costs.records_since(local_midnight(now, tz)) if costs is not None else None
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
            history=history,
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
        slots = build_horizon(
            markets,
            now,
            buy=self._buy,
            sell=self._sell,
            load=self._load,
            solar=solar_fn,
            daylight=self._daylight,
            excluded=self._excluded if self.excluded_entity else None,
        )
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
                "vacation": self._on_vacation(now),
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
            self.hour = {"start": hour_start, "kwh": 0.0, "quarters": 0, "excluded_kwh": 0.0, "vacation": False}
        vacation = self.runtime.vacation
        if record.get("vacation") or (vacation is not None and vacation.was(start)):
            self.hour["vacation"] = True
        kwh = house_kwh(record, solar_known) if record.get("complete") else None
        if kwh is not None:
            excluded = float(record.get("excluded_kwh") or 0.0)
            # B41: the house without the excluded load; that load is learned apart.
            self.hour["kwh"] += max(kwh - excluded, 0.0)
            self.hour["excluded_kwh"] = self.hour.get("excluded_kwh", 0.0) + excluded
            self.hour["quarters"] += 1
        if local.minute == 45:
            if self.hour["quarters"] == 4 and self.hour.get("vacation"):
                # B42: away hours go into the vacation profile only (house and air conditioner together).
                total = self.hour["kwh"] + self.hour.get("excluded_kwh", 0.0)
                self.vacation_profile.learn(day_type(local), local.hour, total)
            elif self.hour["quarters"] == 4:
                self.profile.learn(day_type(local), local.hour, self.hour["kwh"])
                if self.excluded_entity:
                    self.excluded_profile.learn(day_type(local), local.hour, self.hour.get("excluded_kwh", 0.0))
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
        excluded = self.excluded_entity
        ids = [*costs.import_counters, *costs.export_counters, battery, *([solar] if solar else []), *([excluded] if excluded else [])]
        end = dt_util.now().replace(minute=0, second=0, microsecond=0)
        start = end - timedelta(days=LEARN_FROM_DAYS)
        stats = await hourly_statistics(self.hass, start, end, ids)
        modes: list[tuple[datetime, str | None]] | None = None
        if excluded and self.excluded_climate:
            modes = await climate_history(self.hass, start, end, self.excluded_climate)

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
        excluded_rows = by_hour(excluded, "change") if excluded else None
        hours: list[HourEnergy] = []
        for key, mean_w in battery_rows.items():
            parts = [rows.get(key) for rows in imports + exports]
            sun = solar_rows.get(key) if solar_rows is not None else 0.0
            if any(p is None for p in parts) or sun is None:
                continue
            begin = dt_util.utc_from_timestamp(key)
            vacation = self.runtime.vacation
            if vacation is not None and vacation.was(begin):
                continue  # B42: not into the normal profile
            aside = 0.0
            if excluded_rows is not None:
                used = excluded_rows.get(key)
                if used is None:
                    continue  # the house without the excluded load is unknown for this hour
                share = 1.0 if modes is None else blocked_share(modes, begin, begin + timedelta(hours=1), self.excluded_modes)
                aside = max(used, 0.0) * share
            n = len(imports)
            hours.append(
                HourEnergy(
                    start=dt_util.as_local(begin),
                    import_kwh=sum(p for p in parts[:n] if p is not None),
                    export_kwh=sum(p for p in parts[n:] if p is not None),
                    solar_kwh=sun,
                    battery_kwh=mean_w / 1000,
                    excluded_kwh=aside,
                )
            )
        if len(hours) < MIN_FILL_HOURS:
            LOGGER.debug("Recorder gave %s complete hours for the consumption profile: too few", len(hours))
            return len(hours)
        self.profile = profile_from_history(hours)
        if excluded:
            self.excluded_profile = profile_from_history(hours, excluded=True)
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
            "excluded_entity": self.excluded_entity,
            "excluded_profile": self.excluded_profile.as_dict(),
            "vacation_profile": self.vacation_profile.as_dict(),
            "reserve": [[s.start.isoformat(), s.end.isoformat(), s.price] for s in self.reserve],
        }

    def diagnostics(self) -> dict[str, Any]:
        outcome = self.outcome
        return {
            "settings": {
                "wear_cost": self.settings.wear_cost,
                "grid_charge_cost": self.settings.grid_charge_cost,
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
            "excluded_profile": None if not self.excluded_entity else self.excluded_profile.as_dict(),
            "vacation_profile": self.vacation_profile.as_dict() if self.vacation_profile.mean_count else None,
            "vacation": None if self.runtime.vacation is None else self.runtime.vacation.diagnostics(),
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


async def climate_history(hass: HomeAssistant, start: datetime, end: datetime, entity: str) -> list[tuple[datetime, str | None]]:
    """``hvac_mode`` changes of a climate entity from the recorder, oldest first (with the state at ``start``)."""
    from homeassistant.components.recorder.history import state_changes_during_period
    from homeassistant.helpers.recorder import get_instance

    result = await get_instance(hass).async_add_executor_job(
        partial(state_changes_during_period, hass, start, end, entity, no_attributes=True, include_start_time_state=True)
    )
    return [
        (state.last_changed, None if state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN) else state.state) for state in result.get(entity, [])
    ]


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
