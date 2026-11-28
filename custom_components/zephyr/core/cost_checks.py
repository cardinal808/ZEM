"""Checks on the cost log for the diagnostics (TOETS-besparing voorstel 4 and 6).

* **Energy balance per day:** charged × η_in − delivered ÷ η_out should match the change of the
  energy in the battery (ΔSOC × capacity). A large difference points at energy the cost log
  missed or counted twice.
* **Price check:** the mean of the four quarter prices of an hour should match EnergyZero's hour
  price (bare market price, TOETS-besparing bevinding 6). A large difference points at a wrong
  slot, as on 25-11 23:45.

Pure Python.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, tzinfo
from typing import Any, Final

BALANCE_WARN_SHARE: Final = 0.10
"""Difference above this share of the day's throughput is flagged ..."""
BALANCE_WARN_KWH: Final = 0.3
"""... and above this many kWh (small days are noisy)."""
PRICE_WARN_EUR: Final = 0.03
PRICE_WARN_SHARE: Final = 0.25
"""The hour's mean differs from EnergyZero by more than both ..."""
QUARTER_WARN_EUR: Final = 0.05
QUARTER_WARN_SHARE: Final = 0.50
"""... or one quarter by more than both (quarters vary within an hour, a wrong slot more)."""


def energy_balance(
    records: Iterable[Mapping[str, Any]], capacity_kwh: float | None, eta_in: float, eta_out: float, tz: tzinfo
) -> list[dict[str, Any]]:
    """Per local day: expected and measured change of the battery's energy, and a flag."""
    days: dict[str, dict[str, Any]] = {}
    last_soc: float | None = None
    for record in records:
        day = datetime.fromisoformat(record["start"]).astimezone(tz).date().isoformat()
        box = days.setdefault(day, {"day": day, "charged": 0.0, "delivered": 0.0, "soc_start": last_soc, "soc_end": None})
        box["charged"] += float(record.get("charge_kwh") or 0.0)
        box["delivered"] += float(record.get("discharge_kwh") or 0.0)
        soc = record.get("soc")
        if soc is not None:
            if box["soc_start"] is None:
                box["soc_start"] = float(soc)  # first known value of the day (no previous day)
            box["soc_end"] = float(soc)
            last_soc = float(soc)
    out = []
    for box in days.values():
        expected = box["charged"] * eta_in - box["delivered"] / eta_out
        measured = None
        if capacity_kwh and box["soc_start"] is not None and box["soc_end"] is not None:
            measured = (box["soc_end"] - box["soc_start"]) / 100 * capacity_kwh
        diff = None if measured is None else expected - measured
        throughput = box["charged"] + box["delivered"]
        flag = diff is not None and abs(diff) > BALANCE_WARN_KWH and abs(diff) > BALANCE_WARN_SHARE * max(throughput, 0.1)
        out.append(
            {
                "day": box["day"],
                "charged_kwh": round(box["charged"], 3),
                "delivered_kwh": round(box["delivered"], 3),
                "expected_change_kwh": round(expected, 3),
                "soc_change_kwh": None if measured is None else round(measured, 3),
                "difference_kwh": None if diff is None else round(diff, 3),
                "suspect": flag,
            }
        )
    return out


def price_check(records: Iterable[Mapping[str, Any]], hourly: Mapping[datetime, float]) -> list[dict[str, Any]]:
    """Hours whose quarter prices differ clearly from EnergyZero's hour price."""
    hours: dict[datetime, list[float]] = {}
    for record in records:
        market = record.get("market")
        if market is None or record.get("price_source") == "interpolated":
            continue
        start = datetime.fromisoformat(record["start"])
        hours.setdefault(start.replace(minute=0, second=0, microsecond=0), []).append(float(market))
    out = []
    for hour, prices in sorted(hours.items()):
        reference = hourly.get(hour)
        if reference is None:
            continue
        mean = sum(prices) / len(prices)
        diff = mean - reference
        odd = [p for p in prices if abs(p - reference) > QUARTER_WARN_EUR and abs(p - reference) > QUARTER_WARN_SHARE * abs(reference)]
        if (abs(diff) > PRICE_WARN_EUR and abs(diff) > PRICE_WARN_SHARE * abs(reference)) or odd:
            out.append(
                {"hour": hour.isoformat(), "quarters": round(mean, 5), "energyzero": round(reference, 5), "difference": round(diff, 5)}
            )
    return out
