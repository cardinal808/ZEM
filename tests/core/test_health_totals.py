"""Online/offline hysteresis and totals over several sets."""

from __future__ import annotations

import dataclasses

import pytest

from conftest import load_fixture
from zem_core.health import SetHealth
from zem_core.totals import SetSnapshot, compute_totals
from zem_core.zensdk import parse_report


def test_first_success_brings_set_online() -> None:
    h = SetHealth()
    h.record_success(0)
    assert h.online


def test_offline_after_three_failures() -> None:
    h = SetHealth()
    h.record_success(0)
    h.record_failure(5, "timeout")
    h.record_failure(10, "timeout")
    assert h.online
    h.record_failure(15, "timeout")
    assert not h.online
    assert h.offline_since == 15
    assert h.episodes_offline == 1


def test_online_again_after_two_successes() -> None:
    h = SetHealth()
    h.record_success(0)
    for t in (5, 10, 15):
        h.record_failure(t, "x")
    h.record_success(20)
    assert not h.online
    h.record_success(25)
    assert h.online


def test_stale_set_goes_offline() -> None:
    h = SetHealth()
    h.record_success(0)
    h.check_stale(19)
    assert h.online
    h.check_stale(21)
    assert not h.online


def _snap(name: str, capacity: float, soc: float | None = None, **kw: object) -> SetSnapshot:
    report = parse_report(load_fixture(name))
    if soc is not None:
        report = dataclasses.replace(report, soc=soc)
    return SetSnapshot(report=report, capacity_kwh=capacity, **kw)  # type: ignore[arg-type]


def test_totals_weighted_by_capacity() -> None:
    t = compute_totals([_snap("deliver_760", 11.04, 80, online=True), _snap("charge_2400", 2.88, 20, online=True)], now=0)
    assert t.soc == pytest.approx(round(100 * (11.04 * 0.8 + 2.88 * 0.2) / 13.92, 1))
    assert t.capacity_kwh == pytest.approx(13.92)
    assert t.power == pytest.approx(-760 + 2386)
    assert t.charge_power == 2386 and t.discharge_power == 760
    assert t.sets_online == 2


def test_offline_set_keeps_counting_for_five_minutes() -> None:
    online = _snap("standby", 11.04, 50, online=True)
    offline = _snap("standby", 2.88, 90, online=False, offline_since=100.0)
    assert compute_totals([online, offline], now=399).capacity_kwh == pytest.approx(13.92)
    later = compute_totals([online, offline], now=401)
    assert later.capacity_kwh == pytest.approx(11.04)
    assert later.sets_online == 1


def test_disabled_set_drops_out_immediately() -> None:
    t = compute_totals([_snap("standby", 11.04, online=True), _snap("standby", 2.88, online=True, enabled=False)], now=0)
    assert t.capacity_kwh == pytest.approx(11.04)


def test_totals_unknown_without_sets() -> None:
    t = compute_totals([SetSnapshot(report=None, capacity_kwh=0, online=False)], now=0)
    assert t.soc is None and t.capacity_kwh is None
    assert t.sets_online == 0
