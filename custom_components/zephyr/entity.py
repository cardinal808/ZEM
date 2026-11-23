"""Base classes for ZEPHYR entities (SPEC-entiteiten)."""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZephyrConfigEntry, ZephyrRuntime
from .const import DOMAIN, MANUFACTURER
from .coordinator import SetCoordinator


def installation_device(entry: ZephyrConfigEntry) -> DeviceInfo:
    return DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, name="ZEPHYR", manufacturer="ZEPHYR", model="Installation")


class ZephyrSetEntity(CoordinatorEntity[SetCoordinator]):
    """Entity of one set (device "ZEPHYR Set n").

    Entity ids are English and fixed (E1): ``<platform>.zephyr_set_<n>_<key>``.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: SetCoordinator, entry: ZephyrConfigEntry, key: str, platform: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.serial}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"{platform}.zephyr_set_{coordinator.number}_{key}"
        report = coordinator.data.report if coordinator.data else None
        firmware = report.packs[0].firmware if report and report.packs else None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.serial)},
            name=f"ZEPHYR Set {coordinator.number}",
            manufacturer=MANUFACTURER,
            model=coordinator.model_name,
            serial_number=coordinator.serial,
            sw_version=str(firmware) if firmware is not None else None,
            via_device=(DOMAIN, entry.entry_id),
        )

    @property
    def available(self) -> bool:
        data = self.coordinator.data
        return super().available and data is not None and data.online and data.report is not None


class ZephyrTotalEntity(Entity):
    """Entity of the installation (device "ZEPHYR"), fed by all sets."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, runtime: ZephyrRuntime, entry: ZephyrConfigEntry, key: str, platform: str) -> None:
        self._runtime = runtime
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"{platform}.zephyr_{key}"
        self._attr_device_info = installation_device(entry)

    async def async_added_to_hass(self) -> None:
        for coordinator in self._runtime.coordinators.values():
            self.async_on_remove(coordinator.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()


class ZephyrControlEntity(Entity):
    """Entity of the installation fed by the control loop; writes state only on change."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, runtime: ZephyrRuntime, entry: ZephyrConfigEntry, key: str, platform: str) -> None:
        assert runtime.control is not None
        self._control = runtime.control
        self._runtime = runtime
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"{platform}.zephyr_{key}"
        self._attr_device_info = installation_device(entry)
        self._last_written: object = None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._control.async_add_listener(self._handle_update))

    def _fingerprint(self) -> object:
        return (self.state, self.extra_state_attributes)

    @callback
    def _handle_update(self) -> None:
        fingerprint = self._fingerprint()
        if fingerprint != self._last_written:
            self._last_written = fingerprint
            self.async_write_ha_state()
