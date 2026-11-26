"""The panel in the sidebar and the websocket subscription (SPEC-ui §2, §3; UI-1)."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.zephyr.const import DOMAIN
from custom_components.zephyr.panel import FRONTEND_DIR, PANEL_URL, WEBCOMPONENT

from .conftest import FakeSets
from .test_planner import PRICE, _set_prices
from .test_shadow import P1, _install_with_p1


@pytest.fixture
def frontend(hass: HomeAssistant) -> Generator[dict[str, Any]]:
    """A stand-in for HA's frontend: records panel and static-path registrations."""
    calls: dict[str, Any] = {"register": AsyncMock(), "remove": MagicMock()}
    hass.config.components.add("frontend")
    http = MagicMock()
    http.async_register_static_paths = AsyncMock()
    calls["http"] = http
    with (
        patch.object(hass, "http", http),
        patch("homeassistant.components.panel_custom.async_register_panel", calls["register"]),
        patch("homeassistant.components.frontend.async_remove_panel", calls["remove"]),
    ):
        yield calls


def test_built_panel_is_shipped() -> None:
    """HACS only ships custom_components/: the built module, fonts and logo must be there."""
    assert (FRONTEND_DIR / f"{WEBCOMPONENT}.js").is_file()
    assert (FRONTEND_DIR / "logo.png").is_file()
    assert (FRONTEND_DIR / "fonts" / "LICENSE.txt").is_file()
    assert len(list((FRONTEND_DIR / "fonts").glob("*.woff2"))) == 4


async def test_panel_registered_while_loaded(hass: HomeAssistant, fake_sets: FakeSets, frontend: dict[str, Any]) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    await hass.async_block_till_done()

    frontend["http"].async_register_static_paths.assert_awaited_once()
    static = frontend["http"].async_register_static_paths.await_args.args[0][0]
    assert static.url_path == "/zephyr_static"
    assert static.path == str(FRONTEND_DIR)
    assert frontend["register"].await_count == 1  # the reload by the options flow keeps the panel
    frontend["remove"].assert_not_called()
    kwargs = frontend["register"].await_args.kwargs
    assert kwargs["frontend_url_path"] == PANEL_URL
    assert kwargs["webcomponent_name"] == WEBCOMPONENT
    assert kwargs["sidebar_title"] == "ZEPHYR"
    assert kwargs["require_admin"] is False
    assert kwargs["module_url"].startswith("/zephyr_static/zephyr-panel.js?v=")

    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    frontend["remove"].assert_not_called()

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    frontend["remove"].assert_called_once()
    assert frontend["remove"].call_args.args[1] == PANEL_URL


async def test_no_panel_without_frontend(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    """Without HA's frontend (tests, minimal installs) the integration still loads."""
    entry = await _install_with_p1(hass, fake_sets)
    assert entry.state.value == "loaded"


async def test_subscribe_without_installation(hass: HomeAssistant, hass_ws_client: WebSocketGenerator) -> None:
    assert await async_setup_component(hass, DOMAIN, {})
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "zephyr/subscribe"})
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "not_loaded"


