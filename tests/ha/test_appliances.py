"""Planned appliances (B36) in Home Assistant."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets
from .test_planner import PRICE, _set_prices, _setup, _test_day, _tick  # noqa: F401 (_test_day: autouse)

PLUG = "sensor.washer_power"


async def _add(hass: HomeAssistant, entry: Any, name: str, kind: str, **details: Any) -> None:
    result = await hass.config_entries.subentries.async_init((entry.entry_id, "appliance"), context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"name": name, "kind": kind})
    assert result["step_id"] == "details"
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], details)
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()


async def test_plan_a_wash_with_the_button(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    _set_prices(hass)
    entry = await _setup(hass, fake_sets, freezer, (9, 0), price_entity=PRICE)
    await _add(hass, entry, "Wasmachine", "washer", window_from="08:00:00", window_until="20:00:00")
    await _add(hass, entry, "Droger", "dryer_condenser", window_from="08:00:00", window_until="20:00:00")
    await _tick(hass, freezer, 5)
    assert hass.states.get("button.zephyr_wasmachine_plan") is not None
    assert hass.states.get("sensor.zephyr_wasmachine_planned").state == "0"

    await hass.services.async_call("button", "press", {"entity_id": "button.zephyr_wasmachine_plan"}, blocking=True)
    await hass.services.async_call("button", "press", {"entity_id": "button.zephyr_wasmachine_plan"}, blocking=True)
    await hass.services.async_call("zephyr", "plan_appliance", {"appliance": "droger"}, blocking=True)
    await _tick(hass, freezer, 70)
    assert hass.states.get("sensor.zephyr_wasmachine_planned").state == "2"
    best = hass.states.get("sensor.zephyr_wasmachine_best_start")
    assert best is not None and best.state not in ("unknown", "unavailable")
    start = dt_util.parse_datetime(best.state)
    assert start is not None and dt_util.as_local(start).hour < 20
    dryer = dt_util.parse_datetime(hass.states.get("sensor.zephyr_droger_best_start").state)
    washes = sorted(dt_util.parse_datetime(s) for s in best.attributes["starts"])
    assert dryer is not None and dryer >= washes[-1] + timedelta(minutes=120)  # after the last wash
    planner = entry.runtime_data.planner
    assert sum(s.appliance_kwh for s in planner.outcome.slots) > 2.0  # 2 washes + a dryer in the plan

    diag = await async_get_config_entry_diagnostics(hass, entry)
    names = {a["name"] for a in diag["appliances"]["appliances"]}
    assert names == {"Wasmachine", "Droger"} and len(diag["appliances"]["planned"]) == 3

    await hass.services.async_call("button", "press", {"entity_id": "button.zephyr_wasmachine_clear"}, blocking=True)
    assert hass.states.get("sensor.zephyr_wasmachine_planned").state == "0"


async def test_a_run_on_the_plug_is_learned_and_fulfils_the_plan(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory
) -> None:
    _set_prices(hass)
    hass.states.async_set(PLUG, "0", {"unit_of_measurement": "W", "device_class": "power"})
    entry = await _setup(hass, fake_sets, freezer, (9, 0), price_entity=PRICE)
    await _add(hass, entry, "Wasmachine", "washer", power_entity=PLUG, window_from="08:00:00", window_until="20:00:00")
    await hass.services.async_call("button", "press", {"entity_id": "button.zephyr_wasmachine_plan"}, blocking=True)
    assert hass.states.get("sensor.zephyr_wasmachine_planned").state == "1"
    # A 40-minute run on the plug.
    for watts, minutes in ((2000, 15), (150, 25), (0, 10)):
        hass.states.async_set(PLUG, str(watts), {"unit_of_measurement": "W", "device_class": "power"})
        await hass.async_block_till_done()
        if watts:
            assert hass.states.get("binary_sensor.zephyr_wasmachine_running").state == "on"
        await _tick(hass, freezer, minutes * 60)
    manager = entry.runtime_data.appliances
    washer = next(iter(manager.appliances.values()))
    assert len(washer.runs) == 1 and washer.runs[0].minutes == 40
    assert hass.states.get("sensor.zephyr_wasmachine_planned").state == "0"  # the planned run took place
    assert hass.states.get("binary_sensor.zephyr_wasmachine_running").state == "off"


async def test_profile_learned_from_the_recorder_at_once(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    """Three washes in the plug's history: the learned profile replaces the default at start."""
    from types import SimpleNamespace
    from unittest.mock import patch

    from homeassistant.core import State

    day = dt_util.now() - timedelta(days=3)
    states = []
    for d in range(3):
        start = day + timedelta(days=d)
        for minutes, watts in ((0, 2200), (10, 300), (70, 0)):  # 70 minutes, ~0.65 kWh
            states.append(State(PLUG, str(watts), last_changed=start + timedelta(minutes=minutes)))

    class Recorder:
        async def async_add_executor_job(self, fn: Any, *args: Any) -> Any:
            return fn(*args)

    def history(_hass: Any, _start: Any, _end: Any, entity: str) -> dict[str, list[State]]:
        return {entity: states}

    _set_prices(hass)
    hass.states.async_set(PLUG, "0", {"unit_of_measurement": "W", "device_class": "power"})
    with (
        patch("homeassistant.helpers.recorder.get_instance", return_value=Recorder()),
        patch("homeassistant.components.recorder.history.state_changes_during_period", history),
    ):
        entry = await _setup(hass, fake_sets, freezer, (9, 0), price_entity=PRICE)
        await _add(hass, entry, "Wasmachine", "washer", power_entity=PLUG)
        await hass.async_block_till_done()
    washer = next(iter(entry.runtime_data.appliances.appliances.values()))
    assert len(washer.runs) == 3 and washer.profile_source == "learned"
    assert len(washer.profile()) == 70
    assert SimpleNamespace(**hass.states.get("sensor.zephyr_wasmachine_planned").attributes).profile == "learned"


