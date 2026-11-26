"""Sensors: per set and totals (read-only in M2)."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
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
from homeassistant.util import dt as dt_util

from . import ZephyrConfigEntry, ZephyrRuntime
from .control import ZephyrControl
from .coordinator import SetCoordinator, SetData
from .core.engine import Action
from .core.forecast_plan import ACTION_KEYS, PlanOutcome, PlanState, reason
from .core.models import SetStatus
from .core.totals import Totals
from .cost_recorder import CostRecorder
from .energy_recorder import EnergyRecorder
from .entity import ZephyrControlEntity, ZephyrSetEntity, ZephyrTotalEntity, installation_device
from .planner_runner import PlanRunner

StateValue = float | int | str | None


@dataclass(frozen=True, kw_only=True)
class ZephyrSetSensorDescription(SensorEntityDescription):
    value_fn: Callable[[SetData], StateValue]


@dataclass(frozen=True, kw_only=True)
class ZephyrTotalSensorDescription(SensorEntityDescription):
    value_fn: Callable[[Totals], StateValue]


def _r(fn: Callable[[SetData], StateValue]) -> Callable[[SetData], StateValue]:
    """Guard against a missing report."""

    def wrapped(data: SetData) -> StateValue:
        return fn(data) if data.report is not None else None

    return wrapped


SET_SENSORS: tuple[ZephyrSetSensorDescription, ...] = (
    ZephyrSetSensorDescription(
        key="state_of_charge",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_r(lambda d: d.report.soc if d.report else None),
    ),
    ZephyrSetSensorDescription(
        key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=_r(lambda d: d.report.battery_power_ac if d.report else None),
    ),
    ZephyrSetSensorDescription(
        key="charge_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=_r(lambda d: max(d.report.battery_power_ac, 0.0) if d.report else None),
    ),
    ZephyrSetSensorDescription(
        key="discharge_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=_r(lambda d: max(-d.report.battery_power_ac, 0.0) if d.report else None),
    ),
    ZephyrSetSensorDescription(
        key="solar_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=_r(lambda d: d.report.solar_power if d.report else None),
    ),
    ZephyrSetSensorDescription(
        key="status",
        device_class=SensorDeviceClass.ENUM,
        options=[s.value for s in SetStatus],
        value_fn=lambda d: d.status.value,
    ),
    ZephyrSetSensorDescription(
        key="capacity",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda d: d.capacity.capacity_kwh if d.capacity else None,
    ),
    ZephyrSetSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=_r(lambda d: d.report.max_pack_temperature if d.report else None),
    ),
    ZephyrSetSensorDescription(
        key="offgrid_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=_r(lambda d: d.report.offgrid_power if d.report else None),
    ),
    ZephyrSetSensorDescription(
        key="device_min_soc",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_r(lambda d: d.report.min_soc if d.report else None),
    ),
    ZephyrSetSensorDescription(
        key="device_max_soc",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_r(lambda d: d.report.max_soc if d.report else None),
    ),
    ZephyrSetSensorDescription(
        key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=_r(lambda d: d.report.rssi if d.report else None),
    ),
)

TOTAL_SENSORS: tuple[ZephyrTotalSensorDescription, ...] = (
    ZephyrTotalSensorDescription(
        key="state_of_charge",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda t: t.soc,
    ),
    ZephyrTotalSensorDescription(
        key="energy_stored",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value_fn=lambda t: t.energy_kwh,
    ),
    ZephyrTotalSensorDescription(
        key="capacity",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda t: t.capacity_kwh,
    ),
    ZephyrTotalSensorDescription(
        key="power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda t: t.power,
    ),
    ZephyrTotalSensorDescription(
        key="charge_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda t: t.charge_power,
    ),
    ZephyrTotalSensorDescription(
        key="discharge_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda t: t.discharge_power,
    ),
    ZephyrTotalSensorDescription(
        key="solar_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda t: t.solar_power,
    ),
    ZephyrTotalSensorDescription(key="sets_online", state_class=SensorStateClass.MEASUREMENT, value_fn=lambda t: t.sets_online),
)


async def async_setup_entry(hass: HomeAssistant, entry: ZephyrConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    runtime = entry.runtime_data
    async_add_entities(ZephyrTotalSensor(runtime, entry, d) for d in TOTAL_SENSORS)
    assert runtime.control is not None
    async_add_entities(ZephyrControlSensor(runtime, entry, d) for d in CONTROL_SENSORS)
    if runtime.planner is not None:
        async_add_entities(ZephyrPlanSensor(runtime.planner, entry, d) for d in PLAN_SENSORS)
    if runtime.costs is not None:
        async_add_entities(ZephyrCostSensor(runtime.costs, entry, kind, period) for kind in ("costs", "savings") for period in COST_PERIODS)
    energy = runtime.energy
    if energy is not None:
        with_solar = any(
            c.data is not None and c.data.report is not None and c.data.report.solar_power_inputs for c in runtime.coordinators.values()
        )
        async_add_entities(ZephyrEnergyTotalSensor(energy, entry, key) for key in ENERGY_TOTALS if key != "solar" or with_solar)
    for subentry_id, coordinator in runtime.coordinators.items():
        if energy is not None:
            report = coordinator.data.report if coordinator.data is not None else None
            async_add_entities(
                (
                    ZephyrSetEnergySensor(coordinator, entry, energy, counter)
                    for counter in ENERGY_SET_SENSORS
                    if counter != "solar" or (report is not None and report.solar_power_inputs)
                ),
                config_subentry_id=subentry_id,
            )
        async_add_entities(
            [
                *(ZephyrSetSensor(coordinator, entry, d) for d in SET_SENSORS),
                ZephyrSetSetpointSensor(coordinator, entry, runtime.control),
                ZephyrSetCounterSensor(coordinator, entry, runtime.control, "write_count"),
                ZephyrSetCounterSensor(coordinator, entry, runtime.control, "switch_count"),
            ],
            config_subentry_id=subentry_id,
        )


class ZephyrSetSensor(ZephyrSetEntity, SensorEntity):
    entity_description: ZephyrSetSensorDescription

    def __init__(self, coordinator: SetCoordinator, entry: ZephyrConfigEntry, description: ZephyrSetSensorDescription) -> None:
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


class ZephyrTotalSensor(ZephyrTotalEntity, SensorEntity):
    entity_description: ZephyrTotalSensorDescription

    def __init__(self, runtime: ZephyrRuntime, entry: ZephyrConfigEntry, description: ZephyrTotalSensorDescription) -> None:
        super().__init__(runtime, entry, description.key, "sensor")
        self.entity_description = description

    @property
    def native_value(self) -> StateValue:
        return self.entity_description.value_fn(self._runtime.totals())


# --- control loop (M3: shadow mode) ---------------------------------------------


@dataclass(frozen=True, kw_only=True)
class ZephyrControlSensorDescription(SensorEntityDescription):
    value_fn: Callable[[ZephyrControl], StateValue]
    attrs_fn: Callable[[ZephyrControl], dict[str, Any] | None] = lambda c: None


def _language(control: ZephyrControl) -> str:
    return str(control.hass.config.language or "en")


CONTROL_SENSORS: tuple[ZephyrControlSensorDescription, ...] = (
    ZephyrControlSensorDescription(
        key="setpoint",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda c: c.result.setpoint if c.result else None,
    ),
    ZephyrControlSensorDescription(
        key="grid_power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda c: c.result.grid_power if c.result else None,
    ),
    ZephyrControlSensorDescription(
        key="action",
        device_class=SensorDeviceClass.ENUM,
        options=[a.value for a in Action],
        value_fn=lambda c: c.result.action.value if c.result else None,
    ),
    ZephyrControlSensorDescription(
        key="reason",
        value_fn=lambda c: c.result.reason.text(_language(c))[:255] if c.result else None,
        attrs_fn=lambda c: {"code": c.result.reason.code.value} if c.result else None,
    ),
    ZephyrControlSensorDescription(
        key="control",
        device_class=SensorDeviceClass.ENUM,
        options=["shadow", "active"],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda c: "shadow" if c.shadow else "active",
    ),
)


class ZephyrControlSensor(ZephyrControlEntity, SensorEntity):
    entity_description: ZephyrControlSensorDescription

    def __init__(self, runtime: ZephyrRuntime, entry: ZephyrConfigEntry, description: ZephyrControlSensorDescription) -> None:
        super().__init__(runtime, entry, description.key, "sensor")
        self.entity_description = description

    @property
    def native_value(self) -> StateValue:
        return self.entity_description.value_fn(self._control)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return self.entity_description.attrs_fn(self._control)


class ZephyrSetSetpointSensor(ZephyrSetEntity, SensorEntity):
    """What ZEPHYR would command this set (in shadow mode not sent)."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SetCoordinator, entry: ZephyrConfigEntry, control: ZephyrControl) -> None:
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


