"""Learned consumption profile (SPEC-planner §2.3).

* Per hour of the day, separately for workdays and weekends (holidays count as
  weekend when the caller says so): a running mean of the house consumption.
* An hour value counts once it has enough measurements (workday 3, weekend 2);
  before that the mean of all hours (daily mean / 24) is used.
* Memory: about 4 working weeks / 5 weekends (exponential weights).
* Steering during the day: when the last hours were above or below the
  expectation, the next hours are corrected by that ratio, damped and bounded,
  fading back to 1.

Pure Python; the caller feeds measured hours and asks for forecasts. Stored as a
plain dict in ZEPHYR's own storage, so a reset is immediate (§2.3).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Final

WORKDAY: Final = "workday"
WEEKEND: Final = "weekend"
MIN_COUNT: Final[dict[str, int]] = {WORKDAY: 3, WEEKEND: 2}
MEMORY: Final[dict[str, float]] = {WORKDAY: 20.0, WEEKEND: 10.0}
"""Samples per hour value: 4 working weeks of 5 days, 5 weekends of 2 days."""
STEER_HOURS: Final = 3
STEER_LIMITS: Final[tuple[float, float]] = (0.6, 1.6)
STEER_HALF_LIFE: Final = 2.0
"""Hours after which half of the correction is left."""


@dataclass(slots=True)
class LoadProfile:
    values: dict[str, list[float]] = field(default_factory=lambda: {WORKDAY: [0.0] * 24, WEEKEND: [0.0] * 24})
    counts: dict[str, list[int]] = field(default_factory=lambda: {WORKDAY: [0] * 24, WEEKEND: [0] * 24})
    mean: float = 0.0
    """Running mean of all hours (kWh per hour)."""
    mean_count: int = 0
    recent: deque[tuple[float, float]] = field(default_factory=lambda: deque(maxlen=STEER_HOURS))
    """(measured, expected) of the last hours, for steering."""

    def expected(self, day_type: str, hour: int) -> float:
        if self.counts[day_type][hour] >= MIN_COUNT[day_type]:
            return self.values[day_type][hour]
        return self.mean

    def learn(self, day_type: str, hour: int, kwh: float) -> None:
        """Add a measured hour (house consumption without separately counted loads)."""
        self.recent.append((kwh, self.expected(day_type, hour)))
        n = self.counts[day_type][hour]
        weight = 1.0 / min(n + 1, MEMORY[day_type])
        self.values[day_type][hour] += (kwh - self.values[day_type][hour]) * weight
        self.counts[day_type][hour] = n + 1
        self.mean_count += 1
        self.mean += (kwh - self.mean) / min(self.mean_count, 24 * 28)

    def steering(self) -> float:
        """Ratio measured / expected over the last hours, bounded (1 = no correction)."""
        measured = sum(m for m, _ in self.recent)
        expected = sum(e for _, e in self.recent)
        if len(self.recent) < STEER_HOURS or expected <= 0:
            return 1.0
        low, high = STEER_LIMITS
        return max(low, min(high, measured / expected))

    def forecast(self, day_type: str, hour: int, hours_ahead: float) -> float:
        """Expected kWh in ``hour``, ``hours_ahead`` from now, with the fading correction."""
        fade = float(0.5 ** (max(hours_ahead, 0.0) / STEER_HALF_LIFE))
        return self.expected(day_type, hour) * (1 + (self.steering() - 1) * fade)

    def reset(self) -> None:
        fresh = LoadProfile()
        self.values, self.counts, self.mean, self.mean_count, self.recent = (
            fresh.values,
            fresh.counts,
            fresh.mean,
            fresh.mean_count,
            fresh.recent,
        )

    def as_dict(self) -> dict[str, Any]:
        return {"values": self.values, "counts": self.counts, "mean": self.mean, "mean_count": self.mean_count}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> LoadProfile:
        profile = cls()
        if not data:
            return profile
        for kind in (WORKDAY, WEEKEND):
            values = (data.get("values") or {}).get(kind)
            counts = (data.get("counts") or {}).get(kind)
            if isinstance(values, list) and len(values) == 24 and isinstance(counts, list) and len(counts) == 24:
                profile.values[kind] = [float(v) for v in values]
                profile.counts[kind] = [int(c) for c in counts]
        profile.mean = float(data.get("mean", 0.0))
        profile.mean_count = int(data.get("mean_count", 0))
        return profile


@dataclass(frozen=True, slots=True)
class HourEnergy:
    """Energy of one hour from the meter history (kWh): for the first fill of the profile."""

    start: datetime
    """Local start of the hour (aware)."""
    import_kwh: float
    export_kwh: float
    solar_kwh: float
    battery_kwh: float
    """Into the battery (+) or out of it (−)."""
    excluded_kwh: float = 0.0
    """Use of a load the battery may not feed in that hour (B41); not part of ``house_kwh``."""

    @property
    def house_kwh(self) -> float:
        total = max(self.import_kwh - self.export_kwh + self.solar_kwh - self.battery_kwh, 0.0)
        return max(total - self.excluded_kwh, 0.0)


def day_type_of(local: datetime, workdays: Mapping[date, bool] | None = None) -> str:
    """Workday or weekend; ``workdays`` (from the Workday integration) overrides the weekday: a holiday is a weekend day."""
    if workdays is not None and local.date() in workdays:
        return WORKDAY if workdays[local.date()] else WEEKEND
    return WEEKEND if local.weekday() >= 5 else WORKDAY


def profile_from_history(hours: Iterable[HourEnergy], excluded: bool = False, workdays: Mapping[date, bool] | None = None) -> LoadProfile:
    """A profile learned from past hours, oldest first (§2.3: first fill).

    ``excluded``: learn the excluded load (B41) instead of the house.
    """
    profile = LoadProfile()
    for hour in sorted(hours, key=lambda h: h.start):
        profile.learn(day_type_of(hour.start, workdays), hour.start.hour, hour.excluded_kwh if excluded else hour.house_kwh)
    profile.recent.clear()  # steering is for the live hours only
    return profile


def blocked_share(changes: Iterable[tuple[datetime, str | None]], start: datetime, end: datetime, blocked: Iterable[str]) -> float:
    """Share (0-1) of [start, end) a climate entity spent in a blocked mode (B41, first fill).

    ``changes``: (moment, hvac_mode) oldest first, the first one at or before ``start``.
    """
    modes = frozenset(blocked)
    total = (end - start).total_seconds()
    if total <= 0:
        return 0.0
    inside = 0.0
    items = list(changes)
    for i, (moment, mode) in enumerate(items):
        until = items[i + 1][0] if i + 1 < len(items) else end
        a, b = max(moment, start), min(until, end)
        if b > a and mode in modes:
            inside += (b - a).total_seconds()
    return inside / total
