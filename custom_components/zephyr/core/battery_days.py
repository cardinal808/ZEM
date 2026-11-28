"""Screen Accu: what the battery did per day (SPEC-ui §4.3, 0.8.71).

From the cost log's closed quarters: per local day the energy into the battery from the sun and the grid,
out of it to the house and the grid (the routes of :func:`stroom.split_quarter`), the lowest and highest
state of charge at a quarter's end, and the cycles (delivered ÷ usable capacity). Over the week also the
round-trip efficiency, with the change in stored energy taken into account, and the mean price of the
energy taken from the grid into the battery.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, timedelta, tzinfo
from typing import Any, Final

from .stroom import split_quarter

MIN_EFFICIENCY_KWH: Final = 2.0
"""Below this much energy in (after the change in storage) the efficiency says nothing."""


def _local_day(record: dict[str, Any], tz: tzinfo) -> date:
    return datetime.fromisoformat(record["start"]).astimezone(tz).date()


def battery_days(
    records: Iterable[dict[str, Any]],
    last: date,
    tz: tzinfo,
    usable_kwh: float | None,
    capacity_kwh: float | None,
    count: int = 7,
) -> dict[str, Any]:
    """Per day (oldest first, ``last`` = today) and the week; days without quarters have ``quarters`` 0."""
    first = last - timedelta(days=count - 1)
    days: dict[date, dict[str, Any]] = {
        first + timedelta(days=i): {
            "solar_battery": 0.0,
            "grid_battery": 0.0,
            "battery_house": 0.0,
            "battery_grid": 0.0,
            "soc_min": None,
            "soc_max": None,
            "quarters": 0,
        }
        for i in range(count)
    }
    priced_kwh = priced_cost = 0.0
    soc_first: float | None = None
    soc_last: float | None = None
    for record in sorted(records, key=lambda r: r["start"]):
        if record.get("source") == "hourly":
            continue  # worked out afterwards from hourly statistics: no quarters
        day = days.get(_local_day(record, tz))
        if day is None:
            continue
        split = split_quarter(record)
        for key in ("solar_battery", "grid_battery", "battery_house", "battery_grid"):
            day[key] += split[key]
        day["quarters"] += 1
        buy = record.get("buy")
        if isinstance(buy, int | float) and split["grid_battery"] > 0:
            priced_kwh += split["grid_battery"]
            priced_cost += split["grid_battery"] * buy
        soc = record.get("soc")
        if isinstance(soc, int | float):
            day["soc_min"] = soc if day["soc_min"] is None else min(day["soc_min"], soc)
            day["soc_max"] = soc if day["soc_max"] is None else max(day["soc_max"], soc)
            if soc_first is None:
                soc_first = float(soc)
            soc_last = float(soc)

    def r(value: float) -> float:
        return round(value, 2)

    def cycles(delivered: float) -> float | None:
        return None if not usable_kwh or usable_kwh <= 0 else round(delivered / usable_kwh, 2)

    out_days: list[dict[str, Any]] = []
    solar = grid = delivered = 0.0
    for day_date, d in days.items():
        out = d["battery_house"] + d["battery_grid"]
        solar += d["solar_battery"]
        grid += d["grid_battery"]
        delivered += out
        out_days.append(
            {
                "date": day_date.isoformat(),
                "solar_battery": r(d["solar_battery"]),
                "grid_battery": r(d["grid_battery"]),
                "battery_house": r(d["battery_house"]),
                "battery_grid": r(d["battery_grid"]),
                "soc_min": d["soc_min"],
                "soc_max": d["soc_max"],
                "cycles": cycles(out) if d["quarters"] else None,
                "quarters": d["quarters"],
            }
        )
    charged = solar + grid
    efficiency: float | None = None
    if capacity_kwh and soc_first is not None and soc_last is not None:
        # What went in minus what stayed in the battery came out again (or was lost).
        stored = (soc_last - soc_first) / 100 * capacity_kwh
        used_in = charged - stored
        if used_in >= MIN_EFFICIENCY_KWH and delivered > 0:
            value = delivered / used_in
            efficiency = round(value, 3) if 0.5 <= value <= 0.98 else None  # outside: a gap in the log
    return {
        "days": out_days,
        "week": {
            "solar_battery": r(solar),
            "grid_battery": r(grid),
            "charged": r(charged),
            "delivered": r(delivered),
            "cycles": cycles(delivered),
            "efficiency": efficiency,
            "grid_price": None if priced_kwh < 0.01 else round(priced_cost / priced_kwh, 4),
        },
        "usable_kwh": None if usable_kwh is None else r(usable_kwh),
    }
