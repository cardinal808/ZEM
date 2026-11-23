"""Runs the engine in Home Assistant: P1 events in, decisions out.

M3: shadow mode only. The engine computes what ZEPHYR would do, entities and
the decision log show it, but nothing is sent to the sets.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN, UnitOfPower
from homeassistant.core import Event, EventStateChangedData, EventStateReportedData, HomeAssistant, State, callback
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
        self.engine.controller.trust_commands = False  # shadow mode: commands are not carried out
        self.shadow = True
        self.result: StepResult | None = None
        self.log: deque[dict[str, Any]] = deque(maxlen=LOG_SIZE)
        self._listeners: list[Callable[[], None]] = []
        self._previous_mode = Mode.ZERO_METER

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
        self._apply_poll_interval()

        def stop() -> None:
            for unsub in unsubs:
                unsub()

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

    # --- the step ---------------------------------------------------------------

    @callback
    def async_step(self) -> None:
        now = time.monotonic()
        views = [
            SetView(
                key=key,
                number=c.number,
                report=c.data.report if c.data else None,
                online=bool(c.data and c.data.online),
            )
            for key, c in self.runtime.coordinators.items()
        ]
        result = self.engine.step(now, views)
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
                    "p1": result.grid_power,
                    "battery": sum(v.report.battery_power_ac for v in views if v.report and v.online),
                    "setpoint": result.setpoint,
                    "reason": result.reason.code.value,
                    "commands": [{"set": self.runtime.coordinators[c.key].number, "kind": c.kind, **c.props} for c in result.commands],
                    "sent": False if self.shadow else None,
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