class ZephyrSetCounterSensor(ZephyrSetEntity, SensorEntity):
    """Writes (RAM + flash) or relay switches of this set over the last 24 hours (B33).

    In shadow mode the writes are what ZEPHYR would send; relay switches are what
    the set really does.
    """

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: SetCoordinator, entry: ZephyrConfigEntry, control: ZephyrControl, key: str) -> None:
        super().__init__(coordinator, entry, key, "sensor")
        self._control = control
        self._key = key

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._control.async_add_listener(self._on_control))

    def _counts(self) -> dict[str, int]:
        return self._control.engine.counters(time.monotonic()).get(self.coordinator.subentry_id, {})

    @callback
    def _on_control(self) -> None:
        if self._attr_native_value != self._value(self._counts()):
            self.async_write_ha_state()

    def _value(self, counts: dict[str, int]) -> int | None:
        if self._key == "write_count":
            return counts.get("ram_24h", 0) + counts.get("flash_24h", 0)
        return counts.get("relay_24h")  # None (unknown) when the set does not report acStatus

    @property
    def native_value(self) -> int | None:
        self._attr_native_value = self._value(self._counts())
        return self._attr_native_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        counts = self._counts()
        if self._key == "write_count":
            keys: tuple[str, ...] = ("ram_1h", "ram_24h", "flash_1h", "flash_24h", "skipped_1h", "skipped_24h", "flash_paused")
            causes = {k: v for k, v in counts.items() if k.startswith("flash_") and k.endswith("_24h") and k != "flash_24h"}
            return {k: counts.get(k, 0) for k in keys} | causes | {"sent": not self._control.shadow}
        else:
            keys = ("relay_1h", "relay_24h")
            if "relay_24h" not in counts:
                return {"relay_reported": False, "sent": not self._control.shadow}
        return {k: counts.get(k, 0) for k in keys} | {"sent": not self._control.shadow}


