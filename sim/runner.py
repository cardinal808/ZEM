"""Closed-loop simulation: house + P1 meter + ZemEngine + simulated sets."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field

from zem_core.engine import Mode, SetView, StepResult, ZemEngine
from zem_core.settings import Settings

from .device import SimSet

Profile = Callable[[float], float]
"""Watts as a function of time in seconds."""


def constant(watts: float) -> Profile:
    return lambda t: watts


def steps(*points: tuple[float, float]) -> Profile:
    """Piecewise constant: (start_time, watts) pairs."""
    pts = sorted(points)

    def f(t: float) -> float:
        value = 0.0
        for start, watts in pts:
            if t >= start:
                value = watts
        return value

    return f


@dataclass
class Trace:
    t: list[float] = field(default_factory=list)
    grid: list[float] = field(default_factory=list)
    battery: list[float] = field(default_factory=list)
    setpoint: list[int] = field(default_factory=list)
    soc: list[float] = field(default_factory=list)
    results: list[tuple[float, StepResult]] = field(default_factory=list)


@dataclass
class Simulation:
    load: Profile
    solar: Profile = field(default_factory=lambda: constant(0.0))
    sets: list[SimSet] = field(default_factory=lambda: [SimSet()])
    settings: Settings = field(default_factory=Settings)
    mode: Mode = Mode.ZERO_METER
    p1_interval: float = 1.0
    p1_jitter: float = 0.0
    """The meter interval varies uniformly by up to ± this many seconds (fixed seed)."""
    step_interval: float | None = None
    """How often ZEM steps (Home Assistant: 1 s). None: on every P1 report."""
    p1_outages: list[tuple[float, float]] = field(default_factory=list)
    """(start, end) periods without P1 reports."""
    poll_interval: float = 2.0
    write_delay: float = 0.2
    dt: float = 0.1
    discharge_blocked: Callable[[float], bool] = field(default_factory=lambda: lambda t: False)
    engine: ZemEngine = field(init=False)

    def __post_init__(self) -> None:
        self.engine = ZemEngine(self.settings, self.mode)

    def grid(self) -> float:
        # + import. Battery power + = charging (takes from the house).
        return self.load(self.now) - self.solar(self.now) + sum(s.power for s in self.sets)

    def run(self, duration: float, start: float = 0.0) -> Trace:
        self.now = start
        trace = Trace()
        next_p1 = start
        next_step = start
        next_poll = start
        rng = random.Random(1)
        reports = {i: s.report(start) for i, s in enumerate(self.sets)}
        pending: list[tuple[float, int, dict[str, int]]] = []
        steps_total = round(duration / self.dt)
        for _ in range(steps_total):
            for s in self.sets:
                s.advance(self.now, self.dt)
            for item in [p for p in pending if p[0] <= self.now]:
                pending.remove(item)
                self.sets[item[1]].apply(self.now, item[2])
            if self.now >= next_poll:
                for i, s in enumerate(self.sets):
                    if s.online:
                        reports[i] = s.report(self.now)
                next_poll += self.poll_interval
            due_step = False
            if self.now >= next_p1:
                next_p1 += self.p1_interval + (rng.uniform(-self.p1_jitter, self.p1_jitter) if self.p1_jitter else 0.0)
                if not any(a <= self.now < b for a, b in self.p1_outages):
                    self.engine.p1_reported(self.now, self.grid())
                due_step = self.step_interval is None
            if self.step_interval is not None and self.now >= next_step:
                next_step += self.step_interval
                due_step = True
            if due_step:
                views = [SetView(str(i), i + 1, reports[i], self.sets[i].online) for i in range(len(self.sets))]
                result = self.engine.step(self.now, views, discharge_blocked=self.discharge_blocked(self.now))
                for cmd in result.commands:
                    pending.append((self.now + self.write_delay, int(cmd.key), cmd.props))
                trace.results.append((self.now, result))
                trace.setpoint.append(result.setpoint)
                if result.mode_finished:
                    self.engine.set_mode(Mode.ZERO_METER, self.now)
            trace.t.append(self.now)
            trace.grid.append(self.grid())
            trace.battery.append(sum(s.power for s in self.sets))
            trace.soc.append(self.sets[0].soc)
            self.now = round(self.now + self.dt, 6)
        return trace


def share_within(trace: Trace, target: float, band: float, start: float = 0.0) -> float:
    vals = [g for t, g in zip(trace.t, trace.grid, strict=True) if t >= start]
    return sum(1 for g in vals if abs(g - target) <= band) / max(1, len(vals))


def time_to_settle(trace: Trace, after: float, target: float, band: float, hold: float = 3.0) -> float | None:
    """Seconds after ``after`` until the grid stays within the band for ``hold`` s."""
    inside_since: float | None = None
    for t, g in zip(trace.t, trace.grid, strict=True):
        if t < after:
            continue
        if abs(g - target) <= band:
            inside_since = t if inside_since is None else inside_since
            if t - inside_since >= hold:
                return inside_since - after
        else:
            inside_since = None
    return None


def energy_wh(trace: Trace, sign: int, start: float = 0.0, end: float = 1e18) -> float:
    """Grid import (sign +1) or export (sign −1) energy in Wh."""
    dt = trace.t[1] - trace.t[0] if len(trace.t) > 1 else 0.1
    return sum(max(sign * g, 0.0) for t, g in zip(trace.t, trace.grid, strict=True) if start <= t < end) * dt / 3600


def writes(sim: Simulation) -> int:
    return sum(len(s.writes) for s in sim.sets)
