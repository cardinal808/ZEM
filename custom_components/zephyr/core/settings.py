"""Settings with defaults and validation (SPEC-basis §11).

Every setting has a default, so ZEPHYR works without filling anything in.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, replace
from typing import Any


class SettingsError(ValueError):
    """A setting is outside its allowed range."""


@dataclass(frozen=True, slots=True)
class Settings:
    # Battery limits
    min_soc: float = 10.0
    """%, 5–50."""
    max_soc: float = 95.0
    """%, 70–100."""
    max_charge_power: int | None = None
    """W; None = device limit."""
    max_deliver_power: int | None = None
    """W; None = device limit."""
    standby_after: float = 300.0
    """s without a setpoint before a set goes to standby."""
    recharge_below_min_power: int = 300
    """W used to recharge when the SOC dropped below the minimum."""

    # Controller (advanced)
    target_grid_deliver: float = 15.0
    """W on the grid while delivering (+ = import)."""
    target_grid_charge: float = -30.0
    """W on the grid while charging from solar surplus (− = export)."""
    gain_import: float = 1.0
    gain_export: float = 1.0
    """Share of the grid error corrected per step. 1.0 because the controller
    waits until the set has settled (simulation, M3); SPEC-basis started at 0.7/0.9."""
    deadband: float = 25.0
    min_power: int = 100
    """W; smaller setpoints become 0."""
    switch_threshold: float = 50.0
    """W the new direction must exceed ..."""
    switch_delay: float = 10.0
    """... for this many seconds before charging and delivering swap."""
    min_step_interval: float = 2.0
    """s between controller steps."""
    ramp_up_rate: float = 330.0
    """W/s the set needs to ramp up (measured)."""
    min_settle: float = 3.0
    startup_time: float = 2.5
    """s a set needs to start from 0 W / standby (measured)."""
    report_lag: float = 1.5
    """s the report lags behind the set."""
    deviation_limit: float = 200.0
    """W between command and measurement that counts as "set cannot follow" ..."""
    deviation_time: float = 15.0
    """... when it lasts this many seconds."""

    # P1 meter
    p1_stale_after: float = 10.0
    """s without a P1 report before the setpoint goes to 0 (at least 2.5 meter intervals)."""
    p1_balanced_silence: float = 30.0
    """s without a P1 report before 0 W while the last value was balanced (within the dead zone)."""
    p1_lost_after: float = 60.0
    """s without a P1 report before the sets go to standby (at least 6 meter intervals)."""
    slow_p1_interval: float = 2.5
    """Above this mean interval (s) the meter counts as slow."""
    too_slow_p1_interval: float = 25.0
    """Above this interval (s) zero-meter control stops. DSMR 4 meters send every 10 s."""
    slow_gain: float = 1.0
    """The controller waits for a new P1 value after the set has settled, so full correction is safe."""
    slow_deadband: float = 50.0

    # Blocks
    discharge_block_delay: float = 10.0

    def validated(self) -> Settings:
        """Return self when every value is in range; raise otherwise."""
        checks: dict[str, tuple[float, float]] = {
            "min_soc": (5, 50),
            "max_soc": (70, 100),
            "standby_after": (30, 3600),
            "recharge_below_min_power": (50, 2400),
            "target_grid_deliver": (-200, 200),
            "target_grid_charge": (-500, 100),
            "gain_import": (0.1, 1.0),
            "gain_export": (0.1, 1.0),
            "deadband": (0, 300),
            "min_power": (0, 500),
            "switch_threshold": (0, 500),
            "switch_delay": (0, 120),
            "min_step_interval": (0.5, 30),
        }
        for name, (lo, hi) in checks.items():
            value = getattr(self, name)
            if not lo <= value <= hi:
                raise SettingsError(f"{name}={value} outside {lo}–{hi}")
        for name in ("max_charge_power", "max_deliver_power"):
            value = getattr(self, name)
            if value is not None and not 0 <= value <= 10000:
                raise SettingsError(f"{name}={value} outside 0–10000")
        if self.min_soc >= self.max_soc:
            raise SettingsError("min_soc must be below max_soc")
        return self

    def with_changes(self, **changes: Any) -> Settings:
        known = {f.name for f in fields(self)}
        unknown = set(changes) - known
        if unknown:
            raise SettingsError(f"unknown settings: {sorted(unknown)}")
        return replace(self, **changes).validated()
