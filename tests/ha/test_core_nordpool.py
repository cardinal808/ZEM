"""Prices from HA's own Nord Pool integration (action ``nordpool.get_prices_for_date``, per MWh)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.zephyr.config_flow import suggest_price
from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics
from custom_components.zephyr.prices import price_state

from .conftest import FakeSets
from .test_planner import _setup, _test_day, _tick  # noqa: F401 (_test_day: autouse)


async def test_prices_from_the_core_nord_pool(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    nordpool = MockConfigEntry(domain="nordpool", data={"areas": ["NL"], "currency": "EUR"})
    nordpool.add_to_hass(hass)
    sensor = er.async_get(hass).async_get_or_create("sensor", "nordpool", "NL-current_price", config_entry=nordpool).entity_id
    hass.states.async_set(sensor, "0.1", {"unit_of_measurement": "EUR/kWh"})
    asked: list[date] = []
    published = {"tomorrow": False}

    async def get_prices(call: ServiceCall) -> dict[str, Any]:
        day: date = call.data["date"]
        asked.append(day)
        if day > dt_util.now().date() and not published["tomorrow"]:
            raise ValueError("No prices for tomorrow yet")
        start = datetime.combine(day, datetime.min.time(), dt_util.get_default_time_zone())
        return {
            "NL": [
                {"start": (start + timedelta(hours=h)).isoformat(), "end": (start + timedelta(hours=h + 1)).isoformat(), "price": 100.0 + h}
                for h in range(24)
            ]
        }

    hass.services.async_register("nordpool", "get_prices_for_date", get_prices, supports_response=SupportsResponse.ONLY)
    assert suggest_price(hass) == sensor

    entry = await _setup(hass, fake_sets, freezer, (9, 0), price_entity=sensor)
    state = price_state(hass, sensor)
    assert state is not None and state.attributes["raw_today"][9]["value"] == 0.109  # €109/MWh at 09:00
    assert state.attributes["raw_tomorrow"] == []
    await _tick(hass, freezer, 10)
    assert hass.states.get("sensor.zephyr_plan_state").state == "active"

    # Tomorrow appears in the afternoon: asked again every 15 minutes until it is there.
    published["tomorrow"] = True
    await _tick(hass, freezer, 15 * 60, step=60)
    assert len(price_state(hass, sensor).attributes["raw_tomorrow"]) == 24
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["prices"]["core_nordpool"] is True and diag["prices"]["area"] == "NL"
    assert sorted(diag["prices"]["days"].values()) == [24, 24]
    count = len(asked)
    await _tick(hass, freezer, 15 * 60, step=60)
    assert len(asked) == count  # both days known: no more questions


async def test_the_hacs_nord_pool_is_read_as_before(hass: HomeAssistant) -> None:
    hass.states.async_set("sensor.nordpool_kwh_nl_eur", "0.1", {"raw_today": [], "raw_tomorrow": []})
    state = price_state(hass, "sensor.nordpool_kwh_nl_eur")
    assert state is hass.states.get("sensor.nordpool_kwh_nl_eur")
