"""Calibration safety net (SPEC-planner §3.5)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from zephyr_core.calibration import HARD_PENALTY, REST_MAX, SOFT_PENALTY, Calibration, penalty
from zephyr_core.planner import Battery, PlannerSettings, Slot, plan

T0 = datetime(2026, 11, 1, 12, tzinfo=UTC)


def test_penalty_grows_from_half_the_interval() -> None:
    assert penalty(5, 21) == 0.0
    assert penalty(10.5, 21) == 0.0
    assert penalty(15.75, 21) == pytest.approx(SOFT_PENALTY / 2)
    assert penalty(21, 21) == HARD_PENALTY
    assert penalty(30, 0) == 0.0  # 0 = off


def test_new_installation_counts_from_now() -> None:
    c = Calibration()
    c.update(T0, 50, False)
    assert c.last_full == T0 and not c.active(T0)


def test_due_full_rest_and_done_when_the_set_finished() -> None:
    c = Calibration(last_full=T0)
    day22 = T0 + timedelta(days=22)
    assert c.active(day22) and c.penalty(day22) == HARD_PENALTY
    assert c.update(day22, 80, False) is None
    assert c.update(day22 + timedelta(hours=1), 99.5, False) == "rest"
    assert c.resting and c.active(day22) and c.penalty(day22) == 0.0
    assert c.update(day22 + timedelta(hours=1, minutes=10), 100, True) is None  # the set calibrates
    end = day22 + timedelta(hours=1, minutes=40)
    assert c.update(end, 100, False) == "done"
    assert not c.resting and c.last_full == end and not c.active(end)


def test_rest_ends_after_two_hours_without_a_calibration() -> None:
    c = Calibration(last_full=T0)
    day22 = T0 + timedelta(days=22)
    c.update(day22, 100, False)
    assert c.resting
    assert c.update(day22 + REST_MAX, 100, False) == "done" and not c.resting


def test_full_on_its_own_resets_the_count_without_rest() -> None:
    c = Calibration(last_full=T0)
    day5 = T0 + timedelta(days=5)
    assert c.update(day5, 100, False) == "full" and c.last_full == day5 and not c.resting
    # The set calibrated by itself (socStatus 1 → 0): counts as full too.
    day9 = T0 + timedelta(days=9)
    c.update(day9, 80, True)
    assert c.update(day9 + timedelta(minutes=20), 80, False) == "done" and c.last_full == day9 + timedelta(minutes=20)


def test_store_round_trip() -> None:
    c = Calibration(last_full=T0, resting_since=T0 + timedelta(days=21))
    back = Calibration.from_dict(c.as_dict(), 14)
    assert back.last_full == c.last_full and back.resting_since == c.resting_since and back.interval_days == 14


def test_planner_charges_full_once_when_calibration_is_due() -> None:
    battery = Battery(capacity_kwh=5.0, charge_kw=2.4, deliver_kw=2.4, eta_in=0.95, eta_out=0.95)
    slots = [Slot(hours=1.0, buy=0.30 + 0.01 * (i % 5), sell=0.05, load_kwh=0.3, solar_kwh=0.0) for i in range(12)]
    cfg = PlannerSettings(wear_cost=0.03, grid_charge_cost=0.01)
    lazy = plan(slots, battery, 1.0, cfg)
    assert max(s.energy_after for s in lazy.steps) < 4.9  # flat prices: no reason to charge full
    due = plan(slots, battery, 1.0, PlannerSettings(wear_cost=0.03, grid_charge_cost=0.01, calibration_penalty=HARD_PENALTY))
    assert max(s.energy_after for s in due.steps) >= 5.0 - 0.01
    first_full = next(i for i, s in enumerate(due.steps) if s.energy_after >= 4.99)
    # It picks the cheaper hours (buy 0.30) to fill up, not the dearest.
    assert all(slots[i].buy <= 0.32 for i, a in enumerate(due.actions[: first_full + 1]) if a.value == "L")


def test_already_full_needs_nothing_extra() -> None:
    battery = Battery(capacity_kwh=5.0, charge_kw=2.4, deliver_kw=2.4)
    slots = [Slot(hours=1.0, buy=0.30, sell=0.05, load_kwh=0.3, solar_kwh=0.0) for _ in range(6)]
    a = plan(slots, battery, 5.0, PlannerSettings())
    b = plan(slots, battery, 5.0, PlannerSettings(calibration_penalty=HARD_PENALTY))
    assert a.actions == b.actions
