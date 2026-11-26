"""Pre-flight check before going live: basic functions in LIVE configuration (slow 2400 Pro model).

Standby, zero on the meter, fast charge/discharge, battery full and empty, with the controller set
up as in live control (``set_live``: from the measurement, waiting for the set) and the set model
seen live on 25-11 (relay opens at 0 W, ~8 s start-up).
"""

from __future__ import annotations

from dataclasses import replace
from itertools import pairwise

from sim.device import SimSet
from sim.runner import Simulation, constant, energy_wh, share_within, steps
from zephyr_core.engine import Mode, ReasonCode, SetView, ZephyrEngine
from zephyr_core.settings import Settings


def _set(**kw: object) -> SimSet:
    base: dict[str, object] = {"startup": 8.0, "report_lag": 1.5, "relay_off_on_zero": True, "ramp_down": 600}
    base.update(kw)
    return SimSet(**base)  # type: ignore[arg-type]


def _live(sim: Simulation) -> Simulation:
    sim.engine.set_live(True, 0.0, [])
    return sim


def _charge_starts(sim: Simulation) -> int:
    lims = [w.get("inputLimit", 0) for _, w in sim.sets[0].writes if "inputLimit" in w]
    return sum(1 for a, b in pairwise([0, *lims]) if a == 0 and b > 0)


def _standby_writes(sim: Simulation) -> list[float]:
    return [t for t, w in sim.sets[0].writes if w.get("smartMode") == 0 and "socSet" not in w]


def test_live_constant_load() -> None:
    sim = _live(Simulation(load=constant(400), sets=[_set()], step_interval=1.0))
    tr = sim.run(300)
    assert share_within(tr, 15, 50, start=30) > 0.95
    assert len([t for t, _ in sim.sets[0].writes if t > 60]) <= 6


def test_live_kettle_and_drop() -> None:
    sim = _live(Simulation(load=steps((0, 400), (60, 2400), (240, 400)), sets=[_set()], step_interval=1.0))
    tr = sim.run(360)
    export_s = sum(0.1 for t, g in zip(tr.t, tr.grid, strict=True) if 240 <= t < 280 and g < -100)
    assert export_s < 4
    assert (
        share_within(
            tr,
            15,
            60,
            start=120,
        )
        > 0.5
    )


def test_live_full_from_solar_stops_and_goes_to_standby() -> None:
    sim = _live(Simulation(load=constant(400), solar=constant(1200), sets=[_set(soc=94.0)], step_interval=1.0))
    tr = sim.run(1800)
    assert max(tr.soc) <= 95.6
    assert energy_wh(tr, +1, start=30) < 3  # no grid charging
    assert _charge_starts(sim) == 1
    last = tr.results[-1][1]
    assert last.setpoint == 0 and last.reason.code is ReasonCode.FULL
    stby = _standby_writes(sim)
    assert len(stby) == 1  # one flash write once idle for 5 min
    assert not [t for t, _ in sim.sets[0].writes if t > stby[0]]  # silence afterwards


def test_live_full_then_evening_delivers_from_standby() -> None:
    sim = _live(Simulation(load=constant(500), solar=steps((0, 1300), (1200, 0)), sets=[_set(soc=94.5)], step_interval=1.0))
    tr = sim.run(1600)
    assert _standby_writes(sim)
    deliver_from = next(t for t, r in tr.results if t > 1200 and r.setpoint < 0)
    assert deliver_from - 1200 < 25
    assert share_within(tr, 15, 50, start=1260) > 0.9


def test_live_full_hysteresis_no_charge_restart_until_two_percent() -> None:
    # Full at 95 %; alternating clouds: delivering takes it a little below 95, charging only restarts at ≤ 93 %.
    sim = _live(
        Simulation(
            load=constant(600),
            solar=lambda t: 1600.0 if int(t // 300) % 2 == 0 else 0.0,
            sets=[_set(soc=94.6, capacity_kwh=2.0)],
            step_interval=1.0,
        )
    )
    tr = sim.run(3600)
    for (_, a), (_, b) in pairwise(tr.results):
        if a.setpoint <= 0 < b.setpoint:
            soc_now = next(s for t, s in zip(tr.t, tr.soc, strict=True) if t >= _)
            assert soc_now <= 93.6, soc_now
    assert max(tr.soc) <= 95.6
    assert len(_standby_writes(sim)) <= 10


def test_live_empty_stops_without_flapping() -> None:
    sim = _live(Simulation(load=constant(800), sets=[_set(soc=10.9)], step_interval=1.0))
    tr = sim.run(1200)
    assert min(tr.soc) >= 10.3
    assert tr.results[-1][1].reason.code is ReasonCode.EMPTY
    outs = [w.get("outputLimit", 0) for _, w in sim.sets[0].writes if "outputLimit" in w]
    assert sum(1 for a, b in pairwise([0, *outs]) if a == 0 and b > 0) <= 1


def test_live_standby_mode_writes_standby_once() -> None:
    sim = _live(Simulation(load=constant(800), sets=[_set()], step_interval=1.0))
    sim.run(60)
    assert sim.sets[0].power < -500
    sim.engine.set_mode(Mode.STANDBY, 60.0)
    n = len(sim.sets[0].writes)
    tr = sim.run(300, start=60.0)
    new = sim.sets[0].writes[n:]
    assert len(new) == 1 and new[0][1] == {"inputLimit": 0, "outputLimit": 0, "smartMode": 0}
    assert abs(sim.sets[0].power) < 1 and tr.results[-1][1].reason.code is ReasonCode.STANDBY_MODE


def test_live_fast_charge_until_full_then_back() -> None:
    sim = Simulation(load=constant(300), sets=[_set(soc=93.0, capacity_kwh=2.0)], step_interval=1.0, mode=Mode.FAST_CHARGE)
    _live(sim)
    tr = sim.run(900)
    assert max(tr.soc) <= 95.8
    assert sim.engine.mode is Mode.ZERO_METER
    assert max(sim.sets[0].writes, key=lambda w: w[1].get("inputLimit", 0))[1]["inputLimit"] == 2400
    assert tr.results[-1][1].setpoint <= 0


def test_live_fast_discharge_until_empty() -> None:
    sim = Simulation(load=constant(300), sets=[_set(soc=12.0, capacity_kwh=2.0)], step_interval=1.0, mode=Mode.FAST_DISCHARGE)
    _live(sim)
    tr = sim.run(900)
    assert min(tr.soc) >= 10.0
    assert sim.engine.mode is Mode.ZERO_METER


def test_device_soclimit_full_bit_stops_charging() -> None:
    eng = ZephyrEngine(Settings())
    s = SimSet(soc=80.0)
    rep = replace(s.report(0), soc_limit_charge_stopped=True)
    eng.set_live(True, 0.0, [])
    for t in range(0, 40):
        eng.p1_reported(float(t), -800.0)
        r = eng.step(float(t), [SetView("0", 1, rep, True)])
        assert r.setpoint <= 0
    assert r.reason.code is ReasonCode.FULL


def test_full_battery_fast_charge_finishes_at_once() -> None:
    eng = ZephyrEngine(Settings(), Mode.FAST_CHARGE)
    rep = SimSet(soc=96.0).report(0)
    r = eng.step(0.0, [SetView("0", 1, rep, True)])
    assert r.mode_finished and r.setpoint == 0
