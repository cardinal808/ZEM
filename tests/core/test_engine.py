"""Engine: modes, safety, write rules (single steps, without the simulator)."""

from __future__ import annotations

import copy

import pytest

from conftest import load_fixture
from zephyr_core.engine import Action, Mode, ReasonCode, SetView, ZephyrEngine
from zephyr_core.settings import Settings, SettingsError
from zephyr_core.zensdk import parse_report


def _view(fixture: str = "deliver_760", online: bool = True) -> SetView:
    return SetView("a", 1, parse_report(load_fixture(fixture)), online)


def test_after_start_wait_for_p1_without_touching_the_sets() -> None:
    e = ZephyrEngine()
    r = e.step(0, [_view()])
    assert r.reason.code is ReasonCode.P1_MISSING
    assert r.action is Action.HOLD
    assert r.commands == ()
    assert "P1" in r.reason.text("nl")
    e.p1_reported(5, 300)
    assert e.step(5, [_view()]).reason.code is not ReasonCode.P1_MISSING


def test_without_p1_sets_go_to_standby_with_clear_reason() -> None:
    e = ZephyrEngine()
    e.step(0, [_view()])
    r = e.step(61, [_view()])
    assert r.reason.code is ReasonCode.P1_MISSING
    assert r.action is Action.STANDBY
    assert [c.kind for c in r.commands if c.kind != "soc_limits"] == ["standby"]


def test_soc_limits_are_aligned_once() -> None:
    e = ZephyrEngine(Settings(min_soc=10, max_soc=95))
    e.p1_reported(0, 0)
    first = e.step(0, [_view()])
    assert [c.props for c in first.commands if c.kind == "soc_limits"] == [{"minSoc": 100, "socSet": 950, "smartMode": 0}]
    e.p1_reported(2, 0)
    assert not [c for c in e.step(2, [_view()]).commands if c.kind == "soc_limits"]


def test_offline_set_gets_no_commands() -> None:
    e = ZephyrEngine()
    e.p1_reported(0, 500)
    r = e.step(0, [_view(online=False)])
    assert r.commands == ()
    assert r.reason.code is ReasonCode.NO_SET


def test_standby_mode() -> None:
    e = ZephyrEngine(mode=Mode.STANDBY)
    e.p1_reported(0, 500)
    r = e.step(0, [_view()])
    assert r.action is Action.STANDBY and r.setpoint == 0


def test_fast_discharge_uses_full_power() -> None:
    e = ZephyrEngine(mode=Mode.FAST_DISCHARGE)
    r = e.step(0, [_view()])
    assert r.setpoint == -2400
    power = next(c for c in r.commands if c.kind == "power")
    assert power.props["outputLimit"] == 2400


def test_temperature_blocks_charging() -> None:
    data = load_fixture("charge_2400")
    for p in data["packData"]:
        p["maxTemp"] = 2731 + 600  # 60 °C
    e = ZephyrEngine(mode=Mode.FAST_CHARGE)
    r = e.step(0, [SetView("a", 1, parse_report(data), True)])
    assert r.setpoint == 0
    assert r.reason.code is ReasonCode.TEMPERATURE


def test_settings_validation() -> None:
    with pytest.raises(SettingsError):
        Settings(min_soc=60).validated()
    with pytest.raises(SettingsError):
        Settings().with_changes(max_soc=101)
    with pytest.raises(SettingsError):
        Settings().with_changes(unknown=1)
    assert Settings().with_changes(min_soc=20).min_soc == 20


def test_p1_interval_measured_on_new_values() -> None:
    # An integration that re-reports the same value every 0.4 s for a meter with a new value every 10 s.
    e = ZephyrEngine()
    t = 0.0
    value = 800.0
    while t < 120:
        if round(t * 10) % 100 == 0:
            value = 800.0 + (t % 20)  # new meter value every 10 s
        e.p1_reported(t, value)
        t = round(t + 0.4, 1)
    r = e.step(t, [_view()])
    assert r.p1_interval is not None and 9.0 <= r.p1_interval <= 11.0


def _view_battery(deliver: int) -> SetView:
    data = copy.deepcopy(load_fixture("deliver_760"))
    data["properties"]["outputHomePower"] = deliver
    data["properties"]["packInputPower"] = deliver
    return SetView("a", 1, parse_report(data), True)


