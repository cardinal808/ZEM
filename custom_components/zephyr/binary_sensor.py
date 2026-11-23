"""Binary sensors per set: online and fault."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ZephyrConfigEntry, ZephyrRuntime
from .coordinator import SetCoordinator
from .entity import ZephyrControlEntity, ZephyrSetEntity


async def async_setup_entry(hass: HomeAssistant, entry: ZephyrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities([ZephyrP1Sensor(entry.runtime_data, entry)])
    for subentry_id, coordinator in entry.runtime_data.coordinators.items():
        async_add_entities(
            [ZephyrOnlineSensor(coordinator, entry), ZephyrFaultSensor(coordinator, entry)],
            config_subentry_id=subentry_id,
        )


class ZephyrOnlineSensor(ZephyrSetEntity, BinarySensorEntity):
    """On when the set answers; always available itself."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: SetCoordinator, entry: ZephyrConfigEntry) -> None:
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


class ZephyrFaultSensor(ZephyrSetEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: SetCoordinator, entry: ZephyrConfigEntry) -> None:
        super().__init__(coordinator, entry, "fault", "binary_sensor")

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data
        return bool(data and data.report and data.report.fault)


class ZephyrP1Sensor(ZephyrControlEntity, BinarySensorEntity):
    """On when the P1 meter reports fresh values."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, runtime: ZephyrRuntime, entry: ZephyrConfigEntry) -> None:
        super().__init__(runtime, entry, "p1_ok", "binary_sensor")

    @property
    def is_on(self) -> bool:
        result = self._control.result
        return bool(result and result.p1_ok)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        result = self._control.result
        return {"source": self._control.p1_entity, "interval_s": result.p1_interval if result else None}
