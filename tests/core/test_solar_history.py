"""Daily solar forecast next to the production counter."""

from __future__ import annotations

import datetime as dt

from zephyr_core.solar_history import SolarHistory, energy_kwh, parse_detailed_forecast

TZ = dt.timezone(dt.timedelta(hours=1))


def _detail(day: str) -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    for half in range(48):
        start = dt.datetime.fromisoformat(f"{day}T00:00:00+01:00") + dt.timedelta(minutes=30 * half)
        kw = 1.0 if 20 <= half < 28 else 0.0  # 4 h at 1 kW = 4 kWh
        items.append(
            {
                "period_start": start if half % 2 else start.isoformat(),
                "pv_estimate": kw,
                "pv_estimate10": kw / 2,
                "pv_estimate90": kw * 1.5,
            }
        )
    return items


def test_parse_accepts_datetimes_and_strings_and_skips_junk() -> None:
    periods = parse_detailed_forecast([*_detail("2026-11-24"), {"pv_estimate": 1}, "x"])
    assert len(periods) == 48
    assert periods[1].start == "2026-11-24T00:30:00+01:00"
    assert parse_detailed_forecast(None) == [] and parse_detailed_forecast("abc") == []


def test_forecast_totals_and_hourly_production() -> None:
    h = SolarHistory()
    assert h.record_forecast("2026-11-24", "2026-11-23T23:00:30+01:00", "sensor.solcast", parse_detailed_forecast(_detail("2026-11-24")))
    f = h.days["2026-11-24"]["forecast"]
    assert (f["total_kwh"], f["total10_kwh"], f["total90_kwh"]) == (4.0, 2.0, 6.0)
    counter = 1000.0
    for hour in range(24):
        h.record_counter("2026-11-24", hour, counter)
        h.record_counter("2026-11-24", hour, counter + 5)  # a second reading in the same hour is ignored
        counter += 0.5 if 10 <= hour < 14 else 0.0
    h.record_counter("2026-11-25", 0, counter)
    assert h.production_per_hour("2026-11-24")[11] == 0.5
    row = h.summary()[0]
    assert row["actual_kwh"] == 2.0 and row["hours_measured"] == 24 and row["forecast_kwh"] == 4.0


def test_counter_drop_gives_no_value_and_old_days_are_pruned() -> None:
    h = SolarHistory()
    h.record_counter("2025-01-01", 0, 1.0)
    h.record_counter("2026-11-24", 5, 100.0)
    h.record_counter("2026-11-24", 6, 2.0)  # new meter
    assert 5 not in h.production_per_hour("2026-11-24")
    assert "2025-01-01" not in h.days
    assert SolarHistory.from_dict(h.as_dict()).days == h.days


def test_energy_units() -> None:
    assert energy_kwh(1500, "Wh") == 1.5 and energy_kwh(2, "kWh") == 2 and energy_kwh(1, "W") is None


def test_missing_reading_is_spread_over_the_hours() -> None:
    """26-11: no reading in hour 1 (restart); the day total still counts."""
    h = SolarHistory()
    counter = 100.0
    for hour in range(24):
        if hour != 11:  # no reading in the middle of the day
            h.record_counter("2026-11-26", hour, counter)
        counter += 1.0 if 9 <= hour < 15 else 0.0
    h.record_counter("2026-11-27", 0, counter)
    hourly = h.production_per_hour("2026-11-26")
    assert len(hourly) == 24
    assert hourly[10] == hourly[11] == 1.0  # the 2 kWh from 10 to 12 o'clock, spread evenly
    assert h.summary()[0]["actual_kwh"] == 6.0
