"""Consumers in view (screen *Stroom*): power now and kWh today from a plug's power readings.

The consumers are the appliances with a plug (B36) and the airco (B41); their floor is set in
the panel (*Instellingen → Huis in beeld*). Energy today comes from integrating the power:
each reading counts until the next one (a smart plug only reports on a change), split at
local midnight. A reading older than ``MAX_HOLD_SECONDS`` no longer counts.

Pure Python, no Home Assistant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Final

FLOORS: Final = ("attic", "first", "ground", "shed", "outside")
MAX_HOLD_SECONDS: Final = 6 * 3600.0
"""A reading older than this no longer counts (sensor gone without becoming unavailable)."""


@dataclass(slots=True)
class DayEnergy:
    """kWh today per device from its power readings."""

    day: date | None = None
    kwh: dict[str, float] = field(default_factory=dict)
    _last: dict[str, tuple[float, float]] = field(default_factory=dict)
    """Per device: (epoch time, W) of the reading that counts now."""

    def observe(self, device_id: str, watts: float | None, now: float, today: date, midnight: float) -> None:
        """A new reading (None = unavailable). ``midnight`` = epoch time of today's local 00:00."""
        self._roll(today)
        self._count(device_id, now, midnight)
        if watts is None:
            self._last.pop(device_id, None)
        else:
            self._last[device_id] = (now, max(0.0, watts))

    def today(self, device_id: str, now: float, today: date, midnight: float) -> float:
        """kWh today, including the time since the last reading."""
        if self.day != today:
            last = self._last.get(device_id)
            if last is None:
                return 0.0
            return self._span(last, midnight, now)
        last = self._last.get(device_id)
        extra = 0.0 if last is None else self._span(last, midnight, now)
        return self.kwh.get(device_id, 0.0) + extra

    def power(self, device_id: str, now: float) -> float | None:
        last = self._last.get(device_id)
        if last is None or now - last[0] > MAX_HOLD_SECONDS:
            return None
        return last[1]

    def keep_only(self, ids: set[str]) -> None:
        self.kwh = {k: v for k, v in self.kwh.items() if k in ids}
        self._last = {k: v for k, v in self._last.items() if k in ids}

    def _roll(self, today: date) -> None:
        if self.day != today:
            self.day, self.kwh = today, {}

    def _count(self, device_id: str, now: float, midnight: float) -> None:
        last = self._last.get(device_id)
        if last is None:
            return
        self.kwh[device_id] = self.kwh.get(device_id, 0.0) + self._span(last, midnight, now)
        self._last[device_id] = (now, last[1])

    @staticmethod
    def _span(last: tuple[float, float], midnight: float, now: float) -> float:
        start, watts = last
        start = max(start, midnight, now - MAX_HOLD_SECONDS)
        return 0.0 if now <= start else watts * (now - start) / 3_600_000

    def as_dict(self) -> dict[str, Any]:
        return {"day": None if self.day is None else self.day.isoformat(), "kwh": {k: round(v, 5) for k, v in self.kwh.items()}}

    def restore(self, data: dict[str, Any] | None, today: date) -> None:
        if not data or data.get("day") != today.isoformat():
            return
        self.day = today
        for key, value in (data.get("kwh") or {}).items():
            if isinstance(value, int | float):
                self.kwh[str(key)] = float(value)
