"""Counters per set: writes to RAM and flash, skipped refreshes, relay switches (B33).

Kept as time stamps over a rolling 24 hours, so the counts do not depend on a
calendar or time zone. In shadow mode the writes are what ZEPHYR *would* send;
the relay switches are what the set really does (seen in ``acStatus``).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

DAY = 86_400.0
HOUR = 3_600.0
_MAX_EVENTS = 100_000
"""Upper bound per list; at one event per second that is more than a day."""


def _events() -> deque[float]:
    return deque(maxlen=_MAX_EVENTS)


@dataclass(slots=True)
class SetCounters:
    ram: deque[float] = field(default_factory=_events)
    """Power commands (``smartMode`` 1, RAM only)."""
    flash: deque[float] = field(default_factory=_events)
    """Standby and SOC-limit commands (stored in flash)."""
    skipped: deque[float] = field(default_factory=_events)
    """Refreshes not sent because the set already reported the same limits."""
    relay: deque[float] = field(default_factory=_events)
    """Changes of ``acStatus`` (0 off, 1 delivering, 2 charging): relay switches."""
    last_ac_status: int | None = None
    flash_causes: dict[str, deque[float]] = field(default_factory=dict)
    """Flash writes per cause: standby, soc_limits, test (PLAN-M4b §2.7)."""

    def record(self, kind: str, now: float) -> None:
        if kind == "power":
            self.ram.append(now)
        elif kind == "skipped":
            self.skipped.append(now)
        else:
            self.flash.append(now)
            self.flash_causes.setdefault(kind, _events()).append(now)

    def flash_count(self, now: float, window: float) -> int:
        return sum(1 for t in self.flash if now - t <= window)

    def observe_ac_status(self, value: int | None, now: float) -> None:
        if value is None:
            return  # not every model reports it (SolarFlow 2400 AC+ does not)
        if self.last_ac_status is not None and value != self.last_ac_status:
            self.relay.append(now)
        self.last_ac_status = value

    def snapshot(self, now: float) -> dict[str, int]:
        """Counts per hour and 24 hours. Without ``acStatus`` from the set, no relay counts."""
        out: dict[str, int] = {}
        names = ("ram", "flash", "skipped", "relay") if self.last_ac_status is not None else ("ram", "flash", "skipped")
        for name in names:
            events: deque[float] = getattr(self, name)
            while events and now - events[0] > DAY:
                events.popleft()
            out[f"{name}_24h"] = len(events)
            out[f"{name}_1h"] = sum(1 for t in events if now - t <= HOUR)
        for cause, events in self.flash_causes.items():
            while events and now - events[0] > DAY:
                events.popleft()
            out[f"flash_{cause}_24h"] = len(events)
        return out
