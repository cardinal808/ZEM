"""B41 (SPEC-airco) in Home Assistant: the air conditioner is not fed from the battery while heating."""

from __future__ import annotations

import time
from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

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

    # Cost log: the quarter gets the air conditioner's kWh counted while it was excluded.
    costs = entry.runtime_data.costs
    assert costs is not None
    boundary = dt_util.now().replace(second=0, microsecond=0)
    await costs.async_close(boundary)  # first close: reference
    _energy(hass, 115.5)
    freezer.tick(timedelta(seconds=500))
    await hass.async_block_till_done()
    record = await costs.async_close(boundary + timedelta(minutes=15))
    assert record is not None and record["excluded_kwh"] == 0.25

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


async def test_panel_now_shows_the_airco(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    """SPEC-ui-airco §2.1: now.excluded per state (UI-A1)."""
    from custom_components.zephyr.websocket_api import now_snapshot

    entry = await _install_with_p1(hass, fake_sets)
    assert now_snapshot(hass, entry)["excluded"] is None  # not set up

    _energy(hass, 115.0)
    _climate(hass, "heat", "heating")
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"], {"p1_entity": P1, "excluded_energy_entity": ENERGY, "excluded_climate_entity": CLIMATE}
    )
    await hass.async_block_till_done()
    ex = now_snapshot(hass, entry)["excluded"]
    assert ex["active"] is True and ex["mode"] == "heat" and ex["action"] == "heating"
    assert ex["quality"] == "starting" and ex["has_climate"] is True and ex["blocked_modes"] == ["heat"]

    freezer.tick(timedelta(seconds=500))
    _energy(hass, 115.25)
    await hass.async_block_till_done()
    ex = now_snapshot(hass, entry)["excluded"]
    assert ex["power_w"] == 1800 and ex["quality"] == "ok" and ex["mean_step_interval_s"] == 500

    freezer.tick(timedelta(seconds=1200))  # counter late: > 2 × the interval
    ex = now_snapshot(hass, entry)["excluded"]
    assert ex["quality"] == "fading" and ex["power_w"] < 1800

    _climate(hass, "cool", "cooling")  # cooling may use the battery
    await hass.async_block_till_done()
    ex = now_snapshot(hass, entry)["excluded"]
    assert ex["active"] is False and ex["power_w"] == 0 and ex["mode"] == "cool"


async def test_panel_now_counter_without_climate(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    from custom_components.zephyr.websocket_api import now_snapshot

    _energy(hass, 10.0)
    entry = await _install_with_p1(hass, fake_sets)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": P1, "excluded_energy_entity": ENERGY})
    await hass.async_block_till_done()
    ex = now_snapshot(hass, entry)["excluded"]
    assert ex["quality"] == "no_climate" and ex["active"] is True and ex["has_climate"] is False
