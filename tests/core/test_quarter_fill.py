"""Filling the unmeasured part of a cost quarter (OPDRACHT-onvolledige-kwartieren)."""

from __future__ import annotations

import pytest

from zephyr_core.costs import add_to_day, quarter_status
from zephyr_core.quarter_fill import (
    HISTORY,
    INTERPOLATED,
    NONE,
    OWN_RATE,
    Part,
    QuarterFill,
    fill_part,
    interpolate,
    scale_to,
)


def test_part_of_a_quarter_between_neighbours() -> None:
    # 10 of 15 minutes at 400 W; neighbours 400 W and 600 W → the missing 5 minutes at ~500 W.
    done = fill_part(Part(0.4 * 10 / 60, 10 / 15), 0.1, 0.15)
    assert done is not None and done.method == INTERPOLATED
    assert done.kwh == pytest.approx(0.108, abs=0.001)


def test_measured_flow_is_left_alone() -> None:
    assert fill_part(Part(0.1, 0.97), 0.2, 0.3) is None


def test_without_neighbours_own_rate_then_history_then_nothing() -> None:
    own = fill_part(Part(0.05, 0.5), None, None, history=0.3)
    assert own is not None and own.method == OWN_RATE and own.kwh == pytest.approx(0.1)
    hist = fill_part(Part(0.0, 0.0), None, None, history=0.3)
    assert hist is not None and hist.method == HISTORY and hist.kwh == pytest.approx(0.3)
    none = fill_part(Part(0.0, 0.0), None, None)
    assert none is not None and none.method == NONE and none.kwh == 0.0


def test_solar_at_night_is_zero() -> None:
    done = fill_part(Part(0.0, 0.0), 0.2, 0.2, allowed=False)
    assert done is not None and done.kwh == 0.0


def test_interpolate_and_scale_on_a_counter() -> None:
    # 3 quarters between 0.10 and 0.30 rise; a counter of 0.80 kWh over the gap sets the total.
    values = interpolate(0.10, 0.30, 3)
    assert values == pytest.approx([0.15, 0.20, 0.25])
    scaled = scale_to(values, 0.80)
    assert sum(scaled) == pytest.approx(0.80) and scaled[0] < scaled[1] < scaled[2]
    assert scale_to([0.0, 0.0], 0.4) == [0.2, 0.2]
    assert interpolate(None, 0.2, 2) == [0.2, 0.2]
    assert interpolate(None, None, 2) is None


def test_status_and_day_counts() -> None:
    fill = QuarterFill()
    assert fill.status == "measured"
    fill.methods["import_kwh"] = INTERPOLATED
    fill.added["import_kwh"] = 0.04
    fill.causes.append("p1")
    record = {"import_kwh": 0.1, "complete": True, **fill.as_record()}
    assert record["status"] == "estimated"
    day: dict[str, float] = {}
    add_to_day(day, record)
    add_to_day(day, {"import_kwh": 0.0, "complete": False})  # before 0.8.79: incomplete = missing
    assert day["estimated"] == 1 and day["incomplete"] == 1
    assert day["cause_p1"] == 1 and day["method_interpolated"] == 1 and day["filled_import_kwh"] == pytest.approx(0.04)
    assert quarter_status({"complete": True, "estimated": True}) == "estimated"


def test_gap_without_counters_is_interpolated_and_solar_stops_at_sunset() -> None:
    from zephyr_core.quarter_fill import SCALED, fill_gap

    before = {"import_kwh": 0.10, "solar_ext_kwh": 0.2, "status": "measured"}
    fills = fill_gap(before, {"import_kwh": 0.30, "solar_ext_kwh": 0.0}, 3, {}, [True, False, False])
    assert [f.values["import_kwh"] for f in fills] == pytest.approx([0.15, 0.20, 0.25])
    assert all(f.methods["import_kwh"] == INTERPOLATED and f.status == "estimated" for f in fills)
    assert [f.values["solar_ext_kwh"] for f in fills][1:] == [0.0, 0.0]
    scaled = fill_gap(before, {"import_kwh": 0.30}, 3, {"import_kwh": 0.9}, [True] * 3)
    assert sum(f.values["import_kwh"] for f in scaled) == pytest.approx(0.9)
    assert scaled[0].methods["import_kwh"] == SCALED and "ha_off" in scaled[0].causes
    nothing = fill_gap(None, {"import_kwh": None}, 2, {}, [True, True])
    assert nothing[0].status == "missing"
