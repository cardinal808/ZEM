"""P1 profile from the meter interval (OPDRACHT-p1-profiel)."""

from __future__ import annotations

from conftest import load_fixture
from zephyr_core.engine import ReasonCode, SetView, ZephyrEngine
from zephyr_core.p1_profile import FAST, MEDIUM, SLOW, TOO_SLOW, P1Profile, classify
from zephyr_core.zensdk import parse_report


def _view() -> SetView:
    return SetView("a", 1, parse_report(load_fixture("deliver_760")), True)


def _feed(e: ZephyrEngine, start: float, end: float, every: float, base: float = 300.0, gap_every: int = 0) -> float:
    """Meter samples every ``every`` s with a changing value; every ``gap_every``-th sample missing."""
    t, n = start, 0
    while t < end:
        n += 1
        if not (gap_every and n % gap_every == 0):
            e.p1_reported(t, base + (n % 7) * 10)
            e.step(t, [_view()])
        t += every
    return t


def test_classify() -> None:
    assert [classify(x) for x in (1.0, 2.0, 5.0, 7.0, 10.0, 25.0, 30.0)] == [FAST, FAST, MEDIUM, MEDIUM, SLOW, SLOW, TOO_SLOW]


def test_dsmr4_with_gaps_is_slow_and_never_stale() -> None:
    e = ZephyrEngine()
    _feed(e, 0, 1800, 10.0, gap_every=9)  # every 9th sample missing: gaps of 20 s
    view = e.p1_profile_view(1800)
    assert view["profile"] == SLOW and view["interval_s"] == 10.0
    assert view["stale_after_s"] == 30.0 and view["stale_24h"] == 0
    assert view["step_filter"] is False and view["deviation_time_s"] == 20.0


def test_constant_load_on_a_slow_meter_stays_slow() -> None:
    e = ZephyrEngine()
    t = _feed(e, 0, 600, 10.0)
    for _ in range(60):  # the same value, re-reported every 10 s (last_reported runs)
        e.p1_reported(t, 500.0)
        assert e.step(t, [_view()]).reason.code not in (ReasonCode.P1_STALE, ReasonCode.P1_TOO_SLOW)
        t += 10
    assert e.p1_profile.profile == SLOW


def test_homewizard_dsmr5_is_medium_and_one_second_is_fast() -> None:
    medium, fast = ZephyrEngine(), ZephyrEngine()
    _feed(medium, 0, 600, 5.0)
    _feed(fast, 0, 120, 1.0)
    assert medium.p1_profile.profile == MEDIUM and medium.p1_profile.step_filter
    assert fast.p1_profile.profile == FAST and fast.p1_profile.step_filter


def test_profile_changes_only_after_ten_minutes() -> None:
    p = P1Profile()
    assert p.update(0, 10.0, 10) == SLOW
    assert p.update(100, 1.0, 30) == SLOW  # a short run of fast samples
    assert p.update(400, 10.0, 30) == SLOW  # back: the candidate is forgotten
    assert p.update(500, 1.0, 30) == SLOW
    assert p.update(1099, 1.0, 30) == SLOW
    assert p.update(1100, 1.0, 30) == FAST
    # Within the margin of a bound: no change (slow → medium only below 5.6 s).
    q = P1Profile()
    q.update(0, 10.0, 10)
    q.update(10, 6.0, 30)
    assert q.update(700, 6.0, 30) == SLOW


def test_fewer_than_ten_intervals_is_medium() -> None:
    p = P1Profile()
    assert p.update(0, 10.0, 5) == MEDIUM and not p.decided


def test_slow_profile_passes_a_real_step_at_once() -> None:
    e = ZephyrEngine()
    t = _feed(e, 0, 600, 10.0)
    e.p1_reported(t, 1500.0)  # +1 200 W in one sample: no step hold on a slow meter
    assert e.grid_filter.holding is False
    assert e.grid_filter.value(t) == 1500.0


def test_fast_meter_still_holds_a_short_peak() -> None:
    e = ZephyrEngine()
    t = _feed(e, 0, 120, 1.0)
    e.p1_reported(t, 2500.0)
    assert e.grid_filter.holding is True
