"""``switch.zephyr_control``: ZEPHYR controls the battery (live) or only computes (shadow).

Off by default (PLAN-M4b §2.2, L3, L5). After a restart of Home Assistant or a reload,
the switch comes back on only when the option "Live control off after a restart" is
disabled; during the test phase that option is on, so the user confirms every time.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import ZephyrConfigEntry, ZephyrRuntime
from .const import CONF_LIVE_OFF_AFTER_RESTART, DOMAIN, LOGGER
from .entity import ZephyrControlEntity


async def async_setup_entry(hass: HomeAssistant, entry: ZephyrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities([ZephyrControlSwitch(entry.runtime_data, entry)])


class ZephyrControlSwitch(ZephyrControlEntity, SwitchEntity, RestoreEntity):
    _attr_icon = "mdi:battery-sync"

    def __init__(self, runtime: ZephyrRuntime, entry: ZephyrConfigEntry) -> None:
        super().__init__(runtime, entry, "control", "switch")
        self._entry = entry

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is None or last.state != STATE_ON:
            return
        issue_id = "live_off_after_restart"
        if self._entry.options.get(CONF_LIVE_OFF_AFTER_RESTART, True):
            ir.async_create_issue(
                self.hass, DOMAIN, issue_id, is_fixable=False, severity=ir.IssueSeverity.WARNING, translation_key=issue_id
            )
            return
        try:
            await self._control.async_set_live(True)
        except Exception as err:
            LOGGER.warning("Live control not resumed after the restart: %s", err)

    @property
    def is_on(self) -> bool:
        return not self._control.shadow

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"blockers": self._control.live_blockers() if self._control.shadow else []}

    async def async_turn_on(self, **kwargs: Any) -> None:
        ir.async_delete_issue(self.hass, DOMAIN, "live_off_after_restart")
        await self._control.async_set_live(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._control.async_set_live(False)
        self.async_write_ha_state()
