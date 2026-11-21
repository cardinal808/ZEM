"""Binary sensors per set: online and fault."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ZemConfigEntry
from .coordinator import SetCoordinator
from .entity import ZemSetEntity


async def async_setup_entry(hass: HomeAssistant, entry: ZemConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    for subentry_id, coordinator in entry.runtime_data.coordinators.items():
        async_add_entities(
            [ZemOnlineSensor(coordinator, entry), ZemFaultSensor(coordinator, entry)],
            config_subentry_id=subentry_id,
        )


class ZemOnlineSensor(ZemSetEntity, BinarySensorEntity):
    """On when the set answers; always available itself."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: SetCoordinator, entry: ZemConfigEntry) -> None:
        super().__init__(coordinator, entry, "online", "binary_sensor")

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.online)

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        h = self.coordinator.health
        return {"offline_episodes": h.episodes_offline, "last_error": h.last_error}


class ZemFaultSensor(ZemSetEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: SetCoordinator, entry: ZemConfigEntry) -> None:
        super().__init__(coordinator, entry, "fault", "binary_sensor")

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data
        return bool(data and data.report and data.report.fault)
