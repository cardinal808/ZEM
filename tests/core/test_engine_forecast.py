"""Mode Dynamic Forecasting: the engine carries out the planner's action (SPEC-planner §7)."""

from __future__ import annotations

from conftest import load_fixture
from zephyr_core.engine import Action, Mode, ReasonCode, SetView, ZephyrEngine
from zephyr_core.planner import Action as Plan
from zephyr_core.settings import Settings
from zephyr_core.zensdk import parse_report


def _view(fixture: str = "deliver_760", **props: int) -> SetView:
    data = load_fixture(fixture)
    data["properties"].update(props)
    return SetView("a", 1, parse_report(data), True)


def _engine() -> ZephyrEngine:
    return ZephyrEngine(Settings(min_soc=10, max_soc=95), Mode.FORECAST)


def _step(e: ZephyrEngine, t: float, plan: Plan | None, grid: float = 300.0, view: SetView | None = None):  # type: ignore[no-untyped-def]
    e.p1_reported(t, grid)
    return e.step(t, [view or _view()], plan_action=plan)


def test_charge_at_full_power_from_the_start() -> None:
    e = _engine()
    r = _step(e, 0, Plan.CHARGE)
    assert r.reason.code is ReasonCode.PLAN_CHARGE
    assert r.setpoint == 2400
    assert r.action is Action.CHARGE
    assert "laadt 2400 W uit het net" in r.reason.text("nl")


def test_charge_keeps_going_10_s_after_the_plan_stops_then_pauses_2_minutes() -> None:
    e = _engine()
    _step(e, 0, Plan.CHARGE)
    r = _step(e, 5, Plan.DELIVER)
    assert r.reason.code is ReasonCode.PLAN_CHARGE  # within 10 s: keep charging
    r = _step(e, 11, Plan.DELIVER)
    assert r.reason.code is not ReasonCode.PLAN_CHARGE
    assert r.setpoint <= 0
    # Back to L within 2 minutes: wait, without delivering.
    r = _step(e, 60, Plan.CHARGE)
    assert r.reason.code is ReasonCode.PLAN_CHARGE_WAIT
    assert r.setpoint <= 0
    assert "pauze van 2 minuten" in r.reason.text("nl")
    r = _step(e, 11 + 121, Plan.CHARGE)
    assert r.reason.code is ReasonCode.PLAN_CHARGE


def test_full_battery_with_plan_charge_holds() -> None:
    e = _engine()
    r = _step(e, 0, Plan.CHARGE, view=_view(electricLevel=95))
    assert r.setpoint <= 0
    assert r.reason.code is not ReasonCode.PLAN_CHARGE


def test_hold_does_not_deliver() -> None:
    e = _engine()
    for t in range(0, 20, 2):
        r = _step(e, t, Plan.HOLD, grid=800)
    assert r.setpoint == 0
    assert r.reason.code is ReasonCode.PLAN_HOLD
    assert r.action is Action.HOLD


def test_hold_still_charges_from_solar_surplus() -> None:
    e = _engine()
    for t in range(0, 30, 2):
        r = _step(e, t, Plan.HOLD, grid=-1500, view=_view(packInputPower=0, outputHomePower=0, outputLimit=0, acMode=1))
    assert r.setpoint > 0
    assert r.reason.code is ReasonCode.CHARGING_SOLAR


def test_deliver_and_no_plan_are_zero_on_the_meter() -> None:
    for plan in (Plan.DELIVER, None):
        e = _engine()
        for t in range(0, 20, 2):
            r = _step(e, t, plan, grid=300)
        assert r.setpoint < 0
        assert r.reason.code is ReasonCode.DELIVERING


def test_export_at_full_power_but_not_right_after_grid_charging() -> None:
    e = _engine()
    r = _step(e, 0, Plan.EXPORT)
    assert r.reason.code is ReasonCode.PLAN_EXPORT and r.setpoint == -2400
    e = _engine()
    _step(e, 0, Plan.CHARGE)
    r = _step(e, 20, Plan.EXPORT)
    assert r.reason.code is not ReasonCode.PLAN_EXPORT  # grid charging stopped < 2 min ago
    r = _step(e, 20 + 121, Plan.EXPORT)
    assert r.reason.code is ReasonCode.PLAN_EXPORT


def test_export_stops_at_min_soc() -> None:
    e = _engine()
    r = _step(e, 0, Plan.EXPORT, view=_view(electricLevel=10))
    assert r.reason.code is not ReasonCode.PLAN_EXPORT
    assert r.setpoint >= 0


def test_plan_is_ignored_in_zero_meter_mode() -> None:
    e = ZephyrEngine(Settings(min_soc=10, max_soc=95), Mode.ZERO_METER)
    r = _step(e, 0, Plan.CHARGE)
    assert r.reason.code is not ReasonCode.PLAN_CHARGE
