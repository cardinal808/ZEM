"""Cost log (B38, SPEC-kosten): prices, the three situations, pools, net metering per year."""

from __future__ import annotations

import datetime as dt

import pytest

from zephyr_core.costs import (
    Pools,
    QuarterInput,
    QuarterMeter,
    Tariffs,
    add_to_day,
    counter_delta,
    evaluate,
    summarize,
    to_csv,
)

UTC = dt.UTC
T = Tariffs(energy_tax=0.0916, vat=21.0, markup_import=0.0165, markup_export=0.0)
T2026 = dt.datetime(2026, 11, 25, 12, 0, tzinfo=UTC)
T2027 = dt.datetime(2027, 3, 1, 12, 0, tzinfo=UTC)


def q(start: dt.datetime = T2026, **kw: float | None) -> QuarterInput:
    values: dict[str, float | None] = {
        "import_kwh": 0.0,
        "export_kwh": 0.0,
        "charge_kwh": 0.0,
        "discharge_kwh": 0.0,
        "solar_kwh": 0.0,
        "market": 0.10,
    }
    values.update(kw)
    return QuarterInput(start=start, minutes=15, **values)  # type: ignore[arg-type]


def test_prices_with_and_without_saldering() -> None:
    assert T.buy(0.10) == pytest.approx((0.10 + 0.0165 + 0.0916) * 1.21)
    sell, part = T.sell(0.10, T2026)
    assert sell == pytest.approx(0.10 * 1.21 + 0.0916 * 1.21)
    assert part == pytest.approx(sell - 0.10)
    assert T.sell(0.10, T2027) == (pytest.approx(0.10), 0.0)
    # Negative market price: import still costs the tax, export costs money without saldering.
    assert T.sell(-0.05, T2027)[0] == pytest.approx(-0.05)


def test_no_battery_no_solar_matches_actual() -> None:
    r = evaluate(q(import_kwh=0.3), T, Pools())
    assert r["cost"] == r["cost_no_battery"] == r["cost_no_solar"] == pytest.approx(0.3 * T.buy(0.10), abs=1e-5)
    assert r["house_kwh"] == 0.3


def test_solar_surplus_into_battery_then_evening() -> None:
    pools = Pools()
    # Noon: 1 kWh solar, house 0.2, battery takes 0.8 (no export).
    noon = evaluate(q(solar_kwh=1.0, charge_kwh=0.8), T, pools)
    assert noon["cost"] == 0.0
    assert noon["export_no_battery_kwh"] == pytest.approx(0.8)
    assert noon["cost_no_battery"] == pytest.approx(-0.8 * T.sell(0.10, T2026)[0], abs=1e-5)
    assert pools.solar_kwh == pytest.approx(0.8)
    # Evening, expensive: the battery delivers 0.7 for the house.
    evening = evaluate(q(dt.datetime(2026, 11, 25, 18, tzinfo=UTC), discharge_kwh=0.7, market=0.30, stored_kwh=0.0), T, pools)
    assert evening["cost"] == 0.0
    assert evening["cost_no_battery"] == pytest.approx(0.7 * T.buy(0.30), abs=1e-5)
    # All delivered energy came from solar; the battery is empty after it, so the loss (0.1 kWh)
    # also counts against solar via the battery: value = 0.7 × buy − all given-up export revenue.
    expected = 0.7 * T.buy(0.30) - 0.8 * T.sell(0.10, T2026)[0]
    assert evening["solar_via_battery"] == pytest.approx(expected, abs=1e-5)
    day: dict[str, float] = {}
    add_to_day(day, noon)
    add_to_day(day, evening)
    s = summarize({"2026-11-25": day}, dt.date(2026, 11, 25), dt.date(2026, 11, 25), T).as_dict()
    # Without solar: house 0.2 at noon + 0.7 in the evening from the grid.
    assert s["cost_no_solar"] == pytest.approx(0.2 * T.buy(0.10) + 0.7 * T.buy(0.30), abs=0.01)
    assert s["savings_trade"] == pytest.approx(0.0, abs=0.01)  # the battery only moved solar
    assert s["savings"] == pytest.approx(s["cost_no_solar"] - s["cost"], abs=0.01)


def test_grid_charging_is_trade() -> None:
    pools = Pools()
    night = evaluate(q(dt.datetime(2026, 11, 25, 2, tzinfo=UTC), import_kwh=1.0, charge_kwh=1.0, market=0.05), T, pools)
    evening = evaluate(q(dt.datetime(2026, 11, 25, 18, tzinfo=UTC), discharge_kwh=0.9, market=0.35), T, pools)
    assert pools.solar_kwh == 0.0 and night["solar_via_battery"] == 0.0 and evening["solar_via_battery"] == 0.0
    day: dict[str, float] = {}
    add_to_day(day, night)
    add_to_day(day, evening)
    s = summarize({"2026-11-25": day}, dt.date(2026, 11, 25), dt.date(2026, 11, 25), T).as_dict()
    trade = 0.9 * T.buy(0.35) - 1.0 * T.buy(0.05)
    assert s["savings_battery"] == pytest.approx(trade, abs=0.01)
    assert s["savings_trade"] == pytest.approx(trade, abs=0.01)


