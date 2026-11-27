"""Solar power now from panels the sets do not see (screen *Nu*, flow).

Two ways, the first that works:

1. **Power sensors** (W or kW) of inverters: added up. A sensor that is unavailable is left
   out; when all are, there is no value.
2. **Estimate from the solar energy counter** (kWh, total increasing) when no power sensor is
   set: step size / time between two steps. Between steps the power can only fall
   (step size / time since the last step), so the estimate fades out when the counter stops.

PV on the sets themselves comes from the sets (``solarInputPower``) and is added by the caller.

Pure Python, no Home Assistant.
"""

from __future__ import annotations

MIN_STEP_INTERVAL = 20.0
"""s: steps closer together than this are counter noise or a restart, not a measurement."""
MAX_POWER = 100_000.0
"""W: no estimate above this (a counter that jumps after a gap)."""


def watts(state: str | None, unit: str | None) -> float | None:
    """Power of one sensor state in W (kW and MW converted); None when not a number."""
    if state is None:
        return None
    try:
        value = float(state)
    except ValueError:
        return None
    factor = {"kW": 1000.0, "MW": 1_000_000.0}.get(unit or "W", 1.0)
    return max(0.0, value * factor)


def total(values: list[float | None]) -> float | None:
    """Sum of the sensors that have a value; None when none has."""
    known = [v for v in values if v is not None]
    return sum(known) if known else None


class CounterPower:
    """Power (W) estimated from an energy counter's steps."""

    __slots__ = ("_kwh", "_power", "_step_at", "_step_kwh")

    def __init__(self) -> None:
        self._kwh: float | None = None
        self._step_at: float | None = None
        self._step_kwh = 0.0
        self._power = 0.0

    def observe(self, kwh: float, now: float) -> None:
        if self._kwh is None or kwh < self._kwh:
            self._kwh, self._step_at = kwh, now  # first reading or a reset: reference only
            return
        delta = kwh - self._kwh
        if delta <= 0:
            return
        assert self._step_at is not None
        dt = now - self._step_at
        self._kwh, self._step_at = kwh, now
        if dt < MIN_STEP_INTERVAL:
            return
        self._step_kwh = delta
        self._power = min(MAX_POWER, delta * 3_600_000 / dt)

    def power(self, now: float) -> float | None:
        """None until the counter made a measured step."""
        if self._step_at is None or self._step_kwh <= 0:
            return None
        elapsed = now - self._step_at
        power = self._power
        if elapsed > 0:
            power = min(power, self._step_kwh * 3_600_000 / elapsed)
        return max(0.0, power)
