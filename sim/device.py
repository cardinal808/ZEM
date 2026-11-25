"""Model of one Zendure set, tuned to our measurements (MEET-zensdk, OPNAME-analyse-1).

- Starting from standby takes ``startup`` seconds before power flows.
- Power ramps up at ``ramp_up`` W/s and down at ``ramp_down`` W/s.
- The report lags ``report_lag`` seconds behind reality.
- Charging stops at the set's own maximum SOC, delivering at its minimum.
"""

from __future__ import annotations

import copy
import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from zephyr_core.models import SetReport
from zephyr_core.zensdk import parse_report, validate_command

TEMPLATE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "report_standby.json"


@dataclass
class SimSet:
    serial: str = "EEB4AEXAMPLE001"
    capacity_kwh: float = 11.04
    soc: float = 50.0
    max_power: float = 2400.0
    startup: float = 2.5
    ramp_up: float = 330.0
    ramp_down: float = 2000.0
    report_lag: float = 1.0
    efficiency: float = 0.92
    min_soc: float = 10.0
    max_soc: float = 100.0
    fault: bool = False
    online: bool = True
    relay_off_on_zero: bool = False
    """Seen live (2400 Pro, 25-11): with both limits 0 in RAM the relay opens (acStatus 0) and the
    next start takes ``startup`` seconds again, as from standby."""

    power: float = 0.0
    """Actual AC power, + charging."""
    ac_mode: int = 2
    input_limit: int = 0
    output_limit: int = 0
    smart_mode: int = 0
    standby: bool = True
    _wake_at: float | None = None
    _history: deque[tuple[float, float, float]] = field(default_factory=lambda: deque(maxlen=400))
    writes: list[tuple[float, dict[str, int]]] = field(default_factory=list)

    def apply(self, now: float, props: dict[str, int]) -> None:
        validate_command(props)
        self.writes.append((now, dict(props)))
        if "minSoc" in props:
            self.min_soc = props["minSoc"] / 10
        if "socSet" in props:
            self.max_soc = props["socSet"] / 10
        self.ac_mode = props.get("acMode", self.ac_mode)
        self.input_limit = props.get("inputLimit", self.input_limit)
        self.output_limit = props.get("outputLimit", self.output_limit)
        self.smart_mode = props.get("smartMode", self.smart_mode)
        if self.input_limit == 0 and self.output_limit == 0 and (self.smart_mode == 0 or self.relay_off_on_zero):
            self.standby = True
            self._wake_at = None
        elif self.standby and (self.input_limit or self.output_limit):
            self.standby = False
            self._wake_at = now + self.startup

    def _target(self) -> float:
        if self.fault:
            return 0.0
        if self.ac_mode == 1 and self.input_limit > 0 and self.soc < self.max_soc:
            return float(min(self.input_limit, self.max_power))
        if self.ac_mode == 2 and self.output_limit > 0 and self.soc > self.min_soc:
            return -float(min(self.output_limit, self.max_power))
        return 0.0

    def advance(self, now: float, dt: float) -> None:
        target = 0.0 if (self._wake_at is not None and now < self._wake_at) else self._target()
        if target * self.power < 0:
            target = 0.0  # pass through zero on a change of direction
        diff = target - self.power
        up = abs(target) > abs(self.power)
        rate = self.ramp_up if up else self.ramp_down
        step = rate * dt
        self.power = target if abs(diff) <= step else self.power + step * (1 if diff > 0 else -1)
        energy_kwh = self.power * dt / 3600 / 1000
        if self.power > 0:
            self.soc += 100 * energy_kwh * self.efficiency / self.capacity_kwh
        else:
            self.soc += 100 * energy_kwh / self.efficiency / self.capacity_kwh
        self.soc = min(100.0, max(0.0, self.soc))
        self._history.append((now, self.power, self.soc))

    def report(self, now: float) -> SetReport:
        lagged_power, lagged_soc = self.power, self.soc
        for t, p, soc in reversed(self._history):
            if t <= now - self.report_lag:
                lagged_power, lagged_soc = p, soc
                break
        data: dict[str, Any] = copy.deepcopy(json.loads(TEMPLATE.read_text()))
        props = data["properties"]
        data["sn"] = self.serial
        charge = max(lagged_power, 0.0)
        deliver = max(-lagged_power, 0.0)
        props.update(
            {
                "electricLevel": round(lagged_soc),
                "gridInputPower": round(charge),
                "outputHomePower": round(deliver),
                "outputPackPower": round(charge),
                "packInputPower": round(deliver),
                "packState": 1 if charge > 20 else 2 if deliver > 20 else 0,
                "acMode": self.ac_mode,
                "inputLimit": self.input_limit,
                "outputLimit": self.output_limit,
                "smartMode": self.smart_mode,
                "minSoc": round(self.min_soc * 10),
                "socSet": round(self.max_soc * 10),
                "is_error": 1 if self.fault else 0,
            }
        )
        for pack in data["packData"]:
            pack["state"] = props["packState"]
            pack["power"] = round(abs(lagged_power) / len(data["packData"]))
        return parse_report(data)
