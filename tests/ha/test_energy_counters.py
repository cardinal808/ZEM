"""Own energy counters per set as entities (SPEC-tellers T1)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets
from .test_shadow import _install_with_p1

CHARGED = "sensor.zephyr_set_1_energy_charged"
TOTAL = "sensor.zephyr_energy_charged"


async def _wait(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: int) -> None:
    for _ in range(seconds // 5):
        freezer.tick(timedelta(seconds=5))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()


async def test_counters_follow_the_pack_power(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets, "charge_2400")
    await _wait(hass, freezer, 900)
    state = hass.states.get(CHARGED)
    assert state is not None
    assert state.attributes["state_class"] == "total_increasing" and state.attributes["unit_of_measurement"] == "kWh"
    assert float(state.state) == pytest.approx(2.386 * 0.25, abs=0.02)
    assert float(hass.states.get(TOTAL).state) == pytest.approx(float(state.state), abs=0.002)
    assert float(hass.states.get("sensor.zephyr_set_1_energy_discharged").state) == 0.0
    # Diagnostic counters exist but are disabled by default.
    registry = er.async_get(hass)
    assert registry.async_get("sensor.zephyr_set_1_dc_energy_charged").disabled_by is not None

    # 30 s unreadable: the counter keeps counting the held power.
    before = float(hass.states.get(CHARGED).state)
    fake_sets.fail("10.0.0.10")
    await _wait(hass, freezer, 30)
    fake_sets.add("10.0.0.10", "charge_2400")
    await _wait(hass, freezer, 30)
    assert float(hass.states.get(CHARGED).state) == pytest.approx(before + 2.386 * 60 / 3600, abs=0.01)

    # A reload keeps the counter state.
    value = float(hass.states.get(CHARGED).state)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    await _wait(hass, freezer, 5)
    assert float(hass.states.get(CHARGED).state) == pytest.approx(value, abs=0.01)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["energy_counters"]["sets"][0]["set"] == 1
