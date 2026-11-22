"""Engine: modes, safety, write rules (single steps, without the simulator)."""

from __future__ import annotations

import copy

import pytest

from conftest import load_fixture
from zem_core.engine import Action, Mode, ReasonCode, SetView, ZemEngine
from zem_core.settings import Settings, SettingsError
from zem_core.zensdk import parse_report


def _view(fixture: str = "deliver_760", online: bool = True) -> SetView:
    return SetView("a", 1, parse_report(load_fixture(fixture)), online)


def test_after_start_wait_for_p1_without_touching_the_sets() -> None:
    e = ZemEngine()
    r = e.step(0, [_view()])
    assert r.reason.code is ReasonCode.P1_MISSING
    assert r.action is Action.HOLD
    assert r.commands == ()
    assert "P1" in r.reason.text("nl")
    e.p1_reported(5, 300)
    assert e.step(5, [_view()]).reason.code is not ReasonCode.P1_MISSING


def test_without_p1_sets_go_to_standby_with_clear_reason() -> None:
    e = ZemEngine()
    e.step(0, [_view()])
    r = e.step(61, [_view()])
    assert r.reason.code is ReasonCode.P1_MISSING
    assert r.action is Action.STANDBY
    assert [c.kind for c in r.commands if c.kind != "soc_limits"] == ["standby"]


def test_soc_limits_are_aligned_once() -> None:
    e = ZemEngine(Settings(min_soc=10, max_soc=95))
    e.p1_reported(0, 0)
    first = e.step(0, [_view()])
    assert [c.props for c in first.commands if c.kind == "soc_limits"] == [{"minSoc": 100, "socSet": 950, "smartMode": 0}]
    e.p1_reported(2, 0)
    assert not [c for c in e.step(2, [_view()]).commands if c.kind == "soc_limits"]


def test_offline_set_gets_no_commands() -> None:
    e = ZemEngine()
    e.p1_reported(0, 500)
    r = e.step(0, [_view(online=False)])
    assert r.commands == ()
    assert r.reason.code is ReasonCode.NO_SET


def test_standby_mode() -> None:
    e = ZemEngine(mode=Mode.STANDBY)
    e.p1_reported(0, 500)
    r = e.step(0, [_view()])
    assert r.action is Action.STANDBY and r.setpoint == 0


def test_fast_discharge_uses_full_power() -> None:
    e = ZemEngine(mode=Mode.FAST_DISCHARGE)
    r = e.step(0, [_view()])
    assert r.setpoint == -2400
    power = next(c for c in r.commands if c.kind == "power")
    assert power.props["outputLimit"] == 2400


def test_temperature_blocks_charging() -> None:
    data = load_fixture("charge_2400")
    for p in data["packData"]:
        p["maxTemp"] = 2731 + 600  # 60 °C
    e = ZemEngine(mode=Mode.FAST_CHARGE)
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
    e = ZemEngine()
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
    e = ZemEngine()
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
    e = ZemEngine()
    e.controller.trust_commands = False
    reasons = set()
    for t in range(40):
        e.p1_reported(t, -1300 + (t % 3) * 10)
        reasons.add(e.step(t + 0.5, [view]).reason.code)
    assert reasons == {ReasonCode.FULL}


def test_fault_level_without_error_does_not_block() -> None:
    # A 2400 AC+ at 100 % reported faultLevel 2 with is_error 0; ZEM must still be able to deliver.
    report = parse_report(load_fixture("ac_plus_full_fault_level"))
    assert report.fault_level == 2
    assert not report.fault
    e = ZemEngine()
    for t in range(0, 30, 3):
        e.p1_reported(t, 600 + t)
        r = e.step(t, [SetView("a", 1, report, True)])
    assert r.reason.code is not ReasonCode.NO_SET
    assert r.setpoint < 0


def test_silent_balanced_grid_is_not_stale() -> None:
    # A P1 sensor that only reports changes stays silent at exactly 0 W; the setpoint holds.
    e = ZemEngine()
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
    e = ZemEngine()
    for t in range(0, 20):
        e.p1_reported(t, 600 + t)
        e.step(t, [_view()])
    assert e.step(19 + 11, [_view()]).reason.code is ReasonCode.P1_STALE
