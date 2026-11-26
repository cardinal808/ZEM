"""Plan against reality (B38): what the day-ahead plan expected next to what happened.

The planner keeps, per quarter of tomorrow, what its plan expects (use without the excluded
load, solar, grid import and export, cost, SOC at the end of the quarter). Every new plan
overwrites tomorrow's expectations; at midnight the day starts and they are fixed: the
plan as it stood at the end of the day before. The cost log stores them with each quarter
(``ahead_*``) and adds them, with the matching measured values, to the day totals, so a
day can be compared over the same quarters.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, date, tzinfo
from typing import Any, Final

from .forecast_plan import PlanOutcome

AHEAD_KEYS: Final = ("load", "excluded", "solar", "import", "export", "cost", "soc")
"""Expected values per quarter; ``soc`` in %, ``cost`` in € (grid only, no wear), the rest kWh."""

DAY_PAIRS: Final = (
    ("ahead_load_kwh", "ahead_actual_load_kwh"),
    ("ahead_solar_kwh", "ahead_actual_solar_kwh"),
    ("ahead_import_kwh", "ahead_actual_import_kwh"),
    ("ahead_export_kwh", "ahead_actual_export_kwh"),
    ("ahead_cost", "ahead_actual_cost"),
)
"""Day-total fields: expected and measured, over the quarters that have both."""

ABS_FIELDS: Final = ("ahead_load_abs_err", "ahead_solar_abs_err")


def expectations(outcome: PlanOutcome, day: date, tz: tzinfo) -> dict[str, dict[str, float]]:
    """Expected values per quarter (UTC ISO start) of local ``day``; indicative slots left out."""
    bat = outcome.battery
    out: dict[str, dict[str, float]] = {}
    for slot, step in zip(outcome.slots, outcome.plan.steps, strict=False):
        if slot.indicative or slot.start.astimezone(tz).date() != day:
            continue
        item = {
            "load": round(slot.load_kwh, 3),
            "excluded": round(slot.excluded_kwh, 3),
            "solar": round(slot.solar_kwh, 3),
            "import": round(step.grid_import, 3),
            "export": round(step.grid_export, 3),
            "cost": round(step.cost, 5),
        }
        if bat is not None and bat.capacity_kwh > 0:
            item["soc"] = round(bat.floor + step.energy_after / bat.capacity_kwh * 100, 1)
        out[slot.start.astimezone(UTC).isoformat()] = item
    return out


def record_fields(expected: Mapping[str, float] | None) -> dict[str, Any]:
    """Fields for a cost-log quarter from its expectation (empty without one)."""
    if not expected:
        return {}
    fields: dict[str, Any] = {f"ahead_{key}": expected[key] for key in ("cost", "soc") if key in expected}
    for key in ("load", "excluded", "solar", "import", "export"):
        if key in expected:
            fields[f"ahead_{key}_kwh"] = expected[key]
    return fields


def add_to_day(day: dict[str, float], record: Mapping[str, Any]) -> None:
    """Add a quarter's expectation and the matching measured values to a day total.

    Only quarters with an expectation count; measured load = house without the excluded
    load (as the planner plans it); solar and cost only when they were measured.
    """
    if record.get("ahead_load_kwh") is None:
        return
    day["ahead_quarters"] = day.get("ahead_quarters", 0) + 1
    house = record.get("house_kwh")
    if house is not None:
        actual = float(house) - float(record.get("excluded_kwh") or 0.0)
        expected = float(record["ahead_load_kwh"])
        _add(day, "ahead_load_kwh", expected)
        _add(day, "ahead_actual_load_kwh", actual)
        _add(day, "ahead_load_abs_err", abs(actual - expected))
    if record.get("solar_kwh") is not None and record.get("ahead_solar_kwh") is not None:
        actual, expected = float(record["solar_kwh"]), float(record["ahead_solar_kwh"])
        _add(day, "ahead_solar_kwh", expected)
        _add(day, "ahead_actual_solar_kwh", actual)
        _add(day, "ahead_solar_abs_err", abs(actual - expected))
    for key in ("import", "export"):
        if record.get(f"ahead_{key}_kwh") is not None:
            _add(day, f"ahead_{key}_kwh", float(record[f"ahead_{key}_kwh"]))
            _add(day, f"ahead_actual_{key}_kwh", float(record.get(f"{key}_kwh") or 0.0))
    if record.get("cost") is not None and record.get("ahead_cost") is not None:
        _add(day, "ahead_cost", float(record["ahead_cost"]))
        _add(day, "ahead_actual_cost", float(record["cost"]))
    if record.get("ahead_soc") is not None:
        day["ahead_soc_end"] = float(record["ahead_soc"])
        if record.get("soc") is not None:
            day["ahead_actual_soc_end"] = float(record["soc"])


def _add(day: dict[str, float], key: str, value: float) -> None:
    day[key] = round(day.get(key, 0.0) + value, 5)


def day_check(day: str, total: Mapping[str, Any]) -> dict[str, Any] | None:
    """Plan against reality for one day total (None when the day had no expectations)."""
    if not total.get("ahead_quarters"):
        return None
    out: dict[str, Any] = {"date": day, "quarters": int(total["ahead_quarters"]), "of": int(total.get("quarters", 0))}
    for expected_key, actual_key in DAY_PAIRS:
        name = expected_key.removeprefix("ahead_").removesuffix("_kwh")
        if expected_key in total:
            expected, actual = float(total[expected_key]), float(total.get(actual_key, 0.0))
            out[name] = {"expected": round(expected, 3), "actual": round(actual, 3), "diff": round(actual - expected, 3)}
    for key in ABS_FIELDS:
        if key in total:
            out[key.removeprefix("ahead_")] = round(float(total[key]), 3)
    if "ahead_soc_end" in total:
        out["soc_end"] = {"expected": total["ahead_soc_end"], "actual": total.get("ahead_actual_soc_end")}
    return out


def checks(days: Mapping[str, Mapping[str, Any]], first: date, last: date) -> list[dict[str, Any]]:
    """Plan against reality per day from ``first`` to ``last`` (days without expectations left out)."""
    out = []
    for key in sorted(days):
        if first.isoformat() <= key <= last.isoformat():
            item = day_check(key, days[key])
            if item is not None:
                out.append(item)
    return out


def summary(items: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Totals over several days: expected, actual and mean absolute error per day."""
    out: dict[str, Any] = {"days": len(items)}
    for name in ("load", "solar", "import", "export", "cost"):
        rows = [i[name] for i in items if name in i]
        if rows:
            expected = sum(r["expected"] for r in rows)
            actual = sum(r["actual"] for r in rows)
            out[name] = {
                "expected": round(expected, 3),
                "actual": round(actual, 3),
                "diff": round(actual - expected, 3),
                "mean_abs_day": round(sum(abs(r["diff"]) for r in rows) / len(rows), 3),
            }
    return out
