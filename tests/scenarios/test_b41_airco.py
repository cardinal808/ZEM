"""B41 (SPEC-airco) in the closed-loop simulator: the battery does not feed the air conditioner."""

from __future__ import annotations

from sim.runner import Simulation, constant, steps
from zephyr_core.engine import ReasonCode


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _after(trace, start, values):  # type: ignore[no-untyped-def]
    return [v for t, v in zip(trace.t, values, strict=True) if t >= start]


def test_battery_delivers_only_for_the_rest_of_the_house() -> None:
    # House 600 W + air conditioner 1 000 W (heating).
    sim = Simulation(load=constant(1600), excluded_load=lambda t: 1000.0)
    tr = sim.run(180)
    assert abs(_mean(_after(tr, 60, tr.grid)) - 1000) < 40
    assert abs(_mean(_after(tr, 60, tr.battery)) + 600) < 40
    reasons = [r.reason for t, r in tr.results if t >= 60 and r.reason.code is ReasonCode.DELIVERING]
    assert reasons and all(r.params.get("excluded") == 1000 for r in reasons)


def test_air_conditioner_larger_than_the_house_demand_no_grid_charging() -> None:
    # The estimate is higher than what the house uses: deliver nothing, never charge from the grid.
    sim = Simulation(load=constant(800), excluded_load=lambda t: 2000.0)
    tr = sim.run(120)
    assert max(_after(tr, 20, tr.battery)) <= 10
    assert min(_after(tr, 30, tr.battery)) >= -60


def test_solar_surplus_still_charges() -> None:
    # Solar 2 500 W, house 500 W + air conditioner 1 000 W: 1 000 W surplus goes into the battery.
    sim = Simulation(load=constant(1500), solar=constant(2500), excluded_load=lambda t: 1000.0)
    tr = sim.run(120)
    assert abs(_mean(_after(tr, 60, tr.battery)) - 1000) < 40


def test_air_conditioner_stops_battery_takes_over() -> None:
    sim = Simulation(load=steps((0, 1600), (120, 600)), excluded_load=lambda t: 1000.0 if t < 120 else 0.0)
    tr = sim.run(240)
    assert abs(_mean(_after(tr, 180, tr.grid))) < 40
    assert abs(_mean(_after(tr, 180, tr.battery)) + 600) < 40
