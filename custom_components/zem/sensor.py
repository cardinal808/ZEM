"""Sensors: per set and totals (read-only in M2)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import ZemConfigEntry, ZemRuntime
from .control import ZemControl
from .coordinator import SetCoordinator, SetData
from .core.engine import Action
from .core.models import SetStatus
from .core.totals import Totals
from .entity import ZemControlEntity, ZemSetEntity, ZemTotalEntity

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


SET_SENSORS: tuple[ZemSetSensorDescription, ...] = (
    ZemSetSensorDescription(
        key="state_of_charge",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_r(lambda d: d.report.soc if d.report else None),
    ),
    ZemSetSensorDescription(
        key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=_r(lambda d: d.report.battery_power_ac if d.report else None),
    ),
    ZemSetSensorDescription(
        key="charge_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=_r(lambda d: max(d.report.battery_power_ac, 0.0) if d.report else None),
    ),
    ZemSetSensorDescription(
        key="discharge_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=_r(lambda d: max(-d.report.battery_power_ac, 0.0) if d.report else None),
    ),
    ZemSetSensorDescription(
        key="solar_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=_r(lambda d: d.report.solar_power if d.report else None),
    ),
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
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
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
    ZemTotalSensorDescription(
        key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda t: t.power,
    ),
    ZemTotalSensorDescription(
        key="charge_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda t: t.charge_power,
    ),
    ZemTotalSensorDescription(
        key="discharge_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda t: t.discharge_power,
    ),
    ZemTotalSensorDescription(
        key="solar_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda t: t.solar_power,
    ),
    ZemTotalSensorDescription(key="sets_online", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda t: t.sets_online),
)


async def async_setup_entry(hass: HomeAssistant, entry: ZemConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    runtime = entry.runtime_data
    async_add_entities(ZemTotalSensor(runtime, entry, d) for d in TOTAL_SENSORS)
    assert runtime.control is not None
    async_add_entities(ZemControlSensor(runtime, entry, d) for d in CONTROL_SENSORS)
    for subentry_id, coordinator in runtime.coordinators.items():
        async_add_entities(
            [*(ZemSetSensor(coordinator, entry, d) for d in SET_SENSORS), ZemSetSetpointSensor(coordinator, entry, runtime.control)],
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


# --- control loop (M3: shadow mode) ---------------------------------------------


@dataclass(frozen=True, kw_only=True)
class ZemControlSensorDescription(SensorEntityDescription):
    value_fn: Callable[[ZemControl], StateValue]
    attrs_fn: Callable[[ZemControl], dict[str, Any] | None] = lambda c: None


def _language(control: ZemControl) -> str:
    return str(control.hass.config.language or "en")


CONTROL_SENSORS: tuple[ZemControlSensorDescription, ...] = (
    ZemControlSensorDescription(
        key="setpoint",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda c: c.result.setpoint if c.result else None,
    ),
    ZemControlSensorDescription(
        key="grid_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda c: c.result.grid_power if c.result else None,
    ),
    ZemControlSensorDescription(
        key="action",
        device_class=SensorDeviceClass.ENUM,
        options=[a.value for a in Action],
        value_fn=lambda c: c.result.action.value if c.result else None,
    ),
    ZemControlSensorDescription(
        key="reason",
        value_fn=lambda c: c.result.reason.text(_language(c))[:255] if c.result else None,
        attrs_fn=lambda c: {"code": c.result.reason.code.value} if c.result else None,
    ),
    ZemControlSensorDescription(
        key="control",
        device_class=SensorDeviceClass.ENUM,
        options=["shadow", "active"],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: "shadow" if c.shadow else "active",
    ),
)


class ZemControlSensor(ZemControlEntity, SensorEntity):
    entity_description: ZemControlSensorDescription

    def __init__(self, runtime: ZemRuntime, entry: ZemConfigEntry, description: ZemControlSensorDescription) -> None:
        super().__init__(runtime, entry, description.key, "sensor")
        self.entity_description = description

    @property
    def native_value(self) -> StateValue:
        return self.entity_description.value_fn(self._control)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self.entity_description.attrs_fn(self._control)


class ZemSetSetpointSensor(ZemSetEntity, SensorEntity):
    """What ZEM would command this set (in shadow mode not sent)."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SetCoordinator, entry: ZemConfigEntry, control: ZemControl) -> None:
        super().__init__(coordinator, entry, "setpoint", "sensor")
        self._control = control

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._control.async_add_listener(self._on_control))

    @callback
    def _on_control(self) -> None:
        if self._attr_native_value != self._value():
            self.async_write_ha_state()

    def _value(self) -> int | None:
        result = self._control.result
        return result.targets.get(self.coordinator.subentry_id) if result else None

    @property
    def native_value(self) -> int | None:
        self._attr_native_value = self._value()
        return self._attr_native_value
