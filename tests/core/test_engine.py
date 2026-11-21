"""Engine: modes, safety, write rules (single steps, without the simulator)."""

from __future__ import annotations

import pytest

from conftest import load_fixture
from zem_core.engine import Action, Mode, ReasonCode, SetView, ZemEngine
from zem_core.settings import Settings, SettingsError
from zem_core.zensdk import parse_report


def _view(fixture: str = "deliver_760", online: bool = True) -> SetView:
    return SetView("a", 1, parse_report(load_fixture(fixture)), online)


def test_without_p1_sets_go_to_standby_with_clear_reason() -> None:
    e = ZemEngine()
    r = e.step(0, [_view()])
    assert r.reason.code is ReasonCode.P1_MISSING
    assert r.action is Action.STANDBY
    assert [c.kind for c in r.commands if c.kind != "soc_limits"] == ["standby"]
    assert "P1" in r.reason.text("nl")


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
