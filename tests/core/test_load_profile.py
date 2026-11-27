"""Learned consumption profile (SPEC-planner §2.3)."""

from __future__ import annotations

import pytest

from zephyr_core.load_profile import WEEKEND, WORKDAY, LoadProfile


def _days(profile: LoadProfile, kind: str, days: int, shape: list[float]) -> None:
    for _ in range(days):
        for hour, kwh in enumerate(shape):
            profile.learn(kind, hour, kwh)


SHAPE = [0.2] * 7 + [0.8] * 2 + [0.4] * 8 + [1.0] * 5 + [0.3] * 2


def test_daily_mean_until_enough_measurements() -> None:
    p = LoadProfile()
    _days(p, WORKDAY, 2, SHAPE)
    assert p.expected(WORKDAY, 18) == pytest.approx(sum(SHAPE) / 24)
    _days(p, WORKDAY, 1, SHAPE)
    assert p.expected(WORKDAY, 18) == pytest.approx(1.0)
    assert p.expected(WEEKEND, 18) == pytest.approx(1.0)  # weekend still unknown: the workday's hour


def test_profile_follows_a_change_within_weeks() -> None:
    p = LoadProfile()
    _days(p, WORKDAY, 20, SHAPE)
    _days(p, WORKDAY, 40, [v * 1.5 for v in SHAPE])  # ~8 working weeks
    assert p.expected(WORKDAY, 18) == pytest.approx(1.5, rel=0.05)


def test_steering_corrects_and_fades() -> None:
    p = LoadProfile()
    _days(p, WORKDAY, 5, SHAPE)
    for hour in (10, 11, 12):
        p.learn(WORKDAY, hour, 0.8)  # twice the expected 0.4
    assert p.steering() == pytest.approx(1.6)  # bounded
    near, far = p.forecast(WORKDAY, 13, 0.5), p.forecast(WORKDAY, 20, 8)
    assert near > 0.6
    assert far == pytest.approx(p.expected(WORKDAY, 20), rel=0.05)


def test_storage_round_trip_and_reset() -> None:
    p = LoadProfile()
    _days(p, WEEKEND, 3, SHAPE)
    q = LoadProfile.from_dict(p.as_dict())
    assert q.expected(WEEKEND, 18) == p.expected(WEEKEND, 18)
    q.reset()
    assert q.expected(WEEKEND, 18) == 0.0 and q.mean_count == 0


def test_first_fill_from_meter_history() -> None:
    """House = import − export + solar − battery per hour; three workdays make an hour count (§2.3)."""
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    from zephyr_core.load_profile import WEEKEND, WORKDAY, HourEnergy, profile_from_history

    tz = ZoneInfo("Europe/Amsterdam")
    monday = datetime(2026, 11, 23, tzinfo=tz)
    hours = []
    for day in range(3):
        for hour in range(24):
            evening = 1.2 if 17 <= hour < 22 else 0.25
            # Battery delivered 1.0 kWh in the evening: import is lower, the house is not.
            battery = -1.0 if 17 <= hour < 22 else 0.0
            hours.append(HourEnergy(monday + timedelta(days=day, hours=hour), evening + battery, 0.0, 0.0, battery))
    noon = HourEnergy(monday + timedelta(hours=12), 0.1, 0.5, 0.9, 0.2)
    assert noon.house_kwh == pytest.approx(0.3)
    profile = profile_from_history(hours)
    assert profile.mean_count == 72
    assert profile.expected(WORKDAY, 18) == pytest.approx(1.2)
    assert profile.expected(WORKDAY, 3) == pytest.approx(0.25)
    assert profile.expected(WEEKEND, 18) == pytest.approx(1.2)  # no weekends yet: the workday's shape
    assert profile.steering() == 1.0


def test_workday_overrides_the_weekday() -> None:
    from datetime import date, datetime

    from zephyr_core.load_profile import WEEKEND, WORKDAY, day_type_of

    christmas = datetime(2026, 12, 25, 12)  # a Friday
    assert day_type_of(christmas) == WORKDAY
    assert day_type_of(christmas, {date(2026, 12, 25): False}) == WEEKEND
    assert day_type_of(datetime(2026, 12, 26, 12), {date(2026, 12, 25): False}) == WEEKEND  # Saturday by the weekday


def test_without_either_day_type_the_mean() -> None:
    p = LoadProfile()
    _days(p, WORKDAY, 1, SHAPE)
    assert p.expected(WEEKEND, 18) == pytest.approx(p.mean)
