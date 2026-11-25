"""Shadow mode with the twin: another system drives the set, ZEPHYR computes alongside.

The yardstick is ZEPHYR live on the same house: the shadow run must predict its
writes, direction swaps and grid energy, whatever the other system does.
"""

from __future__ import annotations

import random

from sim.runner import Profile, Simulation, energy_wh, writes
from zephyr_core.engine import Mode, ZephyrEngine
from zephyr_core.settings import Settings

DURATION = 1800
NERVOUS = Settings(deadband=5, target_grid_charge=0, noise_band=0, min_command_step=10)
"""Another controller that corrects every few watts: the hardest case for a shadow run."""


def _house(seed: int = 1) -> tuple[Profile, Profile]:
    rng = random.Random(seed)
    noise: dict[int, float] = {}

    def load(t: float) -> float:
        k = int(t)
        if k not in noise:
            noise[k] = rng.gauss(0, 25)
        return 450 + noise[k] + (2100 if 600 <= t < 640 else 0) + (900 if 1000 <= t < 1300 else 0)

    def solar(t: float) -> float:
        return 2400.0 if t < 1400 else 300.0

    return load, solar


def _shadow(other: Settings, mode: Mode = Mode.ZERO_METER) -> tuple[Simulation, ZephyrEngine, list[int]]:
    load, solar = _house()
    observer = ZephyrEngine()
    observer.enable_twin()
    sim = Simulation(load=load, solar=solar, settings=other, mode=mode, observer=observer)
    trace = sim.run(DURATION)
    power = [c for _, r in trace.shadow for c in r.commands if c.kind == "power"]
    swaps = sum(1 for c in power if "acMode" in c.props)
    return sim, observer, [len(power), swaps]


def _live() -> tuple[int, int, float, float]:
    load, solar = _house()
    sim = Simulation(load=load, solar=solar)
    trace = sim.run(DURATION)
    swaps = sum(1 for _, w in sim.sets[0].writes if "acMode" in w)
    return writes(sim), swaps, energy_wh(trace, +1), energy_wh(trace, -1)


def test_twin_predicts_live_control_while_another_controller_drives_the_set() -> None:
    live_writes, live_swaps, live_import, live_export = _live()
    for other in (Settings(), NERVOUS):
        _, observer, (shadow_writes, shadow_swaps) = _shadow(other)
        assert abs(shadow_writes - live_writes) <= 0.25 * live_writes
        assert shadow_swaps == live_swaps
        summary = observer.twin_summary()
        assert summary is not None
        assert abs(summary["import_wh_zephyr"] - live_import) < 6
        assert abs(summary["export_wh_zephyr"] - live_export) < 6


def test_twin_ignores_a_grid_charge_by_the_other_system() -> None:
    """The other system charges at full power from the grid (a planned cheap hour): the twin
    still charges only from the solar surplus, as ZEPHYR live would."""
    sim, observer, _ = _shadow(Settings(), Mode.FAST_CHARGE)
    assert max(s.power for s in sim.sets) > 2000  # the real set charges flat out
    summary = observer.twin_summary()
    assert summary is not None
    _, _, live_import, _ = _live()
    assert summary["import_wh_measured"] > 10 * max(live_import, 1)  # the real grid charge
    assert abs(summary["import_wh_zephyr"] - live_import) < 6
