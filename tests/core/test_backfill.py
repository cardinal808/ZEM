"""Savings before the cost log, from hourly statistics (core/backfill.py)."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from zephyr_core.backfill import SOURCE_HOURLY, HourInput, backfill_days, series_to_hours
from zephyr_core.costs import Summary, Tariffs

TZ = ZoneInfo("Europe/Amsterdam")


def _day(evening_discharge: float = 0.5, night_charge: float = 0.0) -> list[HourInput]:
    start = datetime(2026, 11, 10, tzinfo=TZ)
    hours = []
    for h in range(24):
        t = start + timedelta(hours=h)
        market = 0.10 if h < 6 else 0.30 if 17 <= h < 21 else 0.20
        dis = evening_discharge if 17 <= h < 21 else 0.0
        chg = night_charge if 2 <= h < 4 else 0.0
        hours.append(
            HourInput(t, import_kwh=0.6 - dis + chg, export_kwh=0.0, charge_kwh=chg, discharge_kwh=dis, solar_kwh=0.0, market=market)
        )
    return hours


def test_a_day_is_worked_out_like_the_cost_log() -> None:
    result = backfill_days(_day(), lambda d: Tariffs(), TZ)
    assert result.hours == 24 and result.skipped == 0
    day = result.days["2026-11-10"]
    assert day["source"] == SOURCE_HOURLY
    assert day["quarters"] == 96 and not day.get("incomplete")
    summary = Summary(days=1, totals=day)
    # 4 evening hours × 0,5 kWh not bought at the evening price.
    buy = Tariffs().buy(0.30)
    assert summary.savings_battery == pytest.approx(4 * 0.5 * buy, abs=0.01)
    assert summary.as_dict()["mean_buy_price"] is not None


def test_charging_at_night_and_missing_hours() -> None:
    hours = _day(night_charge=1.0)
    hours[10] = HourInput(hours[10].start, None, 0.0, 0.0, 0.0, 0.0, 0.2)
    result = backfill_days(hours, lambda d: Tariffs(), TZ)
    day = result.days["2026-11-10"]
    assert result.skipped == 1 and day["hours"] == 23
    assert day["incomplete"] == 4 and day["quarters"] == 92
    t = Tariffs()
    expected = 4 * 0.5 * t.buy(0.30) - 2 * 1.0 * t.buy(0.10)
    assert Summary(days=1, totals=day).savings_battery == pytest.approx(expected, abs=0.01)


def test_series_to_hours_needs_every_counter() -> None:
    t0 = datetime(2026, 11, 10, 12, tzinfo=TZ)
    t1 = t0 + timedelta(hours=1)
    series = {
        "imp1": {t0: 0.2, t1: 0.1},
        "imp2": {t0: 0.1},
        "exp": {t0: 0.0, t1: 0.3},
        "sun": {t0: 0.5, t1: 0.6},
        "price": {t0: 0.21, t1: 0.22},
    }
    hours = series_to_hours([t0, t1], series, ["imp1", "imp2"], ["exp"], lambda t: 0.0, lambda t: 0.1, "sun", "price")
    assert hours[0].import_kwh == pytest.approx(0.3) and hours[0].market == 0.21
    assert hours[1].import_kwh is None  # imp2 has no value for t1
    assert hours[1].solar_kwh == 0.6 and hours[1].discharge_kwh == 0.1
    assert backfill_days(hours, lambda d: Tariffs(), TZ).skipped == 1
    assert date(2026, 11, 10).isoformat() in backfill_days(hours, lambda d: Tariffs(), TZ).days
