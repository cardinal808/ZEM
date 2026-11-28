"""Live, idle by our own command: a start is computed from the P1 alone (diagnosis 28-11)."""

from __future__ import annotations

from zephyr_core.controller import ControllerInput, ZeroMeterController
from zephyr_core.settings import Settings


def _live_idle() -> ZeroMeterController:
    controller = ZeroMeterController(Settings().validated(), trust_commands=False)
    controller.wait_for_reach = True
    controller.take_over(0, 0.0)
    return controller


def _run(controller: ZeroMeterController, grid: float, reported: float, seconds: int, start: float = 100.0) -> list[int]:
    out = []
    for i in range(seconds):
        now = start + i
        result = controller.step(
            ControllerInput(
                now=now, grid_power=grid, battery_power=reported, max_charge=2400, max_deliver=2400, p1_interval=1.0, sample=int(now)
            )
        )
        out.append(result.setpoint)
    return out


def test_small_surplus_with_a_lagging_report_does_not_start() -> None:
    # 28-11 11:52: 50 W export, the report still said 169 W after 0 W was sent: start at 170 W.
    assert set(_run(_live_idle(), grid=-53, reported=169, seconds=20)) == {0}


def test_surplus_above_the_minimum_starts_with_the_surplus_after_confirmation() -> None:
    setpoints = _run(_live_idle(), grid=-160, reported=169, seconds=10)
    first = next(i for i, sp in enumerate(setpoints) if sp != 0)
    assert first >= 1  # start hysteresis: two samples above the minimum
    assert 100 <= setpoints[first] <= 140  # the surplus (160 W − 30 W target), not 169 + 160


def test_import_starts_delivering_from_the_p1_alone() -> None:
    setpoints = _run(_live_idle(), grid=300, reported=-150, seconds=10)
    assert -310 <= min(setpoints) <= -250
