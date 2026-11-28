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


async def test_stop_while_live_keeps_the_last_command(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    """HA stops without a restart: no 0 W either (nobody shuts HA down; at a power cut there is no time)."""
    await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    await _p1(hass, freezer, 300)
    count = len(fake_sets.writes)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    assert len(fake_sets.writes) == count


def _power_writes(fake_sets: FakeSets, start: int) -> list[dict[str, int]]:
    """Power and acMode commands (the fake set keeps reporting other SOC limits: those it gets anyway)."""
    return [p for _, p in fake_sets.writes[start:] if {"outputLimit", "inputLimit", "acMode"} & set(p)]


async def test_reload_while_live_hands_over(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    """A reload leaves the sets at their command: no 0 W, no acMode, live at once (handover.py)."""
    entry = await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    for _ in range(3):
        await _p1(hass, freezer, 300)
    old = entry.runtime_data.control
    setpoint = old.engine.controller.setpoint
    count = len(fake_sets.writes)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    control = entry.runtime_data.control
    assert control is not old and control.handed_over
    assert not control.shadow and hass.states.get("switch.zephyr_control").state == "on"
    assert control.engine.controller.setpoint == setpoint
    assert _power_writes(fake_sets, count) == []  # nothing at the reload itself
    for _ in range(3):
        await _p1(hass, freezer, 300)
    writes = _power_writes(fake_sets, count)
    assert all(w.get("outputLimit", 1) != 0 and "acMode" not in w for w in writes), writes
    assert [e["event"] for e in control.live_history][-1] == "handover"
    freezer.tick(timedelta(seconds=200))  # the hand-over timer was cancelled: no late 0 W
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert not any(w == {"inputLimit": 0, "outputLimit": 0, "smartMode": 1} for w in _power_writes(fake_sets, count))


async def test_unload_without_new_setup_goes_to_zero(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    """Nobody takes the control over within 120 s (a failed setup): the sets go to 0 W then."""
    from custom_components.zephyr.handover import HANDOVER_FOR

    entry = await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    await _p1(hass, freezer, 300)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    count = len(fake_sets.writes)
    freezer.tick(timedelta(seconds=HANDOVER_FOR + 1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert _power_writes(fake_sets, count) == [{"inputLimit": 0, "outputLimit": 0, "smartMode": 1}]


async def test_disable_while_live_sends_zero(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    from homeassistant.config_entries import ConfigEntryDisabler

    entry = await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    await _p1(hass, freezer, 300)
    assert await hass.config_entries.async_set_disabled_by(entry.entry_id, ConfigEntryDisabler.USER)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert fake_sets.writes[-1][1] == {"inputLimit": 0, "outputLimit": 0, "smartMode": 1}


async def test_remove_while_live_sends_zero(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    await _p1(hass, freezer, 300)
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
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
    # Mid-day: the test ticks forward a minute or two and must not cross midnight
    # (it failed in CI when run at 23:59, because "today's" prices no longer covered now).
    from homeassistant.util import dt as dt_util

    freezer.move_to(dt_util.now().replace(hour=12, minute=10, second=0, microsecond=0))
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


async def _slow_start(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, seconds: int) -> None:
    """The set keeps reporting its old limits (0 W, smartMode 0) while the house asks 750 W."""
    answer = fake_sets.answers["10.0.0.10"]
    for _ in range(seconds):
        answer["timestamp"] += 1
        await _p1(hass, freezer, 750)


async def test_slow_start_is_not_a_second_controller(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    # Seen 26-11 (0.6.2): from standby the set showed outputLimit 0 / smartMode 0 for more than 6 s
    # after ZEPHYR wrote 730 W (relay start 9-17 s); ZEPHYR took that for a second controller
    # and went back to shadow mode three times in a row.
    await _install_with_p1(hass, fake_sets, "standby")
    for _ in range(3):
        await _p1(hass, freezer, 750)
    await _switch(hass, True)
    await _slow_start(hass, fake_sets, freezer, 15)
    assert hass.states.get("switch.zephyr_control").state == "on"
    sent = [p for _, p in fake_sets.writes if p.get("outputLimit")]
    assert sent, fake_sets.writes
    # Now the set has started: it reports the command.
    answer = fake_sets.answers["10.0.0.10"]
    answer["properties"].update({"outputLimit": sent[-1]["outputLimit"], "smartMode": 1, "outputHomePower": sent[-1]["outputLimit"]})
    for _ in range(10):
        answer["timestamp"] += 1
        await _p1(hass, freezer, 10)
    assert hass.states.get("switch.zephyr_control").state == "on"
    diag = await async_get_config_entry_diagnostics(hass, hass.config_entries.async_entries(DOMAIN)[0])
    assert next(iter(diag["control"]["live"]["writes"].values()))["smartmode_reverted_24h"] == 0


async def test_set_that_never_applies_counts_as_second_controller(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory
) -> None:
    await _install_with_p1(hass, fake_sets, "standby")
    for _ in range(3):
        await _p1(hass, freezer, 750)
    await _switch(hass, True)
    await _slow_start(hass, fake_sets, freezer, 45)
    assert hass.states.get("switch.zephyr_control").state == "off"


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
    # Once 0 W before letting go: the set must not stay at ZEPHYR's last power.
    assert fake_sets.writes[-1][1] == {"inputLimit": 0, "outputLimit": 0, "smartMode": 1}
    from homeassistant.helpers import issue_registry as ir

    assert ir.async_get(hass).async_get_issue(DOMAIN, "second_controller") is not None
    control = hass.config_entries.async_entries(DOMAIN)[0].runtime_data.control
    last = control.last_shadow
    assert last is not None and last["reason"] == "second_controller" and last["reports"]
    assert last["reports"][-1]["reported"] == [0, 1500] and not control.wanted_live
    foreign = [e for e in control.log if e.get("event") == "foreign_report"]
    assert len(foreign) == 2 and foreign[-1]["reported"] == [0, 1500] and "recent" in foreign[-1]


async def test_calibrating_set_is_left_alone(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    # The set calibrates itself (socStatus 1) and sets its own limits: no second controller, and
    # ZEPHYR writes nothing to it (SPEC-basis §8), also not after the 5 minutes to standby.
    await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 20)
    await _switch(hass, True)
    for _ in range(3):
        await _p1(hass, freezer, 20)
    count = len(fake_sets.writes)
    answer = fake_sets.answers["10.0.0.10"]
    answer["properties"].update({"socStatus": 1, "outputLimit": 1500, "inputLimit": 0})
    for i in range(40):
        answer["timestamp"] = 1795500000 + i
        freezer.tick(timedelta(seconds=10))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        await _p1(hass, freezer, 20)
    assert hass.states.get("switch.zephyr_control").state == "on"
    assert fake_sets.writes[count:] == []


async def test_restart_while_live_keeps_the_last_command(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    """OPDRACHT-tellers-relais-flash: a restart of HA writes no 0 W (no relay switch, no grid draw)."""
    from homeassistant.const import RESTART_EXIT_CODE

    await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    await _p1(hass, freezer, 300)
    count = len(fake_sets.writes)
    hass.exit_code = RESTART_EXIT_CODE
    try:
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        await hass.async_block_till_done()
    finally:
        hass.exit_code = 0
    assert len(fake_sets.writes) == count


async def test_live_counters_match_the_writes_and_survive_a_reload(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory
) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    shadow = next(iter(diag["control"]["counters"].values()))  # what ZEPHYR would have sent
    await _switch(hass, True)
    for watts in (300, 500, 200, 400):
        await _p1(hass, freezer, watts)
    await hass.async_block_till_done(wait_background_tasks=True)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    counts = next(iter(diag["control"]["counters"].values()))
    writes = next(iter(diag["control"]["live"]["writes"].values()))
    live = counts["ram_24h"] + counts["flash_24h"] - shadow["ram_24h"] - shadow["flash_24h"]
    assert live == writes["ok_24h"] > 0
    assert counts["days"] and counts["days"][-1]["ram"] == counts["ram_24h"]
    decisions = diag["control"]["decisions"]
    assert all(d["commands"] for d in decisions if d.get("sent"))
    assert diag["control"]["p1_profile"]["timestamps"] == "last_reported"
    assert any(d.get("sent") for d in decisions)

    before = counts["ram_24h"]
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert next(iter(diag["control"]["counters"].values()))["ram_24h"] >= before


async def test_calibration_raises_the_limit_and_rests_at_full(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory
) -> None:
    """SPEC-planner §3.5: limit to 100 % while due (cause calibration), no delivering while resting."""
    entry = await _install_with_p1(hass, fake_sets)
    control = entry.runtime_data.control
    user_max = control.engine.settings.max_soc
    control.set_calibration(True, False)
    assert control.engine.settings.max_soc == 100.0 and control.engine.limits_cause == "calibration"
    for _ in range(20):  # import: zero-meter delivers
        await _p1(hass, freezer, 800)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["control"]["last"]["setpoint"] < 0, diag["control"]["last"]
    control.set_calibration(True, True)  # full: rest while the set calibrates
    for _ in range(20):
        await _p1(hass, freezer, 800)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["control"]["last"]["setpoint"] >= 0  # nothing delivered while resting
    control.set_calibration(False, False)
    assert control.engine.settings.max_soc == user_max and not control.calibration_rest


def test_report_equal_to_an_earlier_own_command_is_not_foreign() -> None:
    # 28-11: ZEPHYR sent A, then B a few seconds later; the set, slow, still showed A.
    from custom_components.zephyr.control import _matches_earlier

    recent = [(100.0, 0, 800), (105.0, 0, 1200)]
    assert _matches_earlier(0, 810, recent, 115.0, 30.0)
    assert not _matches_earlier(0, 810, recent, 140.0, 30.0)  # too long ago: foreign after all
    assert not _matches_earlier(0, 1500, recent, 115.0, 30.0)  # never sent by ZEPHYR


async def test_p1_hiccup_holds_and_is_counted(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    """OPDRACHT-p1-profiel §7.1/§8: P1 briefly unavailable while delivering: no command, counted."""
    from .test_shadow import P1

    entry = await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    for _ in range(4):
        await _p1(hass, freezer, 20)
    count = len(fake_sets.writes)
    for _ in range(2):  # two hiccups shortly after each other, as 15:53:57 and 15:53:59
        freezer.tick(timedelta(seconds=1))
        hass.states.async_set(P1, "unavailable")
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        await _p1(hass, freezer, 20)
    assert _power_writes(fake_sets, count) == []
    diag = await async_get_config_entry_diagnostics(hass, entry)
    profile = diag["control"]["p1_profile"]
    assert profile["invalid_24h"] == 2 and profile["invalid_longest_24h_s"] == 1.0 and not profile["invalid_now"]


async def test_reload_reason_is_logged(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    await _p1(hass, freezer, 300)
    hass.config_entries.async_update_entry(entry, options={**entry.options, "price_entity": "sensor.other_price"})
    await hass.async_block_till_done()
    control = entry.runtime_data.control
    assert control.handed_over and not control.shadow
    assert control.live_history[-1] == control.live_history[-1] | {"event": "handover", "changed": ["price_entity"]}
    assert any(e.get("event") == "handover" and e.get("changed") == ["price_entity"] for e in control.log)


async def test_decisions_show_report_age_and_follow_reports_after_a_command(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory
) -> None:
    """Diagnosis 28-11: the reported power lagged after a command; the log now shows it."""
    entry = await _install_with_p1(hass, fake_sets)
    await _p1(hass, freezer, 300)
    await _switch(hass, True)
    for _ in range(3):
        await _p1(hass, freezer, 300)
    control = entry.runtime_data.control
    last = [d for d in control.log if "reason" in d][-1]
    assert {"ac", "report_age_s", "content_age_s"} <= set(last)
    assert last["ac"] == [0, 760]
    # A command, then the set's report changes while nothing else does: an extra line.
    control._watch_reports_until = float("inf")
    answer = fake_sets.answers["10.0.0.10"]
    assert isinstance(answer, dict)
    answer["properties"]["outputHomePower"] = 700
    answer["timestamp"] += 5
    freezer.tick(timedelta(seconds=6))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await _p1(hass, freezer, 300)
    assert any(d.get("ac") == [0, 700] for d in control.log)
