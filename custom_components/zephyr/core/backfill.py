"""Savings for days before the cost log, worked out again from hourly statistics (Bjorn, 26-11: choice 2).

The cost log (B38) counts per quarter from the moment ZEPHYR runs. For the days
before, Home Assistant still has hourly statistics of the meters: grid import
and export, solar, the battery's charge and discharge counters and the price.
Every hour goes through the same ``evaluate`` as a quarter (60 minutes), so the
screen *Besparing* uses one method for every day. Less precise than quarters:
import and export within one hour cancel each other out in the comparison
without the battery.

Pure, no Home Assistant.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date, datetime, tzinfo
from typing import Any, Final

from .costs import Pools, QuarterInput, Tariffs, add_to_day, evaluate

SOURCE_HOURLY: Final = "hourly"
"""Marks a day total that was worked out from hourly statistics."""

QUARTERS_PER_HOUR: Final = 4


@dataclass(frozen=True, slots=True)
class HourInput:
    start: datetime
    """Start of the hour (aware)."""
    import_kwh: float | None
    export_kwh: float | None
    charge_kwh: float | None
    discharge_kwh: float | None
    solar_kwh: float | None
    market: float | None
    """Mean market price of the hour (€/kWh)."""


@dataclass(slots=True)
class BackfillResult:
    days: dict[str, dict[str, Any]]
    hours: int
    """Hours that were counted."""
    skipped: int
    """Hours without grid or battery data (not counted; the day is then marked incomplete)."""


def backfill_days(
    hours: Iterable[HourInput],
    tariffs_for: Callable[[date], Tariffs],
    tz: tzinfo,
) -> BackfillResult:
    """Day totals (local dates) in the form of the cost log, marked as hourly."""
    pools = Pools()
    days: dict[str, dict[str, Any]] = {}
    counted = skipped = 0
    for hour in sorted(hours, key=lambda h: h.start):
        local = hour.start.astimezone(tz)
        key = local.date().isoformat()
        day = days.setdefault(key, {"source": SOURCE_HOURLY, "hours": 0, "missing_hours": 0})
        values = (hour.import_kwh, hour.export_kwh, hour.charge_kwh, hour.discharge_kwh)
        if any(v is None for v in values):
            skipped += 1
            day["missing_hours"] += 1
            continue
        imp, exp, chg, dis = (max(float(v or 0.0), 0.0) for v in values)
        record = evaluate(
            QuarterInput(
                start=hour.start,
                minutes=60,
                import_kwh=imp,
                export_kwh=exp,
                charge_kwh=chg,
                discharge_kwh=dis,
                solar_kwh=hour.solar_kwh,
                market=hour.market,
                # Without sun times: an hour with solar counts as daylight (for a solar bonus).
                daylight=(hour.solar_kwh or 0.0) > 0.01,
            ),
            tariffs_for(local.date()),
            pools,
        )
        add_to_day(day, record)
        day["hours"] += 1
        counted += 1
    for day in days.values():
        # The cost log counts quarters; an hour stands for four.
        day["quarters"] = day["hours"] * QUARTERS_PER_HOUR
        if day["missing_hours"]:
            day["incomplete"] = day.get("incomplete", 0) + day["missing_hours"] * QUARTERS_PER_HOUR
        # Counts are per quarter; the summed buy price too (mean buy price = buy / priced).
        for name in ("priced", "no_price", "solar_priced", "no_solar", "buy"):
            if name in day:
                day[name] *= QUARTERS_PER_HOUR
    return BackfillResult({k: v for k, v in days.items() if v["hours"]}, counted, skipped)


def series_to_hours(
    starts: Iterable[datetime],
    series: dict[str, dict[datetime, float]],
    import_ids: list[str],
    export_ids: list[str],
    charge: Callable[[datetime], float | None],
    discharge: Callable[[datetime], float | None],
    solar_id: str | None,
    price_id: str | None,
) -> list[HourInput]:
    """Hours from statistics per entity (hour start → change or mean). A missing counter makes the value unknown."""

    def total(ids: list[str], t: datetime) -> float | None:
        values = [series.get(i, {}).get(t) for i in ids]
        return None if not ids or any(v is None for v in values) else sum(v for v in values if v is not None)

    out = []
    for t in starts:
        out.append(
            HourInput(
                start=t,
                import_kwh=total(import_ids, t),
                export_kwh=total(export_ids, t),
                charge_kwh=charge(t),
                discharge_kwh=discharge(t),
                solar_kwh=series.get(solar_id, {}).get(t) if solar_id else None,
                market=series.get(price_id, {}).get(t) if price_id else None,
            )
        )
    return out