def test_pools_capped_by_stored_energy() -> None:
    pools = Pools(solar_kwh=4.0, grid_kwh=4.0, solar_value=0.8)
    evaluate(q(stored_kwh=2.0), T, pools)  # type: ignore[arg-type]
    assert pools.solar_kwh == pytest.approx(1.0) and pools.grid_kwh == pytest.approx(1.0)
    assert pools.solar_value == pytest.approx(0.2)


def test_quarter_without_price_keeps_energy() -> None:
    r = evaluate(q(import_kwh=0.2, market=None), T, Pools())
    assert r["cost"] is None and r["import_kwh"] == 0.2
    day: dict[str, float] = {}
    add_to_day(day, r)
    assert day["no_price"] == 1 and day["import_kwh"] == 0.2
    s = summarize({"2026-11-25": day}, dt.date(2026, 11, 25), dt.date(2026, 11, 25), T)
    assert s.cost is None and s.as_dict()["quarters_without_price"] == 1


def test_without_solar_counter_battery_savings_still_known() -> None:
    r = evaluate(q(import_kwh=0.0, discharge_kwh=0.5, solar_kwh=None, market=0.3), T, Pools())
    day: dict[str, float] = {}
    add_to_day(day, r)
    s = summarize({"2026-11-25": day}, dt.date(2026, 11, 25), dt.date(2026, 11, 25), T)
    assert s.savings_battery == pytest.approx(0.5 * T.buy(0.3), abs=1e-4)
    assert s.savings_solar is None and s.as_dict()["includes_solar"] is False


def test_yearly_saldering_correction_only_for_the_surplus() -> None:
    days = {"2026-06-01": {}, "2026-12-01": {}}
    add_to_day(days["2026-06-01"], evaluate(q(dt.datetime(2026, 6, 1, 12, tzinfo=UTC), export_kwh=3.0), T, Pools()))
    add_to_day(days["2026-12-01"], evaluate(q(dt.datetime(2026, 12, 1, 18, tzinfo=UTC), import_kwh=1.0), T, Pools()))
    year = summarize(days, dt.date(2026, 1, 1), dt.date(2026, 12, 31), T)
    _, part = T.sell(0.10, T2026)
    assert year.saldering_correction == pytest.approx(2.0 / 3.0 * 3.0 * part, abs=1e-4)
    month = summarize(days, dt.date(2026, 6, 1), dt.date(2026, 6, 30), T)
    assert month.saldering_correction == 0.0
    # From 2027 no netting part at all.
    assert summarize(days, dt.date(2027, 1, 1), dt.date(2027, 12, 31), T).saldering_correction == 0.0


def test_meter_integrates_and_skips_gaps() -> None:
    m = QuarterMeter()
    m.sample(0.0, 1000.0, -500.0)
    m.sample(1.0, -2000.0, 600.0, 100.0)
    m.sample(2.0, None, 600.0, 100.0)  # P1 stale from here
    m.sample(40.0, 1000.0, 0.0)  # 38 s gap: not integrated
    done = m.take(41.0)
    assert done.import_kwh == pytest.approx(1000 / 3600 / 1000 + 1 / 3600)
    assert done.export_kwh == pytest.approx(2000 / 3600 / 1000)
    assert done.discharge_kwh == pytest.approx(0.5 / 3600)
    assert done.charge_kwh == pytest.approx(0.6 / 3600)
    assert done.grid_seconds == 3.0 and done.battery_seconds == 3.0
    assert m.import_kwh == 0.0
    m.sample(42.0, 1000.0, 0.0)
    assert m.take(42.0).import_kwh == pytest.approx(1 / 3600)  # the held 1000 W from 41 s


def test_counter_delta() -> None:
    assert counter_delta(10.0, 10.5) == 0.5
    assert counter_delta(4000.0, 0.3) == 0.3  # new meter
    assert counter_delta(None, 1.0) is None


@pytest.mark.parametrize(("day", "quarters"), [("2026-03-29", 92), ("2026-10-25", 100)])
def test_dst_days_count_all_quarters(day: str, quarters: int) -> None:
    from zoneinfo import ZoneInfo

    tz = ZoneInfo("Europe/Amsterdam")
    start = dt.datetime.fromisoformat(day).replace(tzinfo=tz).astimezone(UTC)
    end = (dt.datetime.fromisoformat(day) + dt.timedelta(days=1)).replace(tzinfo=tz).astimezone(UTC)
    days: dict[str, dict[str, float]] = {}
    t = start
    while t < end:
        key = t.astimezone(tz).date().isoformat()
        add_to_day(days.setdefault(key, {}), evaluate(q(t, import_kwh=0.1), T, Pools()))
        t += dt.timedelta(minutes=15)
    assert days[day]["quarters"] == quarters
    assert days[day]["import_kwh"] == pytest.approx(quarters * 0.1)


def test_csv_has_header_and_rows() -> None:
    text = to_csv([evaluate(q(import_kwh=0.1), T, Pools())])
    lines = text.strip().split("\n")
    assert lines[0].startswith("start,minutes,import_kwh")
    assert len(lines) == 2
