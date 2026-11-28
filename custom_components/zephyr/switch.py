"""``switch.zephyr_control``: ZEPHYR controls the battery (live) or only computes (shadow).

Off by default (PLAN-M4b §2.2, L3, L5). After a restart of Home Assistant or a reload,
the switch comes back on only when the option "Live control off after a restart" is
disabled; during the test phase that option is on, so the user confirms every time.

What the user wants (live or not) is kept apart from the state: a start that cannot go
live yet keeps trying and does not turn the wish off, also not over a next restart.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.restore_state import ExtraStoredData, RestoredExtraData, RestoreEntity

from . import ZephyrConfigEntry, ZephyrRuntime
from .const import CONF_LIVE_OFF_AFTER_RESTART, DOMAIN, LOGGER
from .entity import ZephyrControlEntity, ZephyrVacationEntity
from .vacation import VacationManager

RESUME_EVERY = timedelta(seconds=5)
RESUME_FOR = timedelta(minutes=10)
"""After a restart live control comes back as soon as it can: every 5 s for this long, then
a repair issue and every 30 s until it can (or the user switches off)."""
RESUME_SLOW = timedelta(seconds=30)


async def async_setup_entry(hass: HomeAssistant, entry: ZephyrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    entities: list[SwitchEntity] = [ZephyrControlSwitch(entry.runtime_data, entry)]
    if entry.runtime_data.vacation is not None:
        entities.append(ZephyrVacationSwitch(entry.runtime_data.vacation, entry))
    async_add_entities(entities)


class ZephyrControlSwitch(ZephyrControlEntity, SwitchEntity, RestoreEntity):
    _attr_icon = "mdi:battery-sync"

    def __init__(self, runtime: ZephyrRuntime, entry: ZephyrConfigEntry) -> None:
        super().__init__(runtime, entry, "control", "switch")
        self._entry = entry
        self._resume_unsub: Callable[[], None] | None = None
        self._resume_since: float | None = None
        self._resume_slow = False

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        extra = await self.async_get_last_extra_data()
        stored = extra.as_dict().get("wanted_live") if extra is not None else None
        wanted = stored if isinstance(stored, bool) else last is not None and last.state == STATE_ON
        if not wanted:
            return  # a new installation, or shadow mode before: stay in shadow mode
        self._control.wanted_live = True
        issue_id = "live_off_after_restart"
        if self._entry.options.get(CONF_LIVE_OFF_AFTER_RESTART, False):
            ir.async_create_issue(
                self.hass, DOMAIN, issue_id, is_fixable=False, severity=ir.IssueSeverity.WARNING, translation_key=issue_id
            )
            return
        # Live before the restart: live again as soon as the P1 reports and the sets are online.
        self._resume_since = time.monotonic()
        self._resume_slow = False
        self._resume_unsub = async_track_time_interval(self.hass, self._try_resume, RESUME_EVERY)
        self.async_on_remove(self._stop_resume)
        await self._try_resume()

    async def _try_resume(self, _now: Any = None) -> None:
        if not self._control.shadow or not self._control.wanted_live:
            self._stop_resume()
            return
        blockers = self._control.live_blockers()
        if not blockers:
            try:
                await self._control.async_set_live(True, reason="resumed")
            except Exception as err:
                LOGGER.debug("Live control not resumed yet: %s", err)
                return
            LOGGER.info("Live control resumed after the restart")
            ir.async_delete_issue(self.hass, DOMAIN, "live_not_resumed")
            self._stop_resume()
            self.async_write_ha_state()
            return
        if not self._resume_slow and self._resume_since is not None and time.monotonic() - self._resume_since > RESUME_FOR.total_seconds():
            # Not given up: a set or P1 that comes back later still gets live control back.
            LOGGER.warning("Live control not resumed after the restart yet, trying on: %s", "; ".join(blockers))
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                "live_not_resumed",
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key="live_not_resumed",
                translation_placeholders={"reasons": "; ".join(blockers)},
            )
            self._control.note_live("not_resumed", "blocked", blockers=blockers)
            self._resume_slow = True
            if self._resume_unsub is not None:
                self._resume_unsub()
            self._resume_unsub = async_track_time_interval(self.hass, self._try_resume, RESUME_SLOW)

    @callback
    def _stop_resume(self) -> None:
        if self._resume_unsub is not None:
            self._resume_unsub()
            self._resume_unsub = None
        self._resume_since = None
        self._resume_slow = False

    @property
    def is_on(self) -> bool:
        return not self._control.shadow

    @property
    def extra_restore_state_data(self) -> ExtraStoredData:
        return RestoredExtraData({"wanted_live": self._control.wanted_live})

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        last = self._control.last_shadow
        return {
            "blockers": self._control.live_blockers() if self._control.shadow else [],
            "wanted_live": self._control.wanted_live,
            "resuming": self._resume_unsub is not None,
            "last_shadow_at": None if last is None else last["time"],
            "last_shadow_reason": None if last is None else last["reason"],
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._stop_resume()
        ir.async_delete_issue(self.hass, DOMAIN, "live_off_after_restart")
        ir.async_delete_issue(self.hass, DOMAIN, "live_not_resumed")
        await self._control.async_set_live(True)
        self._control.wanted_live = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._stop_resume()
        self._control.wanted_live = False
        await self._control.async_set_live(False)
        self.async_write_ha_state()


class ZephyrVacationSwitch(ZephyrVacationEntity, SwitchEntity):
    """``switch.zephyr_vacation`` (B42): away; the planner uses the standby use and learns apart."""

    _attr_icon = "mdi:airplane"

    def __init__(self, vacation: VacationManager, entry: ZephyrConfigEntry) -> None:
        super().__init__(vacation, entry, "vacation", "switch")

    @property
    def is_on(self) -> bool:
        return self._vacation.active()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        state = self._vacation.state
        return {
            "until": None if state.until is None else state.until.isoformat(),
            "automatic": state.auto,
            "since": None if state.started is None else state.started.isoformat(),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._vacation.set_manual(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._vacation.set_manual(False)
