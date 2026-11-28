"""Price forecast from jeroen.nl (OPDRACHT-prijsvoorspelling-jeroen).

The fixture is made up with the shape of the ha-jeroen-nl sensor (28-11-2026): the real
forecast may only be used privately, so it is not in this public repository.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from zephyr_core.price_forecast import VALUE_LOW, VALUE_MID, extend_markets, parse_forecast, stale

TZ = ZoneInfo("Europe/Amsterdam")
Q = timedelta(minutes=15)


def _attrs(
    first_forecast: datetime, quarters: int, made: str = "2026-11-28T04:00:00+01:00", unit: str = "€/kWh", band: bool = True
) -> dict:
    rows = []
    t = first_forecast - 8 * Q
    for _ in range(8):  # fixed quarters before the forecast
        rows.append({"start": t.isoformat(), "end": (t + Q).isoformat(), "price": 0.36, "market": 0.19})
        t += Q
    for i in range(quarters):
        row = {"start": t.isoformat(), "end": (t + Q).isoformat(), "price": 0.40, "market": 0.20 + 0.001 * i, "forecast": True}
        if band:
            row.update({"low": 0.17 + 0.001 * i, "high": 0.26 + 0.001 * i})
        rows.append(row)
        t += Q
    return {"prices": rows, "forecast_made": made, "unit_of_measurement": unit}


def _markets(start: datetime, end: datetime, pattern_until: datetime | None = None) -> list[tuple[datetime, float, bool]]:
    out = []
    t = start
    while t < end:
        out.append((t, 0.18, False))
        t += Q
    while pattern_until is not None and t < pattern_until:
        out.append((t, 0.18, True))
        t += Q
    return out


NOW = datetime(2026, 11, 28, 14, 0, tzinfo=UTC)
KNOWN_END = datetime(2026, 11, 29, 23, 0, tzinfo=UTC)  # local midnight 29→30-11


def test_reads_only_forecast_quarters_and_units() -> None:
    f = parse_forecast("0.36", _attrs(KNOWN_END, 96))
    assert len(f.slots) == 96 and f.slots[0].start == KNOWN_END and f.slots[0].band
    assert f.slots[0].market == pytest.approx(0.20) and f.slots[0].low == pytest.approx(0.17)
    mwh = parse_forecast("360", _attrs(KNOWN_END, 4, unit="EUR/MWh"))
    assert mwh.slots[0].market == pytest.approx(0.0002)
    cents = parse_forecast("36", _attrs(KNOWN_END, 4, unit="ct/kWh"))
    assert cents.slots[0].market == pytest.approx(0.002)
    plain = parse_forecast("0.36", _attrs(KNOWN_END, 4, band=False))
    assert plain.slots[0].low == plain.slots[0].market and plain.issues


def test_unreadable_sensor_is_flagged_but_unavailable_is_not() -> None:
    assert parse_forecast("0.36", {}).readable is False
    assert parse_forecast("unavailable", {}).readable is True


def test_extends_after_nord_pool_for_the_chosen_days() -> None:
    f = parse_forecast("0.36", _attrs(KNOWN_END, 2 * 96))
    markets = _markets(NOW, KNOWN_END)
    one = extend_markets(markets, f, NOW, TZ, 1, VALUE_LOW)
    assert one.reason is None and len(one.used) == 96  # Monday 30-11, local
    assert one.markets[-1][2] is True and one.markets[len(markets)][1] == pytest.approx(0.17)
    two = extend_markets(markets, f, NOW, TZ, 2, VALUE_MID)
    assert len(two.used) == 192 and two.markets[len(markets)][1] == pytest.approx(0.20)
    assert extend_markets(markets, f, NOW, TZ, 0).used == []


def test_before_tomorrow_is_known_the_forecast_replaces_todays_pattern() -> None:
    today_end = datetime(2026, 11, 28, 23, 0, tzinfo=UTC)
    morning = datetime(2026, 11, 28, 9, 0, tzinfo=UTC)
    markets = _markets(morning, today_end, pattern_until=KNOWN_END)
    f = parse_forecast("0.36", _attrs(today_end, 96))
    ext = extend_markets(markets, f, morning, TZ, 1)
    assert ext.reason is None
    assert all(m[1] != 0.18 for m in ext.markets if m[2])  # no pattern left
    assert len(ext.markets) == len([m for m in markets if not m[2]]) + 96


def test_nord_pool_wins_a_gap_stops_and_old_forecasts_are_ignored() -> None:
    markets = _markets(NOW, KNOWN_END)
    overlap = parse_forecast("0.36", _attrs(KNOWN_END - 4 * Q, 100))
    ext = extend_markets(markets, overlap, NOW, TZ, 1)
    starts = [m[0] for m in ext.markets]
    assert len(starts) == len(set(starts))  # no double slots
    assert all(not m[2] for m in ext.markets if m[0] < KNOWN_END)  # Nord Pool kept
    gap = parse_forecast("0.36", _attrs(KNOWN_END + Q, 96))
    assert extend_markets(markets, gap, NOW, TZ, 1).reason == "gap"
    old = parse_forecast("0.36", _attrs(KNOWN_END, 96, made="2026-11-26T04:00:00+01:00"))
    assert stale(old, NOW) and extend_markets(markets, old, NOW, TZ, 1).reason == "stale"
    assert extend_markets([], overlap, NOW, TZ, 1).reason == "no_known_prices"


def test_days_of_92_and_100_quarters() -> None:
    # 29-03-2026 (spring, 23 h) and 25-10-2026 (autumn, 25 h): up to local midnight.
    spring_known_end = datetime(2026, 3, 28, 23, 0, tzinfo=UTC)
    f = parse_forecast("0.36", _attrs(spring_known_end, 120, made="2026-03-28T04:00:00+01:00"))
    ext = extend_markets(_markets(spring_known_end - 8 * Q, spring_known_end), f, spring_known_end - 8 * Q, TZ, 1)
    assert len(ext.used) == 92
    autumn_known_end = datetime(2026, 10, 24, 22, 0, tzinfo=UTC)
    f = parse_forecast("0.36", _attrs(autumn_known_end, 120, made="2026-10-24T04:00:00+02:00"))
    ext = extend_markets(_markets(autumn_known_end - 8 * Q, autumn_known_end), f, autumn_known_end - 8 * Q, TZ, 1)
    assert len(ext.used) == 100


def test_expensive_monday_morning_charges_sunday_night_only_when_taken_into_account() -> None:
    # Known prices to Sunday 24:00 (flat 0.20); forecast Monday 07–09 at 0.60 (low 0.55). Taking it
    # into account the planner charges Sunday night; with low just under the break-even it does not.
    from zephyr_core.forecast_plan import BatteryInput, build_horizon, make_plan
    from zephyr_core.planner import Action, PlannerSettings

    sunday = datetime(2026, 11, 29, 22, 0, tzinfo=TZ)
    known_end = datetime(2026, 11, 30, 0, 0, tzinfo=TZ).astimezone(UTC)
    markets = _markets(sunday.astimezone(UTC), known_end)

    def forecast(peak_low: float) -> list[dict]:
        rows = []
        t = known_end
        for _ in range(96):
            hour = t.astimezone(TZ).hour
            market = 0.60 if 7 <= hour < 9 else 0.20
            low = peak_low if 7 <= hour < 9 else 0.20
            rows.append(
                {"start": t.isoformat(), "end": (t + Q).isoformat(), "market": market, "low": low, "high": market + 0.1, "forecast": True}
            )
            t += Q
        return rows

    battery = BatteryInput(capacity_kwh=11.04, soc=10.0, min_soc=10.0, max_soc=95.0, charge_kw=2.4, deliver_kw=2.4)

    def first_action(peak_low: float) -> Action:
        f = parse_forecast("0.3", {"prices": forecast(peak_low), "forecast_made": "2026-11-29T05:00:00+01:00"})
        ext = extend_markets(markets, f, sunday.astimezone(UTC), TZ, 1)
        slots = build_horizon(
            ext.markets,
            sunday.astimezone(UTC),
            buy=lambda t, m: (m + 0.09) * 1.21,
            sell=lambda t, m, day: m,
            load=lambda t, ahead: 0.2,
            solar=lambda t: 0.0,
            daylight=lambda t: False,
        )
        return make_plan(slots, battery, sunday.astimezone(UTC), PlannerSettings(wear_cost=0.03)).action

    assert first_action(0.55) is Action.CHARGE
    assert first_action(0.22) is not Action.CHARGE


def _real_shape(first: datetime, quarters: int, reversed_band: int | None = None) -> dict:
    """As ha-jeroen-nl builds a row (sensor.py ``_row``): ``market`` bare, ``price``, ``low`` and
    ``high`` all-in with its own tariff, (market + markup + tax) × (1 + VAT). Made-up values."""

    def all_in(market: float) -> float:
        return round((market + 0.02 + 0.1108) * 1.21, 5)

    rows = []
    t = first - 4 * Q
    for i in range(4):
        m = 0.15 + 0.01 * i
        rows.append({"start": t.isoformat(), "end": (t + Q).isoformat(), "price": all_in(m), "market": m})
        t += Q
    for i in range(quarters):
        m = 0.20 + 0.005 * i
        low, high = m - 0.02, m + 0.06
        if i == reversed_band:
            low, high = m + 0.03, m + 0.05  # a band that does not hold the expected price
        row = {"start": t.isoformat(), "end": (t + Q).isoformat(), "price": all_in(m), "market": m, "forecast": True}
        row.update({"low": all_in(low), "high": all_in(high)})
        rows.append(row)
        t += Q
    return {"prices": rows, "forecast_made": "2026-11-28T04:00:00+01:00", "unit_of_measurement": "€/kWh"}


def test_all_in_band_is_turned_back_into_bare_prices() -> None:
    # Seen 28-11 (meerekenen): expected € 0.47, band € 0.66–0.82: the band came all-in.
    f = parse_forecast("0.40", _real_shape(KNOWN_END, 8))
    assert f.band_all_in == 8 and not f.issues
    for i, slot in enumerate(f.slots):
        m = 0.20 + 0.005 * i
        assert slot.band and slot.low <= slot.market <= slot.high
        assert slot.low == pytest.approx(m - 0.02, abs=1e-4) and slot.high == pytest.approx(m + 0.06, abs=1e-4)


def test_band_that_does_not_hold_the_market_price_is_dropped() -> None:
    f = parse_forecast("0.40", _real_shape(KNOWN_END, 8, reversed_band=3))
    slot = f.slots[3]
    assert not slot.band and slot.low == slot.market == slot.high
    assert any("does not hold the market price" in issue for issue in f.issues)
    assert all(s.band for i, s in enumerate(f.slots) if i != 3)


def test_bare_band_stays_as_it_is() -> None:
    f = parse_forecast("0.36", _attrs(KNOWN_END, 4))
    assert f.band_all_in == 0 and f.slots[0].low == pytest.approx(0.17)
