"""Runs the engine in Home Assistant: P1 events in, decisions out.

Shadow mode (default): the engine computes what ZEPHYR would do with a virtual
set; nothing is sent. Live mode (``switch.zephyr_control``, M4b): the commands
go to the sets through one writer per set.
"""

from __future__ import annotations

import asyncio
import math
import time
from collections import deque
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from functools import partial
from typing import TYPE_CHECKING, Any

from homeassistant.const import EVENT_HOMEASSISTANT_STOP, RESTART_EXIT_CODE, STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfEnergy, UnitOfPower
from homeassistant.core import Event, EventStateChangedData, EventStateReportedData, HomeAssistant, State, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_state_report_event,
    async_track_time_interval,
)
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_EXCLUDED_CLIMATE,
    CONF_EXCLUDED_ENERGY,
    CONF_EXCLUDED_MODES,
    CONF_EXPENSIVE_HOURS,
    CONF_MAX_SOC,
    CONF_MIN_PRICE,
    CONF_MIN_SOC,
    CONF_P1_ENTITY,
    CONF_P1_EXPORT,
    CONF_P1_IMPORT,
    CONF_P1_SOURCE,
    CONF_PRICE_ENTITY,
    CONF_RESERVE_SOC,
    CONF_SOLAR_ENERGY,
    CONF_SOLAR_POWER,
    DEFAULT_EXCLUDED_MODES,
    DEFAULT_EXPENSIVE_HOURS,
    DEFAULT_RESERVE_SOC,
    DOMAIN,
    LOGGER,
    P1_SOURCE_PAIR,
    SCAN_INTERVAL_ACTIVE,
    SCAN_INTERVAL_IDLE,
)
from .core.engine import Mode, Reason, ReasonCode, SetView, StepResult, ZephyrEngine
from .core.excluded_load import ExcludedLoad, exclusion_for_controller
from .core.price_window import NO_PRICES, PriceDecision, decide, parse_nordpool_raw
from .core.settings import Settings
from .core.solar_now import CounterPower, total, watts
from .core.stroom import ZERO_REASONS, RegulationLog, ZeroScore
from .core.zensdk import power_command, standby_command
from .log_file import FLUSH_EVERY, MAX_LINES, LogFile
from .prices import price_state
from .writer import SetWriter

if TYPE_CHECKING:
    from . import ZephyrConfigEntry, ZephyrRuntime

LIVE_HISTORY = 20


def _p1_watts(state: State | None) -> float | None:
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
        return None
    try:
        value = float(state.state)
    except ValueError:
        return None
    if state.attributes.get("unit_of_measurement") == UnitOfPower.KILO_WATT:
        value *= 1000
    return value


