"""Screen Accu: what the battery did per day (from the cost log)."""

from __future__ import annotations

from datetime import date
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from zephyr_core.battery_days import battery_days

AMS = ZoneInfo("Europe/Amsterdam")


def q(start: str, **kw: Any) -> dict[str, Any]:
    base: dict[str, Any] = {"start": start, "charge_kwh": 0.0, "discharge_kwh": 0.0, "solar_kwh": 0.0, "house_kwh": 0.0}
    base.update(kw)
    return base


def test_routes_per_local_day_and_soc_range() -> None:
    records = [
        # 27-11 local: sun charges 0.3, house takes 0.1 from the sun
        q("2026-11-27T11:00:00+00:00", solar_kwh=0.4, house_kwh=0.1, charge_kwh=0.3, soc=40),
        # 27-11 local: grid charges 1.0 at € 0.20
        q("2026-11-27T13:00:00+00:00", charge_kwh=1.0, buy=0.20, soc=50),
        # 28-11 00:15 local is still 27-11 in UTC: belongs to 28-11
        q("2026-11-27T23:15:00+00:00", discharge_kwh=0.5, house_kwh=0.6, soc=45),
    ]
    view = battery_days(records, date(2026, 11, 28), AMS, usable_kwh=10.0, capacity_kwh=11.0)
    days = {d["date"]: d for d in view["days"]}
    assert len(view["days"]) == 7 and view["days"][0]["date"] == "2026-11-22"
    d27 = days["2026-11-27"]
    assert d27["solar_battery"] == 0.3 and d27["grid_battery"] == 1.0
    assert d27["soc_min"] == 40 and d27["soc_max"] == 50 and d27["quarters"] == 2
    assert d27["cycles"] == 0.0
    d28 = days["2026-11-28"]
    assert d28["battery_house"] == 0.5 and d28["battery_grid"] == 0.0 and d28["cycles"] == 0.05
    assert days["2026-11-22"]["quarters"] == 0 and days["2026-11-22"]["cycles"] is None
    week = view["week"]
    assert week["charged"] == 1.3 and week["delivered"] == 0.5
    assert week["grid_price"] == pytest.approx(0.20)


def test_discharge_beyond_the_house_goes_to_the_grid() -> None:
    view = battery_days([q("2026-11-28T08:00:00+00:00", discharge_kwh=0.5, house_kwh=0.2)], date(2026, 11, 28), AMS, 10.0, 11.0)
    today = view["days"][-1]
    assert today["battery_house"] == 0.2 and today["battery_grid"] == 0.3


def test_efficiency_counts_the_change_in_storage() -> None:
    # 6 kWh in, 4.3 kWh out, battery 10 % (1.1 kWh) fuller at the end: 4.3 / (6 - 1.1) ≈ 0.878
    records = [
        q("2026-11-25T01:45:00+00:00", soc=20),
        q("2026-11-25T02:00:00+00:00", charge_kwh=6.0, soc=85),
        q("2026-11-25T18:00:00+00:00", discharge_kwh=4.3, house_kwh=4.3, soc=30),
    ]
    view = battery_days(records, date(2026, 11, 28), AMS, 10.0, 11.0)
    assert view["week"]["efficiency"] == pytest.approx(0.878, abs=0.001)


def test_no_efficiency_with_too_little_energy_or_an_odd_result() -> None:
    small = [
        q("2026-11-25T01:45:00+00:00", soc=20),
        q("2026-11-25T02:00:00+00:00", charge_kwh=1.0, soc=29),
        q("2026-11-25T18:00:00+00:00", discharge_kwh=0.9, house_kwh=1, soc=20),
    ]
    assert battery_days(small, date(2026, 11, 28), AMS, 10.0, 11.0)["week"]["efficiency"] is None
    odd = [
        q("2026-11-25T01:45:00+00:00", soc=50),
        q("2026-11-25T02:00:00+00:00", charge_kwh=3.0, soc=77),
        q("2026-11-25T18:00:00+00:00", discharge_kwh=3.0, house_kwh=3, soc=50),
    ]
    assert battery_days(odd, date(2026, 11, 28), AMS, 10.0, 11.0)["week"]["efficiency"] is None


def test_hourly_backfill_and_unknown_capacity() -> None:
    records = [q("2026-11-28T08:00:00+00:00", source="hourly", discharge_kwh=2.0, house_kwh=2.0)]
    view = battery_days(records, date(2026, 11, 28), AMS, None, None)
    assert view["days"][-1]["quarters"] == 0
    assert view["week"]["cycles"] is None and view["usable_kwh"] is None


def test_efficiency_starts_at_the_first_soc() -> None:
    """28-11: the cost log charged 5 kWh in the night before its first SoC; that charge must not count."""
    records = [
        q("2026-11-25T23:00:00+00:00", charge_kwh=5.0),  # no SoC yet
        q("2026-11-26T08:00:00+00:00", soc=92),
        q("2026-11-26T18:00:00+00:00", discharge_kwh=4.3, house_kwh=4.3, soc=50),
        q("2026-11-27T02:00:00+00:00", charge_kwh=2.5, soc=72),
        q("2026-11-27T18:00:00+00:00", discharge_kwh=2.6, house_kwh=2.6, soc=46),
        q("2026-11-27T19:00:00+00:00", discharge_kwh=0.5, house_kwh=0.5),  # after the last SoC
    ]
    week = battery_days(records, date(2026, 11, 28), AMS, 10.0, 11.0)["week"]
    # in 2.5, out 6.9, SoC 92 → 46 = 5.06 kWh out of storage: 6.9 / (2.5 + 5.06) ≈ 0.913
    assert week["efficiency"] == pytest.approx(0.913, abs=0.001)
    assert week["efficiency_days"] == 2
    assert week["charged"] == 7.5 and week["delivered"] == 7.4  # the days still show everything