async def test_panel_plans_and_clears_runs_over_the_websocket(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, hass_ws_client: Any
) -> None:
    """SPEC-ui-planner §4.1: list, plan, remove one run, clear; the subscription carries a revision."""
    client = await hass_ws_client(hass)
    _set_prices(hass)
    entry = await _setup(hass, fake_sets, freezer, (9, 0), price_entity=PRICE)
    await _add(hass, entry, "Wasmachine", "washer", window_from="08:00:00", window_until="20:00:00")
    await _add(hass, entry, "Droger", "dryer_condenser", window_from="08:00:00", window_until="20:00:00")
    await _tick(hass, freezer, 5)

    await client.send_json_auto_id({"type": "zephyr/appliances"})
    msg = await client.receive_json()
    assert msg["success"] is True
    view = msg["result"]
    assert {a["name"] for a in view["appliances"]} == {"Wasmachine", "Droger"} and view["planned"] == []
    washer = next(a for a in view["appliances"] if a["name"] == "Wasmachine")
    assert washer["profile"] == "default" and "profile_w" not in washer and washer["plug"] is False
    assert washer["window"] == {"from": "08:00:00", "until": "20:00:00"} and washer["kwh"] > 0
    revision = view["revision"]

    await client.send_json_auto_id({"type": "zephyr/appliances/plan", "appliance": washer["id"], "runs": 2})
    msg = await client.receive_json()
    assert msg["success"] is True and len(msg["result"]["planned"]) == 2
    await client.send_json_auto_id({"type": "zephyr/appliances/plan", "appliance": "droger"})
    msg = await client.receive_json()
    assert msg["result"]["planned"][-1]["after"] == "Wasmachine"
    assert msg["result"]["revision"] > revision
    await _tick(hass, freezer, 70)

    await client.send_json_auto_id({"type": "zephyr/appliances"})
    planned = (await client.receive_json())["result"]["planned"]
    assert all(p["best_start"] is not None and "saving" in p for p in planned)

    await client.send_json_auto_id({"type": "zephyr/appliances/clear", "index": 0})
    msg = await client.receive_json()
    assert len(msg["result"]["planned"]) == 2
    await client.send_json_auto_id({"type": "zephyr/appliances/clear", "index": 9})
    assert (await client.receive_json())["success"] is False
    await client.send_json_auto_id({"type": "zephyr/appliances/clear", "appliance": "Droger"})
    assert len((await client.receive_json())["result"]["planned"]) == 1
    await client.send_json_auto_id({"type": "zephyr/appliances/clear"})
    assert (await client.receive_json())["result"]["planned"] == []
    await client.send_json_auto_id({"type": "zephyr/appliances/plan", "appliance": "Vaatwasser"})
    assert (await client.receive_json())["success"] is False

    from custom_components.zephyr.websocket_api import now_snapshot

    assert now_snapshot(hass, entry)["appliances_revision"] == entry.runtime_data.appliances.revision