class ZephyrControl:
    """Owns the engine and feeds it."""

    def __init__(self, hass: HomeAssistant, entry: ZephyrConfigEntry, runtime: ZephyrRuntime) -> None:
        self.peak_days: dict[str, dict[str, float]] = {}
        """Short peaks the step filter left to the grid, per local day (kWh, holds)."""
        self._peak_day: str | None = None
        self._peak_base: tuple[float, int] | None = None
        self.hass = hass
        self.entry = entry
        self.runtime = runtime
        options = entry.options
        self.p1_pair: tuple[str, str] | None = None
        if options.get(CONF_P1_SOURCE) == P1_SOURCE_PAIR and options.get(CONF_P1_IMPORT) and options.get(CONF_P1_EXPORT):
            self.p1_pair = (options[CONF_P1_IMPORT], options[CONF_P1_EXPORT])
        self.p1_entity: str | None = None if self.p1_pair else options.get(CONF_P1_ENTITY)
        self._pair_pending: Callable[[], None] | None = None
        self.engine = ZephyrEngine(settings_from_options(entry.options), Mode.ZERO_METER)
        self.user_max_soc = self.engine.settings.max_soc
        self.calibration_active = False
        self.calibration_rest = False
        """Calibration (SPEC-planner §3.5): upper limit 100 %; at 100 % no delivering until the set calibrated."""
        self.engine.enable_twin()  # shadow mode: a virtual set carries out the commands (core/twin.py)
        self.shadow = True
        self.wanted_live = False
        """The user wants live control; the switch keeps this over restarts. A start that cannot
        go live yet (P1 or set not there) keeps it, so ZEPHYR goes on trying."""
        self.live_history: deque[dict[str, Any]] = deque(maxlen=LIVE_HISTORY)
        """Switches between live and shadow with the reason, kept over restarts (diagnostics)."""
        self._live_store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.live")
        self._foreign_seen: list[dict[str, Any]] = []
        self.result: StepResult | None = None
        self.log: deque[dict[str, Any]] = deque(maxlen=MAX_LINES)
        self.log_file = LogFile(hass, entry.entry_id, self.log)
        """The log over the last 48 hours, kept over restarts (log_file.py)."""
        self._listeners: list[Callable[[], None]] = []
        self._previous_mode = Mode.ZERO_METER
        self.writers = {key: SetWriter(hass, c) for key, c in runtime.coordinators.items()}
        for key, writer in self.writers.items():
            writer.on_written = partial(self._count_written, key)
            writer.on_superseded = partial(self._count_superseded, key)
        self.engine.day_of = lambda _now: dt_util.now().date().isoformat()
        self._writes_store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.writes")
        self.live_since: float | None = None
        self.price_entity: str | None = options.get(CONF_PRICE_ENTITY)
        self.expensive_hours = int(options.get(CONF_EXPENSIVE_HOURS, DEFAULT_EXPENSIVE_HOURS))
        self.reserve_soc = float(options.get(CONF_RESERVE_SOC, DEFAULT_RESERVE_SOC))
        self.min_price: float | None = options.get(CONF_MIN_PRICE)
        self.price: PriceDecision | None = None
        self._price_at = -1e9
        self._foreign: deque[float] = deque(maxlen=20)
        self._checked_report: dict[str, int | None] = {}
        self.test: dict[str, Any] | None = None
        self.p1_watts: float | None = None
        """Last P1 value (W, + import) and when it came (monotonic); read by the cost log."""
        self.p1_at: float | None = None
        self._test_task: asyncio.Task[None] | None = None
        # B41: a load the battery may not feed (the air conditioner while heating).
        self.excluded_energy: str | None = options.get(CONF_EXCLUDED_ENERGY)
        self.excluded_climate: str | None = options.get(CONF_EXCLUDED_CLIMATE) if self.excluded_energy else None
        self.excluded: ExcludedLoad | None = (
            ExcludedLoad(options.get(CONF_EXCLUDED_MODES, DEFAULT_EXCLUDED_MODES), has_climate=self.excluded_climate is not None)
            if self.excluded_energy
            else None
        )
        # Solar the sets do not see (panel *Nu*): inverter power sensors, else an estimate from the counter.
        self.solar_power_entities: list[str] = list(options.get(CONF_SOLAR_POWER) or [])
        self.solar_energy: str | None = options.get(CONF_SOLAR_ENERGY)
        self.solar_counter = CounterPower()
        self.zero = ZeroScore()
        self.regulation = RegulationLog()
        """The last 10 minutes of the controller (screen Stroom)."""
        """How well the meter stayed at its target today (screen Stroom)."""
        self._zero_store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.{entry.entry_id}.zero")

    # --- lifecycle ----------------------------------------------------------

    @callback
    def _track_peaks(self) -> None:
        """Short peaks left to the grid per local day (PLANNING 1.3), 14 days in memory."""
        today = dt_util.now().date().isoformat()
        kwh, holds = self.engine.peak_kwh, self.engine.grid_filter.holds
        if self._peak_day != today or self._peak_base is None:
            self._peak_day, self._peak_base = today, (kwh, holds)
        base_kwh, base_holds = self._peak_base
        self.peak_days[today] = {"kwh": round(kwh - base_kwh, 4), "holds": holds - base_holds}
        for day in sorted(self.peak_days)[:-14]:
            del self.peak_days[day]

    def apply_options(self, options: Mapping[str, Any]) -> None:
        """Battery limits and zero-meter settings changed without a reload (UI-7)."""
        self.user_max_soc = float(_limits(options).get("max_soc", self.engine.settings.max_soc))
        limits = _limits(options)
        if self.calibration_active:
            limits["max_soc"] = 100.0
        self.engine.update_settings(self.engine.settings.with_changes(**limits))
        self.expensive_hours = int(options.get(CONF_EXPENSIVE_HOURS, DEFAULT_EXPENSIVE_HOURS))
        self.reserve_soc = float(options.get(CONF_RESERVE_SOC, DEFAULT_RESERVE_SOC))
        self.min_price = options.get(CONF_MIN_PRICE)
        self.solar_power_entities = list(options.get(CONF_SOLAR_POWER) or [])

    def set_calibration(self, active: bool, rest: bool) -> None:
        """Raise the set's upper SOC limit to 100 % while a calibration is due (one flash write
        each way, cause "calibration"), and hold delivering while the set calibrates at 100 %."""
        self.calibration_rest = rest
        if active == self.calibration_active:
            return
        self.calibration_active = active
        self.engine.limits_cause = "calibration"
        max_soc = 100.0 if active else self.user_max_soc
        self.engine.update_settings(self.engine.settings.with_changes(max_soc=max_soc))
        self._log_event("calibration_on" if active else "calibration_off", max_soc=max_soc)

    def async_start(self) -> Callable[[], None]:
        unsubs: list[Callable[[], None]] = []
        issue_id = "p1_missing"
        if self.p1_pair:
            unsubs.append(async_track_state_change_event(self.hass, list(self.p1_pair), self._on_pair_event))
            unsubs.append(async_track_state_report_event(self.hass, list(self.p1_pair), self._on_pair_event))
            watts = self._pair_watts()
            if watts is not None:
                self._p1_value(watts)
            unsubs.append(self._cancel_pair_pending)
        elif self.p1_entity:
            unsubs.append(async_track_state_change_event(self.hass, [self.p1_entity], self._on_p1_changed))
            unsubs.append(async_track_state_report_event(self.hass, [self.p1_entity], self._on_p1_reported))
            watts = _p1_watts(self.hass.states.get(self.p1_entity))
            if watts is not None:
                self._p1_value(watts)
        if self.excluded is not None and self.excluded_energy:
            unsubs.append(async_track_state_change_event(self.hass, [self.excluded_energy], self._on_excluded_energy))
            self._excluded_energy_state(self.hass.states.get(self.excluded_energy))
            if self.excluded_climate:
                unsubs.append(async_track_state_change_event(self.hass, [self.excluded_climate], self._on_excluded_climate))
                self._excluded_climate_state(self.hass.states.get(self.excluded_climate))
        if self.solar_energy:
            unsubs.append(async_track_state_change_event(self.hass, [self.solar_energy], self._on_solar_energy))
            self._solar_energy_state(self.hass.states.get(self.solar_energy))
        if self.p1_pair or self.p1_entity:
            ir.async_delete_issue(self.hass, DOMAIN, issue_id)
        else:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="p1_missing",
            )
            unsubs.append(lambda: ir.async_delete_issue(self.hass, DOMAIN, issue_id))
        unsubs.append(async_track_time_interval(self.hass, self._on_tick, timedelta(seconds=1)))
        unsubs.append(async_track_time_interval(self.hass, self._save_zero, timedelta(minutes=5)))
        unsubs.append(self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self._on_stop))
        self.hass.async_create_task(self._restore_zero(), "zephyr: restore the zero score")
        self.hass.async_create_task(self._restore_writes(), "zephyr: restore the write counters")
        self.hass.async_create_task(self.log_file.async_restore(), "zephyr: restore the log")
        unsubs.append(async_track_time_interval(self.hass, self.log_file.async_flush, FLUSH_EVERY))
        self.hass.async_create_task(self._restore_live_history(), "zephyr: restore the live history")
        unsubs.append(async_track_time_interval(self.hass, self._save_writes, timedelta(minutes=5)))

        def save_writes() -> None:
            self.hass.async_create_task(self._save_writes(), "zephyr: save the write counters")

        unsubs.append(save_writes)

        unsubs.append(self.log_file.flush_at_unload)
        self._apply_poll_interval()

        def stop() -> None:
            for unsub in unsubs:
                unsub()
            if self._test_task is not None and not self._test_task.done():
                self._test_task.cancel()
            if not self.shadow:
                # Unload or reload while live: leave the sets at 0 W, not at the last power.
                self.shadow = True
                self.note_live("shadow", "unload")
                self.hass.async_create_background_task(self._all_to_zero(), "zephyr stop: sets to 0 W")

        return stop

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    # --- inputs -----------------------------------------------------------------

    @callback
    def _on_solar_energy(self, event: Event[EventStateChangedData]) -> None:
        self._solar_energy_state(event.data["new_state"])

    def _solar_energy_state(self, state: State | None) -> None:
        if state is None:
            return
        try:
            kwh = float(state.state)
        except ValueError:
            return
        if state.attributes.get("unit_of_measurement") == UnitOfEnergy.WATT_HOUR:
            kwh /= 1000
        self.solar_counter.observe(kwh, time.monotonic())

    def external_solar(self) -> tuple[float | None, bool]:
        """Solar power (W) the sets do not see, and whether it is an estimate from the counter.

        ZEPHYR's own sensors are skipped: the sets' PV is already counted from the sets.
        """
        from homeassistant.helpers import entity_registry as er

        registry = er.async_get(self.hass)
        ids = [e for e in self.solar_power_entities if (entry := registry.async_get(e)) is None or entry.platform != DOMAIN]
        if ids:
            states = [self.hass.states.get(e) for e in ids]
            return total([None if s is None else watts(s.state, s.attributes.get("unit_of_measurement")) for s in states]), False
        if self.solar_energy:
            return self.solar_counter.power(time.monotonic()), True
        return None, False

    @callback
    def _on_excluded_energy(self, event: Event[EventStateChangedData]) -> None:
        self._excluded_energy_state(event.data["new_state"])

    def _excluded_energy_state(self, state: State | None) -> None:
        if self.excluded is None or state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
            return
        try:
            kwh = float(state.state)
        except ValueError:
            return
        if state.attributes.get("unit_of_measurement") == UnitOfEnergy.WATT_HOUR:
            kwh /= 1000
        self.excluded.observe_counter(kwh, time.monotonic())

    @callback
    def _on_excluded_climate(self, event: Event[EventStateChangedData]) -> None:
        self._excluded_climate_state(event.data["new_state"])

    def _excluded_climate_state(self, state: State | None) -> None:
        if self.excluded is None:
            return
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
            self.excluded.observe_climate(None, None, time.monotonic())
            return
        action = state.attributes.get("hvac_action")
        self.excluded.observe_climate(state.state, None if action is None else str(action), time.monotonic())

    @callback
    def _on_p1_changed(self, event: Event[EventStateChangedData]) -> None:
        self._on_p1(event.data["new_state"])

    @callback
    def _on_p1_reported(self, event: Event[EventStateReportedData]) -> None:
        self._on_p1(event.data["new_state"])

    # Two sensors (import and export, as the DSMR integration gives them). One telegram
    # updates both, one after the other: wait a moment so we see the pair, not half of it.
    PAIR_SETTLE = 0.2

    @callback
    def _on_pair_event(self, _event: Event[Any]) -> None:
        if self._pair_pending is None:
            self._pair_pending = async_call_later(self.hass, self.PAIR_SETTLE, self._on_pair_settled)

    @callback
    def _on_pair_settled(self, _now: datetime) -> None:
        self._pair_pending = None
        watts = self._pair_watts()
        if watts is None:
            return
        self._p1_value(watts)
        self.async_step()

    @callback
    def _cancel_pair_pending(self) -> None:
        if self._pair_pending is not None:
            self._pair_pending()
            self._pair_pending = None

    def _pair_watts(self) -> float | None:
        assert self.p1_pair is not None
        imported = _p1_watts(self.hass.states.get(self.p1_pair[0]))
        exported = _p1_watts(self.hass.states.get(self.p1_pair[1]))
        if imported is None or exported is None:
            return None
        return imported - exported

    @property
    def p1_description(self) -> str | None:
        if self.p1_pair:
            return f"{self.p1_pair[0]} - {self.p1_pair[1]}"
        return self.p1_entity

    @callback
    def _on_p1(self, state: State | None) -> None:
        watts = _p1_watts(state)
        if watts is None:
            return
        self._p1_value(watts)
        self.async_step()

    def _p1_value(self, watts: float) -> None:
        now = time.monotonic()
        self.p1_watts, self.p1_at = watts, now
        self.engine.p1_reported(now, watts)

    @callback
    def _on_tick(self, _now: datetime) -> None:
        self.async_step()  # also when P1 is silent: staleness and timers

    @property
    def previous_mode(self) -> Mode:
        """The mode a fast mode returns to."""
        return self._previous_mode

    @callback
    def async_set_mode(self, mode: Mode) -> None:
        if mode in (Mode.FAST_CHARGE, Mode.FAST_DISCHARGE) and self.engine.mode not in (Mode.FAST_CHARGE, Mode.FAST_DISCHARGE):
            self._previous_mode = self.engine.mode
        changed = mode is not self.engine.mode
        self.engine.set_mode(mode, time.monotonic())
        self._apply_poll_interval()
        if changed and self.runtime.planner is not None:
            self.runtime.planner.async_request()  # §5: recalculate on a mode change
        self.async_step()

    # --- live mode (PLAN-M4b §2.2) ---------------------------------------------

    def _views(self) -> list[SetView]:
        return [
            SetView(
                key=key,
                number=c.number,
                report=c.data.report if c.data else None,
                online=bool(c.data and c.data.online),
            )
            for key, c in self.runtime.coordinators.items()
        ]

    def live_blockers(self) -> list[str]:
        """Why live control cannot start now (empty: it can)."""
        reasons: list[str] = []
        if not (self.p1_pair or self.p1_entity):
            reasons.append("no P1 sensor chosen")
        elif self.result is None or not self.result.p1_ok:
            reasons.append("P1 is not reporting")
        if not self.runtime.coordinators:
            reasons.append("no sets")
        for c in self.runtime.coordinators.values():
            data = c.data
            if data is None or not data.online or data.report is None:
                reasons.append(f"set {c.number} is offline")
            elif data.serial_mismatch:
                reasons.append(f"set {c.number} reports a different serial number")
            elif data.report.fault:
                reasons.append(f"set {c.number} reports an error")
        if self._test_task is not None and not self._test_task.done():
            reasons.append("a write test is running")
        return reasons

    async def async_set_live(self, live: bool, reason: str = "user") -> None:
        if live == (not self.shadow):
            return
        now = time.monotonic()
        if live:
            blockers = self.live_blockers()
            if blockers:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="live_not_possible",
                    translation_placeholders={"reasons": "; ".join(blockers)},
                )
            ir.async_delete_issue(self.hass, DOMAIN, "second_controller")
            self._foreign.clear()
            self._foreign_seen.clear()
            for writer in self.writers.values():
                writer.last_props = None
                writer.last_at = None
            self.engine.set_live(True, now, self._views())
            self.shadow = False
            self.live_since = now
            LOGGER.info("ZEPHYR now controls the sets")
        else:
            self.shadow = True
            self.live_since = None
            self.engine.set_live(False, now, self._views())
            # Once 0 W in RAM, then nothing more: the current system can take over (PLAN-M4b §4).
            await self._all_to_zero()
            LOGGER.info("ZEPHYR back in shadow mode")
        self._log_event("live" if live else "shadow")
        self.note_live("live" if live else "shadow", reason)
        self.async_step()

    # --- why live started or stopped, kept over restarts -----------------------------

    def note_live(self, event: str, reason: str, **details: Any) -> None:
        """Record a switch between live and shadow (or a failed resume) and save it."""
        self.live_history.append({"time": dt_util.utcnow().isoformat(timespec="seconds"), "event": event, "reason": reason, **details})
        self.hass.async_create_task(self._save_live_history(), "zephyr: save the live history")

    @property
    def last_shadow(self) -> dict[str, Any] | None:
        """The last time live control stopped, with the reason."""
        return next((e for e in reversed(self.live_history) if e["event"] == "shadow"), None)

    async def _restore_live_history(self) -> None:
        data = await self._live_store.async_load()
        old = [e for e in (data or {}).get("history", []) if isinstance(e, dict) and "event" in e]
        new = list(self.live_history)
        self.live_history.clear()
        self.live_history.extend(old + new)

    async def _save_live_history(self) -> None:
        await self._live_store.async_save({"history": list(self.live_history)})

    async def _all_to_zero(self) -> None:
        keys = [key for key in self.writers if self._online(key) and not self._busy_itself(key)]
        now = time.monotonic()
        for key in keys:
            self.engine.counters_record(key, "power", now)
        await asyncio.gather(*(self.writers[key].send_now(power_command(0, include_ac_mode=False)) for key in keys))

    def _busy_itself(self, key: str) -> bool:
        """The set calibrates itself or is in bypass: ZEPHYR leaves it alone (SPEC-basis §8)."""
        data = self.runtime.coordinators[key].data
        report = data.report if data else None
        return bool(report and (report.calibrating or report.bypass))

    def _online(self, key: str) -> bool:
        data = self.runtime.coordinators[key].data
        return bool(data and data.online)

    async def _on_stop(self, _event: Event) -> None:
        if not self.shadow and self.hass.exit_code == RESTART_EXIT_CODE:
            # A restart: the sets keep their last command and ZEPHYR takes over again after
            # the start (B35, B47). 0 W would open the relay and draw from the grid meanwhile.
            LOGGER.info("Home Assistant restarts: the sets keep their last command")
            self.live_history.append({"time": dt_util.utcnow().isoformat(timespec="seconds"), "event": "restart", "reason": "ha_restart"})
        elif not self.shadow:
            await self._all_to_zero()
        await self._save_zero()
        await self._save_writes()
        await self.log_file.async_flush()
        await self._save_live_history()

    def _count_written(self, key: str, kinds: list[str]) -> None:
        now = time.monotonic()
        for kind in kinds:
            self.engine.counters_record(key, kind, now)

    def _count_superseded(self, key: str, kinds: list[str]) -> None:
        self.engine.counters_record(key, "superseded", time.monotonic())

    async def _restore_writes(self) -> None:
        self.engine.counters_restore(await self._writes_store.async_load(), time.monotonic(), time.time())

    async def _save_writes(self, _now: datetime | None = None) -> None:
        await self._writes_store.async_save(self.engine.counters_export(time.monotonic(), time.time()))

    async def _restore_zero(self) -> None:
        data = await self._zero_store.async_load()
        if self.zero.day is None or not self.zero.buckets:
            self.zero.restore(data, dt_util.now().date())

    async def _save_zero(self, _now: datetime | None = None) -> None:
        if self.zero.day is not None:
            await self._zero_store.async_save(self.zero.as_dict())

    def _zero_step(self, now: float, result: StepResult, excluded: float) -> None:
        """Feed the zero score: steering only when live and regulating the meter (core/stroom.py)."""
        local = dt_util.now()
        steering = not self.shadow and result.reason.code.value in ZERO_REASONS and result.grid_power is not None
        grid = result.grid_power
        target = 0.0 if grid is None else exclusion_for_controller(excluded, grid, result.battery_power or 0.0)
        deviation = None if grid is None else grid - target
        self.regulation.add(now, grid, target, result.setpoint, result.battery_power, steering)
        seconds = local.hour * 3600 + local.minute * 60 + local.second + local.microsecond / 1e6
        self.zero.add(now, local.date(), seconds, steering, deviation)

    # --- write test (PLAN-M4b §2.8) ---------------------------------------------

    async def async_test_command(self, power: int, duration: float) -> None:
        if not self.shadow:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="test_live")
        if self.engine.mode is not Mode.STANDBY:
            raise HomeAssistantError(translation_domain=DOMAIN, translation_key="test_not_standby")
        if self._test_task is not None and not self._test_task.done():
            self._test_task.cancel()
            await asyncio.wait([self._test_task])
        self._test_task = self.hass.async_create_background_task(self._run_test(int(power), float(duration)), "zephyr write test")

    async def _run_test(self, power: int, duration: float) -> None:
        self.test = {"power": power, "duration": duration, "started": dt_util.utcnow().isoformat(timespec="seconds"), "reports": []}
        try:
            if power != 0:
                for key, writer in self.writers.items():
                    data = self.runtime.coordinators[key].data
                    if not self._online(key) or data is None or data.report is None:
                        continue
                    r = data.report
                    await writer.send_now(
                        power_command(power, include_ac_mode=True, charge_max=r.charge_max_limit, deliver_max=r.inverse_max_power)
                    )
                    self.engine.counters_record(key, "power", time.monotonic())
                self._log_event("test", power=power)
                steps = max(1, math.ceil(duration / 2))
                for _ in range(steps):  # counted, not clocked: robust against clock jumps
                    await asyncio.sleep(duration / steps)
                    self._record_test_reports()
        except asyncio.CancelledError:
            pass
        finally:
            for key, writer in self.writers.items():
                if self._online(key):
                    await writer.send_now(standby_command())
                    self.engine.counters_record(key, "test", time.monotonic())
            self._log_event("test_end")
            if self.test is not None:
                self.test["finished"] = dt_util.utcnow().isoformat(timespec="seconds")
            self.async_step()

    def _record_test_reports(self) -> None:
        if self.test is None:
            return
        for c in self.runtime.coordinators.values():
            r = c.data.report if c.data else None
            if r is None:
                continue
            self.test["reports"].append(
                {
                    "set": c.number,
                    "battery": round(r.battery_power_ac),
                    "smartMode": r.smart_mode,
                    "acMode": None if r.ac_mode is None else int(r.ac_mode),
                    "inputLimit": r.input_limit,
                    "outputLimit": r.output_limit,
                }
            )
        del self.test["reports"][:-60]

    def _log_event(self, event: str, **extra: Any) -> None:
        self.log_file.add({"time": dt_util.utcnow().isoformat(timespec="seconds"), "event": event, **extra})

    # --- the step ---------------------------------------------------------------

    @callback
    def async_step(self) -> None:
        now = time.monotonic()
        views = self._views()
        price_block, reserve_charge = self._price_inputs(now, views)
        plan_action = None
        planner = self.runtime.planner
        if self.engine.mode is Mode.FORECAST and planner is not None:
            plan_action = planner.action_at(dt_util.utcnow())
        excluded = self.excluded.power(now) if self.excluded is not None else 0.0
        self._track_peaks()
        curtail = self.runtime.curtail
        self.engine.count_commands = self.shadow  # live: counted once the set accepted the write
        result = self.engine.step(
            now,
            views,
            discharge_blocked=self.calibration_rest,
            price_block=price_block,
            reserve_charge=reserve_charge,
            plan_action=plan_action,
            excluded_load=excluded,
            export_blocked=curtail.export_blocked if curtail is not None else None,
        )
        if not self.shadow:
            self._check_reports(now)
        if not self.shadow:
            for command in result.commands:
                writer = self.writers.get(command.key)
                if writer is not None:
                    writer.send(command.props, command.kinds)
        if result.mode_finished:
            LOGGER.debug("Fast mode finished, back to %s", self._previous_mode)
            self.engine.set_mode(self._previous_mode, now)
        previous = self.result
        self.result = result
        self._zero_step(now, result, excluded)
        if result.commands or previous is None or (previous.setpoint, previous.reason) != (result.setpoint, result.reason):
            self.log_file.add(
                {
                    "time": dt_util.utcnow().isoformat(timespec="seconds"),
                    "mode": result.mode.value,
                    "p1": None if result.grid_power is None else round(result.grid_power),
                    "battery": None if result.battery_power is None else round(result.battery_power),
                    **(
                        {
                            "p1_measured": None if result.measured_grid_power is None else round(result.measured_grid_power),
                            "battery_real": round(sum(v.report.battery_power_ac for v in views if v.report and v.online)),
                        }
                        if self.engine.twin_enabled
                        else {}
                    ),
                    "setpoint": result.setpoint,
                    "reason": result.reason.code.value,
                    **({"reason_params": result.reason.params} if result.reason.params else {}),
                    **({"excluded": round(self.engine.excluded_now)} if self.engine.excluded_now else {}),
                    "commands": [{"set": self.runtime.coordinators[c.key].number, "kind": c.kind, **c.props} for c in result.commands],
                    "sent": not self.shadow and bool(result.commands),
                }
            )
        for listener in list(self._listeners):
            listener()

    # --- prices: deliver in the most expensive hours, reserve (PLAN-M4b §2.6) ----------

    def _price_inputs(self, now: float, views: list[SetView]) -> tuple[Reason | None, tuple[int, float] | None]:
        if not self.price_entity:
            self.price = None
            return None, None
        if now - self._price_at >= 30 or self.price is None:
            self._price_at = now
            self.price = self._decide_prices(views)
        decision = self.price
        if not decision.have_prices:
            return Reason(ReasonCode.NO_PRICES), None
        block = None
        if not decision.expensive:
            nxt = "-" if decision.next_expensive is None else dt_util.as_local(decision.next_expensive).strftime("%H:%M")
            block = Reason(ReasonCode.NOT_EXPENSIVE, {"next": nxt})
        charge = None
        if decision.reserve_charge:
            charge = (int(self._charge_kw(views) * 1000), self.reserve_soc)
        return block, charge

    def _charge_kw(self, views: list[SetView]) -> float:
        limits = [v.report.charge_max_limit or 2400 for v in views if v.report is not None and v.online]
        settings_max = self.engine.settings.max_charge_power
        total = float(sum(limits))
        if settings_max is not None:
            total = min(total, float(settings_max))
        return total / 1000

    def _deliver_kw(self, views: list[SetView]) -> float:
        limits = [v.report.inverse_max_power or 2400 for v in views if v.report is not None and v.online]
        settings_max = self.engine.settings.max_deliver_power
        total = float(sum(limits))
        if settings_max is not None:
            total = min(total, float(settings_max))
        return total / 1000

    def power_limits_kw(self) -> tuple[float, float]:
        """(charge, deliver) kW of the online sets within the settings, for the planner."""
        views = self._views()
        return self._charge_kw(views), self._deliver_kw(views)

    def _decide_prices(self, views: list[SetView]) -> PriceDecision:
        assert self.price_entity is not None
        state = price_state(self.hass, self.price_entity)
        if state is None:
            return NO_PRICES
        slots = parse_nordpool_raw(state.attributes.get("raw_today")) + parse_nordpool_raw(state.attributes.get("raw_tomorrow"))
        totals = self.runtime.totals()
        return decide(
            slots,
            dt_util.now(),
            hours=self.expensive_hours,
            min_price=self.min_price,
            soc=totals.soc,
            reserve_soc=self.reserve_soc,
            capacity_kwh=totals.capacity_kwh or 0.0,
            charge_kw=self._charge_kw(views),
        )

    # --- checks while live: a second controller, smartMode (PLAN-M4b §2.2, §2.7) ---------

    SETTLE_FOR_CHECK = 6.0
    NOT_APPLIED_AFTER = 20.0
    """A set that still reports its old limits is starting, not controlled by someone else, until
    this long after the write (start from 0 W with the relay open: 9-17 s, seen 25-11)."""
    FOREIGN_WINDOW = 300.0

    def _check_reports(self, now: float) -> None:
        for key, writer in self.writers.items():
            data = self.runtime.coordinators[key].data
            report = data.report if data and data.online else None
            if report is None or writer.last_props is None or writer.last_at is None:
                continue
            if now - writer.last_at < self.SETTLE_FOR_CHECK or self._checked_report.get(key) == report.timestamp:
                continue
            sent = writer.last_props
            if report.calibrating or report.bypass or report.fault:
                # The set itself changes its limits (own calibration, bypass, a fault): not a second
                # controller. ZEPHYR leaves such a set alone and checks again afterwards.
                self._checked_report[key] = report.timestamp
                continue
            limits_sent = "inputLimit" in sent and "outputLimit" in sent
            mismatch = limits_sent and (
                abs(report.input_limit - sent["inputLimit"]) > 20 or abs(report.output_limit - sent["outputLimit"]) > 20
            )
            before = writer.limits_before
            still_old = before is not None and abs(report.input_limit - before[0]) <= 20 and abs(report.output_limit - before[1]) <= 20
            if mismatch and still_old and now - writer.last_at < self.NOT_APPLIED_AFTER:
                continue  # the set has not applied the command yet (starting): check the next report
            self._checked_report[key] = report.timestamp
            if sent.get("smartMode") == 1 and report.smart_mode == 0:
                writer.stats.smartmode_reverted.append(now)
            if mismatch:
                self._foreign.append(now)
                self._foreign_seen.append(
                    {
                        "set": self.runtime.coordinators[key].number,
                        "reported": [report.input_limit, report.output_limit],
                        "sent": [sent["inputLimit"], sent["outputLimit"]],
                        "after_s": round(now - writer.last_at, 1),
                    }
                )
                del self._foreign_seen[:-4]
                LOGGER.warning(
                    "Set %s reports limits ZEPHYR did not write (in %s / out %s, sent %s / %s)",
                    self.runtime.coordinators[key].number,
                    report.input_limit,
                    report.output_limit,
                    sent["inputLimit"],
                    sent["outputLimit"],
                )
        recent = [t for t in self._foreign if now - t <= self.FOREIGN_WINDOW]
        if len(recent) >= 2:
            self._foreign.clear()
            self.hass.async_create_task(self._stop_for_second_controller())

    async def _stop_for_second_controller(self) -> None:
        """Another system writes to the set: stop writing, back to shadow, tell the user (L4)."""
        if self.shadow:
            return
        self.shadow = True
        self.wanted_live = False  # the user decides when to take over again (L4)
        self.live_since = None
        self.engine.set_live(False, time.monotonic(), self._views())
        self.note_live("shadow", "second_controller", reports=list(self._foreign_seen))
        self._foreign_seen.clear()
        # Once 0 W, as when switching off by hand: the set must not stay at ZEPHYR's last power.
        await self._all_to_zero()
        self._log_event("second_controller")
        ir.async_create_issue(
            self.hass, DOMAIN, "second_controller", is_fixable=False, severity=ir.IssueSeverity.ERROR, translation_key="second_controller"
        )
        LOGGER.error("Another system controls the set: ZEPHYR stopped writing and is back in shadow mode")
        self.async_step()

    def _apply_poll_interval(self) -> None:
        active = self.engine.mode is not Mode.STANDBY
        interval = timedelta(seconds=SCAN_INTERVAL_ACTIVE if active else SCAN_INTERVAL_IDLE)
        for coordinator in self.runtime.coordinators.values():
            coordinator.update_interval = interval


def _limits(options: Mapping[str, Any]) -> dict[str, float]:
    defaults = Settings()
    return {
        CONF_MIN_SOC: float(options.get(CONF_MIN_SOC, defaults.min_soc)),
        CONF_MAX_SOC: float(options.get(CONF_MAX_SOC, defaults.max_soc)),
    }


def settings_from_options(options: Mapping[str, Any]) -> Settings:
    """Settings with the values the user chose in the options."""
    changes = {key: float(options[key]) for key in (CONF_MIN_SOC, CONF_MAX_SOC) if key in options}
    return Settings().with_changes(**changes) if changes else Settings()
