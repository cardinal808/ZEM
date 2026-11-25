"""Deliver in the most expensive hours, reserve charging (PLAN-M4b §2.6)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from conftest import load_fixture
from zephyr_core.engine import Reason, ReasonCode, SetView, ZephyrEngine
from zephyr_core.price_window import decide, expensive_slots, parse_nordpool_raw
from zephyr_core.zensdk import parse_report

TZ = timezone(timedelta(hours=1))
DAY = datetime(2026, 11, 25, tzinfo=TZ)
# Hourly prices: cheap night, evening peak 17-21.
PRICES = [0.05, 0.04, 0.03, 0.02, 0.03, 0.05, 0.10, 0.15, 0.14, 0.12, 0.10, 0.09,
          0.08, 0.09, 0.11, 0.14, 0.20, 0.30, 0.35, 0.33, 0.28, 0.18, 0.12, 0.08]  # fmt: skip


def _raw(prices: list[float] = PRICES, step: int = 60) -> list[dict[str, object]]:
    return [
        {"start": DAY + timedelta(minutes=i * step), "end": DAY + timedelta(minutes=(i + 1) * step), "value": p}
        for i, p in enumerate(prices)
    ]


def test_parse_accepts_iso_strings_and_skips_junk() -> None:
    raw = [{"start": "2026-11-25T00:00:00+01:00", "end": "2026-11-25T01:00:00+01:00", "value": 0.1}, {"start": None}, "x"]
    slots = parse_nordpool_raw(raw)
    assert len(slots) == 1 and slots[0].price == 0.1


def test_top_n_hours_hourly_and_quarterly() -> None:
    hourly = expensive_slots(parse_nordpool_raw(_raw()), 4)
    assert sorted(t.hour for t in hourly) == [17, 18, 19, 20]
    quarters = [p for p in PRICES for _ in range(4)]
    q = expensive_slots(parse_nordpool_raw(_raw(quarters, 15)), 4)
    assert len(q) == 16 and {t.hour for t in q} == {17, 18, 19, 20}


def test_expensive_now_and_min_price() -> None:
    slots = parse_nordpool_raw(_raw())
    assert decide(slots, DAY.replace(hour=18, minute=30), hours=4).expensive
    assert not decide(slots, DAY.replace(hour=12), hours=4).expensive
    assert not decide(slots, DAY.replace(hour=20, minute=5), hours=4, min_price=0.30).expensive


def test_no_prices_for_now() -> None:
    d = decide(parse_nordpool_raw(_raw()), DAY + timedelta(days=2), hours=4)
    assert not d.have_prices and not d.expensive


def test_reserve_charges_in_the_cheapest_hours_before_the_peak() -> None:
    slots = parse_nordpool_raw(_raw())
    # 10 % of 11 kWh = 1.1 kWh at 2.4 kW x 0.9: one hour; the cheapest before 17:00 is 03:00.
    kwargs = {"hours": 4, "soc": 10.0, "reserve_soc": 20.0, "capacity_kwh": 11.0, "charge_kw": 2.4}
    at_three = decide(slots, DAY.replace(hour=3, minute=10), **kwargs)
    assert at_three.reserve_charge and [t.hour for t in at_three.reserve_slots] == [3]
    assert not decide(slots, DAY.replace(hour=1), **kwargs).reserve_charge
    # Above the reserve: nothing; in an expensive hour: never charge, the reserve may be used.
    assert not decide(slots, DAY.replace(hour=3), **{**kwargs, "soc": 25.0}).reserve_charge
    assert not decide(slots, DAY.replace(hour=18), **kwargs).reserve_charge


def _view(soc: int) -> SetView:
    data = load_fixture("deliver_760")
    data = {
        **data,
        "properties": {**data["properties"], "electricLevel": soc},
        "packData": [{**p, "socLevel": soc} for p in data["packData"]],
    }
    return SetView("a", 1, parse_report(data), True)


def test_engine_price_block_stops_delivering_with_reason() -> None:
    e = ZephyrEngine()
    block = Reason(ReasonCode.NOT_EXPENSIVE, {"next": "17:00"})
    r = None
    for t in range(0, 30, 2):
        e.p1_reported(t, 400.0 + t)
        r = e.step(t, [_view(60)], price_block=block)
    assert r is not None and r.setpoint == 0 and r.reason.code is ReasonCode.NOT_EXPENSIVE


def test_engine_reserve_charge_until_reserve() -> None:
    e = ZephyrEngine()
    e.p1_reported(0, 200.0)
    r = e.step(0, [_view(12)], reserve_charge=(2400, 20.0))
    assert r.setpoint == 2400 and r.reason.code is ReasonCode.RESERVE_CHARGE
    e.p1_reported(2, 2600.0)
    r = e.step(2, [_view(21)], reserve_charge=(2400, 20.0))
    assert r.reason.code is not ReasonCode.RESERVE_CHARGE
