"""Live control with a set that starts slowly from 0 W (seen live 25-11 on a 2400 Pro).

The relay opens at 0 W; the next start takes ~9 s before power flows. Trusting the last command
made ZEPHYR double it after the settle time (520 -> 1040 W), then export, then 0 W, round and
round. Live control now works from the measured power, aligned with P1, and waits for the set.
"""

from __future__ import annotations

from sim.device import SimSet
from sim.runner import Simulation, constant, share_within


def _slow_set() -> SimSet:
    return SimSet(startup=8.0, report_lag=1.5, relay_off_on_zero=True, ramp_down=600)


def test_slow_start_is_not_doubled() -> None:
    sim = Simulation(load=constant(530), sets=[_slow_set()])
    sim.engine.set_live(True, 0.0, [])
    tr = sim.run(120)
    outputs = [w["outputLimit"] for _, w in sim.sets[0].writes if w.get("outputLimit")]
    assert outputs and max(outputs) <= 600, outputs
    assert min(g for t, g in zip(tr.t, tr.grid, strict=True) if t > 5) > -100  # no export
    assert share_within(tr, 15, 50, start=20) > 0.95


def test_no_on_off_cycle_on_a_steady_load() -> None:
    sim = Simulation(load=constant(530), sets=[_slow_set()])
    sim.engine.set_live(True, 0.0, [])
    sim.run(300)
    zeros_after_start = [t for t, w in sim.sets[0].writes if t > 5 and w.get("outputLimit") == 0 and w.get("inputLimit") == 0]
    assert zeros_after_start == []
