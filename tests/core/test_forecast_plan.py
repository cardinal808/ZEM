"""Planner inputs and outcome (SPEC-planner §2, §4; PT1, PT3, PT7)."""

from __future__ import annotations

import itertools
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from zephyr_core.forecast_plan import (
    QUARTER,
    BatteryInput,
    PlanState,
    build_horizon,
    horizon_markets,
    make_plan,
    market_slots,
    no_prices,
    reason,
    solar_per_quarter,
)
from zephyr_core.planner import Action, PlannerSettings
from zephyr_core.solar_history import ForecastPeriod

TZ = ZoneInfo("Europe/Amsterdam")


def _raw(day: datetime, prices: list[float], minutes: int = 60) -> list[dict[str, Any]]:
    """Prices from local midnight of ``day`` in steps of ``minutes`` (counted in UTC, as the sources do)."""
    start = day.astimezone(ZoneInfo("UTC"))
    step = timedelta(minutes=minutes)
    return [{"start": start + i * step, "end": start + (i + 1) * step, "value": v} for i, v in enumerate(prices)]


def _midnight(y: int, m: int, d: int) -> datetime:
    return datetime(y, m, d, tzinfo=TZ)


def _horizon(markets: list[tuple[datetime, float, bool]], now: datetime, load: float = 0.1, solar: float = 0.0) -> Any:
    return build_horizon(
        markets,
        now,
        buy=lambda t, m: m + 0.12,
        sell=lambda t, m, day: m,
        load=lambda t, ahead: load,
        solar=lambda t: solar,
        daylight=lambda t: False,
    )


BAT = BatteryInput(capacity_kwh=11.04, soc=50.0, min_soc=10.0, max_soc=95.0, charge_kw=2.4, deliver_kw=2.4)


def test_hour_prices_in_mwh_give_four_quarters_each_to_the_end_of_tomorrow() -> None:
    today, tomorrow = _midnight(2026, 11, 26), _midnight(2026, 11, 27)
    attrs = {"raw_today": _raw(today, [100.0] * 24), "raw_tomorrow": _raw(tomorrow, [200.0] * 24), "unit": "EUR/MWh"}
    slots = market_slots(attrs)
    assert len(slots) == 48
    assert slots[0].price == pytest.approx(0.1)
    now = today + timedelta(hours=10, minutes=7)
    markets = horizon_markets(slots, now, TZ)
    assert markets[0][0] == today + timedelta(hours=10)
    assert len(markets) == 14 * 4 + 96
    assert markets[-1][0] == _midnight(2026, 11, 28) - QUARTER
    assert not any(ind for _, _, ind in markets)
    assert markets[-1][1] == pytest.approx(0.2)


def test_cents_are_converted() -> None:
    today = _midnight(2026, 11, 26)
    attrs = {"raw_today": _raw(today, [25.0] * 24), "raw_tomorrow": [], "price_in_cents": True}
    assert market_slots(attrs)[0].price == pytest.approx(0.25)


def test_tomorrow_unknown_uses_todays_pattern_as_indicative() -> None:
    today = _midnight(2026, 11, 26)
    prices = [0.10 + h / 100 for h in range(24)]
    slots = market_slots({"raw_today": _raw(today, prices), "raw_tomorrow": []})
    now = today + timedelta(hours=9)
    markets = horizon_markets(slots, now, TZ)
    known = [m for m in markets if not m[2]]
    indicative = [m for m in markets if m[2]]
    assert len(known) == 15 * 4
    assert len(indicative) == 96
    assert indicative[0][0] == _midnight(2026, 11, 27)
    assert indicative[4 * 20][1] == pytest.approx(prices[20])  # 20:00 tomorrow = 20:00 today

    outcome = make_plan(_horizon(markets, now), BAT, now, PlannerSettings())
    assert outcome.indicative_from == _midnight(2026, 11, 27)
    # Indicative slots do not count in the totals.
    known_cost = sum(s.cost for s, sl in zip(outcome.plan.steps, outcome.slots, strict=True) if not sl.indicative)
    assert outcome.expected_cost == pytest.approx(known_cost)


