"""Buttons: plan or clear a run of an appliance (B36)."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ZephyrConfigEntry
from .entity import ZephyrApplianceEntity


async def async_setup_entry(hass: HomeAssistant, entry: ZephyrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    manager = entry.runtime_data.appliances
    if manager is None:
        return
    for appliance in manager.appliances.values():
        async_add_entities(
            [
                ZephyrPlanButton(manager, appliance, entry, "plan", "button"),
                ZephyrClearButton(manager, appliance, entry, "clear", "button"),
            ],
            config_subentry_id=appliance.id,
        )


class ZephyrPlanButton(ZephyrApplianceEntity, ButtonEntity):
    """Plan one run in the standard window (press again for another run)."""

    _attr_icon = "mdi:calendar-plus"

    async def async_press(self) -> None:
        self.manager.plan(self.appliance.id)


class ZephyrClearButton(ZephyrApplianceEntity, ButtonEntity):
    """Remove the planned runs of this appliance."""

    _attr_icon = "mdi:calendar-remove"

    async def async_press(self) -> None:
        self.manager.clear(self.appliance.id)
