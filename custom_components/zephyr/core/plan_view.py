"""The plan as the panel shows it (SPEC-ui §3.2): every quarter of today and tomorrow.

From local midnight today to the end of the plan's horizon: the price per
quarter (market, all-in buy and sell) and, from the running quarter on, the
planned action and the expected state of charge. Quarters before now show
what happened, from the cost log (UI-3): the action derived from the energy
that went in and out of the battery, the state of charge at the end, and the
prices as they were then.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Any

from .forecast_plan import ACTION_KEYS, QUARTER, PlanOutcome, quarter_floor
from .price_window import PriceSlot

BuyFn = Callable[[datetime, float], float]
SellFn = Callable[[datetime, float, bool], float]
DaylightFn = Callable[[datetime], bool]


MIN_KWH = 0.05
"""Less energy in or out of the battery in a quarter counts as holding (≈ 200 W)."""


def past_action(record: Mapping[str, Any]) -> str:
    """What the battery did in a closed cost quarter: charge, deliver, export or hold."""
    charged = float(record.get("charge_kwh") or 0.0)
    delivered = float(record.get("discharge_kwh") or 0.0)
    if charged >= MIN_KWH and charged >= delivered:
        return "charge"
    if delivered >= MIN_KWH:
        exported = float(record.get("export_kwh") or 0.0)
        return "export" if record.get("plan_action") == "X" and exported >= MIN_KWH else "deliver"
    return "hold"


def _price(prices: Sequence[PriceSlot], moment: datetime) -> float | None:
    for p in prices:
        if p.start <= moment < p.end:
            return p.price
    return None


def _priced(buy: BuyFn, t: datetime, market: float | None) -> float | None:
    return None if market is None else round(buy(t, market), 4)


def _priced_sell(sell: SellFn, daylight: DaylightFn, t: datetime, market: float | None) -> float | None:
    return None if market is None else round(sell(t, market, daylight(t)), 4)


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
    history: Mapping[datetime, Mapping[str, Any]] | None = None,
    curtail: bool = False,
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
                "excluded": round(slot.excluded_kwh, 3),
                "appliances": round(slot.appliance_kwh, 3),
                "indicative": slot.indicative,
                **_surplus(slot.sell, step.spill, curtail),
            }

    out: list[dict[str, Any]] = []
    t = start
    while t < end_utc:
        item: dict[str, Any] = {"start": t.isoformat(), "past": t < current}
        record = history.get(t) if history is not None and t < current else None
        if t in planned:
            item.update(planned[t])
        elif record is not None:
            market = record.get("market")
            item.update(
                {
                    "market": market,
                    "buy": record.get("buy") if record.get("buy") is not None else _priced(buy, t, market),
                    "sell": record.get("sell") if record.get("sell") is not None else _priced_sell(sell, daylight, t, market),
                    "action": past_action(record),
                    "soc": record.get("soc"),
                    "solar": record.get("solar_kwh"),
                    **_house(record),
                    "indicative": False,
                }
            )
            if item["market"] is None:
                found = _price(prices, t)
                item["market"] = None if found is None else round(found, 5)
                item["buy"] = _priced(buy, t, found)
                item["sell"] = _priced_sell(sell, daylight, t, found)
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
                    "excluded": None,
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
    history: Mapping[datetime, Mapping[str, Any]] | None = None,
    curtail_mode: str | None = None,
    curtail: bool = False,
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
        "curtail_mode": curtail_mode,
        "quarters": plan_quarters(outcome, prices, now, tz, buy=buy, sell=sell, daylight=daylight, history=history, curtail=curtail),
        "blocks": [] if outcome is None else [b.as_dict() for b in outcome.blocks],
    }


def _surplus(sell: float, spill: float, curtail: bool) -> dict[str, float]:
    """Solar surplus at a negative export price (B45): curtailed, or exported at a cost."""
    if sell >= 0 or spill <= 0:
        return {"curtail_kwh": 0.0, "export_cost": 0.0}
    if curtail:
        return {"curtail_kwh": round(spill, 3), "export_cost": 0.0}
    return {"curtail_kwh": 0.0, "export_cost": round(-sell * spill, 4)}


def _house(record: Mapping[str, Any]) -> dict[str, Any]:
    """House use without the air conditioner, and the air conditioner apart (B41), like the planner's quarters."""
    house = record.get("house_kwh")
    excluded = record.get("excluded_kwh")
    if house is None or not excluded:
        return {"load": house, "excluded": excluded}
    return {"load": round(max(0.0, house - excluded), 4), "excluded": excluded}
