"""Live control (M4b): switch, writer, write test, stop."""

from __future__ import annotations

from datetime import timedelta

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.zephyr.const import DOMAIN
from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets
from .test_shadow import _install_with_p1, _p1


async def _switch(hass: HomeAssistant, on: bool) -> None:
    await hass.services.async_call("switch", "turn_on" if on else "turn_off", {"entity_id": "switch.zephyr_control"}, blocking=True)
    await hass.async_block_till_done()


async def test_switch_is_off_by_default(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    await _install_with_p1(hass, fake_sets)
    for _ in range(4):
        await _p1(hass, freezer, 300)
    assert hass.states.get("switch.zephyr_control").state == "off"
    assert fake_sets.writes == []


async def test_live_takes_over_and_writes(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    await _install_with_p1(hass, fake_sets)
    for _ in range(3):
        await _p1(hass, freezer, 300)
    await _switch(hass, True)
    assert hass.states.get("switch.zephyr_control").state == "on"
    assert hass.states.get("sensor.zephyr_control").state == "active"
    for _ in range(4):
        await _p1(hass, freezer, 300)
    power = [p for _, p in fake_sets.writes if "outputLimit" in p and p.get("smartMode") == 1]
    assert power, fake_sets.writes
    # Taken over from 760 W, never a step to 0 W; with +300 W import it delivers more.
    assert all(p["outputLimit"] >= 760 for p in power)
    assert max(p["outputLimit"] for p in power) > 760


async def test_leaving_live_sends_zero_once(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    await _p1(hass, freezer, 300)
    await _switch(hass, False)
    assert fake_sets.writes[-1][1] == {"inputLimit": 0, "outputLimit": 0, "smartMode": 1}
    count = len(fake_sets.writes)
    for _ in range(5):
        await _p1(hass, freezer, 400)
    assert len(fake_sets.writes) == count  # shadow again: nothing more


async def test_counters_keep_live_writes_after_switching_off(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory
) -> None:
    # Seen 25-11 (0.5.4): 33 live writes, but the counter said 5 after switching back to shadow.
    entry = await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    for _ in range(4):
        await _p1(hass, freezer, 300)
    await _switch(hass, False)
    ram_written = sum(1 for _, p in fake_sets.writes if p.get("smartMode") == 1)
    assert ram_written >= 2  # at least one command while live and the 0 W when leaving
    diag = await async_get_config_entry_diagnostics(hass, entry)
    counts = next(iter(diag["control"]["counters"].values()))
    assert counts["ram_24h"] >= ram_written


async def test_live_refused_without_p1(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    await _install_with_p1(hass, fake_sets)
    for watts in (300, 310, 305, 300):
        await _p1(hass, freezer, watts)
    for _ in range(12):  # then P1 silent
        freezer.tick(timedelta(seconds=1))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
    with pytest.raises(HomeAssistantError):
        await _switch(hass, True)
    assert hass.states.get("switch.zephyr_control").state == "off"


async def test_stop_while_live_sends_zero(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    await _p1(hass, freezer, 300)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    assert fake_sets.writes[-1][1] == {"inputLimit": 0, "outputLimit": 0, "smartMode": 1}


async def test_write_test_only_in_standby(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(DOMAIN, "test_command", {"power": -300, "duration": 5}, blocking=True)
    await hass.services.async_call("select", "select_option", {"entity_id": "select.zephyr_mode", "option": "standby"}, blocking=True)
    await hass.services.async_call(DOMAIN, "test_command", {"power": -300, "duration": 1}, blocking=True)
    await hass.async_block_till_done(wait_background_tasks=True)
    writes = [p for _, p in fake_sets.writes]
    assert writes[0] == {"acMode": 2, "outputLimit": 300, "inputLimit": 0, "smartMode": 1}
    assert writes[-1] == {"inputLimit": 0, "outputLimit": 0, "smartMode": 0}  # back in standby (flash)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["control"]["live"]["test"]["power"] == -300
    assert diag["control"]["live"]["writes"]["1"]["ok_24h"] == 2


PRICE = "sensor.nordpool_test"


async def _set_prices(hass: HomeAssistant, expensive_now: bool) -> None:
    from homeassistant.util import dt as dt_util

    now = dt_util.now().replace(minute=0, second=0, microsecond=0)
    start = now.replace(hour=0)
    raw = []
    for h in range(24):
        t = start + timedelta(hours=h)
        price = 0.10
        if (t == now) == expensive_now and t.hour in ((now.hour,) if expensive_now else ((now.hour + 3) % 24,)):
            price = 0.50
        raw.append({"start": t, "end": t + timedelta(hours=1), "value": price})
    hass.states.async_set(PRICE, "0.1", {"raw_today": raw, "raw_tomorrow": []})


async def _options(hass: HomeAssistant, entry, **extra: object) -> None:  # type: ignore[no-untyped-def]
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": "sensor.p1_meter_power", **extra})
    await hass.async_block_till_done()


async def test_delivers_only_in_expensive_hours(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    await _set_prices(hass, expensive_now=False)
    await _options(hass, entry, price_entity=PRICE, expensive_hours=1, reserve_soc=0)
    for _ in range(15):
        await _p1(hass, freezer, 300)
    assert hass.states.get("sensor.zephyr_setpoint").state == "0"
    assert hass.states.get("sensor.zephyr_reason").attributes["code"] == "not_expensive"
    diag = await async_get_config_entry_diagnostics(hass, hass.config_entries.async_entries(DOMAIN)[0])
    assert diag["control"]["price"]["decision"]["expensive"] is False

    await _set_prices(hass, expensive_now=True)
    freezer.tick(timedelta(seconds=31))  # the price decision is refreshed every 30 s
    for _ in range(4):
        await _p1(hass, freezer, 300)
    assert float(hass.states.get("sensor.zephyr_setpoint").state) < 0


async def test_second_controller_stops_live(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 20)
    await _switch(hass, True)
    for _ in range(3):
        await _p1(hass, freezer, 20)
    assert fake_sets.writes, "ZEPHYR should have written its take-over command"
    # Another system writes 1500 W; the reports show it, twice, after ZEPHYR's command settled.
    for i in range(2):
        fake_sets.answers["10.0.0.10"]["properties"].update({"outputLimit": 1500, "inputLimit": 0})
        fake_sets.answers["10.0.0.10"]["timestamp"] = 1795500000 + i
        freezer.tick(timedelta(seconds=10))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        await _p1(hass, freezer, 20)
    await hass.async_block_till_done()
    assert hass.states.get("switch.zephyr_control").state == "off"
    from homeassistant.helpers import issue_registry as ir

    assert ir.async_get(hass).async_get_issue(DOMAIN, "second_controller") is not None