def test_one_decision_per_p1_sample() -> None:
    # Shadow mode: the battery measurement moves between P1 samples, but without a
    # new P1 value nothing new is known, so the setpoint stays.
    e = ZephyrEngine()
    e.controller.trust_commands = False
    first = 0
    for t in range(0, 30, 3):
        e.p1_reported(t, 800 + t)  # new meter value every 3 s
        first = e.step(t, [_view_battery(760)]).setpoint
    # The integration re-reports the same value before the next meter value; the
    # battery measurement meanwhile moves. Steps 2.5 s later (past the minimum step).
    e.p1_reported(29.0, 827)
    e.p1_reported(29.5, 827)
    assert e.step(29.5, [_view_battery(460)]).setpoint == first
    e.p1_reported(30.0, 840)  # new value: now it decides again
    assert e.step(30.0, [_view_battery(460)]).setpoint != first


def test_reason_stays_full_between_decisions() -> None:
    # Seen in shadow mode: a full battery with solar surplus alternated between "full" and "demand too small".
    data = copy.deepcopy(load_fixture("charge_2400"))
    data["properties"]["electricLevel"] = 98
    for pack in data["packData"]:
        pack["socLevel"] = 98
    view = SetView("a", 1, parse_report(data), True)
    e = ZephyrEngine()
    e.controller.trust_commands = False
    reasons = set()
    for t in range(40):
        e.p1_reported(t, -1300 + (t % 3) * 10)
        reasons.add(e.step(t + 0.5, [view]).reason.code)
    assert reasons == {ReasonCode.FULL}


def test_fault_level_without_error_does_not_block() -> None:
    # A 2400 AC+ at 100 % reported faultLevel 2 with is_error 0; ZEPHYR must still be able to deliver.
    report = parse_report(load_fixture("ac_plus_full_fault_level"))
    assert report.fault_level == 2
    assert not report.fault
    e = ZephyrEngine()
    for t in range(0, 30, 3):
        e.p1_reported(t, 600 + t)
        r = e.step(t, [SetView("a", 1, report, True)])
    assert r.reason.code is not ReasonCode.NO_SET
    assert r.setpoint < 0


def test_silent_balanced_grid_is_not_stale() -> None:
    # A P1 sensor that only reports changes stays silent at exactly 0 W; the setpoint holds.
    e = ZephyrEngine()
    for t in range(0, 20):
        e.p1_reported(t, 600 - t * 30 if t < 20 else 0)
        e.step(t, [_view()])
    e.p1_reported(20, 0.0)
    held = e.step(20, [_view()])
    for t in range(21, 50):
        r = e.step(t, [_view()])
        assert r.reason.code is not ReasonCode.P1_STALE
        assert r.setpoint == held.setpoint
    assert e.step(52, [_view()]).reason.code is ReasonCode.P1_STALE


def test_silent_unbalanced_grid_is_stale() -> None:
    e = ZephyrEngine()
    for t in range(0, 20):
        e.p1_reported(t, 600 + t)
        e.step(t, [_view()])
    assert e.step(19 + 11, [_view()]).reason.code is ReasonCode.P1_STALE


def _deliver_2400(ac_status: int = 1, output_limit: int = 2400) -> SetView:
    raw = copy.deepcopy(load_fixture("deliver_2400_export_blocked"))
    raw["properties"].update({"acMode": 2, "outputLimit": output_limit, "inputLimit": 0, "smartMode": 1, "acStatus": ac_status})
    return SetView("a", 1, parse_report(raw), True)


def test_refresh_skipped_when_set_reports_same_command() -> None:
    e = ZephyrEngine(mode=Mode.FAST_DISCHARGE)
    assert any(c.kind == "power" for c in e.step(0, [_deliver_2400()]).commands)
    assert not [c for c in e.step(30, [_deliver_2400()]).commands if c.kind == "power"]
    # After 60 s a refresh is due, but the set already reports 2400 W delivering.
    assert not [c for c in e.step(61, [_deliver_2400()]).commands if c.kind == "power"]
    counts = e.counters(61)["a"]
    assert counts["ram_24h"] == 1 and counts["skipped_24h"] == 1


def test_refresh_sent_when_set_reports_other_limit() -> None:
    e = ZephyrEngine(mode=Mode.FAST_DISCHARGE)
    e.step(0, [_deliver_2400(output_limit=760)])
    r = e.step(61, [_deliver_2400(output_limit=760)])
    assert [c.props["outputLimit"] for c in r.commands if c.kind == "power"] == [2400]
    assert e.counters(61)["a"]["ram_24h"] == 2


