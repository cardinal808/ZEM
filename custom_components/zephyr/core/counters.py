"""Counters per set: writes to RAM and flash, skipped refreshes, relay switches (B33).

Kept as time stamps over a rolling 24 hours (the engine's monotonic clock), plus totals per
calendar day for a week. ``as_dict``/``restore`` carry them over a restart of Home Assistant
in wall-clock time (OPDRACHT-tellers-relais-flash §2.1).

In shadow mode the writes are what ZEPHYR *would* send; in live mode a write counts once
the set accepted it, and a command that a newer one replaced before it was sent counts as
``superseded``. Relay switches come in three kinds:

- ``relay`` (``relay_reported``): changes of ``acStatus`` in the reports, what the set really does;
- ``relay_commanded``: commands that turn the direction (``acMode``) against what the set reports;
- ``pack_state``: changes between idle, charging and delivering in the reports (a check).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Final

DAY = 86_400.0
HOUR = 3_600.0
DAYS_KEPT = 7
_MAX_EVENTS = 100_000
"""Upper bound per list; at one event per second that is more than a day."""

FLASH_CAUSES: Final = ("standby", "soc_limits", "startup", "grid_reverse", "test")
"""Causes of flash writes (PLAN-M4b §2.7); ``startup``: SOC limits when the set is first seen."""
KINDS: Final = ("ram", "flash", "skipped", "superseded", "relay", "relay_commanded", "pack_state")


def _events() -> deque[float]:
    return deque(maxlen=_MAX_EVENTS)


@dataclass(slots=True)
class SetCounters:
    ram: deque[float] = field(default_factory=_events)
    """Power commands (``smartMode`` 1, RAM only)."""
    flash: deque[float] = field(default_factory=_events)
    """Standby, SOC-limit and ``gridReverse`` commands (stored in flash)."""
    skipped: deque[float] = field(default_factory=_events)
    """Refreshes not sent because the set already reported the same limits."""
    superseded: deque[float] = field(default_factory=_events)
    """Commands replaced by a newer one before they were sent (live only)."""
    relay: deque[float] = field(default_factory=_events)
    """Changes of ``acStatus`` (0 off, 1 delivering, 2 charging): relay switches."""
    relay_commanded: deque[float] = field(default_factory=_events)
    pack_state: deque[float] = field(default_factory=_events)
    last_ac_status: int | None = None
    last_pack_state: int | None = None
    flash_causes: dict[str, deque[float]] = field(default_factory=dict)
    """Flash writes per cause (PLAN-M4b §2.7)."""
    days: dict[str, dict[str, int]] = field(default_factory=dict)
    """Totals per local calendar day: kind (and ``flash_<cause>``) → count."""

    def _count(self, name: str, now: float, day: str | None) -> None:
        getattr(self, name).append(now)
        self._day(day, name)

    def _day(self, day: str | None, name: str) -> None:
        if day is None:
            return
        totals = self.days.setdefault(day, {})
        totals[name] = totals.get(name, 0) + 1
        for old in sorted(self.days)[:-DAYS_KEPT]:
            del self.days[old]

    def record(self, kind: str, now: float, day: str | None = None) -> None:
        if kind == "power":
            self._count("ram", now, day)
        elif kind in ("skipped", "superseded", "relay_commanded"):
            self._count(kind, now, day)
        else:
            self._count("flash", now, day)
            self.flash_causes.setdefault(kind, _events()).append(now)
            self._day(day, f"flash_{kind}")

    def flash_count(self, now: float, window: float) -> int:
        return sum(1 for t in self.flash if now - t <= window)

    def observe_ac_status(self, value: int | None, now: float, day: str | None = None) -> None:
        if value is None:
            return  # not every model reports it (SolarFlow 2400 AC+ does not)
        if self.last_ac_status is not None and value != self.last_ac_status:
            self._count("relay", now, day)
        self.last_ac_status = value

    def observe_pack_state(self, value: int | None, now: float, day: str | None = None) -> None:
        if value is None:
            return
        if self.last_pack_state is not None and value != self.last_pack_state:
            self._count("pack_state", now, day)
        self.last_pack_state = value

    def _trim(self, now: float) -> None:
        for name in KINDS:
            events: deque[float] = getattr(self, name)
            while events and now - events[0] > DAY:
                events.popleft()
        for events in self.flash_causes.values():
            while events and now - events[0] > DAY:
                events.popleft()

    def snapshot(self, now: float) -> dict[str, Any]:
        """Counts per hour and 24 hours. Without ``acStatus`` from the set, no relay counts."""
        self._trim(now)
        out: dict[str, Any] = {}
        reported = self.last_ac_status is not None
        for name in KINDS:
            if name == "relay" and not reported:
                continue
            events: deque[float] = getattr(self, name)
            out[f"{name}_24h"] = len(events)
            out[f"{name}_1h"] = sum(1 for t in events if now - t <= HOUR)
        by_cause = {cause: len(self.flash_causes.get(cause, ())) for cause in FLASH_CAUSES}
        by_cause |= {cause: len(events) for cause, events in self.flash_causes.items() if cause not in by_cause}
        for cause, count in by_cause.items():
            out[f"flash_{cause}_24h"] = count
        out["flash_by_cause"] = by_cause
        out["days"] = [self._day_view(day, reported) for day in sorted(self.days)]
        return out

    def _day_view(self, day: str, reported: bool) -> dict[str, Any]:
        totals = self.days[day]
        view: dict[str, Any] = {"day": day, **{name: totals.get(name, 0) for name in KINDS}}
        view["flash_by_cause"] = {k[6:]: v for k, v in totals.items() if k.startswith("flash_")}
        if not reported:
            view["relay"] = None
        elif abs(view["relay"] - view["relay_commanded"]) > 2:
            view["relay_mismatch"] = True
        return view

    # --- over a restart ------------------------------------------------------------------

    def as_dict(self, now: float, wall: float) -> dict[str, Any]:
        """Events of the last 24 h in wall-clock seconds, and the day totals."""
        self._trim(now)
        shift = wall - now
        return {
            "events": {name: [round(t + shift, 1) for t in getattr(self, name)] for name in KINDS},
            "flash_causes": {cause: [round(t + shift, 1) for t in events] for cause, events in self.flash_causes.items()},
            "days": self.days,
            "last_ac_status": self.last_ac_status,
        }

    def restore(self, data: Mapping[str, Any] | None, now: float, wall: float) -> None:
        """Take back what ``as_dict`` stored; events older than 24 h are dropped.

        The last ``acStatus`` is kept so the first report after a restart counts a switch
        that happened while Home Assistant was away.
        """
        if not data:
            return
        shift = now - wall

        def events(values: Any) -> deque[float]:
            out = _events()
            out.extend(t + shift for t in sorted(float(v) for v in values or []) if now - (t + shift) <= DAY)
            return out

        stored = data.get("events") or {}
        for name in KINDS:
            restored = events(stored.get(name))
            restored.extend(getattr(self, name))  # anything counted since the start comes after
            setattr(self, name, restored)
        for cause, values in (data.get("flash_causes") or {}).items():
            restored = events(values)
            restored.extend(self.flash_causes.get(cause, ()))
            self.flash_causes[cause] = restored
        for day, totals in (data.get("days") or {}).items():
            merged = dict(totals)
            for name, count in self.days.get(day, {}).items():
                merged[name] = merged.get(name, 0) + count
            self.days[day] = merged
        for old in sorted(self.days)[:-DAYS_KEPT]:
            del self.days[old]
        if self.last_ac_status is None and data.get("last_ac_status") is not None:
            self.last_ac_status = int(data["last_ac_status"])
