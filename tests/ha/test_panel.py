"""The panel in the sidebar and the websocket subscription (SPEC-ui §2, §3; UI-1)."""

from __future__ import annotations

import json
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
    assert now["previous_mode"] == "zero_meter"
    mode_entity, live_entity = now["entities"]["mode"], now["entities"]["live"]
    assert mode_entity.startswith("select.") and hass.states.get(mode_entity) is not None
    assert live_entity.startswith("switch.") and hass.states.get(live_entity) is not None


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

    # After 20:15 the cost log has closed 20:00–20:15: the panel shows what happened (UI-3).
    # (Asked from the planner directly: 16 minutes of fake time would close the test's websocket.)
    await client.close()
    for _ in range(16):
        freezer.tick(timedelta(seconds=60))
        hass.states.async_set(P1, "300", {"device_class": "power", "unit_of_measurement": "W"}, force_update=True)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
    planner = entry.runtime_data.planner
    assert planner is not None
    quarters = planner.view()["quarters"]
    past = quarters[80]
    assert past["past"] is True
    assert past["action"] in ("charge", "deliver", "hold")
    assert past["soc"] is not None
    assert past["buy"] is not None
    assert quarters[81]["past"] is False


async def test_plan_command_without_price_source(hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator) -> None:
    await _install_with_p1(hass, fake_sets)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "zephyr/plan"})
    msg = await client.receive_json()
    assert msg["success"] is False
    assert msg["error"]["code"] == "no_price_source"


async def test_sets_command(hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator) -> None:
    """zephyr/sets: one set with its four packs, cell balance and history, no serial numbers (UI-4)."""
    entry = await _install_with_p1(hass, fake_sets)
    for coordinator in entry.runtime_data.coordinators.values():
        await coordinator.async_refresh()  # a report after the pack recorder started
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "zephyr/sets"})
    msg = await client.receive_json()
    assert msg["success"] is True
    view = msg["result"]
    assert len(view["sets"]) == 1
    s = view["sets"][0]
    assert s["number"] == 1 and s["online"] is True
    assert s["capacity_kwh"] == pytest.approx(11.04)
    assert s["limits"] == {"min": 10.0, "max": 100.0} or s["limits"]["min"] is not None
    packs = s["packs"]
    assert [p["built_in"] for p in packs] == [True, False, False, False]
    assert [p["model"] for p in packs[1:]] == ["AB3000L"] * 3
    assert [p["number"] for p in packs] == [1, 1, 2, 3]
    built_in, first = packs[0], packs[1]
    assert built_in["capacity_kwh"] == pytest.approx(2.40)
    # 3.27–3.28 V at 53 %: shown, but not judged (middle of the curve, SPEC-celbalans)
    assert built_in["cell_delta_mv"] == 10 and built_in["cell_judged"] is False and built_in["cell_status"] is None
    assert first["capacity_kwh"] == pytest.approx(2.88)
    assert first["cell_delta_mv"] == 0
    assert first["temp"] == pytest.approx(12.0)
    assert first["energy_kwh"] == pytest.approx(2.88 * 0.54, abs=0.01)
    assert len(first["history"]) == 7
    assert built_in["history"][-1]["max_mv"] is None  # not judged at 53 %
    assert first["history"][-1]["max_mv"] is None
    text = json.dumps(view)
    for serial in {p.serial for p in entry.runtime_data.coordinators[s["id"]].data.report.packs}:
        assert serial not in text
    assert entry.runtime_data.coordinators[s["id"]].data.report.serial not in text


async def test_events_for_the_screen_diagnose(
    hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator, freezer: FrozenDateTimeFactory
) -> None:
    client = await hass_ws_client(hass)
    entry = await _install_with_p1(hass, fake_sets)
    for watts in ("300", "900"):
        freezer.tick(timedelta(seconds=5))
        hass.states.async_set(P1, watts, {"device_class": "power", "unit_of_measurement": "W"}, force_update=True)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
    # Through the mode entity, like the panel does: the event list shows the change.
    now = (await _first_now(client))["entities"]
    await hass.services.async_call("select", "select_option", {"entity_id": now["mode"], "option": "standby"}, blocking=True)
    await client.send_json_auto_id({"type": "zephyr/events"})
    msg = await client.receive_json()
    assert msg["success"] is True
    view = msg["result"]
    assert view["entry_id"] == entry.entry_id
    assert any(e["kind"] == "reason" and e["text"] is not None for e in view["events"])
    assert any(e["kind"] == "mode" and e["mode"] == "standby" for e in view["events"])
    assert all("time" in e for e in view["events"])
    assert [s["number"] for s in view["sets"]] == [1]
    assert set(view["sets"][0]) == {"number", "ram_24h", "flash_24h", "relay_24h", "failed_24h", "last_error"}
    assert view["sets"][0]["failed_24h"] == 0


async def test_events_without_installation(hass: HomeAssistant, hass_ws_client: WebSocketGenerator) -> None:
    assert await async_setup_component(hass, DOMAIN, {})
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "zephyr/events"})
    msg = await client.receive_json()
    assert msg["success"] is False and msg["error"]["code"] == "not_loaded"


async def _first_now(client: Any) -> dict[str, Any]:
    await client.send_json_auto_id({"type": "zephyr/subscribe"})
    assert (await client.receive_json())["success"] is True
    data: dict[str, Any] = (await client.receive_json())["event"]["data"]
    return data
