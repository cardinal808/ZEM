"""Virtual set for shadow mode: what the grid would do if ZEPHYR were in control.

In shadow mode another system drives the real set. Computing from the real set's
power makes the controller chase that system's decisions and never close its own
loop: every step corrects an error it did not cause, so the counted writes and
direction swaps say little about live control (seen: ~400 "writes" per hour).

The twin instead takes ZEPHYR's own commands and behaves like a set (start-up,
ramp, report lag, the same model as ``sim/device.py``). The engine then works
with a virtual grid::

    P1_virtual(τ) = P1_measured(τ) − real set power(τ) + twin power(τ)

The house and the solar panels stay real; only the battery is swapped. The SOC,
temperatures and limits come from the real set.

The real set's power is only known from its last report, which shows the set
as it was 1-3 s ago (poll interval plus the set's own report lag). Mixing that
with the P1 of *now* put every change of the other system into the virtual
grid as a short spike, which the controller chased (simulation: 166-303 writes
against 98 live). So P1 and the twin are taken ``twin_delay`` (1.5 s) earlier,
from their history: a picture as if the meter were that much slower, and the
controller waits that much longer after a command (``extra_settle``).
Simulation with another controller driving the set: 86-110 writes, 98 live;
grid import and export within a few Wh per half hour.

Known limits: the delay is an estimate (the real poll age varies); the set's
own PV inputs are counted with the real set.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field, replace

from .models import AcMode, PackState, SetReport
from .settings import Settings

RAMP_DOWN = 2000.0
"""W/s a set needs to ramp down (measured: much faster than up)."""


@dataclass(slots=True)
class TwinSet:
    """One virtual set, following the commands ZEPHYR would send."""

    settings: Settings
    power: float = 0.0
    """AC power now, + charging."""
    ac_mode: AcMode = AcMode.CHARGE
    input_limit: int = 0
    output_limit: int = 0
    smart_mode: int = 1
    min_soc: float | None = None
    max_soc: float | None = None
    standby: bool = True
    _wake_at: float | None = None
    _at: float | None = None
    _history: deque[tuple[float, float]] = field(default_factory=lambda: deque(maxlen=200))

    def apply(self, now: float, props: dict[str, int]) -> None:
        """A command ZEPHYR would have sent."""
        self.advance(now)
        if "minSoc" in props:
            self.min_soc = props["minSoc"] / 10
        if "socSet" in props:
            self.max_soc = props["socSet"] / 10
        if "acMode" in props:
            self.ac_mode = AcMode(props["acMode"])
        self.input_limit = props.get("inputLimit", self.input_limit)
        self.output_limit = props.get("outputLimit", self.output_limit)
        self.smart_mode = props.get("smartMode", self.smart_mode)
        if self.input_limit == 0 and self.output_limit == 0 and self.smart_mode == 0:
            self.standby = True
            self._wake_at = None
        elif self.standby and (self.input_limit or self.output_limit):
            self.standby = False
            self._wake_at = now + self.settings.startup_time

    def _target(self, now: float) -> float:
        if self.standby or (self._wake_at is not None and now < self._wake_at):
            return 0.0
        if self.ac_mode is AcMode.CHARGE:
            return float(self.input_limit)
        return -float(self.output_limit)

    def advance(self, now: float) -> float:
        """Move the power towards the command up to ``now``; returns the power."""
        if self._at is None:
            self._at = now
        dt = now - self._at
        if dt > 0:
            target = self._target(now)
            if target * self.power < 0:
                target = 0.0  # through zero on a change of direction
            up = abs(target) > abs(self.power)
            step = (self.settings.ramp_up_rate if up else RAMP_DOWN) * dt
            diff = target - self.power
            self.power = target if abs(diff) <= step else self.power + step * (1 if diff > 0 else -1)
            self._at = now
        if not self._history or self._history[-1][0] < now:
            self._history.append((now, self.power))
        return self.power

    def power_at(self, now: float, t: float) -> float:
        """The power at an earlier time ``t`` (from the history)."""
        self.advance(now)
        value = self._history[0][1] if self._history else 0.0
        for at, p in self._history:
            if at <= t:
                value = p
            else:
                break
        return value

    def reported(self, now: float) -> float:
        """The power as the set would report it (``report_lag`` behind)."""
        return self.power_at(now, now - self.settings.report_lag)

    def view(self, real: SetReport, now: float) -> SetReport:
        """The real report with the battery swapped for the twin."""
        p = self.reported(now)
        charge, deliver = max(p, 0.0), max(-p, 0.0)
        relay = 0 if self.standby else 2 if self.ac_mode is AcMode.CHARGE else 1
        return replace(
            real,
            battery_power_ac=p,
            grid_input_power=charge,
            output_home_power=deliver,
            charge_power_ac=charge,
            deliver_power_ac=deliver,
            ac_mode=self.ac_mode,
            input_limit=self.input_limit,
            output_limit=self.output_limit,
            smart_mode=self.smart_mode,
            ac_status=relay if real.ac_status is not None else None,
            pack_state=PackState.CHARGING if charge > 20 else PackState.DELIVERING if deliver > 20 else PackState.STANDBY,
            min_soc=self.min_soc if self.min_soc is not None else real.min_soc,
            max_soc=self.max_soc if self.max_soc is not None else real.max_soc,
        )


@dataclass(slots=True)
class GridTally:
    """Import and export in Wh since the start, from the P1 reports."""

    import_wh: float = 0.0
    export_wh: float = 0.0
    _last: tuple[float, float] | None = None

    def add(self, now: float, watts: float) -> None:
        if self._last is not None:
            t, w = self._last
            dt = now - t
            if 0 < dt < 120:  # longer gaps: no data, not a constant
                wh = w * dt / 3600
                if wh > 0:
                    self.import_wh += wh
                else:
                    self.export_wh -= wh
        self._last = (now, watts)
