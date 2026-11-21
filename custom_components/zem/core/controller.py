"""Zero-meter controller (SPEC-basis §5).

Computes the total battery setpoint P_doel (+ charging, − delivering) from
the grid meter and the battery's current power. It is a position-form
controller: every step starts from what the battery does now, so there is
no integrator that can wind up, and it recovers at once after a restart.

Within the settling time after a command the last command counts as the
battery power (the report lags behind), so the same error is not
corrected twice (TOETS-specificaties).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .settings import Settings


class Direction(StrEnum):
    NONE = "none"
    CHARGE = "charge"
    DELIVER = "deliver"


@dataclass(frozen=True, slots=True)
class ControllerInput:
    now: float
    grid_power: float
    """P_net,corr in W (+ import)."""
    battery_power: float
    """Measured AC battery power in W (+ charging)."""
    max_charge: float
    """W the battery may charge now (0 = not allowed)."""
    max_deliver: float
    """W the battery may deliver now (0 = not allowed)."""
    p1_interval: float
    """Mean interval of the P1 meter in s."""
    sample: int | None = None
    """Number of the P1 sample; the controller decides once per sample (None: every step)."""


@dataclass(frozen=True, slots=True)
class ControllerOutput:
    setpoint: int
    """W, + charging, − delivering, rounded to 10 W."""
    demand: float
    """Full correction (gain 1), before limits: what the house asks of the battery."""
    regulated: bool
    """False when this step changed nothing (too soon, settling, dead zone)."""
    waiting_for_direction: bool
    """True while a change of direction is held back."""


def _sign_direction(value: float, threshold: float) -> Direction:
    if value > threshold:
        return Direction.CHARGE
    if value < -threshold:
        return Direction.DELIVER
    return Direction.NONE


def _round10(value: float) -> int:
    return int(round(value / 10.0) * 10)


class ZeroMeterController:
    """Stateful zero-meter controller for the total of all sets."""

    def __init__(self, settings: Settings, *, trust_commands: bool = True) -> None:
        self.settings = settings
        self.trust_commands = trust_commands
        """False in shadow mode: commands are not carried out."""
        self.setpoint = 0
        self._prev_setpoint = 0
        self._setpoint_at = -1e9
        self._last_step = -1e9
        self._error_at_command = 0.0
        self._last_direction = Direction.NONE
        self._pending: Direction = Direction.NONE
        self._pending_since: float | None = None
        self._start_count = 0
        self._deviation_since: float | None = None
        self._last_sample: int | None = None

    def reset(self, now: float) -> None:
        """Start from zero (mode change, restart, safety stop)."""
        self.setpoint = 0
        self._prev_setpoint = 0
        self._setpoint_at = now
        self._pending = Direction.NONE
        self._pending_since = None
        self._start_count = 0
        self._deviation_since = None

    # --- helpers -------------------------------------------------------

    def _settle_time(self, p1_interval: float) -> float:
        s = self.settings
        ramp = max(0.0, abs(self.setpoint) - abs(self._prev_setpoint))
        starting = self._prev_setpoint == 0 or self._prev_setpoint * self.setpoint < 0
        if self._prev_setpoint * self.setpoint < 0:
            ramp = abs(self.setpoint)
        settle = ramp / s.ramp_up_rate + s.report_lag + (s.startup_time if starting and self.setpoint != 0 else 0.0)
        return max(s.min_settle, settle, p1_interval)

    def _effective_battery(self, inp: ControllerInput, settling: bool) -> float:
        """The battery power the controller starts from.

        With commands that are carried out (normal operation) that is the
        last command: the report lags behind, so the measurement would make
        the controller correct the same error twice. Only when the
        measurement keeps deviating (the set cannot or will not follow) does
        the measurement count. In shadow mode nothing is carried out, so the
        measurement always counts.
        """
        s = self.settings
        if not self.trust_commands:
            return inp.battery_power
        if settling:
            self._deviation_since = None
            return float(self.setpoint)
        if abs(inp.battery_power - self.setpoint) > s.deviation_limit:
            if self._deviation_since is None:
                self._deviation_since = inp.now
            if inp.now - self._deviation_since >= s.deviation_time:
                return inp.battery_power
        else:
            self._deviation_since = None
        return float(self.setpoint)

    # --- main step -----------------------------------------------------

    def step(self, inp: ControllerInput) -> ControllerOutput:
        s = self.settings
        slow = inp.p1_interval > s.slow_p1_interval
        gain_import = s.slow_gain if slow else s.gain_import
        gain_export = s.slow_gain if slow else s.gain_export
        deadband = s.slow_deadband if slow else s.deadband

        if inp.now - self._last_step < s.min_step_interval:
            return self._unchanged(inp, regulated=False)
        if inp.sample is not None:
            if inp.sample == self._last_sample:
                return self._unchanged(inp, regulated=False)  # nothing new measured
            self._last_sample = inp.sample

        settling = inp.now - self._setpoint_at < self._settle_time(inp.p1_interval)
        battery = self._effective_battery(inp, settling)

        # Target on the grid depends on whether we would charge or deliver.
        target = s.target_grid_deliver
        demand = battery - (inp.grid_power - target)
        if demand > 0:
            target = s.target_grid_charge
            demand = battery - (inp.grid_power - target)
        error = inp.grid_power - target

        if settling:
            # Only react during settling when things got clearly worse (export or a new jump).
            worse = abs(error) > abs(self._error_at_command) + 300 or (error < -100 and self.setpoint <= 0)
            if not worse:
                return self._unchanged(inp, regulated=False, demand=demand)

        if abs(error) < deadband and self._pending is Direction.NONE:
            self._last_step = inp.now
            return self._unchanged(inp, regulated=False, demand=demand)

        gain = gain_import if error > 0 else gain_export
        raw = battery - gain * error
        raw = min(raw, inp.max_charge) if raw > 0 else max(raw, -inp.max_deliver)
        demand_limited = min(demand, inp.max_charge) if demand > 0 else max(demand, -inp.max_deliver)

        # Minimum power with start hysteresis: start only after two samples above it.
        wanted = _sign_direction(demand_limited, s.switch_threshold)
        if abs(demand_limited) < s.min_power:
            self._start_count = 0
            if abs(demand_limited) < 0.8 * s.min_power or self.setpoint == 0:
                raw = 0.0
                wanted = Direction.NONE
        elif self.setpoint == 0:
            self._start_count += 1
            if self._start_count < 2:
                raw = 0.0
                wanted = Direction.NONE
            else:
                raw = max(abs(raw), s.min_power) * (1 if raw > 0 else -1)
        else:
            self._start_count = 0

        # Change of direction only after it persisted (SPEC-basis §5.4).
        waiting = False
        if wanted is not Direction.NONE and self._last_direction is not Direction.NONE and wanted is not self._last_direction:
            if self._pending is not wanted:
                self._pending = wanted
                self._pending_since = inp.now
            assert self._pending_since is not None
            if inp.now - self._pending_since < s.switch_delay:
                raw = 0.0
                waiting = True
            else:
                self._pending = Direction.NONE
                self._pending_since = None
        elif wanted is self._last_direction or wanted is Direction.NONE:
            self._pending = Direction.NONE
            self._pending_since = None

        new = _round10(raw)
        if 0 < abs(new) < s.min_power:
            # Hysteresis: an active set stays at the minimum while demand ≥ 80 % of it.
            keep = self.setpoint != 0 and abs(demand_limited) >= 0.8 * s.min_power
            new = s.min_power * (1 if new > 0 else -1) if keep else 0
        self._last_step = inp.now
        if new != self.setpoint:
            self._prev_setpoint = self.setpoint
            self.setpoint = new
            self._setpoint_at = inp.now
            self._error_at_command = error
        if new > 0:
            self._last_direction = Direction.CHARGE
        elif new < 0:
            self._last_direction = Direction.DELIVER
        return ControllerOutput(setpoint=self.setpoint, demand=demand, regulated=True, waiting_for_direction=waiting)

    def _unchanged(self, inp: ControllerInput, *, regulated: bool, demand: float | None = None) -> ControllerOutput:
        # Limits may have changed (full/empty/blocked): respect them immediately.
        limited = self.setpoint
        if limited > inp.max_charge:
            limited = int(inp.max_charge) // 10 * 10
        if limited < -inp.max_deliver:
            limited = -(int(inp.max_deliver) // 10 * 10)
        if 0 < abs(limited) < self.settings.min_power:
            limited = 0
        if limited != self.setpoint:
            self._prev_setpoint = self.setpoint
            self.setpoint = limited
            self._setpoint_at = inp.now
        return ControllerOutput(
            setpoint=self.setpoint,
            demand=demand if demand is not None else float(self.setpoint),
            regulated=regulated,
            waiting_for_direction=self._pending is not Direction.NONE,
        )
