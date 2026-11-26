"""Vacation (B42): manual switch with an end, or automatic when nobody is home for 24 h.

Owns the :class:`VacationState` (stored in ``zephyr.<entry>.vacation``), checks the end every
minute and, with the option on, follows ``zone.home`` (number of people at home).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import CONF_VACATION_AWAY, DOMAIN, LOGGER
from .core.vacation import AWAY_AFTER, VacationState

STORAGE_VERSION = 1
HOME_ZONE = "zone.home"


class VacationManager:
    def __init__(self, hass: HomeAssistant, entry_id: str, options: Mapping[str, Any]) -> None:
        self.hass = hass
        self.auto_enabled = bool(options.get(CONF_VACATION_AWAY, False))
        self.state = VacationState()
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.vacation")
        self._listeners: list[Callable[[], None]] = []
        self._away_since: datetime | None = None

    async def async_start(self) -> Callable[[], None]:
        self.state = VacationState.from_dict(await self._store.async_load())
        if not self.auto_enabled and self.state.auto:
            self.state.set_auto(False, dt_util.utcnow())
        unsubs = [async_track_time_change(self.hass, self._on_minute, second=5)]
        if self.auto_enabled:
            unsubs.append(async_track_state_change_event(self.hass, [HOME_ZONE], self._on_zone))
        self._evaluate(dt_util.utcnow())

        def stop() -> None:
            for unsub in unsubs:
                unsub()

        return stop

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    # --- read -------------------------------------------------------------------

    def active(self, now: datetime | None = None) -> bool:
        return self.state.active(now or dt_util.utcnow())

    def active_at(self, moment: datetime, now: datetime | None = None) -> bool:
        return self.state.active_at(moment, now or dt_util.utcnow())

    def was(self, moment: datetime, now: datetime | None = None) -> bool:
        return self.state.was(moment, now or dt_util.utcnow())

    def diagnostics(self) -> dict[str, Any]:
        return {"auto_enabled": self.auto_enabled, "active": self.active(), **self.state.as_dict()}

    # --- change -----------------------------------------------------------------

    def set_manual(self, on: bool, until: datetime | None = None) -> None:
        now = dt_util.utcnow()
        if on and until is None and self.state.until is not None and self.state.until > now:
            until = self.state.until  # an end set before switching on
        self.state.set_manual(on, now, until if until is None or until > now else None)
        self._changed()

    def set_until(self, until: datetime | None) -> None:
        self.state.set_until(None if until is None else dt_util.as_utc(until), dt_util.utcnow())
        self._changed()

    @callback
    def _on_minute(self, now: datetime) -> None:
        self._evaluate(dt_util.utcnow())

    @callback
    def _on_zone(self, event: Event[EventStateChangedData]) -> None:
        self._evaluate(dt_util.utcnow())

    def _evaluate(self, now: datetime) -> None:
        changed = self.state.check(now)
        if self.auto_enabled:
            zone = self.hass.states.get(HOME_ZONE)
            people: int | None = None
            if zone is not None and zone.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                try:
                    people = int(float(zone.state))
                except ValueError:
                    people = None
            if people == 0:
                assert zone is not None
                self._away_since = self._away_since or zone.last_changed
                if not self.state.auto and now - self._away_since >= AWAY_AFTER:
                    self.state.set_auto(True, now)
                    LOGGER.info("Nobody home for %s: vacation on", AWAY_AFTER)
                    changed = True
            elif people is not None:
                self._away_since = None
                if self.state.auto:
                    self.state.set_auto(False, now)
                    LOGGER.info("Someone is home again: automatic vacation off")
                    changed = True
        if changed:
            self._changed()

    def _changed(self) -> None:
        self._store.async_delay_save(self.state.as_dict, 1)
        for listener in list(self._listeners):
            listener()