def test_counters_flash_and_relay() -> None:
    e = ZephyrEngine(mode=Mode.STANDBY)
    e.step(0, [_deliver_2400(ac_status=1)])
    e.step(10, [_deliver_2400(ac_status=0)])
    e.step(20, [_deliver_2400(ac_status=2)])
    counts = e.counters(20)["a"]
    assert counts["flash_24h"] >= 1  # standby (and possibly SOC limits)
    assert counts["relay_24h"] == 2 and counts["relay_1h"] == 2
    later = e.counters(20 + 2 * 3600)["a"]
    assert later["relay_1h"] == 0 and later["relay_24h"] == 2
    assert e.counters(20 + 25 * 3600)["a"]["relay_24h"] == 0


def _view_charging(charge: int) -> SetView:
    data = copy.deepcopy(load_fixture("charge_2400"))
    data["properties"]["gridInputPower"] = charge
    data["properties"]["outputPackPower"] = charge
    data["properties"]["outputHomePower"] = 0
    data["properties"]["electricLevel"] = 60
    for pack in data["packData"]:
        pack["socLevel"] = 60
    return SetView("a", 1, parse_report(data), True)


def test_step_filter_does_not_hold_while_charging() -> None:
    # Seen live at noon: a cloud (or a load) turned -1.3 kW export into +2.2 kW import while
    # the battery charged from solar. Holding the step would raise the charge setpoint and
    # charge from the grid; while charging the controller must see the rise at once.
    e = ZephyrEngine()
    e.controller.trust_commands = False
    view = _view_charging(1200)
    before = 0
    for t in range(0, 21):
        e.p1_reported(t, -500.0 - (t % 2) * 10)  # a meter that reports every second
        before = e.step(t, [view]).setpoint
    assert before > 1200  # charging more with the export
    e.p1_reported(22.0, 1500.0)  # past the minimum step interval
    r = e.step(22.0, [view])
    assert e.grid_filter.holding  # the filter saw a step ...
    assert r.setpoint < 1200  # ... but charging goes down right away (held: ~1670 W, from the grid)


def test_shadow_setpoint_follows_battery_when_balanced() -> None:
    # Seen at a tester: another system kept the grid at +25 W with the set delivering 150 W,
    # while ZEPHYR (shadow) kept showing -410 W from an earlier step.
    e = ZephyrEngine()
    e.controller.trust_commands = False
    for t in range(0, 12, 2):
        e.p1_reported(t, 300.0 + t)  # grid +300 W, set delivers 150 W: ZEPHYR wants more
        e.step(t, [_view_battery(150)])
    assert e.step(12, [_view_battery(150)]).setpoint <= -400
    r = None
    for t in range(14, 40, 2):
        e.p1_reported(t, 25.0 + (t % 4))  # the other system balanced the grid
        r = e.step(t, [_view_battery(150)])
    assert r is not None
    assert r.setpoint == -150
    assert not [c for c in r.commands if c.kind == "power"]


def test_no_relay_count_without_ac_status() -> None:
    # The SolarFlow 2400 AC+ does not report acStatus: unknown, not 0.
    raw = copy.deepcopy(load_fixture("deliver_760"))
    raw["properties"].pop("acStatus", None)
    view = SetView("a", 1, parse_report(raw), True)
    e = ZephyrEngine()
    e.p1_reported(0, 100.0)
    e.step(0, [view])
    counts = e.counters(1)["a"]
    assert "relay_24h" not in counts and "ram_24h" in counts


def test_refresh_tolerates_unrounded_limit_of_other_system() -> None:
    # Shadow mode at a tester: the current system wrote 296 W, ZEPHYR's setpoint was 300 W.
    from zephyr_core.engine import _report_matches

    report = _deliver_2400(output_limit=296).report
    assert report is not None
    assert _report_matches(report, -300)
    assert not _report_matches(report, -320)


def test_small_changes_wait_for_the_refresh() -> None:
    from zephyr_core.engine import _SetState

    e = ZephyrEngine()
    state = _SetState(last_power=-180, last_sent_at=0.0)
    assert not e._should_send(state, -170, 5)  # 10 W: meter noise
    assert not e._should_send(state, -200, 5)  # 20 W
    assert e._should_send(state, -210, 5)  # 30 W
    assert e._should_send(state, -170, 60)  # refresh carries the latest setpoint
    assert e._should_send(state, 0, 0.5)  # stopping is never held back


