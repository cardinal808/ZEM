"""Shadow mode: ZEPHYR computes with the P1 meter but writes nothing."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.zephyr.const import DOMAIN
from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets

P1 = "sensor.p1_meter_power"


async def _install_with_p1(hass: HomeAssistant, fake_sets: FakeSets, fixture: str = "deliver_760") -> config_entries.ConfigEntry[Any]:
    fake_sets.add("10.0.0.10", fixture)
    hass.states.async_set(P1, "300", {"device_class": "power", "unit_of_measurement": "W"})
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": "10.0.0.10"})
    entry = result["result"]
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    # The P1 sensor is suggested automatically.
    schema_default = next(k.default() for k in result["data_schema"].schema if k == "p1_entity")
    assert schema_default == P1
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": P1})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    return hass.config_entries.async_entries(DOMAIN)[0]


async def _p1(hass: HomeAssistant, freezer: FrozenDateTimeFactory, watts: float, seconds: float = 1.0) -> None:
    freezer.tick(timedelta(seconds=seconds))
    hass.states.async_set(P1, str(watts), {"device_class": "power", "unit_of_measurement": "W"}, force_update=True)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()


async def test_shadow_mode_computes_and_writes_nothing(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    await _install_with_p1(hass, fake_sets)
    assert hass.states.get("select.zephyr_mode").state == "zero_meter"
    assert hass.states.get("sensor.zephyr_control").state == "shadow"
    for _ in range(6):
        await _p1(hass, freezer, 300)
    # Set delivers 760 W (measured), house still imports 300 W → ZEPHYR would deliver about 1045 W.
    setpoint = float(hass.states.get("sensor.zephyr_setpoint").state)
    assert -1100 <= setpoint <= -1000
    assert hass.states.get("sensor.zephyr_action").state == "deliver"
    assert float(hass.states.get("sensor.zephyr_set_1_setpoint").state) == setpoint
    assert hass.states.get("binary_sensor.zephyr_p1_ok").state == "on"
    assert "Levert" in hass.states.get("sensor.zephyr_reason").state or "Delivering" in hass.states.get("sensor.zephyr_reason").state
    assert fake_sets.writes == []


async def test_p1_silence_is_detected(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    await _install_with_p1(hass, fake_sets)
    for watts in (300, 310, 305, 300):  # a meter with a new value every second
        await _p1(hass, freezer, watts)
    for _ in range(12):
        freezer.tick(timedelta(seconds=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
    assert hass.states.get("binary_sensor.zephyr_p1_ok").state == "off"
    assert hass.states.get("sensor.zephyr_setpoint").state == "0"
    assert hass.states.get("sensor.zephyr_reason").attributes["code"] == "p1_stale"


async def test_standby_mode_and_restore(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    await hass.services.async_call("select", "select_option", {"entity_id": "select.zephyr_mode", "option": "standby"}, blocking=True)
    await _p1(hass, freezer, 500)
    assert hass.states.get("sensor.zephyr_action").state == "standby"
    assert hass.states.get("sensor.zephyr_setpoint").state == "0"
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("select.zephyr_mode").state == "standby"


async def test_decisions_in_diagnostics(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    for watts in (300, 300, 300, -400, -400, -400):
        await _p1(hass, freezer, watts, seconds=2)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    control = diag["control"]
    assert control["shadow"] is True
    assert control["p1_entity"] == P1
    assert control["decisions"]
    assert all(d["sent"] is False for d in control["decisions"])
    assert "10.0.0.10" not in str(diag)


async def test_soc_limits_in_options(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": P1, "min_soc": 15, "max_soc": 100})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    settings = (await async_get_config_entry_diagnostics(hass, entry))["control"]["settings"]
    assert (settings["min_soc"], settings["max_soc"]) == (15.0, 100.0)
