"""The plan as the panel shows it (SPEC-ui §3.2, UI-2)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import pytest

from zephyr_core.forecast_plan import QUARTER, BatteryInput, build_horizon, horizon_markets, make_plan, market_slots
from zephyr_core.plan_view import local_midnight, past_action, plan_quarters, plan_view
from zephyr_core.planner import PlannerSettings

TZ = ZoneInfo("Europe/Amsterdam")
BAT = BatteryInput(capacity_kwh=11.04, soc=50.0, min_soc=10.0, max_soc=95.0, charge_kw=2.4, deliver_kw=2.4, buffer=10.0)


def _raw(day: datetime, prices: list[float]) -> list[dict[str, Any]]:
    start = day.astimezone(UTC)
    return [{"start": start + timedelta(hours=i), "end": start + timedelta(hours=i + 1), "value": v} for i, v in enumerate(prices)]


def _fns() -> dict[str, Any]:
    return {
        "buy": lambda t, m: m + 0.12,
        "sell": lambda t, m, day: m + (0.01 if day else 0.0),
        "daylight": lambda t: 8 <= t.astimezone(TZ).hour < 17,
    }


def _outcome(prices: list[Any], now: datetime) -> Any:
    markets = horizon_markets(prices, now, TZ)
    slots = build_horizon(
        markets,
        now,
        buy=lambda t, m: m + 0.12,
        sell=lambda t, m, d: m,
        load=lambda t, a: 0.1,
        solar=lambda t: 0.0,
        daylight=lambda t: False,
    )
    return make_plan(slots, BAT, now, PlannerSettings())


def test_today_from_midnight_with_past_prices_and_plan_from_now() -> None:
    today = datetime(2026, 11, 26, tzinfo=TZ)
    day = [0.05] * 6 + [0.15] * 11 + [0.40] * 4 + [0.15] * 3
    prices = market_slots({"raw_today": _raw(today, day), "raw_tomorrow": _raw(today + timedelta(days=1), day)})
    now = today + timedelta(hours=20, minutes=7)
    outcome = _outcome(prices, now)
    quarters = plan_quarters(outcome, prices, now, TZ, **_fns())

    assert len(quarters) == 192
    assert quarters[0]["start"] == today.astimezone(UTC).isoformat()
    first_planned = 80  # 20:00
    assert all(q["past"] for q in quarters[:first_planned])
    assert not any(q["past"] for q in quarters[first_planned:])
    past = quarters[10]  # 02:30, from the price sensor only
    assert past["market"] == pytest.approx(0.05)
    assert past["buy"] == pytest.approx(0.17)
    assert past["action"] is None and past["soc"] is None
    assert quarters[40]["sell"] == pytest.approx(0.16)  # 10:00: daylight
    now_q = quarters[first_planned]
    assert now_q["action"] in ("charge", "hold", "deliver", "export")
    assert now_q["soc"] is not None and 20.0 <= now_q["soc"] <= 95.0  # never below min + buffer
    assert now_q["buy"] == pytest.approx(0.52)
    assert quarters[-1]["start"] == (datetime(2026, 11, 28, tzinfo=TZ) - QUARTER).astimezone(UTC).isoformat()


def test_without_tomorrow_the_indicative_pattern_is_marked() -> None:
    today = datetime(2026, 11, 26, tzinfo=TZ)
    prices = market_slots({"raw_today": _raw(today, [0.10 + h / 100 for h in range(24)]), "raw_tomorrow": []})
    now = today + timedelta(hours=9)
    quarters = plan_quarters(_outcome(prices, now), prices, now, TZ, **_fns())
    assert len(quarters) == 192
    assert not any(q["indicative"] for q in quarters[:96])
    assert all(q["indicative"] for q in quarters[96:])


def test_without_plan_only_prices() -> None:
    today = datetime(2026, 11, 26, tzinfo=TZ)
    prices = market_slots({"raw_today": _raw(today, [0.2] * 24), "raw_tomorrow": []})
    now = today + timedelta(hours=12)
    view = plan_view(None, prices, now, TZ, **_fns(), tomorrow_known_at=None, reason=None)
    assert view["state"] is None and view["blocks"] == []
    quarters = view["quarters"]
    assert len(quarters) == 192
    assert quarters[0]["buy"] == pytest.approx(0.32)
    assert quarters[100]["market"] is None  # tomorrow unknown and no plan


@pytest.mark.parametrize(("day", "count"), [(datetime(2026, 3, 29, tzinfo=TZ), 92 + 96), (datetime(2026, 10, 25, tzinfo=TZ), 100 + 96)])
def test_dst_days_have_92_or_100_quarters(day: datetime, count: int) -> None:
    now = day + timedelta(hours=12)
    assert local_midnight(now, TZ) == day.astimezone(UTC)
    assert len(plan_quarters(None, [], now, TZ, **_fns())) == count


def test_view_carries_blocks_reason_and_known_at() -> None:
    today = datetime(2026, 11, 26, tzinfo=TZ)
    day = [0.05] * 6 + [0.40] * 18
    prices = market_slots({"raw_today": _raw(today, day), "raw_tomorrow": _raw(today + timedelta(days=1), day)})
    now = today + timedelta(hours=14)
    known = today + timedelta(hours=13, minutes=12)
    view = plan_view(_outcome(prices, now), prices, now, TZ, **_fns(), tomorrow_known_at=known, reason={"nl": "x", "en": "y"})
    assert view["state"] == "active"
    assert view["soc_now"] == 50.0
    assert view["tomorrow_known_at"] == known.astimezone(UTC).isoformat()
    assert view["reason"] == {"nl": "x", "en": "y"}
    assert view["blocks"] and {"action", "start", "end", "kwh", "price", "indicative"} <= set(view["blocks"][0])
    assert any(b["action"] == "charge" for b in view["blocks"])  # cheap night tomorrow


@pytest.mark.parametrize(
    ("record", "action"),
    [
        ({"charge_kwh": 0.6, "discharge_kwh": 0.0}, "charge"),
        ({"charge_kwh": 0.0, "discharge_kwh": 0.2}, "deliver"),
        ({"charge_kwh": 0.0, "discharge_kwh": 0.6, "export_kwh": 0.4, "plan_action": "X"}, "export"),
        ({"charge_kwh": 0.0, "discharge_kwh": 0.6, "export_kwh": 0.4, "plan_action": "N"}, "deliver"),
        ({"charge_kwh": 0.01, "discharge_kwh": 0.02}, "hold"),
        ({"charge_kwh": None, "discharge_kwh": None}, "hold"),
    ],
)
def test_past_action_from_the_cost_log(record: dict[str, Any], action: str) -> None:
    assert past_action(record) == action


def test_past_quarters_from_the_cost_log() -> None:
    today = datetime(2026, 11, 26, tzinfo=TZ)
    prices = market_slots({"raw_today": _raw(today, [0.2] * 24), "raw_tomorrow": []})
    now = today + timedelta(hours=1, minutes=5)
    q0 = today.astimezone(UTC)
    history = {
        q0: {
            "market": 0.18,
            "buy": 0.31,
            "sell": 0.18,
            "charge_kwh": 0.6,
            "discharge_kwh": 0.0,
            "soc": 52.5,
            "solar_kwh": 0.0,
            "house_kwh": 0.1,
        },
        q0 + QUARTER: {
            "market": None,
            "buy": None,
            "sell": None,
            "charge_kwh": 0.0,
            "discharge_kwh": 0.2,
            "soc": 51.0,
            "solar_kwh": 0.3,
            "house_kwh": 0.5,
            "excluded_kwh": 0.2,
        },
        q0 + 5 * QUARTER: {"charge_kwh": 0.0, "discharge_kwh": 0.2, "soc": 40.0},  # not past yet: ignored
    }
    quarters = plan_quarters(None, prices, now, TZ, **_fns(), history=history)
    first, second, third = quarters[0], quarters[1], quarters[2]
    assert (first["action"], first["soc"], first["buy"], first["load"]) == ("charge", 52.5, 0.31, 0.1)
    assert second["action"] == "deliver" and second["soc"] == 51.0
    # The cost log's house includes the air conditioner; the panel gets them apart, like the planner (B41).
    assert (second["load"], second["excluded"]) == (0.3, 0.2)
    assert first["excluded"] is None
    assert second["market"] == pytest.approx(0.2) and second["buy"] == pytest.approx(0.32)  # price from the sensor
    assert third["action"] is None  # no record (HA was off)
    assert quarters[4]["past"] is False and quarters[5]["action"] is None


def test_future_quarters_carry_the_excluded_load() -> None:
    today = datetime(2026, 11, 26, tzinfo=TZ)
    now = today + timedelta(hours=12)
    prices = market_slots({"raw_today": _raw(today, [0.2] * 24), "raw_tomorrow": []})
    slots = build_horizon(
        horizon_markets(prices, now, TZ),
        now,
        buy=lambda t, m: m + 0.12,
        sell=lambda t, m, d: m,
        load=lambda t, a: 0.1,
        solar=lambda t: 0.3,
        daylight=lambda t: True,
        excluded=lambda t, a: 0.05,
    )
    outcome = make_plan(slots, BAT, now, PlannerSettings())
    quarters = plan_quarters(outcome, prices, now, TZ, **_fns())
    future = [q for q in quarters if not q["past"] and q["action"] is not None]
    assert future and all((q["solar"], q["load"], q["excluded"]) == (0.3, 0.1, 0.05) for q in future)