async def test_stroom_shows_the_plugs_with_floor_and_energy_today(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, hass_ws_client: Any
) -> None:
    """Screen Stroom: power now and kWh today per plug; the floor is set in the panel."""
    from custom_components.zephyr.websocket_api import settings_view, stroom_view

    client = await hass_ws_client(hass)
    _set_prices(hass)
    entry = await _setup(hass, fake_sets, freezer, (9, 0), price_entity=PRICE)
    hass.states.async_set(PLUG, "0", {"unit_of_measurement": "W", "device_class": "power"})
    await _add(hass, entry, "Wasmachine", "washer", power_entity=PLUG, window_from="08:00:00", window_until="20:00:00")
    entry = hass.config_entries.async_get_entry(entry.entry_id)
    washer = next(d for d in stroom_view(entry)["devices"] if d["name"] == "Wasmachine")
    assert washer["floor"] == "attic" and washer["shown"] is True

    await client.send_json_auto_id({"type": "zephyr/house/layout", "floors": {washer["id"]: "first"}, "hidden": []})
    assert (await client.receive_json())["success"]
    assert next(d for d in settings_view(hass, entry)["house"] if d["id"] == washer["id"])["floor"] == "first"

    hass.states.async_set(PLUG, "2", {"unit_of_measurement": "kW", "device_class": "power"})
    await hass.async_block_till_done()
    await _tick(hass, freezer, 30 * 60, step=60)
    hass.states.async_set(PLUG, "0", {"unit_of_measurement": "W", "device_class": "power"})
    await hass.async_block_till_done()
    washer = next(d for d in stroom_view(entry)["devices"] if d["name"] == "Wasmachine")
    assert washer["power_w"] == 0
    assert 0.95 < washer["today_kwh"] < 1.05  # 2 kW for half an hour


async def test_dryer_goes_along_with_the_washing_and_settings_from_the_panel(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, hass_ws_client: Any
) -> None:
    """A dryer set to 'after the washing' is planned once with the washer and cleared with it."""
    client = await hass_ws_client(hass)
    _set_prices(hass)
    entry = await _setup(hass, fake_sets, freezer, (9, 0), price_entity=PRICE)
    await _add(hass, entry, "Wasmachine", "washer", window_from="10:00:00", window_until="15:00:00")
    await _add(hass, entry, "Droger", "dryer_heat_pump", window_from="12:00:00", window_until="20:00:00", after_washer=True)
    manager = hass.config_entries.async_get_entry(entry.entry_id).runtime_data.appliances

    await client.send_json_auto_id({"type": "zephyr/appliances/plan", "appliance": "Wasmachine", "runs": 2})
    view = (await client.receive_json())["result"]
    kinds = [next(a["kind"] for a in view["appliances"] if a["id"] == p["appliance"]) for p in view["planned"]]
    assert sorted(kinds) == ["dryer_heat_pump", "washer", "washer"]  # one dryer, after the last wash
    dryer_run = next(p for p in view["planned"] if p["after"])
    assert dryer_run["after"] == "Wasmachine"
    assert next(a for a in view["appliances"] if a["name"] == "Droger")["after_washer"] is True

    await client.send_json_auto_id({"type": "zephyr/appliances/clear", "appliance": "Wasmachine"})
    assert (await client.receive_json())["result"]["planned"] == []  # the dryer went with it
    assert manager.planned == []

    dryer_id = next(a.id for a in manager.appliances.values() if a.name == "Droger")
    await client.send_json_auto_id(
        {"type": "zephyr/appliances/update", "appliances": [{"id": dryer_id, "window_from": "15:00", "after_washer": False}]}
    )
    result = (await client.receive_json())["result"]
    assert result == {"changed": 1, "reload": True}
    await hass.async_block_till_done()
    data = hass.config_entries.async_get_entry(entry.entry_id).subentries[dryer_id].data
    assert data["window_from"] == "15:00:00" and data["after_washer"] is False
