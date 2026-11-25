"""Cost log (B38): quarters closed on the clock, sensors, export, kept over a reload."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.zephyr.const import DOMAIN
from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets
from .test_shadow import P1, _install_with_p1

PRICE = "sensor.nordpool_test"
IMPORT = ("sensor.meter_energy_consumed_tariff_1", "sensor.meter_energy_consumed_tariff_2")
EXPORT = ("sensor.meter_energy_produced_tariff_1", "sensor.meter_energy_produced_tariff_2")
ENERGY = {"device_class": "energy", "state_class": "total_increasing", "unit_of_measurement": "kWh"}


def _prices(hass: HomeAssistant) -> None:
    start = dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)
    raw = [{"start": start + timedelta(hours=h), "end": start + timedelta(hours=h + 1), "value": 0.10} for h in range(24)]
    hass.states.async_set(PRICE, "0.1", {"raw_today": raw, "raw_tomorrow": [], "unit": "kWh"})


async def _run(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: int, watts: float = 400.0) -> None:
    for _ in range(seconds // 5):
        freezer.tick(timedelta(seconds=5))
        hass.states.async_set(P1, str(watts), {"device_class": "power", "unit_of_measurement": "W"}, force_update=True)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()


async def _setup(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, **options: object):  # type: ignore[no-untyped-def]
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 25, 11, 59, 50, tzinfo=dt_util.get_default_time_zone()))
    entry = await _install_with_p1(hass, fake_sets)
    _prices(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"p1_entity": P1, "price_entity": PRICE, "tariff_markup_import": 0.0165, "tariff_fixed_month": 30.0, **options},
    )
    await hass.async_block_till_done()
    return entry


async def test_quarter_costs_and_sensors(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, tmp_path: Path) -> None:
    entry = await _setup(hass, fake_sets, freezer)
    await _run(hass, freezer, 10)  # 12:00:00 closes the (partial) quarter 11:45–12:00
    await _run(hass, freezer, 900)  # 12:15:00 closes a whole quarter
    costs = entry.runtime_data.costs
    first, record = costs.current[-2:]
    assert first["complete"] is False
    assert record["start"] == "2026-11-25T11:00:00+00:00"
    assert record["complete"] is True
    # House imports 400 W while the set (fixture) delivers 760 W.
    assert record["import_kwh"] == pytest.approx(0.1, abs=0.002)
    assert record["discharge_kwh"] == pytest.approx(0.19, abs=0.003)
    buy = (0.10 + 0.0165 + 0.09161) * 1.21
    assert record["buy"] == pytest.approx(buy, abs=1e-5)
    assert record["cost"] == pytest.approx(record["import_kwh"] * buy, abs=1e-4)
    # Without the battery the house would have drawn 400 + 760 W.
    assert record["cost_no_battery"] == pytest.approx((record["import_kwh"] + record["discharge_kwh"]) * buy, abs=1e-4)
    assert record["cost_no_solar"] is None  # no solar counter configured

    today = hass.states.get("sensor.zephyr_costs_today")
    assert float(today.state) == pytest.approx(sum(r["cost"] for r in costs.current), abs=0.01)
    assert today.attributes["unit_of_measurement"] == "EUR"
    assert today.attributes["state_class"] == "total"
    assert today.attributes["includes_solar"] is False
    assert today.attributes["incomplete_quarters"] == 1
    assert float(hass.states.get("sensor.zephyr_savings_today").state) == pytest.approx(0.19 * buy, abs=0.01)
    assert hass.states.get("sensor.zephyr_costs_year").state == today.state

    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["costs"]["tariffs"]["markup_import"] == 0.0165
    assert len(diag["costs"]["last_quarters"]) == 2

    hass.config.config_dir = str(tmp_path)
    response = await hass.services.async_call(DOMAIN, "export_costs", {}, blocking=True, return_response=True)
    assert response["rows"] == 2
    lines = Path(str(response["path"])).read_text(encoding="utf-8").strip().split("\n")
    assert lines[0].startswith("start,") and len(lines) == 3

    # A reload keeps the day totals and the quarters.
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(entry.runtime_data.costs.current) == 2
    assert hass.states.get("sensor.zephyr_costs_today").state == today.state


async def test_meter_counters_win(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    for entity in (*IMPORT, *EXPORT):
        hass.states.async_set(entity, "100.0", ENERGY)
    entry = await _setup(hass, fake_sets, freezer, cost_import_counters=list(IMPORT), cost_export_counters=list(EXPORT))
    await _run(hass, freezer, 10)
    hass.states.async_set(IMPORT[0], "100.05", ENERGY)
    hass.states.async_set(IMPORT[1], "100.02", ENERGY)
    hass.states.async_set(EXPORT[1], "100.01", ENERGY)
    await _run(hass, freezer, 900)
    record = entry.runtime_data.costs.current[-1]
    assert record["import_kwh"] == pytest.approx(0.07)
    assert record["export_kwh"] == pytest.approx(0.01)
    assert record["complete"] is True
