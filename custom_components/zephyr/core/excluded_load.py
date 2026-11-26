"""A load the battery may not feed (B41, SPEC-airco): its power from an energy counter.

Many devices (an air conditioner via its cloud integration) only offer a coarse energy
counter: steps of e.g. 0.25 kWh every 8-9 minutes. From that ZEPHYR estimates the power:

- on a new step: step size / time since the previous step;
- between steps the power is at most step size / time since the last step, so a stopped
  device fades out by itself;
- a climate entity, if there is one, says at once whether the device runs in a mode the
  battery may not feed (``hvac_mode``) and whether it is running at all (``hvac_action``).
  On a start the estimate begins with the power of the previous run.

Pure Python, no Home Assistant.
"""

from __future__ import annotations

from collections.abc import Collection

MAX_POWER = 4000.0
"""W: no estimate above this (a counter that jumps after a gap)."""
MIN_STEP_INTERVAL = 30.0
"""s: steps closer together than this are counter noise (or a restart), not a measurement."""
IDLE_ACTIONS = frozenset({"idle", "off"})


class ExcludedLoad:
    """Estimated power (W) of one load the battery may not feed."""

    __slots__ = (
        "_action",
        "_energy_total",
        "_interval_sum",
        "_kwh",
        "_last_run_power",
        "_mode",
        "_power",
        "_step_at",
        "_step_kwh",
        "_steps",
        "blocked_modes",
        "has_climate",
    )

    def __init__(self, blocked_modes: Collection[str] = ("heat",), has_climate: bool = False) -> None:
        self.blocked_modes = frozenset(blocked_modes)
        self.has_climate = has_climate
        self._mode: str | None = None
        self._action: str | None = None
        self._kwh: float | None = None
        self._step_at: float | None = None
        self._step_kwh = 0.0
        self._power = 0.0
        self._last_run_power = 0.0
        self._steps = 0
        self._interval_sum = 0.0
        self._energy_total = 0.0

    # --- inputs -----------------------------------------------------------

    def observe_counter(self, kwh: float, now: float) -> None:
        """A counter reading (kWh, total increasing). Equal readings are no new step."""
        if self._kwh is None or kwh < self._kwh:
            self._kwh, self._step_at = kwh, now  # first reading or a reset counter: reference only
            return
        delta = kwh - self._kwh
        if delta <= 0:
            return
        if self.active():
            self._energy_total += delta  # kWh the battery did not feed (for the cost log)
        assert self._step_at is not None
        dt = now - self._step_at
        self._kwh, self._step_at = kwh, now
        if dt < MIN_STEP_INTERVAL:
            return
        self._step_kwh = delta
        self._power = min(MAX_POWER, delta * 3_600_000 / dt)
        self._last_run_power = self._power
        self._steps += 1
        self._interval_sum += dt

    def observe_climate(self, mode: str | None, action: str | None, now: float) -> None:
        """The climate entity's ``hvac_mode`` (state) and ``hvac_action`` (attribute, may be None)."""
        was = self._running_blocked()
        self._mode, self._action = mode, action
        now_running = self._running_blocked()
        if now_running and not was:
            # Start: measure the next step from now (not from the idle time before), and begin
            # with the power of the previous run.
            self._step_at = now
            self._power = self._last_run_power
            self._step_kwh = 0.0
        elif was and not now_running:
            self._power = 0.0

    # --- output -----------------------------------------------------------

    def active(self) -> bool:
        """The load runs in a mode the battery may not feed (without a climate entity: always)."""
        return not self.has_climate or self._running_blocked()

    def power(self, now: float) -> float:
        """Estimated power (W) the battery must not deliver for; 0 when not active."""
        if not self.active() or self._step_at is None:
            return 0.0
        elapsed = now - self._step_at
        power = self._power
        if self._step_kwh > 0 and elapsed > 0:
            power = min(power, self._step_kwh * 3_600_000 / elapsed)
        return max(0.0, power)

    @property
    def energy_total(self) -> float:
        """kWh counted while the load was excluded, since the start (the cost log takes differences)."""
        return self._energy_total

    def diagnostics(self, now: float) -> dict[str, object]:
        return {
            "blocked_modes": sorted(self.blocked_modes),
            "has_climate": self.has_climate,
            "mode": self._mode,
            "action": self._action,
            "active": self.active(),
            "power_w": round(self.power(now)),
            "energy_total_kwh": round(self._energy_total, 3),
            "last_step_kwh": self._step_kwh,
            "last_run_power_w": round(self._last_run_power),
            "mean_step_interval_s": round(self._interval_sum / self._steps) if self._steps else None,
            "seconds_since_step": None if self._step_at is None else round(now - self._step_at),
        }

    def _running_blocked(self) -> bool:
        if self._mode is None or self._mode not in self.blocked_modes:
            return False
        return self._action not in IDLE_ACTIONS


def exclusion_for_controller(excluded: float, grid: float, battery: float) -> float:
    """How much of the excluded load to take out of the P1 for the controller (W).

    ``grid``: P1 (+ import), ``battery``: battery power (+ charging). The house demand is
    ``grid - battery``. Only the part of the load that the battery would otherwise deliver
    for counts: never more than that demand, never below 0, so a surplus (charging from
    solar) is not changed and the controller never charges from the grid for it.
    """
    demand = grid - battery
    return max(0.0, min(excluded, demand))
