"""Correction of closed cost quarters after a filled counter gap (SPEC-tellers T3)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest

from zephyr_core.cost_correction import day_delta, gap_shares, reevaluate
from zephyr_core.costs import Pools, QuarterInput, Tariffs, add_to_day, evaluate

T0 = datetime(2026, 11, 26, 1, 0, tzinfo=UTC)
TARIFFS = Tariffs(markup_import=0.0165)


def _tariffs(_day: date) -> Tariffs:
    return TARIFFS


def _month(_day: date) -> int:
    return 30


def _log(charges: list[float], discharges: list[float]) -> tuple[list[dict[str, Any]], Pools]:
    """A cost log as the recorder keeps it: every quarter with the inputs for a correction."""
    pools = Pools()
    records = []
    for i, (chg, dis) in enumerate(zip(charges, discharges, strict=True)):
        start = T0 + timedelta(minutes=15 * i)
        before = pools.as_dict()
        q = QuarterInput(start, 15, 0.1 + chg, 0.0, chg, dis, None, 0.30 if i < 4 else 0.50, 1.0, 5.0 + sum(charges[: i + 1]), False)
        record = evaluate(q, TARIFFS, pools)
        record.update({"pools": before, "stored_kwh": q.stored_kwh, "daylight": False, "coverage": 1.0, "plan_action": "L"})
        records.append(record)
    return records, pools


def test_gap_shares_by_time() -> None:
    shares = gap_shares(T0 + timedelta(minutes=10), T0 + timedelta(minutes=40))
    assert {k.minute: round(v, 4) for k, v in shares.items()} == {0: round(5 / 30, 4), 15: 0.5, 30: round(10 / 30, 4)}
    assert gap_shares(T0, T0) == {}


def test_correction_equals_a_log_that_measured_it() -> None:
    """Charge in quarters 1–2 was lost in a gap; after the fill the log matches one without the gap."""
    real, real_pools = _log([0.0, 0.6, 0.6, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.5, 0.5])
    lost, _ = _log([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.5, 0.5])
    # The grid import of the gap quarters was measured (P1): give the lost log the same import.
    for r_real, r_lost in zip(real, lost, strict=True):
        r_lost["import_kwh"] = r_real["import_kwh"]
    corrections = {real[1]["start"]: {"charged": 0.6}, real[2]["start"]: {"charged": 0.6}}
    result = reevaluate(lost, corrections, _tariffs, _month, UTC, "2026-11-26T03:00:00+00:00")
    assert result is not None
    pools, changes = result
    assert len(changes) == 5  # from the first corrected quarter to the end
    for fixed, measured in zip(lost, real, strict=True):
        assert fixed["charge_kwh"] == measured["charge_kwh"]
        assert fixed["cost"] == pytest.approx(measured["cost"])
        assert fixed["solar_via_battery"] == measured["solar_via_battery"]
    assert pools.as_dict() == real_pools.as_dict()
    assert lost[1]["estimated"] and lost[1]["corrected_at"] == "2026-11-26T03:00:00+00:00"
    assert "estimated" not in lost[3] and lost[3]["plan_action"] == "L"  # later quarters only re-evaluated


def test_day_delta_replaces_the_contribution() -> None:
    real, _ = _log([0.0, 0.6], [0.0, 0.0])
    lost, _ = _log([0.0, 0.0], [0.0, 0.0])
    lost[1]["import_kwh"] = real[1]["import_kwh"]
    day: dict[str, Any] = {}
    for record in lost:
        add_to_day(day, record)
    old = [dict(r) for r in lost]
    result = reevaluate(lost, {lost[1]["start"]: {"charged": 0.6}}, _tariffs, _month, UTC, "x")
    assert result is not None
    for before, after in result[1]:
        day_delta(day, before, after)
    expected: dict[str, Any] = {}
    for record in real:
        add_to_day(expected, record)
    assert day["charge_kwh"] == pytest.approx(expected["charge_kwh"])
    assert day["cost"] == pytest.approx(expected["cost"])
    assert day["quarters"] == expected["quarters"] == 2
    assert old[1]["charge_kwh"] == 0.0


def test_quarters_without_inputs_are_not_corrected() -> None:
    records, _ = _log([0.0, 0.0], [0.0, 0.0])
    del records[0]["pools"]
    assert reevaluate(records, {records[0]["start"]: {"charged": 0.1}}, _tariffs, _month, UTC, "x") is None
    assert reevaluate(records, {"2020-01-01T00:00:00+00:00": {"charged": 0.1}}, _tariffs, _month, UTC, "x") is None
