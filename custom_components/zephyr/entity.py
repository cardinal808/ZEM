"""Base classes for ZEPHYR entities (SPEC-entiteiten)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from . import ZephyrConfigEntry, ZephyrRuntime
from .const import DOMAIN, MANUFACTURER
from .coordinator import SetCoordinator

if TYPE_CHECKING:
    import asyncio

    from homeassistant.helpers.entity_platform import EntityPlatform

    from .appliances import Appliance, ApplianceManager
    from .vacation import VacationManager


def installation_device(entry: ZephyrConfigEntry) -> DeviceInfo:
    """Link to the installation device; ``async_setup_entry`` creates it with its name and type."""
    return DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})


class InstallationIds(Entity):
    """Keep the entity ids of the installation at ``zephyr_…``.

    With ``has_entity_name`` HA puts the device name in front of a new entity id; the installation
    device is called *ZEPHYR Applicatie* (translated), so a new installation would get
    ``zephyr_applicatie_…``. This suggests ``zephyr_<English name>`` instead, as before 0.8.73.
    Existing entities keep their registered id.
    """

    def add_to_platform_start(self, hass: HomeAssistant, platform: EntityPlatform, parallel_updates: asyncio.Semaphore | None) -> None:
        super().add_to_platform_start(hass, platform, parallel_updates)
        key = self.translation_key
        if key is None or self.entity_id:  # an id of its own, or nothing to name it by
            return
        name = platform.platform_data.object_id_platform_translations.get(f"component.{DOMAIN}.entity.{platform.domain}.{key}.name")
        if name:
            self.entity_id = f"{platform.domain}.{slugify(f'{DOMAIN} {name}')}"


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


class ZephyrTotalEntity(InstallationIds):
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


class ZephyrControlEntity(InstallationIds):
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


class ZephyrVacationEntity(InstallationIds):
    """Entity of the installation for the vacation (B42)."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, vacation: VacationManager, entry: ZephyrConfigEntry, key: str, platform: str) -> None:
        self._vacation = vacation
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"{platform}.zephyr_{key}"
        self._attr_device_info = installation_device(entry)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._vacation.async_add_listener(self.async_write_ha_state))


class ZephyrApplianceEntity(Entity):
    """Entity of a planned appliance (B36): device per appliance, id ``<platform>.zephyr_<slug>_<key>``."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, manager: ApplianceManager, appliance: Appliance, entry: ZephyrConfigEntry, key: str, platform: str) -> None:
        from homeassistant.util import slugify

        self.manager = manager
        self.appliance = appliance
        self._attr_unique_id = f"{appliance.id}_{key}"
        self._attr_translation_key = f"appliance_{key}"
        self.entity_id = f"{platform}.zephyr_{slugify(appliance.name)}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, appliance.id)},
            name=appliance.name,
            manufacturer=MANUFACTURER,
            model="Planned appliance",
            via_device=(DOMAIN, entry.entry_id),
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.manager.async_add_listener(self.async_write_ha_state))
