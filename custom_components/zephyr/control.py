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
from typing import TYPE_CHECKING, Any

from homeassistant.const import EVENT_HOMEASSISTANT_STOP, STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfPower
from homeassistant.core import Event, EventStateChangedData, EventStateReportedData, HomeAssistant, State, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_state_report_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_MAX_SOC,
    CONF_MIN_SOC,
    CONF_P1_ENTITY,
    CONF_P1_EXPORT,
    CONF_P1_IMPORT,
    CONF_P1_SOURCE,
    DOMAIN,
    LOGGER,
    P1_SOURCE_PAIR,
    SCAN_INTERVAL_ACTIVE,
    SCAN_INTERVAL_IDLE,
)
from .core.engine import Mode, SetView, StepResult, ZephyrEngine
from .core.settings import Settings
from .core.zensdk import power_command, standby_command
from .writer import SetWriter

if TYPE_CHECKING:
    from . import ZephyrConfigEntry, ZephyrRuntime

LOG_SIZE = 500


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
        self.engine.enable_twin()  # shadow mode: a virtual set carries out the commands (core/twin.py)
        self.shadow = True
        self.result: StepResult | None = None
        self.log: deque[dict[str, Any]] = deque(maxlen=LOG_SIZE)
        self._listeners: list[Callable[[], None]] = []
        self._previous_mode = Mode.ZERO_METER
        self.writers = {key: SetWriter(hass, c) for key, c in runtime.coordinators.items()}
        self.live_since: float | None = None
        self.test: dict[str, Any] | None = None
        self._test_task: asyncio.Task[None] | None = None

    # --- lifecycle ----------------------------------------------------------

    @callback
    def async_start(self) -> Callable[[], None]:
        unsubs: list[Callable[[], None]] = []
        issue_id = "p1_missing"
        if self.p1_pair:
            unsubs.append(async_track_state_change_event(self.hass, list(self.p1_pair), self._on_pair_event))
            unsubs.append(async_track_state_report_event(self.hass, list(self.p1_pair), self._on_pair_event))
            watts = self._pair_watts()
            if watts is not None:
                self.engine.p1_reported(time.monotonic(), watts)
            unsubs.append(self._cancel_pair_pending)
        elif self.p1_entity:
            unsubs.append(async_track_state_change_event(self.hass, [self.p1_entity], self._on_p1_changed))
            unsubs.append(async_track_state_report_event(self.hass, [self.p1_entity], self._on_p1_reported))
            watts = _p1_watts(self.hass.states.get(self.p1_entity))
            if watts is not None:
                self.engine.p1_reported(time.monotonic(), watts)
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
        unsubs.append(self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self._on_stop))
        self._apply_poll_interval()

        def stop() -> None:
            for unsub in unsubs:
                unsub()
            if self._test_task is not None and not self._test_task.done():
                self._test_task.cancel()
            if not self.shadow:
                # Unload or reload while live: leave the sets at 0 W, not at the last power.
                self.shadow = True
                self.hass.async_create_background_task(self._all_to_zero(), "zephyr stop: sets to 0 W")

        return stop

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    # --- inputs -----------------------------------------------------------------

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
        self.engine.p1_reported(time.monotonic(), watts)
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
        self.engine.p1_reported(time.monotonic(), watts)
        self.async_step()

    @callback
    def _on_tick(self, _now: datetime) -> None:
        self.async_step()  # also when P1 is silent: staleness and timers

    @callback
    def async_set_mode(self, mode: Mode) -> None:
        if mode in (Mode.FAST_CHARGE, Mode.FAST_DISCHARGE) and self.engine.mode not in (Mode.FAST_CHARGE, Mode.FAST_DISCHARGE):
            self._previous_mode = self.engine.mode
        self.engine.set_mode(mode, time.monotonic())
        self._apply_poll_interval()
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

    async def async_set_live(self, live: bool) -> None:
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
        self.async_step()

    async def _all_to_zero(self) -> None:
        await asyncio.gather(
            *(w.send_now(power_command(0, include_ac_mode=False)) for key, w in self.writers.items() if self._online(key)),
        )

    def _online(self, key: str) -> bool:
        data = self.runtime.coordinators[key].data
        return bool(data and data.online)

    async def _on_stop(self, _event: Event) -> None:
        if not self.shadow:
            await self._all_to_zero()

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
                    self.engine.counters_record(key, "standby", time.monotonic())
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
        self.log.append({"time": dt_util.utcnow().isoformat(timespec="seconds"), "event": event, **extra})

    # --- the step ---------------------------------------------------------------

    @callback
    def async_step(self) -> None:
        now = time.monotonic()
        views = self._views()
        result = self.engine.step(now, views)
        if not self.shadow:
            for command in result.commands:
                writer = self.writers.get(command.key)
                if writer is not None:
                    writer.send(command.props)
        if result.mode_finished:
            LOGGER.debug("Fast mode finished, back to %s", self._previous_mode)
            self.engine.set_mode(self._previous_mode, now)
        previous = self.result
        self.result = result
        if result.commands or previous is None or (previous.setpoint, previous.reason) != (result.setpoint, result.reason):
            self.log.append(
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
                    "commands": [{"set": self.runtime.coordinators[c.key].number, "kind": c.kind, **c.props} for c in result.commands],
                    "sent": not self.shadow,
                }
            )
        for listener in list(self._listeners):
            listener()

    def _apply_poll_interval(self) -> None:
        active = self.engine.mode is not Mode.STANDBY
        interval = timedelta(seconds=SCAN_INTERVAL_ACTIVE if active else SCAN_INTERVAL_IDLE)
        for coordinator in self.runtime.coordinators.values():
            coordinator.update_interval = interval


def settings_from_options(options: Mapping[str, Any]) -> Settings:
    """Settings with the values the user chose in the options."""
    changes = {key: float(options[key]) for key in (CONF_MIN_SOC, CONF_MAX_SOC) if key in options}
    return Settings().with_changes(**changes) if changes else Settings()
