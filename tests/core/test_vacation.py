"""B42: vacation state, periods and the base load."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from zephyr_core.vacation import VacationState, base_load

T0 = datetime(2026, 12, 20, 8, tzinfo=UTC)
H = timedelta(hours=1)


def test_manual_with_end_stops_by_itself_and_keeps_the_period() -> None:
    v = VacationState()
    v.set_manual(True, T0, until=T0 + 48 * H)
    assert v.active(T0 + H)
    assert v.active_at(T0 + 47 * H, T0 + H) and not v.active_at(T0 + 49 * H, T0 + H)  # return home is planned
    assert v.was(T0 + 2 * H, T0 + 3 * H)
    assert not v.check(T0 + 47 * H)
    assert v.check(T0 + 48 * H + timedelta(minutes=1))
    assert not v.active(T0 + 49 * H) and not v.manual
    assert v.periods == [(T0, T0 + 48 * H)]
    assert v.was(T0 + 10 * H, T0 + 60 * H) and not v.was(T0 + 50 * H, T0 + 60 * H)


def test_manual_without_end_and_switching_off() -> None:
    v = VacationState()
    v.set_manual(True, T0)
    assert v.active_at(T0 + 100 * H, T0 + H)  # no end known: the whole horizon
    v.set_manual(False, T0 + 5 * H)
    assert v.periods == [(T0, T0 + 5 * H)] and v.started is None


def test_auto_away_and_manual_together() -> None:
    v = VacationState()
    v.set_auto(True, T0)
    v.set_manual(True, T0 + H, until=T0 + 10 * H)
    assert v.active_at(T0 + 20 * H, T0 + 2 * H)  # still away automatically: no known end
    v.set_auto(False, T0 + 5 * H)
    assert v.active(T0 + 6 * H)  # manual keeps it on
    v.check(T0 + 10 * H)
    assert not v.active(T0 + 11 * H)
    assert v.periods == [(T0, T0 + 10 * H)]


def test_storage_round_trip_and_old_periods_dropped() -> None:
    v = VacationState()
    v.set_manual(True, T0 - timedelta(days=500))
    v.set_manual(False, T0 - timedelta(days=499))
    v.set_manual(True, T0, until=T0 + H)
    v.check(T0 + 2 * H)
    assert v.periods == [(T0, T0 + H)]
    again = VacationState.from_dict(v.as_dict())
    assert again == v
    assert VacationState.from_dict(None) == VacationState()


def test_base_load() -> None:
    assert base_load([0.43, 0.22, 0.25, 0.0], 0.35) == 0.22
    assert base_load([], 0.35) == 0.35