def test_going_live_takes_over_without_step_to_zero() -> None:
    # B35 / PLAN-M4b §2.3: the set delivers 760 W; going live must not first write 0 W.
    e = ZephyrEngine()
    e.enable_twin()
    for t in range(0, 6, 2):
        e.p1_reported(t, 20.0 + t)
        e.step(t, [_view()])
    e.set_live(True, 6, [_view()])
    assert not e.twin_enabled
    e.p1_reported(7, 25.0)
    r = e.step(7, [_view()])
    powers = [c.props for c in r.commands if c.kind == "power"]
    assert r.setpoint <= -700
    assert all(p.get("outputLimit", 0) >= 700 for p in powers)


def test_counters_survive_switching_live_and_back() -> None:
    # Seen 25-11 (0.5.4): every switch emptied the counters (33 writes, counter said 5), and with
    # them the flash safety net forgot its history.
    from zephyr_core.settings import Settings

    e = ZephyrEngine(Settings().with_changes(flash_limit_hour=2))
    e.enable_twin()
    e.counters_record("a", "power", 1.0)
    e.counters_record("a", "standby", 2.0)
    e.counters_record("a", "standby", 3.0)
    e.set_live(True, 4, [_view()])
    e.set_live(False, 5, [_view()])
    c = e.counters(6)["a"]
    assert c["ram_24h"] == 1
    assert c["flash_24h"] == 2
    assert c["flash_standby_24h"] == 2
    e.set_mode(Mode.STANDBY, 9)
    r = e.step(10, [_view()])
    assert "standby" not in [cmd.kind for cmd in r.commands]  # still over the hourly flash limit


def test_flash_safety_net_uses_ram_instead_of_standby() -> None:
    # PLAN-M4b §2.7: after the flash limit, standby becomes 0 W in RAM.
    from zephyr_core.settings import Settings

    e = ZephyrEngine(Settings().with_changes(flash_limit_hour=2), mode=Mode.STANDBY)
    for i in range(2):
        e.counters_record("a", "standby", float(i))
    r = e.step(10, [_view()])
    kinds = [c.kind for c in r.commands]
    assert "standby" not in kinds
    assert any(c.kind == "power" and c.props.get("smartMode") == 1 for c in r.commands)
    assert e.counters(10)["a"]["flash_paused"] == 1
    assert e.counters(10)["a"]["flash_standby_24h"] == 2


def test_calibrating_or_bypass_set_gets_no_commands() -> None:
    # SPEC-basis §8: no 0 W and no standby while the set calibrates itself or is in bypass.
    from dataclasses import replace

    from sim.device import SimSet

    for flag in ("calibrating", "bypass"):
        for mode in (Mode.ZERO_METER, Mode.STANDBY):
            eng = ZephyrEngine(Settings(), mode)
            eng.set_live(True, 0.0, [])
            rep = replace(SimSet(soc=60).report(0), **{flag: True})
            for t in range(400):
                eng.p1_reported(float(t), 300.0)
                r = eng.step(float(t), [SetView("0", 1, rep, True)])
                assert r.commands == (), (flag, mode, t, r.commands)


def _at_soc(soc: int, fixture: str = "standby") -> SetView:
    data = load_fixture(fixture)
    data["properties"]["electricLevel"] = soc
    return SetView("a", 1, parse_report(data), True)


@pytest.mark.parametrize("soc", [9, 5])
def test_recharge_starts_just_below_the_minimum(soc: int) -> None:
    e = ZephyrEngine(Settings(min_soc=10, max_soc=95))
    e.p1_reported(0, 300)
    r = e.step(0, [_at_soc(soc)])
    assert r.reason.code is ReasonCode.RECHARGE_MIN
    assert r.setpoint == 300


def test_no_recharge_at_the_minimum() -> None:
    e = ZephyrEngine(Settings(min_soc=10, max_soc=95))
    e.p1_reported(0, 300)
    r = e.step(0, [_at_soc(10)])
    assert r.reason.code is not ReasonCode.RECHARGE_MIN
    assert r.setpoint <= 0


def _grid_reverse(result) -> list[int]:  # type: ignore[no-untyped-def]
    return [c.props["gridReverse"] for c in result.commands if "gridReverse" in c.props]


