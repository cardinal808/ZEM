"""Vacation (B42): away from home, use is low and must not end up in the normal profile.

Two ways to be on vacation:

- **manual**: a switch, with an optional end (``until``); at the end it switches off by itself;
- **auto** (option): nobody home for ``AWAY_AFTER`` (zone.home = 0); ends when someone is back.

Past vacations are kept as periods, so the recorder fill and a profile reset can skip them.
Pure Python, no Home Assistant.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

AWAY_AFTER = timedelta(hours=24)
KEEP_PERIODS = timedelta(days=400)


@dataclass(slots=True)
class VacationState:
    manual: bool = False
    until: datetime | None = None
    """End of a manual vacation (aware); None = until switched off."""
    auto: bool = False
    started: datetime | None = None
    """Start of the current vacation (manual or auto)."""
    periods: list[tuple[datetime, datetime]] = field(default_factory=list)
    """Past vacations, oldest first."""

    # --- now and the plan ---------------------------------------------------

    def active(self, now: datetime) -> bool:
        return (self.manual and (self.until is None or now < self.until)) or self.auto

    def active_at(self, moment: datetime, now: datetime) -> bool:
        """Is ``moment`` (in the plan's horizon) still vacation, as far as known now?

        A manual vacation with an end stops at that end, so the planner charges for the
        return home. Without an end (or when away automatically) the whole horizon counts.
        """
        if not self.active(now):
            return False
        if self.manual and self.until is not None and not self.auto:
            return moment < self.until
        return True

    def was(self, moment: datetime, now: datetime) -> bool:
        """Was ``moment`` (in the past) part of a vacation?"""
        if self.started is not None and self.active(now) and self.started <= moment:
            return True
        return any(start <= moment < end for start, end in self.periods)

    # --- changes ---------------------------------------------------------------

    def set_manual(self, on: bool, now: datetime, until: datetime | None = None) -> None:
        self.check(now)
        was = self.active(now)
        self.manual = on
        self.until = until if on else None
        self._transition(was, now)

    def set_until(self, until: datetime | None, now: datetime) -> None:
        self.check(now)
        was = self.active(now)
        self.until = until
        self._transition(was, now)

    def set_auto(self, on: bool, now: datetime) -> None:
        self.check(now)
        was = self.active(now)
        self.auto = on
        self._transition(was, now)

    def check(self, now: datetime) -> bool:
        """Time passed: end a manual vacation at its end. Returns True when the state changed."""
        if self.manual and self.until is not None and now >= self.until:
            end = self.until
            self.manual, self.until = False, None
            if not self.auto:
                self._close(end, now)
            return True
        return False

    def _transition(self, was: bool, now: datetime) -> None:
        now_active = self.active(now)
        if now_active and not was:
            self.started = now
        elif was and not now_active:
            self._close(now, now)

    def _close(self, end: datetime, now: datetime) -> None:
        if self.started is not None and end > self.started:
            self.periods.append((self.started, end))
        self.started = None
        self.periods = [(s, e) for s, e in self.periods if e >= now - KEEP_PERIODS]

    # --- storage ---------------------------------------------------------------

    def as_dict(self) -> dict[str, Any]:
        return {
            "manual": self.manual,
            "until": None if self.until is None else self.until.isoformat(),
            "auto": self.auto,
            "started": None if self.started is None else self.started.isoformat(),
            "periods": [[s.isoformat(), e.isoformat()] for s, e in self.periods],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> VacationState:
        if not data:
            return cls()

        def moment(value: Any) -> datetime | None:
            return None if not value else datetime.fromisoformat(str(value))

        periods: list[tuple[datetime, datetime]] = []
        for item in data.get("periods") or []:
            start, end = moment(item[0]), moment(item[1])
            if start is not None and end is not None:
                periods.append((start, end))
        return cls(
            manual=bool(data.get("manual")),
            until=moment(data.get("until")),
            auto=bool(data.get("auto")),
            started=moment(data.get("started")),
            periods=periods,
        )


def base_load(hourly: Iterable[float], default: float) -> float:
    """Standby use (kWh per hour) while away: the lowest of the given hours, else ``default``."""
    values = [v for v in hourly if v > 0]
    return min(values) if values else default
