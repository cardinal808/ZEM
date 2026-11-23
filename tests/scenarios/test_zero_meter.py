"""Scenarios B1–B12 of SPEC-basis §13 in the closed-loop simulator."""

from __future__ import annotations

from itertools import pairwise

from sim.device import SimSet
from sim.runner import Simulation, constant, energy_wh, share_within, steps, time_to_settle, writes
from zephyr_core.engine import Mode, ReasonCode
from zephyr_core.settings import Settings

TARGET = 15.0  # W on the grid while delivering


def _setpoints_after(trace, start):  # type: ignore[no-untyped-def]
    return [r.setpoint for t, r in trace.results if t >= start]


def test_b1_constant_load() -> None:
    sim = Simulation(load=constant(400))
    tr = sim.run(240)
    settle = time_to_settle(tr, 0, TARGET, 30)
    assert settle is not None and settle <= 12  # from standby: start-up 2.5 s included
    assert share_within(tr, TARGET, 30, start=20) > 0.99
    late_writes = [w for s in sim.sets for t, w in s.writes if t > 60]
    assert len(late_writes) <= 4  # only the 60 s refresh


def test_b2_kettle() -> None:
    sim = Simulation(load=steps((0, 400), (60, 2400), (240, 400)))
    tr = sim.run(300)
    up = time_to_settle(tr, 60, TARGET, 50)
    assert up is not None and up <= 8
    export_s = sum(0.1 for t, g in zip(tr.t, tr.grid, strict=True) if 240 <= t < 270 and g < -100)
    assert export_s < 3


def test_b3_clouds_do_not_switch_direction() -> None:
    # Solar jumps between 300 and 1500 W every 5 s, house uses 500 W.
    sim = Simulation(load=constant(500), solar=lambda t: 1500.0 if int(t // 5) % 2 else 300.0)
    tr = sim.run(300)
    assert all(sp <= 0 for sp in _setpoints_after(tr, 0))


def test_b4_charges_from_surplus_until_full() -> None:
    s = SimSet(soc=94.0)
    sim = Simulation(load=constant(500), solar=constant(1300), sets=[s])
    tr = sim.run(1800)
    assert max(tr.soc) <= 95.6
    assert max(_setpoints_after(tr, 0)) > 0  # it did charge
    assert tr.setpoint[-1] == 0
    # Never charged from the grid: import stays small during charging.
    assert energy_wh(tr, +1) < 2


def test_b5_stops_at_minimum_without_flapping() -> None:
    s = SimSet(soc=10.9)
    sim = Simulation(load=constant(800), sets=[s])
    tr = sim.run(1200)
    assert min(tr.soc) >= 10.3
    sps = _setpoints_after(tr, 0)
    starts = sum(1 for a, b in pairwise(sps) if a == 0 and b < 0)
    assert starts <= 1
    assert tr.results[-1][1].reason.code is ReasonCode.EMPTY


def test_b6_p1_outage() -> None:
    # Balanced grid: a short silence holds the setpoint (sensors that only report changes),
    # a longer one gives 0 W.
    sim = Simulation(load=constant(800), p1_outages=[(100, 115), (200, 240)])
    tr = sim.run(320)
    at = {round(t): r for t, r in tr.results}
    assert at[99].setpoint < 0
    assert at[111].setpoint == at[99].setpoint
    assert at[235].setpoint == 0
    assert at[235].reason.code is ReasonCode.P1_STALE
    assert at[280].setpoint < 0
    assert share_within(tr, TARGET, 50, start=280) > 0.95


def test_b7_slow_meter() -> None:
    sim = Simulation(load=constant(600), p1_interval=10.0)
    tr = sim.run(600)
    assert share_within(tr, TARGET, 50, start=120) > 0.95
    sps = _setpoints_after(tr, 120)
    assert len(set(sps)) <= 2  # no oscillation


def test_b7b_dsmr4_meter_with_jitter() -> None:
    # DSMR 4: a new value about every 10 s (here 8.5-11.5 s), ZEPHYR steps every second as in Home Assistant.
    load = steps((0, 600), (120, 900), (240, 450), (360, 1500), (480, 700))
    sim = Simulation(load=load, p1_interval=10.0, p1_jitter=1.5, step_interval=1.0)
    tr = sim.run(720)
    assert all(r.reason.code not in (ReasonCode.P1_TOO_SLOW, ReasonCode.P1_STALE) for _, r in tr.results)
    assert share_within(tr, TARGET, 50, start=30) > 0.9
    assert sum(len(r.commands) for _, r in tr.results) < 30


def test_b8_fast_charge_returns_to_zero_meter() -> None:
    s = SimSet(soc=93.0)
    sim = Simulation(load=constant(300), sets=[s], mode=Mode.FAST_CHARGE)
    tr = sim.run(1200)
    assert any(r.mode_finished for _, r in tr.results)
    assert sim.engine.mode is Mode.ZERO_METER
    assert max(tr.soc) <= 95.6


def test_b9_fault_stops_control() -> None:
    s = SimSet()
    sim = Simulation(load=constant(800), sets=[s])
    sim.run(60)
    s.fault = True
    tr = sim.run(60, start=60)
    assert all(sp == 0 for sp in _setpoints_after(tr, 70))
    assert tr.results[-1][1].reason.code is ReasonCode.NO_SET


def test_b10_restart_while_delivering() -> None:
    s = SimSet()
    sim = Simulation(load=constant(800), sets=[s])
    sim.run(120)
    assert s.power < -500
    sim.engine = type(sim.engine)(Settings())  # Home Assistant restarted
    tr = sim.run(120, start=120)
    first = tr.results[0][1]
    assert first.setpoint == 0
    settle = time_to_settle(tr, 120, TARGET, 50)
    assert settle is not None and settle <= 15


def test_b11_discharge_block() -> None:
    sim = Simulation(load=constant(800), discharge_blocked=lambda t: t >= 60)
    tr = sim.run(120)
    at = {round(t): r for t, r in tr.results}
    assert at[59].setpoint < 0
    assert at[72].setpoint == 0
    assert at[72].reason.code is ReasonCode.BLOCKED


def test_b11_block_still_allows_solar_charging() -> None:
    sim = Simulation(load=constant(400), solar=constant(1400), discharge_blocked=lambda t: True)
    tr = sim.run(120)
    assert max(_setpoints_after(tr, 30)) > 0


def test_b12_big_load_drops() -> None:
    sim = Simulation(load=steps((0, 2400), (120, 200)))
    tr = sim.run(180)
    export_s = sum(0.1 for t, g in zip(tr.t, tr.grid, strict=True) if 120 <= t < 150 and g < -100)
    assert export_s < 3


def test_write_count_stays_low() -> None:
    sim = Simulation(load=steps((0, 400), (60, 900), (120, 1500), (180, 600), (240, 300)))
    sim.run(600)
    assert writes(sim) <= 40