def test_pt1_source_still_shows_yesterday_after_midnight() -> None:
    """At 00:30 'today' still holds yesterday's prices: no price for now, never charge on them."""
    yesterday = _midnight(2026, 11, 25)
    slots = market_slots({"raw_today": _raw(yesterday, [0.01] * 24), "raw_tomorrow": []})
    now = _midnight(2026, 11, 26) + timedelta(minutes=30)
    assert horizon_markets(slots, now, TZ) == []
    outcome = no_prices(now, None)
    assert outcome.state == PlanState.NO_PRICES
    assert outcome.action is Action.DELIVER
    assert reason(outcome, "nl", TZ) == "Geen prijs voor dit kwartier (sinds 00:30): Nul op de meter tot er weer prijzen zijn."
    assert make_plan([], BAT, now, PlannerSettings()).state == PlanState.NO_PRICES


@pytest.mark.parametrize(("day", "quarters"), [((2026, 3, 29), 92), ((2026, 10, 25), 100)])
def test_pt7_daylight_saving_days(day: tuple[int, int, int], quarters: int) -> None:
    start = _midnight(*day)
    nxt = datetime(*day, tzinfo=TZ) + timedelta(days=1)  # wall clock: next local midnight
    n = int((nxt.astimezone(ZoneInfo("UTC")) - start.astimezone(ZoneInfo("UTC"))).total_seconds() // 900)
    assert n == quarters
    raw = _raw(start, [0.1 + i / 1000 for i in range(n)], minutes=15)
    slots = market_slots({"raw_today": raw, "raw_tomorrow": []})
    markets = horizon_markets(slots, start, TZ)
    today = [m for m in markets if not m[2]]
    assert len(today) == quarters
    starts = [m[0] for m in markets]
    assert len(set(starts)) == len(starts)
    assert all(b - a == QUARTER for a, b in itertools.pairwise(starts))
    assert markets[0][0] == start
    last = markets[-1][0].astimezone(TZ)
    assert (last.hour, last.minute) == (23, 45)
    assert last.date() == (start + timedelta(days=1)).date()


def test_solar_half_hours_per_quarter() -> None:
    periods = [
        ForecastPeriod("2026-11-26T11:00:00+00:00", 2.0, 1.0, 3.0),
        ForecastPeriod("2026-11-26T11:30:00+00:00", 1.0, 0.5, 1.5),
    ]
    per_quarter = solar_per_quarter(periods)
    t = datetime.fromisoformat("2026-11-26T11:00:00+00:00")
    assert per_quarter[t] == pytest.approx(0.5)
    assert per_quarter[t + QUARTER] == pytest.approx(0.5)
    assert per_quarter[t + 2 * QUARTER] == pytest.approx(0.25)
    assert per_quarter[t + 3 * QUARTER] == pytest.approx(0.25)
    assert len(per_quarter) == 4


def _night_and_evening() -> tuple[list[tuple[datetime, float, bool]], datetime]:
    """Cheap at night, expensive in the evening, tomorrow known."""
    today, tomorrow = _midnight(2026, 11, 26), _midnight(2026, 11, 27)
    day = [0.05] * 6 + [0.15] * 11 + [0.40] * 4 + [0.15] * 3
    slots = market_slots({"raw_today": _raw(today, day), "raw_tomorrow": _raw(tomorrow, day)})
    now = today + timedelta(hours=1)
    return horizon_markets(slots, now, TZ), now


def test_charges_at_night_for_the_evening_with_blocks_figures_and_reason() -> None:
    markets, now = _night_and_evening()
    empty = BatteryInput(capacity_kwh=11.04, soc=10.0, min_soc=10.0, max_soc=95.0, charge_kw=2.4, deliver_kw=2.4)
    outcome = make_plan(_horizon(markets, now, load=0.2), empty, now, PlannerSettings(wear_cost=0.03))
    assert outcome.state == PlanState.ACTIVE
    assert outcome.action is Action.CHARGE
    assert outcome.planned_grid_charge_kwh > 1.0
    assert outcome.planned_grid_charge_cost == pytest.approx(
        sum(k * s.buy for k, s in zip(outcome.grid_kwh, outcome.slots, strict=True) if not s.indicative)
    )
    first = outcome.blocks[0]
    assert first.action is Action.CHARGE and first.start == markets[0][0]
    five = markets[0][0].astimezone(TZ).replace(hour=17)
    assert any(b.action is Action.DELIVER and b.start <= five < b.end for b in outcome.blocks)
    assert outcome.planned_export_kwh == 0.0
    text = reason(outcome, "nl", TZ)
    assert text.startswith("Laden uit het net is nu gunstig: €0,17, de accu levert vanaf 11:00 bij gemiddeld €0,35")
    assert reason(outcome, "en", TZ).startswith("Charging from the grid is cheap now: €0.17")
    timeline = outcome.timeline()
    assert len(timeline) == len(outcome.slots)
    assert timeline[0]["action"] == "L" and timeline[0]["battery_kw"] > 2.0


def test_battery_empty_state_and_empty_at() -> None:
    markets, now = _night_and_evening()
    evening = now.replace(hour=17)
    markets = [m for m in markets if m[0] >= evening]
    low = BatteryInput(capacity_kwh=11.04, soc=10.2, min_soc=10.0, max_soc=95.0, charge_kw=2.4, deliver_kw=2.4)
    outcome = make_plan(_horizon(markets, evening, load=0.2), low, evening, PlannerSettings())
    assert outcome.action is Action.DELIVER
    assert outcome.state == PlanState.BATTERY_EMPTY
    half = BatteryInput(capacity_kwh=11.04, soc=20.0, min_soc=10.0, max_soc=95.0, charge_kw=2.4, deliver_kw=2.4)
    outcome = make_plan(_horizon(markets, evening, load=0.2), half, evening, PlannerSettings())
    assert outcome.action is Action.DELIVER
    assert outcome.empty_at is not None and outcome.empty_at.astimezone(TZ).hour < 21
    assert reason(outcome, "nl", TZ).startswith("Leveren is nu gunstig: €0,52")


def test_buffer_is_a_reserve_at_the_bottom_of_the_battery() -> None:
    """B37: the planner never plans to deliver from the buffer, but sees and refills it."""
    bat = BatteryInput(capacity_kwh=10.0, soc=30.0, min_soc=10.0, max_soc=90.0, charge_kw=2.4, deliver_kw=2.4, buffer=10.0)
    assert bat.battery().capacity_kwh == pytest.approx(8.0)
    assert bat.battery().reserve_kwh == pytest.approx(1.0)
    assert bat.energy_now == pytest.approx(2.0)
    below = BatteryInput(capacity_kwh=10.0, soc=15.0, min_soc=10.0, max_soc=90.0, charge_kw=2.4, deliver_kw=2.4, buffer=10.0)
    assert below.energy_now == pytest.approx(0.5)


def test_hold_reason_names_the_delivery_block() -> None:
    markets, now = _night_and_evening()
    noon = now.replace(hour=12)  # 0.15 now, 0.40 from 17:00
    markets = [m for m in markets if m[0] >= noon]
    full = BatteryInput(capacity_kwh=5.0, soc=95.0, min_soc=10.0, max_soc=95.0, charge_kw=2.4, deliver_kw=2.4)
    outcome = make_plan(_horizon(markets, noon, load=0.3), full, noon, PlannerSettings(wear_cost=0.03))
    assert outcome.action is Action.HOLD
    assert reason(outcome, "nl", TZ).startswith("Vasthouden: €0,27 nu is te goedkoop om te leveren; de accu levert vanaf 17:")


def test_reserve_fills_gaps_by_time_and_the_source_wins() -> None:
    from zephyr_core.forecast_plan import merge_reserve, remember

    today, tomorrow = _midnight(2026, 11, 26), _midnight(2026, 11, 27)
    before = market_slots({"raw_today": _raw(today, [0.1] * 24), "raw_tomorrow": _raw(tomorrow, [0.2] * 24)})
    late = today + timedelta(hours=23, minutes=50)
    reserve = remember([], before, late)
    assert len(reserve) == 26  # 22:00 and 23:00 today (ended less than an hour ago or running) and all of tomorrow
    # After midnight the source still shows yesterday: the saved prices give a price for now.
    after = tomorrow + timedelta(minutes=30)
    stale = market_slots({"raw_today": _raw(today, [0.1] * 24), "raw_tomorrow": []})
    prices = merge_reserve(stale, reserve)
    markets = horizon_markets(prices, after, TZ)
    assert markets and markets[0][1] == pytest.approx(0.2) and not markets[0][2]
    # The source is back with quarter prices: it wins, saved hour slots that overlap it go.
    fresh = market_slots({"raw_today": _raw(tomorrow, [0.3] * 96, minutes=15), "raw_tomorrow": []})
    merged = merge_reserve(fresh, reserve)
    assert all(s.price == pytest.approx(0.3) for s in merged if s.start >= tomorrow)
    updated = remember(reserve, fresh, after)
    assert all(s.price == pytest.approx(0.3) for s in updated if s.start >= tomorrow)
    assert all(s.end > after - timedelta(hours=1) for s in updated)


def test_reason_mentions_saved_prices() -> None:
    markets, now = _night_and_evening()
    outcome = make_plan(_horizon(markets, now), BAT, now, PlannerSettings())
    outcome.state = PlanState.PRICE_RESERVE
    assert reason(outcome, "nl", TZ).startswith("Bewaarde prijzen (de bron heeft nog geen prijs voor nu). ")


def test_charge_with_a_full_battery_is_shown_as_hold() -> None:
    """With a full battery the planner may keep 'charging' (same cost as holding): show H, state Full."""
    markets, now = _night_and_evening()
    full = BatteryInput(capacity_kwh=11.04, soc=95.0, min_soc=10.0, max_soc=95.0, charge_kw=2.4, deliver_kw=2.4)
    outcome = make_plan(_horizon(markets, now, load=0.05), full, now, PlannerSettings(wear_cost=0.03))
    for action, grid in zip(outcome.plan.actions, outcome.grid_kwh, strict=True):
        assert action is not Action.CHARGE or grid >= 0.01
    assert all(b.action is not Action.CHARGE or b.kwh >= 0.01 for b in outcome.blocks)
    assert outcome.action is not Action.CHARGE


def test_buffer_status_in_the_outcome() -> None:
    """B37: short buffer, refilled in a cheap hour or not at all (reason)."""
    markets, now = _night_and_evening()
    cfg = PlannerSettings(wear_cost=0.03, grid_charge_cost=0.01)
    short = BatteryInput(capacity_kwh=10.0, soc=12.0, min_soc=10.0, max_soc=90.0, charge_kw=2.4, deliver_kw=2.4, buffer=10.0)
    status = make_plan(_horizon(markets, now), short, now, cfg).buffer
    assert status is not None and status["short"] and status["kwh"] == 1.0 and status["now_kwh"] == 0.2
    assert status["refill_by"] == "grid" and status["refill_at"] is not None
    flat = [(t, 0.30, ind) for t, _, ind in markets]
    none = make_plan(_horizon(flat, now), short, now, cfg).buffer
    assert none is not None and none["refill_at"] is None and none["reason"] == "no_cheap_moment"
    full = BatteryInput(capacity_kwh=10.0, soc=50.0, min_soc=10.0, max_soc=90.0, charge_kw=2.4, deliver_kw=2.4, buffer=10.0)
    assert make_plan(_horizon(markets, now), full, now, cfg).buffer == {"kwh": 1.0, "now_kwh": 1.0, "short": False}
