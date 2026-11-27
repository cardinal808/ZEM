"""Suggestions in the settings: by integration and device, not only by name."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zephyr.config_flow import suggest_meter_counters, suggest_p1_entity, suggest_solar

POWER = {"device_class": "power", "unit_of_measurement": "W", "state_class": "measurement"}
ENERGY = {"device_class": "energy", "unit_of_measurement": "kWh", "state_class": "total_increasing"}


def _entity(hass: HomeAssistant, platform: str, unique_id: str, object_id: str, attrs: dict, model: str | None = None) -> str:
    config = MockConfigEntry(domain=platform)
    config.add_to_hass(hass)
    device_id = None
    if model is not None:
        device = dr.async_get(hass).async_get_or_create(
            config_entry_id=config.entry_id, identifiers={(platform, unique_id)}, manufacturer="HomeWizard", model=model
        )
        device_id = device.id
    entity = (
        er.async_get(hass)
        .async_get_or_create("sensor", platform, unique_id, suggested_object_id=object_id, config_entry=config, device_id=device_id)
        .entity_id
    )
    hass.states.async_set(entity, "100", attrs)
    return entity


async def test_homewizard_p1_by_device_not_its_plug(hass: HomeAssistant) -> None:
    _entity(hass, "homewizard", "plug_power", "keuken_stekker_vermogen", POWER, model="HWE-SKT")
    meter = _entity(hass, "homewizard", "p1_power", "meterkast_vermogen", POWER, model="HWE-P1")
    _entity(hass, "homewizard", "p1_power_l1", "meterkast_vermogen_l1", POWER, model="HWE-P1")
    assert suggest_p1_entity(hass) == meter


async def test_solar_counter_of_an_inverter_wins_over_a_name(hass: HomeAssistant) -> None:
    hass.states.async_set("sensor.pv_estimate_total", "1", ENERGY)  # a name match, not an inverter
    inverter = _entity(hass, "solaredge_modbus_multi", "ac_energy", "dak_ac_energie", ENERGY)
    _forecast, energy = suggest_solar(hass)
    assert energy == inverter


async def test_meter_counters_without_tariffs_by_integration(hass: HomeAssistant) -> None:
    imp = _entity(hass, "homewizard", "import", "meterkast_energy_import", ENERGY, model="HWE-P1")
    exp = _entity(hass, "homewizard", "export", "meterkast_energy_export", ENERGY, model="HWE-P1")
    assert suggest_meter_counters(hass) == ([imp], [exp])


async def test_diagnostics_show_the_p1_profile_and_dsmr_version(hass: HomeAssistant, fake_sets: Any) -> None:
    from custom_components.zephyr.diagnostics import _dsmr_version

    meter = _entity(hass, "homewizard", "p1_power", "meterkast_vermogen", POWER, model="HWE-P1")
    device_id = er.async_get(hass).async_get(meter).device_id
    version = (
        er.async_get(hass)
        .async_get_or_create("sensor", "homewizard", "p1_dsmr_version", suggested_object_id="meterkast_dsmr_version", device_id=device_id)
        .entity_id
    )
    hass.states.async_set(version, "42")
    control = SimpleNamespace(p1_entity=meter, p1_pair=None)
    assert _dsmr_version(hass, control) == "42"
    assert _dsmr_version(hass, SimpleNamespace(p1_entity="sensor.other", p1_pair=None)) == "42"  # the only one by name


async def test_dsmr_version_via_the_meter_counters_or_by_name(hass: HomeAssistant) -> None:
    """Peter: the P1 power is a template; the reader's counters show the device. Bjorn: sensor.dsmr_version."""
    from custom_components.zephyr.diagnostics import _dsmr_version

    counter = _entity(hass, "homewizard", "p1_import_t1", "p1_meter_energy_import_tariff_1", ENERGY, model="HWE-P1")
    device_id = er.async_get(hass).async_get(counter).device_id
    version = (
        er.async_get(hass)
        .async_get_or_create("sensor", "homewizard", "p1_dsmr", suggested_object_id="p1_meter_dsmr_version", device_id=device_id)
        .entity_id
    )
    hass.states.async_set(version, "40")
    hass.states.async_set("sensor.homewizard_p1_vermogen", "300", POWER)  # a template: no device
    control = SimpleNamespace(p1_entity="sensor.homewizard_p1_vermogen", p1_pair=None)
    assert _dsmr_version(hass, control, [counter]) == "40"
    assert _dsmr_version(hass, control) == "40"  # by name: the only ...dsmr_version sensor
    hass.states.async_set("sensor.dsmr_version", "50")
    assert _dsmr_version(hass, control) is None  # two by name: unknown