async def test_subscribe_sends_now_and_updates(
    hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator, freezer: FrozenDateTimeFactory
) -> None:
    client = await hass_ws_client(hass)  # authenticate before moving the clock (the token has a lifetime)
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 26, 20, 0, 0, tzinfo=dt_util.get_default_time_zone()))
    _set_prices(hass)
    entry = await _install_with_p1(hass, fake_sets)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": P1, "price_entity": PRICE, "plan_buffer": 10})
    await hass.async_block_till_done()
    for _ in range(3):
        freezer.tick(timedelta(seconds=5))
        hass.states.async_set(P1, "300", {"device_class": "power", "unit_of_measurement": "W"}, force_update=True)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    await client.send_json_auto_id({"type": "zephyr/subscribe"})
    msg = await client.receive_json()
    assert msg["success"] is True
    sub_id = msg["id"]

    msg = await client.receive_json()
    assert msg["id"] == sub_id
    assert msg["event"]["type"] == "now"
    now = msg["event"]["data"]
    assert now["mode"] == "zero_meter"
    assert "dynamic_forecasting" in now["modes"]
    assert now["live"] is False
    assert now["action"] in ("charge", "deliver", "hold", "standby")
    assert set(now["reason"]) == {"nl", "en"}
    assert now["soc"] is not None and now["capacity_kwh"] > 0
    assert (now["min_soc"], now["max_soc"], now["buffer_pct"]) == (10.0, 95.0, 10.0)
    assert (now["sets_online"], now["sets_total"]) == (1, 1)
    assert now["price_entity"] is True
    plan = now["plan"]
    assert plan is not None and plan["state"] == "active"
    assert set(plan["reason"]) == {"nl", "en"}
    assert plan["price_now"]["import"] > 0
    assert plan["next"] is None or plan["next"]["action"] in ("charge", "hold", "deliver", "export")

    # A new P1 value leads to an update, but not more often than every 2 s.
    freezer.tick(timedelta(seconds=3))
    hass.states.async_set(P1, "900", {"device_class": "power", "unit_of_measurement": "W"}, force_update=True)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    msg = await client.receive_json()
    assert msg["event"]["type"] == "now"

    # Unsubscribe: no more updates.
    await client.send_json_auto_id({"type": "unsubscribe_events", "subscription": sub_id})
    msg = await client.receive_json()
    assert msg["success"] is True

    # A reload tells a new subscriber's panel to subscribe again.
    await client.send_json_auto_id({"type": "zephyr/subscribe"})
    msg = await client.receive_json()
    second = msg["id"]
    msg = await client.receive_json()
    assert msg["event"]["type"] == "now"
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    msg = await client.receive_json()
    assert msg["id"] == second
    assert msg["event"] == {"type": "unloaded"}


async def test_subscribe_without_price_source(hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator) -> None:
    await _install_with_p1(hass, fake_sets)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "zephyr/subscribe"})
    assert (await client.receive_json())["success"] is True
    now = (await client.receive_json())["event"]["data"]
    assert now["price_entity"] is False
    assert now["plan"] is None
    assert now["modes"] == ["standby", "zero_meter", "fast_charge", "fast_discharge"]


async def test_plan_command(
    hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator, freezer: FrozenDateTimeFactory
) -> None:
    """zephyr/plan: every quarter of today and tomorrow, past ones with prices only (UI-2)."""
    client = await hass_ws_client(hass)
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 26, 20, 0, 0, tzinfo=dt_util.get_default_time_zone()))
    _set_prices(hass)
    entry = await _install_with_p1(hass, fake_sets)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": P1, "price_entity": PRICE})
    await hass.async_block_till_done()
    for _ in range(3):
        freezer.tick(timedelta(seconds=5))
        hass.states.async_set(P1, "300", {"device_class": "power", "unit_of_measurement": "W"}, force_update=True)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    await client.send_json_auto_id({"type": "zephyr/plan"})
    msg = await client.receive_json()
    assert msg["success"] is True
    view = msg["result"]
    assert view["state"] == "active"
    assert set(view["reason"]) == {"nl", "en"}
    assert view["tomorrow_known_at"] is not None
    quarters = view["quarters"]
    assert len(quarters) == 192
    assert quarters[0]["start"] == "2026-11-25T23:00:00+00:00"
    assert quarters[0]["past"] is True and quarters[0]["action"] is None and quarters[0]["buy"] > quarters[0]["market"]
    assert quarters[80]["past"] is False and quarters[80]["action"] in ("charge", "hold", "deliver")
    assert quarters[80]["soc"] is not None
    assert view["blocks"]


async def test_plan_command_without_price_source(hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator) -> None:
    await _install_with_p1(hass, fake_sets)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "zephyr/plan"})
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "no_price_source"
