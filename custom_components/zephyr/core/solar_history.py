"""Daily solar forecast next to the real production (B31, B32).

Each evening ZEPHYR stores the forecast for the next day (half-hour values,
with the lower and upper estimate when the source gives them). Every hour it
stores the production counter, from which the production per hour follows.
Over weeks this is the yardstick for learning the forecast's bias per hour and
its spread (``SPEC-planner.md`` §12.4); the data cannot be recovered later,
so it starts before the planner needs it.

Pure Python: the Home Assistant side passes states in and stores the dict.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Any

KEEP_DAYS = 400


@dataclass(frozen=True, slots=True)
class ForecastPeriod:
    start: str
    """ISO time with offset."""
    estimate: float
    """Mean power in kW over the period."""
    estimate10: float | None
    estimate90: float | None


def _num(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def parse_detailed_forecast(items: Any) -> list[ForecastPeriod]:
    """Solcast ``detailedForecast`` / ``detailedHourly``: period_start, pv_estimate (kW), pv_estimate10, pv_estimate90.

    ``period_start`` may be a datetime (live state attribute) or an ISO string.
    Entries that cannot be read are skipped.
    """
    if not isinstance(items, Iterable) or isinstance(items, (str, bytes, Mapping)):
        return []
    out: list[ForecastPeriod] = []
    for item in items:
        if not isinstance(item, Mapping):
            continue
        start = item.get("period_start")
        if isinstance(start, dt.datetime):
            start = start.isoformat()
        estimate = _num(item.get("pv_estimate"))
        if not isinstance(start, str) or estimate is None:
            continue
        out.append(ForecastPeriod(start, estimate, _num(item.get("pv_estimate10")), _num(item.get("pv_estimate90"))))
    return out


def _period_hours(periods: list[ForecastPeriod]) -> float:
    if len(periods) < 2:
        return 0.5
    first = dt.datetime.fromisoformat(periods[0].start)
    second = dt.datetime.fromisoformat(periods[1].start)
    return max((second - first).total_seconds() / 3600, 1 / 60)


def energy_kwh(value: float, unit: str | None) -> float | None:
    """A production counter in kWh (Wh and MWh are converted)."""
    factor = {"Wh": 0.001, "kWh": 1.0, "MWh": 1000.0}.get(unit or "kWh")
    return None if factor is None else value * factor


@dataclass(slots=True)
class SolarHistory:
    days: dict[str, dict[str, Any]] = field(default_factory=dict)
    """Per local date (YYYY-MM-DD): ``forecast`` and ``counter`` (hour → counter reading in kWh)."""

    # --- recording ------------------------------------------------------

    def record_forecast(self, day: str, captured_at: str, source: str, periods: list[ForecastPeriod]) -> bool:
        """Day-ahead forecast for ``day``. Returns False when there is nothing to store."""
        if not periods:
            return False
        hours = _period_hours(periods)
        total = sum(p.estimate for p in periods) * hours
        low = [p.estimate10 for p in periods]
        high = [p.estimate90 for p in periods]
        entry = self.days.setdefault(day, {})
        entry["forecast"] = {
            "captured_at": captured_at,
            "source": source,
            "period_hours": hours,
            "total_kwh": round(total, 3),
            "total10_kwh": round(sum(v for v in low if v is not None) * hours, 3) if all(v is not None for v in low) else None,
            "total90_kwh": round(sum(v for v in high if v is not None) * hours, 3) if all(v is not None for v in high) else None,
            "periods": [[p.start, p.estimate, p.estimate10, p.estimate90] for p in periods],
        }
        self._prune(day)
        return True

    def record_counter(self, day: str, hour: int, kwh: float) -> None:
        """Production counter at the start of ``hour`` (0–23) on ``day``. The first reading per hour counts."""
        counter = self.days.setdefault(day, {}).setdefault("counter", {})
        counter.setdefault(str(hour), round(kwh, 4))
        self._prune(day)

    def _prune(self, newest: str) -> None:
        limit = (dt.date.fromisoformat(newest) - dt.timedelta(days=KEEP_DAYS)).isoformat()
        for day in [d for d in self.days if d < limit]:
            del self.days[day]

    # --- reading --------------------------------------------------------

    def production_per_hour(self, day: str) -> dict[int, float]:
        """kWh per hour of ``day``, from consecutive counter readings (the next day's 0:00 closes hour 23).

        Counter drops (a new meter, a reset) give no value for that hour.
        """
        readings = {int(h): v for h, v in self.days.get(day, {}).get("counter", {}).items()}
        next_day = (dt.date.fromisoformat(day) + dt.timedelta(days=1)).isoformat()
        midnight = self.days.get(next_day, {}).get("counter", {}).get("0")
        if midnight is not None:
            readings[24] = midnight
        out: dict[int, float] = {}
        known = sorted(h for h in readings if 0 <= h <= 24)
        for start, end in pairwise(known):
            delta = readings[end] - readings[start]
            if delta < 0:
                continue
            # A missing reading in between (HA restart, unknown): spread the step evenly.
            for hour in range(start, end):
                out[hour] = round(delta / (end - start), 4)
        return out

    def summary(self, last: int = 30) -> list[dict[str, Any]]:
        """Per day: forecast (mid, low, high) and the real production, newest last."""
        rows = []
        for day in sorted(self.days)[-last:]:
            forecast = self.days[day].get("forecast") or {}
            hourly = self.production_per_hour(day)
            rows.append(
                {
                    "day": day,
                    "forecast_kwh": forecast.get("total_kwh"),
                    "forecast10_kwh": forecast.get("total10_kwh"),
                    "forecast90_kwh": forecast.get("total90_kwh"),
                    "actual_kwh": round(sum(hourly.values()), 3) if len(hourly) == 24 else None,
                    "hours_measured": len(hourly),
                }
            )
        return rows

    # --- storage ----------------------------------------------------------

    def as_dict(self) -> dict[str, Any]:
        return {"days": self.days}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> SolarHistory:
        days = (data or {}).get("days")
        return cls(days=dict(days) if isinstance(days, Mapping) else {})
