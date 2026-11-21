"""Base classes for ZEM entities (SPEC-entiteiten)."""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ZemConfigEntry, ZemRuntime
from .const import DOMAIN, MANUFACTURER
from .coordinator import SetCoordinator


def installation_device(entry: ZemConfigEntry) -> DeviceInfo:
    return DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, name="ZEM", manufacturer="ZEM", model="Installation")


class ZemSetEntity(CoordinatorEntity[SetCoordinator]):
    """Entity of one set (device "ZEM Set n").

    Entity ids are English and fixed (E1): ``<platform>.zem_set_<n>_<key>``.
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: SetCoordinator, entry: ZemConfigEntry, key: str, platform: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.serial}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"{platform}.zem_set_{coordinator.number}_{key}"
        report = coordinator.data.report if coordinator.data else None
        firmware = report.packs[0].firmware if report and report.packs else None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.serial)},
            name=f"ZEM Set {coordinator.number}",
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


class ZemTotalEntity(Entity):
    """Entity of the installation (device "ZEM"), fed by all sets."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, runtime: ZemRuntime, entry: ZemConfigEntry, key: str, platform: str) -> None:
        self._runtime = runtime
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"{platform}.zem_{key}"
        self._attr_device_info = installation_device(entry)

    async def async_added_to_hass(self) -> None:
        for coordinator in self._runtime.coordinators.values():
            self.async_on_remove(coordinator.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
