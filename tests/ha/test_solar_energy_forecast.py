"""Solar forecast from the Energy dashboard when no forecast sensor is set (Forecast.Solar, Helios, ...)."""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets
from .test_planner import PRICE, _set_prices, _setup, _test_day, _tick  # noqa: F401 (_test_day: autouse)


async def test_planner_uses_the_energy_dashboard_forecast(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    forecast_entry = MockConfigEntry(domain="forecast_solar")
    forecast_entry.add_to_hass(hass)
    other = MockConfigEntry(domain="helios_forecast")
    other.add_to_hass(hass)
    noon = dt_util.start_of_local_day() + timedelta(days=1, hours=12)

    async def forecast_solar(_hass: HomeAssistant, entry_id: str) -> dict[str, Any]:
        wh = 2000 if entry_id == forecast_entry.entry_id else 1000
        return {"wh_hours": {(noon + timedelta(hours=h)).isoformat(): wh for h in range(2)}}

    manager = SimpleNamespace(
        data={
            "energy_sources": [
                {"type": "grid"},
                {"type": "solar", "stat_energy_from": "sensor.pv", "config_entry_solar_forecast": [forecast_entry.entry_id]},
                {"type": "solar", "stat_energy_from": "sensor.pv2", "config_entry_solar_forecast": [other.entry_id]},
            ]
        }
    )

    async def get_manager(_hass: HomeAssistant) -> Any:
        return manager

    async def platforms(_hass: HomeAssistant) -> dict[str, Any]:
        return {"forecast_solar": forecast_solar, "helios_forecast": forecast_solar}

    hass.config.components.add("energy")
    _set_prices(hass)
    with (
        patch("homeassistant.components.energy.data.async_get_manager", get_manager),
        patch("homeassistant.components.energy.websocket_api.async_get_energy_platforms", platforms),
    ):
        entry = await _setup(hass, fake_sets, freezer, (9, 0), price_entity=PRICE)
        await _tick(hass, freezer, 10)

        solar = entry.runtime_data.solar
        assert solar.source == "energy:forecast_solar,helios_forecast"
        first = solar.forecast_periods()[0]
        assert (first.start, first.estimate) == (dt_util.as_utc(noon).isoformat(), 3.0)

        diag = await async_get_config_entry_diagnostics(hass, entry)
        planner = diag["planner"]
        assert planner["inputs"]["solar_source"] == "forecast"
        assert planner["inputs"]["solar_forecast_source"] == "energy:forecast_solar,helios_forecast"
        row = next(r for r in planner["timeline"] if datetime.fromisoformat(r["start"]) == noon)
        assert row["solar"] == 0.75  # 3 kWh in the hour = 0.75 kWh per quarter

        # The day-ahead forecast is stored for the solar history too (B31).
        solar.record_forecast(dt_util.now().replace(hour=23))
        day = (dt_util.now().date() + timedelta(days=1)).isoformat()
        assert solar.history.days[day]["forecast"]["source"].startswith("energy:")
