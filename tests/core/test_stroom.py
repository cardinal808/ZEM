"""Screen Stroom: energy per route (split of a quarter) and the zero score."""

from __future__ import annotations

from datetime import date

import pytest

from zephyr_core.stroom import BUCKET_SECONDS, ZeroScore, routes, split_quarter


def q(**kw: float | str | None) -> dict[str, float | str | None]:
    base: dict[str, float | str | None] = {
        "start": "2026-11-27T10:00:00+00:00",
        "import_kwh": 0.0,
        "export_kwh": 0.0,
        "charge_kwh": 0.0,
        "discharge_kwh": 0.0,
        "solar_kwh": 0.0,
        "house_kwh": 0.0,
    }
    base.update(kw)
    return base


def test_sun_goes_to_the_house_first_then_the_battery_then_the_grid() -> None:
    s = split_quarter(q(solar_kwh=1.0, house_kwh=0.3, charge_kwh=0.5, export_kwh=0.2))
    assert s["solar_house"] == pytest.approx(0.3)
    assert s["solar_battery"] == pytest.approx(0.5)
    assert s["solar_grid"] == pytest.approx(0.2)
    assert s["grid_house"] == s["grid_battery"] == s["battery_house"] == 0


def test_evening_battery_and_grid_share_the_house() -> None:
    s = split_quarter(q(house_kwh=0.4, discharge_kwh=0.3, import_kwh=0.1))
    assert s["battery_house"] == pytest.approx(0.3)
    assert s["grid_house"] == pytest.approx(0.1)
    assert s["battery_grid"] == 0


def test_night_charging_from_the_grid() -> None:
    s = split_quarter(q(house_kwh=0.2, charge_kwh=0.6, import_kwh=0.8))
    assert s["grid_house"] == pytest.approx(0.2)
    assert s["grid_battery"] == pytest.approx(0.6)


def test_routes_add_up_with_shares_airco_and_prices() -> None:
    records = [
        q(solar_kwh=1.0, house_kwh=0.5, charge_kwh=0.5, buy=0.30, excluded_kwh=0.25),
        q(house_kwh=0.5, charge_kwh=1.0, import_kwh=1.5, buy=0.10, excluded_kwh=0.25),
        q(source="hourly", house_kwh=9.0),  # worked out later: left out
    ]
    view = routes(records)
    r = view["routes"]
    assert r["solar_house"] == 0.5 and r["solar_battery"] == 0.5
    assert r["grid_house"] == 0.5 and r["grid_battery"] == 1.0
    assert view["house_kwh"] == 1.0 and view["quarters"] == 2
    assert view["self_use"] == 1.0
    assert view["own_source"] == 0.5
    assert view["grid_battery_price"] == pytest.approx(0.10)
    airco = view["airco"]
    assert airco["kwh"] == 0.5 and airco["share"] == 0.5
    assert airco["solar_kwh"] == pytest.approx(0.25)  # half the house is airco: half the sun to the house
    assert airco["grid_kwh"] == pytest.approx(0.25)
    assert airco["grid_cost"] == pytest.approx(0.03)


def test_no_airco_set_up_gives_no_airco() -> None:
    assert routes([q(house_kwh=1.0, import_kwh=1.0)])["airco"] is None


def test_zero_score_counts_steering_time_in_and_out_of_the_band() -> None:
    z = ZeroScore()
    day = date(2026, 11, 27)
    t, sod = 1000.0, 10 * 3600.0
    z.add(t, day, sod, True, 20)
    for i in range(1, 61):  # 60 s within the band
        z.add(t + i, day, sod + i, True, 20 if i < 60 else 400)
    for i in range(61, 71):  # 10 s at +400 W
        z.add(t + i, day, sod + i, True, 400)
    z.add(t + 71, day, sod + 71, False, 0)
    z.add(t + 100, day, sod + 100, False, 0)  # not steering: not counted
    view = z.view()
    assert view["steering_s"] == 71
    assert view["score"] == pytest.approx(60 / 71, abs=0.001)
    assert view["import_kwh"] == pytest.approx((60 * 20 + 11 * 400) / 3600 / 1000, abs=0.001)
    cell = view["buckets"][int(sod) // BUCKET_SECONDS]
    assert cell is not None and cell[0] == 71
    assert view["buckets"][0] is None


def test_zero_score_skips_long_gaps_and_starts_over_on_a_new_day() -> None:
    z = ZeroScore()
    z.add(0, date(2026, 11, 27), 100, True, 0)
    z.add(100, date(2026, 11, 27), 200, True, 0)  # 100 s gap: not counted
    assert z.view()["steering_s"] == 0
    z.add(101, date(2026, 11, 28), 1, True, 0)
    assert z.view()["date"] == "2026-11-28"


def test_zero_score_survives_a_restart_on_the_same_day_only() -> None:
    z = ZeroScore()
    day = date(2026, 11, 27)
    for i in range(120):
        z.add(i, day, 3600 + i, True, 10)
    stored = z.as_dict()
    again = ZeroScore()
    again.restore(stored, day)
    assert again.view()["steering_s"] == 119
    other = ZeroScore()
    other.restore(stored, date(2026, 11, 28))
    assert other.view()["steering_s"] == 0
