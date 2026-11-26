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


def test_beyond_hold_a_gap_starts() -> None:
    c = EnergyCounters()
    c.observe("A", _charging(), 0.0, good=True)
    c.observe("A", None, 100.0, good=False)
    assert c.sets["A"].gap is not None
    assert c.sets["A"].kwh["charged"] == pytest.approx(2.4 * HOLD / 3600)  # held, then nothing
    c.observe("A", None, 200.0, good=False)
    gap = c.observe("A", _charging(), 300.0, good=True)
    assert gap is not None and gap["seconds"] == 300 - HOLD
    assert gap["start"] == "1970-01-01T00:01:00+00:00" and gap["end"] == "1970-01-01T00:05:00+00:00"


def test_long_pause_between_good_reports_is_a_gap() -> None:
    c = EnergyCounters()
    c.observe("A", _charging(), 0.0, good=True)
    c.observe("A", _charging(), 600.0, good=True)  # HA hung for 10 minutes: interpolated
    assert c.sets["A"].kwh["charged"] == pytest.approx(2.4 * 600 / 3600)
    assert len(c.sets["A"].gaps) == 1 and c.sets["A"].gaps[0]["method"] == "interpolate"


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
    again.observe("A", _charging(), 1810.0, good=True)  # a quick restart: just counts on
    assert again.sets["A"].kwh["charged"] == pytest.approx(1.2 + 2.4 * 10 / 3600)
    assert again.sets["A"].gaps == []


def test_pack_energy() -> None:
    report = _report("standby")
    capacities = {p.serial: 2.88 for p in report.packs}
    expected = sum(2.88 * p.soc / 100 for p in report.packs)
    assert pack_energy(report, capacities) == pytest.approx(expected)
    assert pack_energy(report, {}) is None


# --- T2: filling gaps ------------------------------------------------------------------

CAPACITY = {"JO2A": 2.40, "GO2A": 2.88}


def _caps(report: SetReport) -> dict[str, float]:
    return {p.serial: CAPACITY[p.serial[:4]] for p in report.packs}


def _with_soc(report: SetReport, soc: float) -> SetReport:
    return dataclasses.replace(report, packs=tuple(dataclasses.replace(p, soc=soc) for p in report.packs))


def _energy(report: SetReport) -> float:
    return sum(_caps(report)[p.serial] * p.soc / 100 for p in report.packs)


def test_short_gap_at_the_same_power_is_interpolated() -> None:
    c = EnergyCounters()
    before = _with_soc(_charging(), 50.0)
    _run_caps(c, before, 0.0, 60.0)
    c.observe("A", None, 70.0, good=False)
    # 5 min later: 2.4 kW all the time → ≈ 0.2 kWh in, ≈ 0.18 kWh in the packs (2 % of 11.04 kWh ≈ 0.22).
    after = _with_soc(_charging(), 52.0)
    gap = c.observe("A", after, 360.0, good=True, capacities=_caps(after), daylight=lambda a, b: False)
    assert gap is not None and gap["method"] == "interpolate"
    assert c.sets["A"].kwh["charged"] == pytest.approx(2.4 * 360 / 3600)
    assert c.sets["A"].estimated["charged"] == pytest.approx(2.4 * (360 - 120) / 3600)
    assert c.sets["A"].kwh["solar"] == 0.0


def _run_caps(c: EnergyCounters, report: SetReport, start: float, end: float) -> None:
    t = start
    while t <= end:
        c.observe("A", report, t, good=True, capacities=_caps(report))
        t += 5.0


def test_different_power_fills_from_the_soc() -> None:
    c = EnergyCounters()
    before = _with_soc(_charging(2400.0), 50.0)
    _run_caps(c, before, 0.0, 0.0)
    after = _with_soc(_charging(600.0), 55.0)  # +5 % of 11.04 kWh
    gap = c.observe("A", after, 300.0, good=True, capacities=_caps(after))
    assert gap is not None and gap["method"] == "soc"
    delta = _energy(after) - _energy(before)
    assert delta == pytest.approx(0.552)
    # In total the packs' gain divided by the efficiency (the held minute included).
    assert c.sets["A"].kwh["charged"] == pytest.approx(delta / 0.92)


def test_soc_drop_fills_delivered() -> None:
    c = EnergyCounters()
    deliver = _report("deliver_760")
    before = _with_soc(deliver, 60.0)
    c.observe("A", before, 0.0, good=True, capacities=_caps(before))
    after = _with_soc(dataclasses.replace(deliver, deliver_power_ac=200.0), 56.0)
    gap = c.observe("A", after, 3600.0, good=True, capacities=_caps(after))
    assert gap is not None and gap["method"] == "soc"
    delta = _energy(before) - _energy(after)
    assert c.sets["A"].kwh["discharged"] == pytest.approx(delta * 0.88)
    assert c.sets["A"].kwh["charged"] == 0.0


def test_interpolation_that_disagrees_with_the_packs_falls_back_to_the_soc() -> None:
    c = EnergyCounters()
    before = _with_soc(_charging(), 50.0)
    c.observe("A", before, 0.0, good=True, capacities=_caps(before))
    after = _with_soc(_charging(), 50.0)  # power said 2.4 kW, but the packs did not fill
    gap = c.observe("A", after, 600.0, good=True, capacities=_caps(after))
    assert gap is not None and gap["method"] == "soc" and gap["kwh"] == {}


def test_long_gap_is_never_interpolated() -> None:
    c = EnergyCounters()
    before = _with_soc(_charging(), 20.0)
    c.observe("A", before, 0.0, good=True, capacities=_caps(before))
    after = _with_soc(_charging(), 40.0)
    gap = c.observe("A", after, 3600.0, good=True, capacities=_caps(after))
    assert gap is not None and gap["method"] == "soc"


def test_set_pv_in_a_gap_by_day_and_by_night() -> None:
    pv = _with_soc(_report("standby", solar_power=400.0, solar_power_inputs=(200.0, 200.0), charge_power_ac=0.0), 50.0)
    for light, expected in ((True, 0.4 * (3600 - HOLD) / 3600), (False, 0.0)):
        c = EnergyCounters()
        c.observe("A", pv, 0.0, good=True, capacities=_caps(pv))
        after = _with_soc(pv, 50.0)
        c.observe("A", after, 3600.0, good=True, capacities=_caps(after), daylight=lambda a, b, light=light: light)
        assert c.sets["A"].kwh["solar"] == pytest.approx(0.4 * HOLD / 3600 + expected)


def test_restart_fills_the_downtime() -> None:
    c = EnergyCounters()
    before = _with_soc(_charging(), 30.0)
    _run_caps(c, before, 0.0, 600.0)
    again = EnergyCounters()
    again.restore(c.as_dict())
    after = _with_soc(_charging(600.0), 40.0)
    gap = again.observe("A", after, 600.0 + 3600.0, good=True, capacities=_caps(after))
    assert gap is not None and gap["restart"] and gap["method"] == "soc"
    assert again.sets["A"].estimated["charged"] == pytest.approx((_energy(after) - _energy(before)) / 0.92)  # no hold after a restart
    assert again.totals["charged"] == pytest.approx(again.sets["A"].kwh["charged"])


def test_unknown_pack_capacity_leaves_a_long_gap_empty() -> None:
    c = EnergyCounters()
    c.observe("A", _charging(), 0.0, good=True)
    gap = c.observe("A", _charging(600.0), 3600.0, good=True)
    assert gap is not None and gap["method"] == "none" and gap["kwh"] == {}
