"""Calibration safety net (SPEC-planner §3.5, Bjorn 28-11).

The Zendure set calibrates its state of charge itself when it is full (``socStatus`` 1 while it
does). The longer the battery goes without reaching 100 %, the further the packs drift apart.
ZEPHYR therefore:

1. remembers when the battery was last full (SOC ≥ ``FULL_SOC``, or a calibration of the set ended);
2. from half the interval on, plans with a growing incentive to reach 100 % (up to
   ``SOFT_PENALTY`` €), and from the interval on with a hard one (``HARD_PENALTY`` €), so the
   planner picks the cheapest moment (solar, a cheap night hour); meanwhile the set's upper SOC
   limit is 100 %;
3. once full, rests: no delivering from the battery until the set's own calibration ended
   (``socStatus`` 1 → 0), at most ``REST_MAX``; then the counter starts again and the user's
   upper limit returns.

Pure logic, no Home Assistant; the HA layer feeds it the battery state and stores ``as_dict``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Final

FULL_SOC: Final = 99.0
SOFT_PENALTY: Final = 0.30
HARD_PENALTY: Final = 2.0
REST_MAX: Final = timedelta(hours=2)
DEFAULT_INTERVAL_DAYS: Final = 21


def penalty(days: float, interval: float) -> float:
    """€ the planner pays when the horizon does not reach 100 % (§3.5)."""
    if interval <= 0 or days < interval / 2:
        return 0.0
    if days >= interval:
        return HARD_PENALTY
    return round(SOFT_PENALTY * (days - interval / 2) / (interval / 2), 4)


@dataclass(slots=True)
class Calibration:
    interval_days: float = DEFAULT_INTERVAL_DAYS
    last_full: datetime | None = None
    resting_since: datetime | None = None
    calibrating: bool = False
    """The set reported ``socStatus`` 1 at the last update."""
    last_event: str | None = None

    def days_since_full(self, now: datetime) -> float:
        if self.last_full is None:
            return 0.0
        return (now - self.last_full).total_seconds() / 86_400

    def penalty(self, now: datetime) -> float:
        return 0.0 if self.resting_since is not None else penalty(self.days_since_full(now), self.interval_days)

    def active(self, now: datetime) -> bool:
        """The upper limit is raised to 100 %: calibration due (soft or hard) or resting at 100 %."""
        return self.interval_days > 0 and (self.resting_since is not None or self.penalty(now) > 0)

    @property
    def resting(self) -> bool:
        return self.resting_since is not None

    def update(self, now: datetime, soc: float | None, calibrating: bool) -> str | None:
        """Feed the battery state; returns what happened (``full``, ``rest``, ``done``) or ``None``."""
        event: str | None = None
        if self.last_full is None:
            self.last_full = now  # a new installation: count from now, never force at once
        ended = self.calibrating and not calibrating
        self.calibrating = calibrating
        if self.resting_since is not None:
            if ended or now - self.resting_since >= REST_MAX:
                self.resting_since, self.last_full, event = None, now, "done"
        elif ended:
            self.last_full, event = now, "done"  # the set calibrated by itself
        elif soc is not None and soc >= FULL_SOC:
            if self.active(now):
                self.resting_since, event = now, "rest"  # full on purpose: let the set calibrate
            else:
                self.last_full, event = now, "full"
        if event is not None:
            self.last_event = event
        return event

    def as_dict(self) -> dict[str, Any]:
        return {
            "last_full": None if self.last_full is None else self.last_full.isoformat(),
            "resting_since": None if self.resting_since is None else self.resting_since.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None, interval_days: float = DEFAULT_INTERVAL_DAYS) -> Calibration:
        out = cls(interval_days=interval_days)
        if data:
            if data.get("last_full"):
                out.last_full = datetime.fromisoformat(data["last_full"])
            if data.get("resting_since"):
                out.resting_since = datetime.fromisoformat(data["resting_since"])
        return out

    def view(self, now: datetime) -> dict[str, Any]:
        return {
            "interval_days": self.interval_days,
            "last_full": None if self.last_full is None else self.last_full.isoformat(),
            "days_since_full": round(self.days_since_full(now), 1),
            "penalty": self.penalty(now),
            "active": self.active(now),
            "resting_since": None if self.resting_since is None else self.resting_since.isoformat(),
            "set_calibrating": self.calibrating,
            "last_event": self.last_event,
        }