COST_PERIODS = ("today", "month", "year")


class ZephyrCostSensor(SensorEntity):
    """Costs or savings of today, this month or this year (B38). € incl. VAT, without fixed costs."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "EUR"
    _attr_state_class = SensorStateClass.TOTAL
    _attr_suggested_display_precision = 2

    def __init__(self, costs: CostRecorder, entry: ZephyrConfigEntry, kind: str, period: str) -> None:
        self._costs = costs
        self._kind = kind
        self._period = period
        key = f"{kind}_{period}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"sensor.zephyr_{key}"
        self._attr_device_info = installation_device(entry)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._costs.async_add_listener(self._handle_update))

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()

    @property
    def native_value(self) -> float | None:
        summary = self._costs.summary(self._period)
        value = summary.cost if self._kind == "costs" else summary.savings
        return None if value is None else round(value, 2)

    @property
    def last_reset(self) -> datetime:
        first, _ = self._costs.period(self._period)
        return dt_util.start_of_local_day(first)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {**self._costs.summary(self._period).as_dict(), "tariffs": self._costs.tariffs.tariffs_for(dt_util.now().date()).source}


# --- planner (M5, SPEC-planner §4) ------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class ZephyrPlanSensorDescription(SensorEntityDescription):
    value_fn: Callable[[PlanRunner, PlanOutcome], StateValue | datetime]
    attrs_fn: Callable[[PlanRunner, PlanOutcome], dict[str, Any] | None] = lambda r, o: None


def _plan_action_attrs(runner: PlanRunner, outcome: PlanOutcome) -> dict[str, Any]:
    return {
        "code": outcome.action.value,
        "blocks": [b.as_dict() for b in outcome.blocks[:24]],
        "timeline": outcome.timeline(),
        "indicative_from": None if outcome.indicative_from is None else outcome.indicative_from.isoformat(),
        "shadow": True,
    }


def _round(value: float, digits: int = 2) -> float:
    return round(value, digits)


PLAN_SENSORS: tuple[ZephyrPlanSensorDescription, ...] = (
    ZephyrPlanSensorDescription(
        key="plan_action",
        device_class=SensorDeviceClass.ENUM,
        options=list(ACTION_KEYS.values()),
        value_fn=lambda r, o: ACTION_KEYS[o.action],
        attrs_fn=_plan_action_attrs,
    ),
    ZephyrPlanSensorDescription(
        key="plan_state",
        device_class=SensorDeviceClass.ENUM,
        options=list(PlanState.ALL),
        value_fn=lambda r, o: o.state,
        attrs_fn=lambda r, o: {"no_prices_since": None if o.no_prices_since is None else o.no_prices_since.isoformat()},
    ),
    ZephyrPlanSensorDescription(
        key="plan_reason",
        value_fn=lambda r, o: reason(o, str(r.hass.config.language or "en"), dt_util.get_default_time_zone())[:255],
    ),
    ZephyrPlanSensorDescription(
        key="planned_grid_charge",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda r, o: _round(o.planned_grid_charge_kwh, 3),
        attrs_fn=lambda r, o: {"cost": _round(o.planned_grid_charge_cost)},
    ),
    ZephyrPlanSensorDescription(
        key="planned_export",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=2,
        value_fn=lambda r, o: _round(o.planned_export_kwh, 3),
        attrs_fn=lambda r, o: {"revenue": _round(o.planned_export_revenue)},
    ),
    ZephyrPlanSensorDescription(
        key="battery_empty_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda r, o: o.empty_at,
    ),
    ZephyrPlanSensorDescription(
        key="plan_calculated_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda r, o: o.calculated_at,
        attrs_fn=lambda r, o: {"duration_s": round(o.duration_s, 3), "expected_cost": _round(o.expected_cost, 3)},
    ),
)


class ZephyrPlanSensor(SensorEntity):
    """What the planner would do (shadow: calculated and shown, not carried out yet)."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _unrecorded_attributes = frozenset({"blocks", "timeline"})
    entity_description: ZephyrPlanSensorDescription

    def __init__(self, runner: PlanRunner, entry: ZephyrConfigEntry, description: ZephyrPlanSensorDescription) -> None:
        self._runner = runner
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_translation_key = description.key
        self.entity_id = f"sensor.zephyr_{description.key}"
        self._attr_device_info = installation_device(entry)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._runner.async_add_listener(self.async_write_ha_state))

    @property
    def available(self) -> bool:
        return self._runner.outcome is not None

    @property
    def native_value(self) -> Any:
        outcome = self._runner.outcome
        return None if outcome is None else self.entity_description.value_fn(self._runner, outcome)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        outcome = self._runner.outcome
        return None if outcome is None else self.entity_description.attrs_fn(self._runner, outcome)


