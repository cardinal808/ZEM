"""Planned appliances: dishwasher, washing machine, dryer (B36, SPEC-geplande-verbruikers).

The user announces a run; the planner counts its energy profile in the expected use and
advises the cheapest start within the window, judged on the whole plan (battery, solar,
prices), not just the price at that moment.

This module is pure: profiles (default per kind or learned from a smart plug), detecting
runs in a power series, spreading a run over quarters and finding the best start.
"""

from __future__ import annotations

import statistics
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Final

QUARTER: Final = timedelta(minutes=15)

DISHWASHER: Final = "dishwasher"
WASHER: Final = "washer"
DRYER_HEAT_PUMP: Final = "dryer_heat_pump"
DRYER_CONDENSER: Final = "dryer_condenser"
OTHER: Final = "other"
KINDS: Final = (DISHWASHER, WASHER, DRYER_HEAT_PUMP, DRYER_CONDENSER, OTHER)
DRYERS: Final = (DRYER_HEAT_PUMP, DRYER_CONDENSER)

MIN_RUNS: Final = 3
"""Runs needed before the learned profile replaces the default one."""
RUNS_KEPT: Final = 20
CHEAPER_BY: Final = 0.02
"""A later start must save at least this much (€) over the earliest good one (ease of use)."""


def _segments(*parts: tuple[int, float]) -> list[float]:
    """Profile per minute from (minutes, W) parts."""
    out: list[float] = []
    for minutes, watts in parts:
        out.extend([watts] * minutes)
    return out


def default_profile(kind: str) -> list[float]:
    """First estimate per minute (W) per kind (SPEC-geplande-verbruikers §3.1)."""
    if kind == DISHWASHER:  # 1.0 kWh, 2:30: heating at the start and drying at the end
        return _segments((15, 2000.0), (105, 50.0), (15, 1700.0), (15, 50.0))
    if kind == WASHER:  # 0.8 kWh, 2:00: heating the first 15 min, then washing, spinning
        return _segments((15, 2000.0), (90, 130.0), (15, 400.0))
    if kind == DRYER_HEAT_PUMP:  # 1.2 kWh, 2:30
        return _segments((150, 480.0))
    if kind == DRYER_CONDENSER:  # 2.5 kWh, 1:45
        return _segments((105, 1430.0))
    return _segments((60, 1000.0))


def profile_kwh(profile: Sequence[float]) -> float:
    return sum(profile) / 60 / 1000


@dataclass(frozen=True, slots=True)
class Run:
    """A run seen on a smart plug."""

    start: datetime
    minutes: int
    kwh: float
    profile: tuple[float, ...]
    """Mean power per minute (W)."""

    def as_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "minutes": self.minutes,
            "kwh": round(self.kwh, 3),
            "profile": [round(w) for w in self.profile],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Run:
        return cls(
            datetime.fromisoformat(data["start"]), int(data["minutes"]), float(data["kwh"]), tuple(float(w) for w in data["profile"])
        )


def detect_runs(
    samples: Sequence[tuple[datetime, float]],
    *,
    on_w: float = 5.0,
    min_minutes: float = 10.0,
    off_minutes: float = 5.0,
) -> list[Run]:
    """Runs in a power series (W, held until the next state change): above ``on_w`` for at
    least ``min_minutes``; a run ends once it stays below for ``off_minutes``. Short pulses (a
    boiling-water tap on the same plug) are left out by the minimum length."""
    runs: list[Run] = []
    ordered = sorted(samples)
    if not ordered:
        return runs
    start: datetime | None = None
    off_since: datetime | None = None
    points: list[tuple[datetime, float]] = []

    def close(end: datetime) -> None:
        assert start is not None
        if (end - start).total_seconds() / 60 >= min_minutes:
            runs.append(_run([p for p in points if p[0] < end], start, end))

    for when, watts in ordered:
        if watts > on_w:
            if start is not None and off_since is not None and (when - off_since).total_seconds() / 60 > off_minutes:
                close(off_since)
                start = None
            if start is None:
                start, points = when, []
            off_since = None
        elif start is not None and off_since is None:
            off_since = when
        if start is not None:
            points.append((when, watts))
    if start is not None and off_since is not None and (ordered[-1][0] - off_since).total_seconds() / 60 >= off_minutes:
        close(off_since)
    return runs


