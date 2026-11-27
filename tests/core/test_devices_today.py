"""Consumers in view: kWh today from a plug's power readings."""

from __future__ import annotations

from datetime import date

import pytest

from zephyr_core.devices import MAX_HOLD_SECONDS, DayEnergy

D1, D2 = date(2026, 11, 27), date(2026, 11, 28)
M1 = 1_000_000.0  # epoch of 27-11 00:00 in this test
M2 = M1 + 86400


def test_a_reading_counts_until_the_next_one() -> None:
    e = DayEnergy()
    e.observe("w", 2000, M1 + 3600, D1, M1)
    assert e.today("w", M1 + 5400, D1, M1) == pytest.approx(1.0)  # still running: up to now
    e.observe("w", 0, M1 + 5400, D1, M1)
    assert e.today("w", M1 + 9000, D1, M1) == pytest.approx(1.0)
    assert e.power("w", M1 + 9000) == 0


def test_midnight_splits_the_energy() -> None:
    e = DayEnergy()
    e.observe("d", 1000, M2 - 1800, D1, M1)  # 23:30, 1 kW
    assert e.today("d", M2 + 1800, D2, M2) == pytest.approx(0.5)  # only the half hour after midnight
    e.observe("d", 0, M2 + 1800, D2, M2)
    assert e.today("d", M2 + 3600, D2, M2) == pytest.approx(0.5)


def test_unavailable_and_stale_readings_stop_counting() -> None:
    e = DayEnergy()
    e.observe("x", 500, M1, D1, M1)
    e.observe("x", None, M1 + 3600, D1, M1)
    assert e.today("x", M1 + 7200, D1, M1) == pytest.approx(0.5)
    assert e.power("x", M1 + 7200) is None
    e.observe("y", 100, M1, D1, M1)
    assert e.power("y", M1 + MAX_HOLD_SECONDS + 1) is None


def test_restored_on_the_same_day_only() -> None:
    e = DayEnergy()
    e.observe("w", 1000, M1, D1, M1)
    e.observe("w", 0, M1 + 3600, D1, M1)
    again = DayEnergy()
    again.restore(e.as_dict(), D1)
    assert again.today("w", M1 + 7200, D1, M1) == pytest.approx(1.0)
    other = DayEnergy()
    other.restore(e.as_dict(), D2)
    assert other.today("w", M2, D2, M2) == 0
