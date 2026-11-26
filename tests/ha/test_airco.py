"""B41 (SPEC-airco) in Home Assistant: the air conditioner is not fed from the battery while heating."""

from __future__ import annotations

import time
from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant

from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets
from .test_shadow import P1, _install_with_p1, _p1

ENERGY = "sensor.airco_energy"
CLIMATE = "climate.airco"


def _energy(hass: HomeAssistant, kwh: float) -> None:
    hass.states.async_set(ENERGY, str(kwh), {"device_class": "energy", "unit_of_measurement": "kWh", "state_class": "total_increasing"})


def _climate(hass: HomeAssistant, mode: str, action: str) -> None:
    hass.states.async_set(CLIMATE, mode, {"hvac_action": action})


async def test_airco_heating_is_not_fed_from_the_battery(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    _energy(hass, 115.0)
    _climate(hass, "heat", "heating")
    entry = await _install_with_p1(hass, fake_sets)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"], {"p1_entity": P1, "excluded_energy_entity": ENERGY, "excluded_climate_entity": CLIMATE}
    )
    await hass.async_block_till_done()
    control = entry.runtime_data.control
    assert control.excluded is not None and control.excluded.active()

    # +0.25 kWh after 500 s: ~1.8 kW.
    freezer.tick(timedelta(seconds=500))
    _energy(hass, 115.25)
    await hass.async_block_till_done()
    assert round(control.excluded.power(time.monotonic())) == 1800

    # P1 2 000 W while the set delivers 760 W: the house wants 2 760 W, of which 1 800 W is the airco.
    for _ in range(20):
        await _p1(hass, freezer, 2000)
    assert round(control.engine.excluded_now) == 1800
    diag = await async_get_config_entry_diagnostics(hass, entry)
    excluded = diag["control"]["excluded_load"]
    assert excluded["active"] and excluded["power_w"] == 1800 and excluded["blocked_modes"] == ["heat"]
    assert any(d.get("excluded") == 1800 for d in diag["control"]["decisions"])

    # The airco stops: at once nothing is excluded any more.
    _climate(hass, "heat", "idle")
    await _p1(hass, freezer, 2000)
    assert control.engine.excluded_now == 0

    # Cooling may come from the battery (default: only heating is blocked).
    _climate(hass, "cool", "cooling")
    await _p1(hass, freezer, 2000)
    assert control.engine.excluded_now == 0


async def test_without_options_nothing_is_excluded(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    assert entry.runtime_data.control.excluded is None
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["control"]["excluded_load"] is None
