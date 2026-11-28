"""Slow P1 profile: the dead zone while delivering stops at 20 W export (OPDRACHT-p1-profiel §7.4)."""

from __future__ import annotations

from zephyr_core.controller import ControllerInput, ZeroMeterController
from zephyr_core.settings import Settings


def _setpoints(grid: float, p1_interval: float, steps: int = 6) -> list[int]:
    """Deliver 600 W (taken over), then a constant grid value, one new sample per meter interval."""
    controller = ZeroMeterController(Settings().validated(), trust_commands=False)
    controller.take_over(-600, 0.0)
    out = []
    now = 0.0
    for sample in range(1, steps + 1):
        now += p1_interval
        result = controller.step(
            ControllerInput(
                now=now,
                grid_power=grid,
                battery_power=float(controller.setpoint),
                max_charge=2400,
                max_deliver=2400,
                p1_interval=p1_interval,
                sample=sample,
            )
        )
        out.append(result.setpoint)
    return out


def test_slow_profile_corrects_export_of_35_w() -> None:
    assert _setpoints(-35, 10.0)[-1] > -600  # delivers less: out of the band −20…+55 W


def test_slow_profile_leaves_import_of_40_w() -> None:
    assert set(_setpoints(40, 10.0)) == {-600}


def test_slow_profile_leaves_export_of_15_w() -> None:
    assert set(_setpoints(-15, 10.0)) == {-600}


def test_fast_profile_unchanged() -> None:
    # Fast meter: dead zone ±25 W around the target of 5 W, as before.
    assert set(_setpoints(-15, 1.0, steps=20)) == {-600}
    assert _setpoints(-35, 1.0, steps=20)[-1] > -600