def _run(points: Sequence[tuple[datetime, float]], start: datetime, end: datetime) -> Run:
    """Mean power per minute from held state values between ``start`` and ``end``."""
    minutes = max(round((end - start).total_seconds() / 60), 1)
    energy = [0.0] * minutes  # W·min per minute
    for (t0, w), (t1, _) in zip(points, [*points[1:], (end, 0.0)], strict=False):
        a, b = max(t0, start), min(t1, end)
        while a < b:
            index = int((a - start).total_seconds() // 60)
            if index >= minutes:
                break
            edge = start + timedelta(minutes=index + 1)
            stop = min(b, edge)
            energy[index] += w * (stop - a).total_seconds() / 60
            a = stop
    profile = tuple(energy)
    return Run(start, minutes, profile_kwh(profile), profile)


def learned_profile(runs: Sequence[Run]) -> list[float] | None:
    """Median per minute of the last runs (aligned at their start, median length); None below MIN_RUNS."""
    if len(runs) < MIN_RUNS:
        return None
    length = int(statistics.median(r.minutes for r in runs))
    return [statistics.median(r.profile[m] if m < len(r.profile) else 0.0 for r in runs) for m in range(length)]


def quarter_energy(profile: Sequence[float], start: datetime) -> dict[datetime, float]:
    """kWh of a run per quarter (quarter start, in ``start``'s time zone)."""
    out: dict[datetime, float] = {}
    for minute, watts in enumerate(profile):
        at = start + timedelta(minutes=minute)
        quarter = at.replace(minute=at.minute - at.minute % 15, second=0, microsecond=0)
        out[quarter] = out.get(quarter, 0.0) + watts / 60 / 1000
    return out


@dataclass(slots=True)
class PlannedRun:
    """One announced run of an appliance."""

    appliance: str
    window_start: datetime
    window_end: datetime
    """The run should be done by then."""
    fixed_start: datetime | None = None
    after: str | None = None
    """Name of an appliance whose planned run must be done first (dryer after washer)."""
    best_start: datetime | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "appliance": self.appliance,
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "fixed_start": None if self.fixed_start is None else self.fixed_start.isoformat(),
            "after": self.after,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PlannedRun:
        fixed = data.get("fixed_start")
        return cls(
            data["appliance"],
            datetime.fromisoformat(data["window_start"]),
            datetime.fromisoformat(data["window_end"]),
            None if fixed is None else datetime.fromisoformat(fixed),
            data.get("after"),
        )


def candidates(run: PlannedRun, minutes: int, now: datetime, not_before: datetime | None = None) -> list[datetime]:
    """Starts every 15 min within the window (not in the past) that finish before its end."""
    if run.fixed_start is not None:
        return [run.fixed_start]
    first = max(run.window_start, now, not_before or run.window_start)
    first = first.replace(second=0, microsecond=0)
    if first.minute % 15:
        first += timedelta(minutes=15 - first.minute % 15)
    out = []
    start = first
    while start + timedelta(minutes=minutes) <= run.window_end:
        out.append(start)
        start += QUARTER
    return out or [first]  # a window too short: start as soon as possible


CostFn = Callable[[Mapping[datetime, float]], float]
"""Cost of the whole plan with this extra use per quarter (kWh)."""


def place_runs(
    runs: Sequence[PlannedRun],
    profiles: Mapping[str, Sequence[float]],
    now: datetime,
    cost: CostFn,
) -> dict[datetime, float]:
    """Choose the best start of every run, one after another; returns the total extra use.

    Every candidate is judged with the whole plan (``cost``), with the runs placed before it.
    Runs with ``after`` wait for the end of that appliance's planned run.
    """
    extra: dict[datetime, float] = {}
    ends: dict[str, datetime] = {}
    ordered = sorted(runs, key=lambda r: (r.after is not None, r.window_start))  # stable: announce order
    for run in ordered:
        profile = profiles.get(run.appliance) or default_profile(OTHER)
        minutes = len(profile)
        # Not before the end of this appliance's previous run, nor of the one it waits for.
        waits = [t for t in (ends.get(run.appliance), ends.get(run.after) if run.after else None) if t is not None]
        options = candidates(run, minutes, now, max(waits) if waits else None)
        best: tuple[float, datetime] | None = None
        first_cost: float | None = None
        for start in options:
            trial = dict(extra)
            for quarter, kwh in quarter_energy(profile, start).items():
                trial[quarter] = trial.get(quarter, 0.0) + kwh
            value = cost(trial)
            if first_cost is None:
                first_cost = value
            if best is None or value < best[0] - CHEAPER_BY:
                best = (value, start)
        assert best is not None and first_cost is not None
        run.best_start = best[1]
        run.details = {
            "cost": round(best[0], 4),
            "cost_now": round(first_cost, 4),
            "saving": round(first_cost - best[0], 4),
            "kwh": round(profile_kwh(profile), 3),
            "minutes": minutes,
        }
        for quarter, kwh in quarter_energy(profile, best[1]).items():
            extra[quarter] = extra.get(quarter, 0.0) + kwh
        ends[run.appliance] = best[1] + timedelta(minutes=minutes)
    return extra


def standard_window(now: datetime, window_from: str | None, window_until: str) -> tuple[datetime, datetime]:
    """The window of a run planned with the button, in ``now``'s time zone.

    ``window_from`` empty: from now. ``window_until`` before (or at) the opening: the next
    day. A window that is already over today: tomorrow's.
    """

    def at(day: datetime, hhmm: str) -> datetime:
        hour, minute = (int(x) for x in hhmm.split(":")[:2])
        return day.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if not window_from:
        end = at(now, window_until)
        if end <= now:
            end += timedelta(days=1)
        return now, end
    start, end = at(now, window_from), at(now, window_until)
    if end <= start:
        end += timedelta(days=1)
    if now >= end:
        start, end = start + timedelta(days=1), end + timedelta(days=1)
    return max(start, now), end
