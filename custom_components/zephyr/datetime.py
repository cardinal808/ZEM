"""``datetime.zephyr_vacation_until`` (B42): the end of a vacation; at that moment it switches off."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ZephyrConfigEntry
from .entity import ZephyrVacationEntity
from .vacation import VacationManager


async def async_setup_entry(hass: HomeAssistant, entry: ZephyrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    if entry.runtime_data.vacation is not None:
        async_add_entities([ZephyrVacationUntil(entry.runtime_data.vacation, entry)])


class ZephyrVacationUntil(ZephyrVacationEntity, DateTimeEntity):
    _attr_icon = "mdi:calendar-end"

    def __init__(self, vacation: VacationManager, entry: ZephyrConfigEntry) -> None:
        super().__init__(vacation, entry, "vacation_until", "datetime")

    @property
    def native_value(self) -> datetime | None:
        return self._vacation.state.until

    async def async_set_value(self, value: datetime) -> None:
        self._vacation.set_until(value)
