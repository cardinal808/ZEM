"""Solar savings split (OPDRACHT-besparing-zon): direct + export = Z0 − Z1, bonus by day only."""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from zephyr_core.costs import Pools, QuarterInput, Summary, Tariffs, add_to_day, evaluate

TARIFFS = Tariffs(markup_import=0.0165, markup_export=0.0165, solar_bonus=10.0)


def _q(daylight: bool, solar: float, imp: float, exp: float, start: datetime | None = None) -> dict:
    q = QuarterInput(
        start=start or datetime(2026, 11, 26, 11, 0, tzinfo=UTC),
        minutes=15,
        import_kwh=imp,
        export_kwh=exp,
        charge_kwh=0.0,
        discharge_kwh=0.0,
        solar_kwh=solar,
        market=0.10,
        daylight=daylight,
    )
    return evaluate(q, TARIFFS, Pools())


def test_direct_plus_export_is_the_solar_saving() -> None:
    r = _q(True, 0.5, 0.0, 0.2)
    assert r["solar_direct_value"] + r["solar_export_value"] == pytest.approx(r["cost_no_solar"] - r["cost_no_battery"], abs=1e-4)
    assert r["solar_bonus_value"] == pytest.approx(0.2 * 0.1 * (0.10 + 0.0165), abs=1e-5)
    assert _q(False, 0.5, 0.0, 0.2)["solar_bonus_value"] == 0.0


def test_after_2027_export_is_worth_less_direct_not() -> None:
    before = _q(True, 0.5, 0.0, 0.2)
    after = _q(True, 0.5, 0.0, 0.2, datetime(2027, 1, 5, 11, 0, tzinfo=UTC))
    assert after["solar_export_value"] < before["solar_export_value"]
    assert after["solar_direct_value"] == pytest.approx(before["solar_direct_value"])


def test_day_totals_and_summary() -> None:
    day: dict = {}
    for _ in range(4):
        add_to_day(day, _q(True, 0.5, 0.0, 0.2))
    s = Summary(days=1, totals=day).as_dict()
    assert s["savings_solar"] == pytest.approx(s["solar_direct_value"] + s["solar_export_value"], abs=0.01)
    assert s["savings_total"] == pytest.approx(s["savings_solar"] + s["savings_battery"], abs=0.01)
    assert s["self_consumption"] == pytest.approx((2.0 - 0.8) / 2.0)


def test_day_boundary_values_the_battery_content() -> None:
    # TOETS-besparing bevinding 2: charged at night at 0.20 and delivered the next evening at
    # 0.40. Day 1 alone used to show a loss and day 2 a big gain; with the content valued, the
    # charge cost waits in the battery and both days add up to the same total.
    from zephyr_core.costs import summarize

    tariffs = Tariffs()
    pools = Pools()
    day1: dict = {}
    day2: dict = {}

    def quarter(when: datetime, imp: float, exp: float, chg: float, dis: float, market: float, stored: float) -> dict:
        before = pools.as_dict()
        q = QuarterInput(when, 15, imp, exp, chg, dis, None, market, stored_kwh=stored)
        record = evaluate(q, tariffs, pools)
        record["pools"] = before
        return record

    add_to_day(day1, quarter(datetime(2026, 11, 26, 2, 0, tzinfo=UTC), 2.0, 0.0, 2.0, 0.0, 0.20, 2.0))
    add_to_day(day2, quarter(datetime(2026, 11, 27, 18, 0, tzinfo=UTC), 0.0, 0.0, 0.0, 1.7, 0.40, 0.0))
    days = {"2026-11-26": day1, "2026-11-27": day2}
    one = summarize(days, date(2026, 11, 26), date(2026, 11, 26), tariffs)
    two = summarize(days, date(2026, 11, 27), date(2026, 11, 27), tariffs)
    both = summarize(days, date(2026, 11, 26), date(2026, 11, 27), tariffs)
    assert one.savings_battery == pytest.approx(0.0, abs=1e-6)  # the cost of the charge is in the battery
    assert one.savings_battery + two.savings_battery == pytest.approx(both.savings_battery, abs=1e-6)
    assert both.content_change == pytest.approx((0.0, 0.0), abs=1e-6)  # empty again: no correction
    assert both.savings_battery == pytest.approx(1.7 * tariffs.buy(0.40) - 2.0 * tariffs.buy(0.20), abs=1e-4)
