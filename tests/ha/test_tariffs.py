"""Tariff table in Home Assistant (B28): supplier choice, verified only, fetching from GitHub."""

from __future__ import annotations

import copy
import json
from collections.abc import Generator
from datetime import timedelta
from typing import Any
from unittest.mock import patch

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.zephyr.core.tariff_table import TariffTable, parse_table
from custom_components.zephyr.tariff_provider import SHIPPED, TABLE_URL, TariffProvider

from .conftest import FakeSets
from .test_costs import _run, _setup

REAL_FETCH = TariffProvider.async_fetch


def _data(verified: bool) -> dict[str, Any]:
    data = copy.deepcopy(json.loads(SHIPPED.read_text(encoding="utf-8")))
    for supplier in data["suppliers"].values():
        for period in supplier["periods"]:
            period["verified"] = verified
    return data


@pytest.fixture
def verified_table() -> Generator[TariffTable]:
    table = parse_table(_data(True))
    with patch("custom_components.zephyr.tariff_provider.load_shipped", return_value=table):
        yield table


async def _supplier_options(hass: HomeAssistant, entry: Any) -> list[str]:
    result = await hass.config_entries.options.async_init(entry.entry_id)
    key = next(k for k in result["data_schema"].schema if k == "tariff_supplier")
    values = [o["value"] for o in result["data_schema"].schema[key].config["options"]]
    hass.config_entries.options.async_abort(result["flow_id"])
    return values


async def test_unverified_supplier_is_not_offered(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    with patch("custom_components.zephyr.tariff_provider.load_shipped", return_value=parse_table(_data(False))):
        entry = await _setup(hass, fake_sets, freezer)
        assert await _supplier_options(hass, entry) == ["own"]


async def test_shipped_zonneplan_is_offered(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _setup(hass, fake_sets, freezer)
    assert await _supplier_options(hass, entry) == ["own", "zonneplan"]


async def test_supplier_from_table_is_used(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, verified_table: TariffTable
) -> None:
    entry = await _setup(hass, fake_sets, freezer, tariff_supplier="zonneplan", tariff_markup_import=0.5)
    assert "zonneplan" in await _supplier_options(hass, entry)
    await _run(hass, freezer, 10)
    await _run(hass, freezer, 900)
    record = entry.runtime_data.costs.current[-1]
    period = verified_table.suppliers["zonneplan"].periods[-1]
    # The table wins over the own margin in the options (0.5).
    assert record["buy"] == pytest.approx((0.10 + period.markup_import + 0.09161) * 1.21, abs=1e-5)
    assert "Zonneplan" in hass.states.get("sensor.zephyr_costs_today").attributes["tariffs"]


async def test_fetch_from_github(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    provider = TariffProvider(hass, "test", {"tariff_supplier": "zonneplan"})
    await provider.async_start()
    newer = _data(True)
    newer["updated"] = "2099-01-01"
    aioclient_mock.get(TABLE_URL, text=json.dumps(newer))
    assert await REAL_FETCH(provider)
    assert provider.origin == "github" and provider.table is not None
    assert provider.tariffs_for(provider.table.updated).source.startswith("Zonneplan")
    assert provider.diagnostics()["last_error"] is None
    # Not again the next day: a month later, or when the supplier changes.
    assert not provider._fetch_due()
    assert provider.fetched_at is not None
    provider.fetched_at -= timedelta(days=31)
    provider.attempted_at = provider.fetched_at
    assert provider._fetch_due()


async def test_fetch_failure_keeps_shipped_table(hass: HomeAssistant, aioclient_mock: AiohttpClientMocker) -> None:
    provider = TariffProvider(hass, "test", {})
    await provider.async_start()
    aioclient_mock.get(TABLE_URL, text='{"format": 99}')
    assert not await REAL_FETCH(provider)
    assert provider.origin == "shipped"
    assert "format" in str(provider.last_error)
    assert not provider._fetch_due()  # at most one attempt a day
