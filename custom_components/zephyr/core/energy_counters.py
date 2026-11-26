"""Own energy counters per set (SPEC-tellers, T1).

zenSDK reports power only. ZEPHYR integrates the powers of each set into counters that only
go up (kWh), per set (by serial number) and for the installation. A read that fails keeps
the last power for ``HOLD`` seconds after the last good report; after that a gap starts. In
T1 a gap is only recorded (start, the set's state at its start); filling it follows in T2.

The installation totals keep a state of their own and add the increases of the sets, so a
set that disappears or is replaced never makes them drop.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, Final

from .models import SetReport

HOLD: Final = 60.0
"""Seconds after the last good report during which the last power keeps counting."""

COUNTER_KEYS: Final = ("charged", "discharged", "solar", "offgrid", "dc_charged", "dc_discharged", "grid_input", "output_home")
TOTAL_KEYS: Final = ("charged", "discharged", "solar")


def powers(report: SetReport) -> dict[str, float]:
    """Power per counter (W ≥ 0) from one report."""
    dc = report.battery_power_dc
    return {
        "charged": max(report.charge_power_ac, 0.0),
        "discharged": max(report.deliver_power_ac, 0.0),
        "solar": max(report.solar_power, 0.0),
        "offgrid": max(report.offgrid_power, 0.0),
        "dc_charged": max(dc, 0.0) if dc is not None else 0.0,
        "dc_discharged": max(-dc, 0.0) if dc is not None else 0.0,
        "grid_input": max(report.grid_input_power, 0.0),
        "output_home": max(report.output_home_power, 0.0),
    }


def pack_energy(report: SetReport, capacities: Mapping[str, float]) -> float | None:
    """Energy in the packs (kWh): Σ capacity × SOC per pack; None if a capacity is unknown."""
    if not report.packs:
        return None
    total = 0.0
    for pack in report.packs:
        capacity = capacities.get(pack.serial)
        if capacity is None:
            return None
        total += capacity * pack.soc / 100
    return total


@dataclass(slots=True)
class Gap:
    """A stretch without good reports longer than HOLD (filled in T2)."""

    start: float
    """Monotonic time the counting stopped (last good report + HOLD)."""
    start_wall: str | None
    """Wall-clock time of the start (ISO), for the diagnostics and after a restart."""
    powers: dict[str, float]
    pack_kwh: float | None
    end: float | None = None
    end_wall: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "start": self.start_wall,
            "end": self.end_wall,
            "seconds": None if self.end is None else round(self.end - self.start),
            "powers": {k: round(v, 1) for k, v in self.powers.items() if v},
            "pack_kwh": None if self.pack_kwh is None else round(self.pack_kwh, 3),
        }


@dataclass(slots=True)
class SetCounter:
    """Counters of one set."""

    serial: str
    kwh: dict[str, float] = field(default_factory=lambda: dict.fromkeys(COUNTER_KEYS, 0.0))
    estimated: dict[str, float] = field(default_factory=lambda: dict.fromkeys(COUNTER_KEYS, 0.0))
    has_solar: bool = False
    has_offgrid: bool = False
    last_t: float | None = None
    """Monotonic time up to which energy has been counted."""
    last_good: float | None = None
    powers: dict[str, float] = field(default_factory=dict)
    pack_kwh: float | None = None
    gap: Gap | None = None
    gaps: list[dict[str, Any]] = field(default_factory=list)
    failed_reads: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "kwh": {k: round(v, 5) for k, v in self.kwh.items()},
            "estimated": {k: round(v, 5) for k, v in self.estimated.items() if v},
            "has_solar": self.has_solar,
            "has_offgrid": self.has_offgrid,
            "gaps": self.gaps[-50:],
        }

    @classmethod
    def from_dict(cls, serial: str, data: Mapping[str, Any]) -> SetCounter:
        counter = cls(serial)
        for key in COUNTER_KEYS:
            counter.kwh[key] = float((data.get("kwh") or {}).get(key, 0.0))
            counter.estimated[key] = float((data.get("estimated") or {}).get(key, 0.0))
        counter.has_solar = bool(data.get("has_solar"))
        counter.has_offgrid = bool(data.get("has_offgrid"))
        counter.gaps = list(data.get("gaps") or [])
        return counter


class EnergyCounters:
    """Counters of all sets and the installation totals."""

    def __init__(self) -> None:
        self.sets: dict[str, SetCounter] = {}
        self.totals: dict[str, float] = dict.fromkeys(TOTAL_KEYS, 0.0)

    def counter(self, serial: str) -> SetCounter:
        if serial not in self.sets:
            self.sets[serial] = SetCounter(serial)
        return self.sets[serial]

    def _add(self, counter: SetCounter, until: float) -> None:
        """Count the held powers from ``last_t`` up to ``until``."""
        if counter.last_t is None or until <= counter.last_t:
            return
        hours = (until - counter.last_t) / 3600
        for key, watts in counter.powers.items():
            energy = watts / 1000 * hours
            if energy <= 0:
                continue
            counter.kwh[key] += energy
            if key in self.totals:
                self.totals[key] += energy
        counter.last_t = until

    def observe(
        self,
        serial: str,
        report: SetReport | None,
        now: float,
        *,
        good: bool,
        wall: str | None = None,
        capacities: Mapping[str, float] | None = None,
    ) -> None:
        """After every read of a set: ``good`` with a fresh ``report``, otherwise a failed read."""
        counter = self.counter(serial)
        if not good or report is None:
            counter.failed_reads += 1
            if counter.last_good is not None:
                limit = counter.last_good + HOLD
                self._add(counter, min(now, limit))
                if now > limit and counter.gap is None:
                    counter.gap = Gap(limit, wall, dict(counter.powers), counter.pack_kwh)
            return
        if counter.last_good is not None and now - counter.last_good > HOLD:
            self._add(counter, counter.last_good + HOLD)
            if counter.gap is None:
                counter.gap = Gap(counter.last_good + HOLD, None, dict(counter.powers), counter.pack_kwh)
        else:
            self._add(counter, now)
        if counter.gap is not None:
            counter.gap.end, counter.gap.end_wall = now, wall
            counter.gaps.append(counter.gap.as_dict())
            counter.gaps = counter.gaps[-50:]
            counter.gap = None
        counter.last_t = now
        counter.last_good = now
        counter.powers = powers(report)
        counter.has_solar = counter.has_solar or bool(report.solar_power_inputs)
        counter.has_offgrid = counter.has_offgrid or report.offgrid_power > 0
        if capacities is not None:
            counter.pack_kwh = pack_energy(report, capacities)

    def restore(self, data: Mapping[str, Any] | None) -> None:
        """Counter states from the store (a restart starts without powers: nothing is held)."""
        data = data or {}
        self.sets = {str(s): SetCounter.from_dict(str(s), d) for s, d in (data.get("sets") or {}).items()}
        stored = data.get("totals") or {}
        self.totals = {k: float(stored.get(k, 0.0)) for k in TOTAL_KEYS}

    def as_dict(self) -> dict[str, Any]:
        return {"sets": {s: c.as_dict() for s, c in self.sets.items()}, "totals": {k: round(v, 5) for k, v in self.totals.items()}}

    def diagnostics(self, serials: Iterable[str] | None = None) -> dict[str, Any]:
        chosen = self.sets if serials is None else {s: self.sets[s] for s in serials if s in self.sets}
        return {
            "totals": {k: round(v, 3) for k, v in self.totals.items()},
            "sets": [
                {
                    "kwh": {k: round(v, 3) for k, v in c.kwh.items()},
                    "failed_reads": c.failed_reads,
                    "open_gap": None if c.gap is None else c.gap.as_dict(),
                    "gaps": c.gaps[-10:],
                }
                for c in chosen.values()
            ],
        }
