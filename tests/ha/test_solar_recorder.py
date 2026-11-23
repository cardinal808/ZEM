"""ZEPHYR stores tomorrow's solar forecast in the evening and the production counter every hour."""

from __future__ import annotations

from datetime import datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.zephyr.const import DOMAIN
from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets

FORECAST = "sensor.solcast_pv_forecast_forecast_tomorrow"
ENERGY = "sensor.solaredge_modbus_ac_energy_kwh"
P1 = "sensor.power_consumption_combined"


def _detail(day: datetime) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for half in range(48):
        start = day + timedelta(minutes=30 * half)
        kw = 2.0 if 22 <= half < 26 else 0.0
        out.append({"period_start": start, "pv_estimate": kw, "pv_estimate10": kw / 2, "pv_estimate90": kw})
    return out


async def test_forecast_and_counter_are_stored(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 23, 22, 58, tzinfo=dt_util.get_default_time_zone()))
    fake_sets.add("10.0.0.10", "deliver_760")
    tomorrow = datetime(2026, 11, 24, tzinfo=dt_util.get_default_time_zone())
    hass.states.async_set(FORECAST, "4.0", {"detailedForecast": _detail(tomorrow), "unit_of_measurement": "kWh"})
    hass.states.async_set(ENERGY, "1000.0", {"device_class": "energy", "state_class": "total_increasing", "unit_of_measurement": "kWh"})
    hass.states.async_set(P1, "0", {"device_class": "power", "unit_of_measurement": "W"})

    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": "10.0.0.10"})
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    result = await hass.config_entries.options.async_init(entry.entry_id)
    suggested = {str(k): k.description["suggested_value"] for k in result["data_schema"].schema if str(k).startswith("solar_")}
    assert suggested == {"solar_forecast_entity": FORECAST, "solar_energy_entity": ENERGY}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"p1_source": "single", "p1_entity": P1, "solar_forecast_entity": FORECAST, "solar_energy_entity": ENERGY}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    # 23:00:05 counter, 23:00:30 forecast for tomorrow, then 00:00:05 the counter of the new day.
    for step, value in ((timedelta(minutes=2, seconds=5), "1000.0"), (timedelta(seconds=25), "1000.0"), (timedelta(hours=1), "1000.5")):
        hass.states.async_set(ENERGY, value, {"device_class": "energy", "state_class": "total_increasing", "unit_of_measurement": "kWh"})
        freezer.tick(step)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    diag = await async_get_config_entry_diagnostics(hass, entry)
    solar = diag["solar"]
    assert solar["days_stored"] == 2
    forecast = solar["recent"]["2026-11-24"]["forecast"]
    assert forecast["total_kwh"] == 4.0 and forecast["total10_kwh"] == 2.0 and len(forecast["periods"]) == 48
    assert solar["recent"]["2026-11-23"]["counter"] == {"23": 1000.0}
    assert solar["recent"]["2026-11-24"]["counter"] == {"0": 1000.5}
    assert entry.runtime_data.solar.history.production_per_hour("2026-11-23") == {23: 0.5}
