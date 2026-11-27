"""Correction of closed cost quarters after a counter gap was filled (SPEC-tellers T3, §6.3).

The own energy counters fill a gap when the set reports again; by then the quarters of the
gap are closed. The filled energy is spread over those quarters by time, and the cost log is
evaluated again from the first corrected quarter up to now, because the pools (solar or grid
in the battery) of every later quarter depend on it. Each quarter keeps the inputs needed for
that (``pools`` before the quarter, ``stored_kwh``, ``daylight``, ``coverage``); quarters
without them cannot be corrected.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta, tzinfo
from typing import Any, Final

from .costs import Pools, QuarterInput, Tariffs, add_to_day, evaluate

QUARTER: Final = timedelta(minutes=15)
MAX_AGE: Final = timedelta(hours=48)
"""Gaps that started longer ago are only filled in the counters, not in the cost log."""
KEEP_FROM_OLD: Final = ("plan_action", "plan_cost")
"""Fields of the stored quarter that a new evaluation must not overwrite."""


def gap_shares(start: datetime, end: datetime) -> dict[datetime, float]:
    """Share of a gap per quarter (by quarter start, UTC): the overlap ÷ the gap length."""
    total = (end - start).total_seconds()
    if total <= 0:
        return {}
    out: dict[datetime, float] = {}
    quarter = start.replace(minute=start.minute - start.minute % 15, second=0, microsecond=0)
    while quarter < end:
        overlap = (min(end, quarter + QUARTER) - max(start, quarter)).total_seconds()
        if overlap > 0:
            out[quarter] = overlap / total
        quarter += QUARTER
    return out


def _input(record: Mapping[str, Any], extra: Mapping[str, float]) -> QuarterInput | None:
    """The evaluation input of a stored quarter plus the corrected energy; None if fields are missing."""
    if "pools" not in record or "daylight" not in record or "coverage" not in record:
        return None
    solar = record.get("solar_kwh")
    return QuarterInput(
        start=datetime.fromisoformat(record["start"]),
        minutes=float(record["minutes"]),
        import_kwh=float(record["import_kwh"]),
        export_kwh=float(record["export_kwh"]),
        charge_kwh=float(record["charge_kwh"]) + extra.get("charged", 0.0),
        discharge_kwh=float(record["discharge_kwh"]) + extra.get("discharged", 0.0),
        solar_kwh=None if solar is None else float(solar) + extra.get("solar", 0.0),
        market=record.get("market"),
        coverage=float(record["coverage"]),
        stored_kwh=record.get("stored_kwh"),
        daylight=bool(record["daylight"]),
    )


def reevaluate(
    records: list[dict[str, Any]],
    corrections: Mapping[str, Mapping[str, float]],
    tariffs_for: Callable[[date], Tariffs],
    days_in_month: Callable[[date], int],
    tz: tzinfo,
    corrected_at: str,
) -> tuple[Pools, list[tuple[dict[str, Any], dict[str, Any]]]] | None:
    """Evaluate ``records`` again from the first corrected quarter; changes them in place.

    ``corrections``: extra kWh per quarter start (ISO) for ``charged``, ``discharged``,
    ``solar``. Returns the pools after the last quarter and the (old, new) pairs, or None
    when nothing could be corrected (no such quarter, or inputs missing).
    """
    first = next((i for i, r in enumerate(records) if r.get("start") in corrections), None)
    if first is None or "pools" not in records[first]:
        return None
    pools = Pools.from_dict(records[first]["pools"])
    changes: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for index in range(first, len(records)):
        old = records[index]
        extra = corrections.get(old["start"], {})
        q = _input(old, extra)
        if q is None:
            return None
        local = q.start.astimezone(tz).date()
        before = pools.as_dict()
        fresh = evaluate(q, tariffs_for(local), pools, days_in_month(local))
        new = {**old, **{k: v for k, v in fresh.items() if k not in KEEP_FROM_OLD}, "pools": before}
        if extra:
            new["estimated"] = True
            new["corrected_at"] = corrected_at
        records[index] = new
        changes.append((old, new))
    return pools, changes


def day_delta(day: dict[str, Any], old: Mapping[str, Any], new: Mapping[str, Any]) -> None:
    """Replace a quarter's contribution to a day total: + new − old (numeric fields)."""
    before: dict[str, Any] = {}
    after: dict[str, Any] = {}
    add_to_day(before, old)
    add_to_day(after, new)
    for key in set(before) | set(after):
        b, a = before.get(key, 0), after.get(key, 0)
        if isinstance(a, bool) or isinstance(b, bool) or not isinstance(a, int | float) or not isinstance(b, int | float):
            continue
        if a != b:
            day[key] = round(day.get(key, 0) + a - b, 5)
