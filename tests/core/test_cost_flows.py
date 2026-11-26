"""Battery and set-PV flows for the cost log (B44 T0): no double count of the sets' own PV."""

from __future__ import annotations

import dataclasses
import datetime as dt
from datetime import UTC

import pytest

from conftest import load_fixture
from zephyr_core.costs import Pools, QuarterInput, QuarterMeter, Tariffs, evaluate
from zephyr_core.totals import COST_HOLD_SECONDS, SetSnapshot, cost_flows
from zephyr_core.zensdk import parse_report


def _snap(name: str = "standby", *, online: bool = True, last_success: float | None = 0.0, **report: object) -> SetSnapshot:
    rep = dataclasses.replace(parse_report(load_fixture(name)), **report)  # type: ignore[arg-type]
    return SetSnapshot(report=rep, capacity_kwh=11.04, online=online, last_success=last_success)


def test_flows_use_the_pack_powers() -> None:
    charging = _snap("charge_2400")
    flows = cost_flows([charging], now=1.0)
    assert flows is not None
    assert flows.charge == pytest.approx(charging.report.charge_power_ac) and flows.deliver == 0.0  # type: ignore[union-attr]
    assert flows.complete


def test_set_pv_is_solar_not_battery() -> None:
    """500 W from the set's own panels straight to the house, battery idle."""
    pv = _snap(
        solar_power=500.0, output_home_power=500.0, grid_input_power=0.0, battery_power_ac=-500.0, charge_power_ac=0.0, deliver_power_ac=0.0
    )
    flows = cost_flows([pv], now=1.0)
    assert flows is not None and flows.charge == 0.0 and flows.deliver == 0.0 and flows.solar == 500.0
    # A quarter of it: the house uses the 500 W once, not twice.
    meter = QuarterMeter()
    meter.sample(0.0, 0.0, flows.charge, flows.deliver, flows.solar)
    done = meter.take(9.0)  # within the max sample gap of 10 s
    q = QuarterInput(
        start=dt.datetime(2026, 11, 26, 12, tzinfo=UTC),
        minutes=15,
        import_kwh=done.import_kwh,
        export_kwh=done.export_kwh,
        charge_kwh=done.charge_kwh,
        discharge_kwh=done.discharge_kwh,
        solar_kwh=done.set_solar_kwh,
        market=0.1,
        coverage=1.0,
        stored_kwh=None,
        daylight=True,
    )
    record = evaluate(q, Tariffs(), Pools())
    assert record["house_kwh"] == pytest.approx(0.5 * 9 / 3600, abs=1e-4)
    assert record["discharge_kwh"] == 0.0


def test_hold_after_the_last_good_report() -> None:
    gone = _snap("deliver_760", online=False, last_success=0.0)
    here = _snap("charge_2400")
    within = cost_flows([gone, here], now=COST_HOLD_SECONDS - 1)
    assert within is not None and within.complete and within.deliver > 0
    beyond = cost_flows([gone, here], now=COST_HOLD_SECONDS + 1)
    assert beyond is not None and not beyond.complete and beyond.deliver == 0.0 and beyond.charge > 0
    assert cost_flows([gone], now=COST_HOLD_SECONDS + 1) is None
