"""Sensors: per set and totals (read-only in M2)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ZemConfigEntry, ZemRuntime
from .coordinator import SetCoordinator, SetData
from .core.models import SetStatus
from .core.totals import Totals
from .entity import ZemSetEntity, ZemTotalEntity

StateValue = float | int | str | None


@dataclass(frozen=True, kw_only=True)
class ZemSetSensorDescription(SensorEntityDescription):
    value_fn: Callable[[SetData], StateValue]


@dataclass(frozen=True, kw_only=True)
class ZemTotalSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Totals], StateValue]


def _r(fn: Callable[[SetData], StateValue]) -> Callable[[SetData], StateValue]:
    """Guard against a missing report."""

    def wrapped(data: SetData) -> StateValue:
        return fn(data) if data.report is not None else None

    return wrapped


POWER = {
    "device_class": SensorDeviceClass.POWER,
    "native_unit_of_measurement": UnitOfPower.WATT,
    "state_class": SensorStateClass.MEASUREMENT,
    "suggested_display_precision": 0,
}

SET_SENSORS: tuple[ZemSetSensorDescription, ...] = (
    ZemSetSensorDescription(
        key="state_of_charge",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_r(lambda d: d.report.soc if d.report else None),
    ),
    ZemSetSensorDescription(key="power", **POWER, value_fn=_r(lambda d: d.report.battery_power_ac if d.report else None)),  # type: ignore[arg-type]
    ZemSetSensorDescription(
        key="charge_power",
        **POWER,  # type: ignore[arg-type]
        value_fn=_r(lambda d: max(d.report.battery_power_ac, 0.0) if d.report else None),
    ),
    ZemSetSensorDescription(
        key="discharge_power",
        **POWER,  # type: ignore[arg-type]
        value_fn=_r(lambda d: max(-d.report.battery_power_ac, 0.0) if d.report else None),
    ),
    ZemSetSensorDescription(key="solar_power", **POWER, value_fn=_r(lambda d: d.report.solar_power if d.report else None)),  # type: ignore[arg-type]
    ZemSetSensorDescription(
        key="status",
        device_class=SensorDeviceClass.ENUM,
        options=[s.value for s in SetStatus],
        value_fn=lambda d: d.status.value,
    ),
    ZemSetSensorDescription(
        key="capacity",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda d: d.capacity.capacity_kwh if d.capacity else None,
    ),
    ZemSetSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_r(lambda d: d.report.max_pack_temperature if d.report else None),
    ),
    ZemSetSensorDescription(
        key="offgrid_power",
        **POWER,  # type: ignore[arg-type]
        entity_registry_enabled_default=False,
        value_fn=_r(lambda d: d.report.offgrid_power if d.report else None),
    ),
    ZemSetSensorDescription(
        key="device_min_soc",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_r(lambda d: d.report.min_soc if d.report else None),
    ),
    ZemSetSensorDescription(
        key="device_max_soc",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_r(lambda d: d.report.max_soc if d.report else None),
    ),
    ZemSetSensorDescription(
        key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_r(lambda d: d.report.rssi if d.report else None),
    ),
)

TOTAL_SENSORS: tuple[ZemTotalSensorDescription, ...] = (
    ZemTotalSensorDescription(
        key="state_of_charge",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda t: t.soc,
    ),
    ZemTotalSensorDescription(
        key="energy_stored",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda t: t.energy_kwh,
    ),
    ZemTotalSensorDescription(
        key="capacity",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda t: t.capacity_kwh,
    ),
    ZemTotalSensorDescription(key="power", **POWER, value_fn=lambda t: t.power),  # type: ignore[arg-type]
    ZemTotalSensorDescription(key="charge_power", **POWER, value_fn=lambda t: t.charge_power),  # type: ignore[arg-type]
    ZemTotalSensorDescription(key="discharge_power", **POWER, value_fn=lambda t: t.discharge_power),  # type: ignore[arg-type]
    ZemTotalSensorDescription(key="solar_power", **POWER, value_fn=lambda t: t.solar_power),  # type: ignore[arg-type]
    ZemTotalSensorDescription(key="sets_online", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda t: t.sets_online),
)


async def async_setup_entry(hass: HomeAssistant, entry: ZemConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    runtime = entry.runtime_data
    async_add_entities(ZemTotalSensor(runtime, entry, d) for d in TOTAL_SENSORS)
    for subentry_id, coordinator in runtime.coordinators.items():
        async_add_entities(
            (ZemSetSensor(coordinator, entry, d) for d in SET_SENSORS),
            config_subentry_id=subentry_id,
        )


class ZemSetSensor(ZemSetEntity, SensorEntity):
    entity_description: ZemSetSensorDescription

    def __init__(self, coordinator: SetCoordinator, entry: ZemConfigEntry, description: ZemSetSensorDescription) -> None:
        super().__init__(coordinator, entry, description.key, "sensor")
        self.entity_description = description

    @property
    def available(self) -> bool:
        if self.entity_description.key == "status":
            return self.coordinator.data is not None  # status shows "offline" itself
        return super().available

    @property
    def native_value(self) -> StateValue:
        data = self.coordinator.data
        return self.entity_description.value_fn(data) if data is not None else None


class ZemTotalSensor(ZemTotalEntity, SensorEntity):
    entity_description: ZemTotalSensorDescription

    def __init__(self, runtime: ZemRuntime, entry: ZemConfigEntry, description: ZemTotalSensorDescription) -> None:
        super().__init__(runtime, entry, description.key, "sensor")
        self.entity_description = description

    @property
    def native_value(self) -> StateValue:
        return self.entity_description.value_fn(self._runtime.totals())