# --- own energy counters (SPEC-tellers T1) ---------------------------------------

ENERGY_SET_SENSORS: dict[str, tuple[str, bool]] = {
    "charged": ("energy_charged", False),
    "discharged": ("energy_discharged", False),
    "solar": ("solar_energy", False),
    "offgrid": ("offgrid_energy", True),
    "dc_charged": ("dc_energy_charged", True),
    "dc_discharged": ("dc_energy_discharged", True),
    "grid_input": ("grid_input_energy", True),
    "output_home": ("output_home_energy", True),
}
"""Counter → (entity key, diagnostic and disabled by default)."""

ENERGY_TOTALS: dict[str, str] = {"charged": "energy_charged", "discharged": "energy_discharged", "solar": "solar_energy"}


class _EnergySensorBase(SensorEntity):
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_suggested_display_precision = 2
    _attr_should_poll = False
    _energy: EnergyRecorder
    _last_value: float | None = None

    def _value(self) -> float | None:
        raise NotImplementedError

    @property
    def native_value(self) -> float | None:
        value = self._value()
        return None if value is None else round(value, 3)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self._energy.async_add_listener(self._handle_energy))

    @callback
    def _handle_energy(self) -> None:
        value = self.native_value
        if value != self._last_value:  # write only when the rounded state moves (recorder)
            self._last_value = value
            self.async_write_ha_state()


class ZephyrSetEnergySensor(ZephyrSetEntity, _EnergySensorBase):
    """An own energy counter of one set."""

    def __init__(self, coordinator: SetCoordinator, entry: ZephyrConfigEntry, energy: EnergyRecorder, counter: str) -> None:
        key, diagnostic = ENERGY_SET_SENSORS[counter]
        super().__init__(coordinator, entry, key, "sensor")
        self._energy = energy
        self._counter = counter
        if diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_entity_registry_enabled_default = False

    @property
    def available(self) -> bool:
        return self._value() is not None

    def _value(self) -> float | None:
        return self._energy.set_kwh(self.coordinator.serial, self._counter)

    @callback
    def _handle_coordinator_update(self) -> None:
        """The counters, not the coordinator, decide when to write."""

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        counter = self._energy.counters.sets.get(self.coordinator.serial)
        if counter is None:
            return None
        attrs: dict[str, Any] = {"estimated_kwh": round(counter.estimated[self._counter], 3)}
        if counter.gaps:
            attrs["last_gap"] = counter.gaps[-1]
        return attrs


class ZephyrEnergyTotalSensor(_EnergySensorBase):
    """An own energy counter of the installation: the increases of all sets."""

    _attr_has_entity_name = True

    def __init__(self, energy: EnergyRecorder, entry: ZephyrConfigEntry, counter: str) -> None:
        key = ENERGY_TOTALS[counter]
        self._energy = energy
        self._counter = counter
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self.entity_id = f"sensor.zephyr_{key}"
        self._attr_device_info = installation_device(entry)

    def _value(self) -> float | None:
        return self._energy.counters.totals[self._counter]
