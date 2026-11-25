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
    assert p.expected(WEEKEND, 18) == pytest.approx(sum(SHAPE) / 24)  # weekend still unknown


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
