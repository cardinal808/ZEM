"""Own energy counters per set (SPEC-tellers T1)."""

from __future__ import annotations

import dataclasses

import pytest

from conftest import load_fixture
from zephyr_core.energy_counters import HOLD, EnergyCounters, pack_energy
from zephyr_core.models import SetReport
from zephyr_core.zensdk import parse_report


def _report(name: str = "charge_2400", **kw: object) -> SetReport:
    return dataclasses.replace(parse_report(load_fixture(name)), **kw)  # type: ignore[arg-type]


def _charging(watts: float = 2400.0) -> SetReport:
    return _report(charge_power_ac=watts, deliver_power_ac=0.0, solar_power=0.0, solar_power_inputs=())


def _run(c: EnergyCounters, serial: str, report: SetReport, start: float, end: float) -> None:
    """Good reports every 5 s from ``start`` to ``end`` (both included)."""
    t = start
    while t <= end:
        c.observe(serial, report, t, good=True)
        t += 5.0


def test_constant_power_for_a_quarter() -> None:
    c = EnergyCounters()
    for t in range(0, 901, 5):
        c.observe("A", _charging(), float(t), good=True)
    assert c.sets["A"].kwh["charged"] == pytest.approx(0.600)
    assert c.totals["charged"] == pytest.approx(0.600)
    assert c.sets["A"].kwh["discharged"] == 0.0


def test_failed_reads_within_hold_keep_counting() -> None:
    c = EnergyCounters()
    c.observe("A", _charging(), 0.0, good=True)
    for t in (5.0, 10.0, 15.0, 20.0, 25.0, 30.0):
        c.observe("A", None, t, good=False)
    _run(c, "A", _charging(), 35.0, 900.0)
    assert c.sets["A"].kwh["charged"] == pytest.approx(0.600)
    assert c.sets["A"].gap is None and c.sets["A"].gaps == []


def test_beyond_hold_a_gap_starts_and_nothing_is_counted() -> None:
    c = EnergyCounters()
    c.observe("A", _charging(), 0.0, good=True)
    c.observe("A", None, 100.0, good=False, wall="2026-11-26T01:00:00+00:00")
    assert c.sets["A"].gap is not None
    c.observe("A", None, 200.0, good=False)
    c.observe("A", _charging(), 300.0, good=True, wall="2026-11-26T01:05:00+00:00")
    assert c.sets["A"].kwh["charged"] == pytest.approx(2.4 * HOLD / 3600)
    gap = c.sets["A"].gaps[-1]
    assert gap["seconds"] == 300 - HOLD and gap["powers"]["charged"] == 2400.0
    assert gap["start"] == "2026-11-26T01:00:00+00:00" and gap["end"] == "2026-11-26T01:05:00+00:00"


def test_long_pause_between_good_reports_is_a_gap() -> None:
    c = EnergyCounters()
    c.observe("A", _charging(), 0.0, good=True)
    c.observe("A", _charging(), 600.0, good=True)  # HA hung for 10 minutes
    assert c.sets["A"].kwh["charged"] == pytest.approx(2.4 * HOLD / 3600)
    assert len(c.sets["A"].gaps) == 1


def test_set_pv_counts_as_solar_not_battery() -> None:
    c = EnergyCounters()
    pv = _report("standby", solar_power=500.0, solar_power_inputs=(250.0, 250.0), charge_power_ac=0.0, deliver_power_ac=0.0)
    _run(c, "A", pv, 0.0, 3600.0)
    counter = c.sets["A"]
    assert counter.kwh["solar"] == pytest.approx(0.5) and counter.kwh["charged"] == 0.0 and counter.kwh["discharged"] == 0.0
    assert counter.has_solar


def test_counters_never_drop_and_totals_add_increases() -> None:
    c = EnergyCounters()
    _run(c, "A", _charging(), 0.0, 900.0)
    _run(c, "B", _charging(1200.0), 0.0, 1800.0)
    assert c.totals["charged"] == pytest.approx(0.6 + 0.6)
    # Set B is replaced by a new serial: the total keeps its value and goes on.
    del c.sets["B"]
    _run(c, "C", _charging(1200.0), 1800.0, 3600.0)
    assert c.totals["charged"] == pytest.approx(1.2 + 0.6)


def test_restore_keeps_states_and_holds_nothing() -> None:
    c = EnergyCounters()
    _run(c, "A", _charging(), 0.0, 1800.0)
    stored = c.as_dict()
    again = EnergyCounters()
    again.restore(stored)
    assert again.sets["A"].kwh["charged"] == pytest.approx(1.2) and again.totals["charged"] == pytest.approx(1.2)
    again.observe("A", _charging(), 50_000.0, good=True)  # first report after the restart: no jump
    assert again.sets["A"].kwh["charged"] == pytest.approx(1.2)


def test_pack_energy() -> None:
    report = _report("standby")
    capacities = {p.serial: 2.88 for p in report.packs}
    expected = sum(2.88 * p.soc / 100 for p in report.packs)
    assert pack_energy(report, capacities) == pytest.approx(expected)
    assert pack_energy(report, {}) is None
