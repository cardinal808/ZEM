"""Deliver only in the most expensive hours, with a reserve (PLAN-M4b §2.6, L6).

A simple forerunner of the planner (M5) for zero-meter control:

* **Expensive hours:** per day the N most expensive hours (in the resolution of
  the prices: quarters count as N × 4 slots). Delivering is allowed only then,
  and optionally only above a minimum price. A ranking, not a threshold: taxes,
  margins and VAT do not change the order, and nothing needs adjusting per season.
* **Reserve (soft, like the buffer of B37):** below the reserve SOC the battery is
  charged from the grid in the cheapest slots before the next expensive block,
  just enough to reach the reserve. In the expensive hours the reserve may be used
  down to the minimum SOC; it never stops delivering.

Pure functions on price slots; the caller reads the Nord Pool sensor.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class PriceSlot:
    start: datetime
    end: datetime
    price: float
    """Bare market price (€/kWh); only the order matters."""

    @property
    def hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600


@dataclass(frozen=True, slots=True)
class PriceDecision:
    have_prices: bool
    expensive: bool
    """Delivering is allowed now."""
    reserve_charge: bool
    """Charge from the grid now to reach the reserve."""
    slot: PriceSlot | None
    next_expensive: datetime | None
    reserve_slots: tuple[datetime, ...]
    """Start times of the slots chosen to charge for the reserve."""

    def as_dict(self) -> dict[str, Any]:
        return {
            "have_prices": self.have_prices,
            "expensive": self.expensive,
            "reserve_charge": self.reserve_charge,
            "price_now": None if self.slot is None else self.slot.price,
            "next_expensive": None if self.next_expensive is None else self.next_expensive.isoformat(),
            "reserve_slots": [t.isoformat() for t in self.reserve_slots],
        }


NO_PRICES = PriceDecision(False, False, False, None, None, ())


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
    return None


def parse_nordpool_raw(items: Iterable[Any] | None) -> list[PriceSlot]:
    """``raw_today`` / ``raw_tomorrow`` of the Nord Pool custom integration: ``{start, end, value}``."""
    slots: list[PriceSlot] = []
    for item in items or ():
        if not isinstance(item, Mapping):
            continue
        start, end, value = _as_datetime(item.get("start")), _as_datetime(item.get("end")), item.get("value")
        if start is None or end is None or end <= start or not isinstance(value, (int, float)) or isinstance(value, bool):
            continue
        slots.append(PriceSlot(start, end, float(value)))
    return sorted(slots, key=lambda s: s.start)


def _day(slot: PriceSlot) -> date:
    return slot.start.date()


def expensive_slots(slots: Sequence[PriceSlot], hours: int) -> set[datetime]:
    """Start times of the N most expensive hours of every day in ``slots``."""
    by_day: dict[date, list[PriceSlot]] = {}
    for s in slots:
        by_day.setdefault(_day(s), []).append(s)
    chosen: set[datetime] = set()
    for day_slots in by_day.values():
        slot_hours = min(s.hours for s in day_slots)
        count = round(hours / slot_hours) if slot_hours > 0 else 0
        ranked = sorted(day_slots, key=lambda s: (-s.price, s.start))
        chosen.update(s.start for s in ranked[:count])
    return chosen


def decide(
    slots: Sequence[PriceSlot],
    now: datetime,
    *,
    hours: int,
    min_price: float | None = None,
    soc: float | None = None,
    reserve_soc: float = 0.0,
    capacity_kwh: float = 0.0,
    charge_kw: float = 0.0,
    efficiency: float = 0.9,
) -> PriceDecision:
    current = next((s for s in slots if s.start <= now < s.end), None)
    if current is None:
        return NO_PRICES
    expensive_set = expensive_slots(slots, hours)
    expensive = current.start in expensive_set and (min_price is None or current.price >= min_price)
    upcoming = [s for s in slots if s.start >= current.start]
    next_expensive = next((s.start for s in upcoming if s.start in expensive_set and s.start > current.start), None)

    reserve: tuple[datetime, ...] = ()
    charge_now = False
    if soc is not None and soc < reserve_soc and capacity_kwh > 0 and charge_kw > 0 and not expensive:
        deficit_kwh = (reserve_soc - soc) / 100 * capacity_kwh
        needed_hours = deficit_kwh / (charge_kw * efficiency)
        window = [s for s in upcoming if s.start not in expensive_set and (next_expensive is None or s.start < next_expensive)]
        if window:
            slot_hours = min(s.hours for s in window)
            count = max(1, math.ceil(needed_hours / slot_hours - 1e-9))
            cheapest = sorted(window, key=lambda s: (s.price, s.start))[:count]
            reserve = tuple(sorted(s.start for s in cheapest))
            charge_now = current.start in reserve
    return PriceDecision(True, expensive, charge_now, current, next_expensive, reserve)