def test_grid_reverse_follows_a_negative_export_price() -> None:
    """The fixture reports gridReverse 1 (export allowed)."""
    e = ZephyrEngine(Settings(min_soc=10, max_soc=100))
    e.p1_reported(0, 0)
    assert _grid_reverse(e.step(0, [_view()])) == []  # not managed
    e.p1_reported(2, 0)
    blocked = e.step(2, [_view()], export_blocked=True)
    assert _grid_reverse(blocked) == [2]
    assert len([c for c in blocked.commands if c.key == "a"]) == len({c.kind for c in blocked.commands if c.key == "a"})
    e.p1_reported(4, 0)
    assert _grid_reverse(e.step(4, [_view()], export_blocked=True)) == []  # sent, waiting for the report
    e.p1_reported(70, 0)
    assert _grid_reverse(e.step(70, [_view()], export_blocked=True)) == [2]  # still not taken after 60 s: again
    e.p1_reported(72, 0)
    assert _grid_reverse(e.step(72, [_view()], export_blocked=False)) == []  # the set already allows export


def test_grid_reverse_rides_along_with_a_power_command() -> None:
    e = ZephyrEngine(Settings(min_soc=10, max_soc=100))
    e.p1_reported(0, 600)
    result = e.step(0, [_view()], export_blocked=True)
    assert [(c.kind, c.props["gridReverse"]) for c in result.commands] == [("power", 2)]  # one write, not two


def test_short_peak_left_to_the_grid_is_counted() -> None:
    """A 2 kW tap for 6 s while delivering: the step filter holds it, the engine counts it."""
    e = ZephyrEngine(Settings(min_soc=10, max_soc=100))
    view = _view()
    t = 0.0
    for _ in range(10):
        e.p1_reported(t, 100)
        e.step(t, [view])
        t += 1.0
    for _ in range(6):
        e.p1_reported(t, 2100)
        e.step(t, [view])
        t += 1.0
    for _ in range(5):
        e.p1_reported(t, 100)
        e.step(t, [view])
        t += 1.0
    assert e.grid_filter.holds == 1
    assert e.peak_kwh == pytest.approx(2.0 * 6 / 3600, rel=0.2)


def _virtual_after_step_of_other_controller(stepped: bool) -> tuple[float, dict[str, float] | None]:
    """DSMR 4: a P1 measurement every 10 s; the other controller steps 650 -> 570 W in between."""
    import dataclasses

    base = _view()
    e = ZephyrEngine()
    e.enable_twin()

    def view(watts: float) -> SetView:
        return dataclasses.replace(base, report=dataclasses.replace(base.report, battery_power_ac=watts))

    for t in range(0, 11):
        battery = -570.0 if stepped and t >= 4 else -650.0
        if t in (0, 10):
            e.p1_reported(float(t), -43.0 if t == 0 else 37.0)
        e.step(float(t), [view(battery)])
    assert e._p1_value is not None
    return e._p1_value, e.twin_alignment(10.5)


def test_virtual_p1_uses_the_battery_at_the_moment_of_the_measurement() -> None:
    # OPDRACHT-p1-profiel §7.2: seen 15:45:18 at Peter, measured -43 W, real battery 652 -> 569 W,
    # virtual P1 -158 W. The measurement that is used is 10 s old: pair it with the battery then.
    steady, _ = _virtual_after_step_of_other_controller(stepped=False)
    stepped, alignment = _virtual_after_step_of_other_controller(stepped=True)
    assert stepped == steady  # no jump from the other controller's step
    assert alignment == {"battery_real_at_p1": -650, "p1_age_s": 10.5}


def test_repeated_p1_value_keeps_the_moment_of_its_measurement() -> None:
    e = ZephyrEngine()
    e.enable_twin()
    e.p1_reported(0.0, 50.0)
    e.step(0.0, [_view()])
    e.p1_reported(5.0, 80.0)  # a new value: the meter interval becomes 5 s
    e.step(5.0, [_view()])
    e.p1_reported(6.0, 80.0)  # a repeat by the integration, not a new measurement
    e.step(7.0, [_view()])
    e.p1_reported(8.0, 80.0)
    alignment = e.twin_alignment(8.0)
    assert alignment is not None and alignment["p1_age_s"] == 3.0  # the measurement of t=5
