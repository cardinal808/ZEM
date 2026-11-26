"""The plan as the panel shows it (SPEC-ui §3.2): every quarter of today and tomorrow.

From local midnight today to the end of the plan's horizon: the price per
quarter (market, all-in buy and sell) and, from the running quarter on, the
planned action and the expected state of charge. Quarters before now carry
only the price (the cost log fills in what happened, UI-3).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Any

from .forecast_plan import ACTION_KEYS, QUARTER, PlanOutcome, quarter_floor
from .price_window import PriceSlot

BuyFn = Callable[[datetime, float], float]
SellFn = Callable[[datetime, float, bool], float]
DaylightFn = Callable[[datetime], bool]


def _price(prices: Sequence[PriceSlot], moment: datetime) -> float | None:
    for p in prices:
        if p.start <= moment < p.end:
            return p.price
    return None


def local_midnight(now: datetime, tz: tzinfo, days: int = 0) -> datetime:
    """Start of today (plus ``days``) in ``tz``, as UTC. Correct on DST days (zoneinfo)."""
    day = now.astimezone(tz).date() + timedelta(days=days)
    return datetime(day.year, day.month, day.day, tzinfo=tz).astimezone(UTC)


def plan_quarters(
    outcome: PlanOutcome | None,
    prices: Sequence[PriceSlot],
    now: datetime,
    tz: tzinfo,
    *,
    buy: BuyFn,
    sell: SellFn,
    daylight: DaylightFn,
) -> list[dict[str, Any]]:
    """Quarters from midnight today to the end of tomorrow (local), in UTC steps (DST: 92 or 100 per day)."""
    start = local_midnight(now, tz)
    end_utc = local_midnight(now, tz, 2)
    current = quarter_floor(now.astimezone(UTC))

    planned: dict[datetime, dict[str, Any]] = {}
    if outcome is not None and outcome.slots:
        bat = outcome.battery
        for slot, action, step in zip(outcome.slots, outcome.plan.actions, outcome.plan.steps, strict=False):
            soc = None
            if bat is not None and bat.capacity_kwh > 0:
                soc = round(bat.floor + step.energy_after / bat.capacity_kwh * 100, 1)
            planned[slot.start.astimezone(UTC)] = {
                "market": round(slot.market, 5),
                "buy": round(slot.buy, 4),
                "sell": round(slot.sell, 4),
                "action": ACTION_KEYS[action],
                "soc": soc,
                "solar": round(slot.solar_kwh, 3),
                "load": round(slot.load_kwh, 3),
                "indicative": slot.indicative,
            }

    out: list[dict[str, Any]] = []
    t = start
    while t < end_utc:
        item: dict[str, Any] = {"start": t.isoformat(), "past": t < current}
        if t in planned:
            item.update(planned[t])
        else:
            market = _price(prices, t)
            item.update(
                {
                    "market": None if market is None else round(market, 5),
                    "buy": None if market is None else round(buy(t, market), 4),
                    "sell": None if market is None else round(sell(t, market, daylight(t)), 4),
                    "action": None,
                    "soc": None,
                    "solar": None,
                    "load": None,
                    "indicative": False,
                }
            )
        out.append(item)
        t += QUARTER
    return out


def plan_view(
    outcome: PlanOutcome | None,
    prices: Sequence[PriceSlot],
    now: datetime,
    tz: tzinfo,
    *,
    buy: BuyFn,
    sell: SellFn,
    daylight: DaylightFn,
    tomorrow_known_at: datetime | None,
    reason: dict[str, str] | None,
) -> dict[str, Any]:
    """Everything the chart *Prijzen en plan* and the cards *Blokken* and *Waarom* need."""
    bat = outcome.battery if outcome is not None else None
    return {
        "now": now.astimezone(UTC).isoformat(),
        "state": None if outcome is None else str(outcome.state),
        "calculated_at": None if outcome is None else outcome.calculated_at.astimezone(UTC).isoformat(),
        "reason": reason,
        "soc_now": None if bat is None else round(bat.soc, 1),
        "tomorrow_known_at": None if tomorrow_known_at is None else tomorrow_known_at.astimezone(UTC).isoformat(),
        "quarters": plan_quarters(outcome, prices, now, tz, buy=buy, sell=sell, daylight=daylight),
        "blocks": [] if outcome is None else [b.as_dict() for b in outcome.blocks],
    }
