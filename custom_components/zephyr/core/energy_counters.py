"""Own energy counters per set (SPEC-tellers, T1 and T2).

zenSDK reports power only. ZEPHYR integrates the powers of each set into counters that only
go up (kWh), per set (by serial number) and for the installation. A read that fails keeps
the last power for ``HOLD`` seconds after the last good report; after that a gap starts.

When the set reports again the gap is filled (T2, SPEC-tellers §5):

1. **interpolate** (gap ≤ 15 min, same direction, power before and after within 20 % or
   200 W): the power linearly between the report before and after the gap, checked against
   the change of the energy in the packs;
2. **from the SOC** otherwise: the change of the energy in the packs (Σ capacity × SOC per
   pack) divided by the charge efficiency, or times the delivery efficiency. Net only.

A restart of Home Assistant is a gap from the last stored state. Times are wall-clock
seconds (epoch), so a gap over a restart can be measured. Filled energy also counts in
``estimated`` and is logged per gap.

The installation totals keep a state of their own and add the increases of the sets, so a
set that disappears or is replaced never makes them drop.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Final

from .models import SetReport

HOLD: Final = 60.0
"""Seconds after the last good report during which the last power keeps counting."""
INTERPOLATE_MAX: Final = 15 * 60.0
"""Longest gap that may be filled by interpolating the power."""
ETA_IN: Final = 0.92
"""Charge efficiency (AC → battery) for filling from the SOC, until one is learned (T4)."""
ETA_OUT: Final = 0.88
"""Delivery efficiency (battery → AC)."""
GAPS_KEPT: Final = 50

COUNTER_KEYS: Final = ("charged", "discharged", "solar", "offgrid", "dc_charged", "dc_discharged", "grid_input", "output_home")
TOTAL_KEYS: Final = ("charged", "discharged", "solar")

DaylightFn = Callable[[float, float], bool]
"""Was there daylight between two epoch times (e.g. at the middle)?"""


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


def _mode(report: SetReport) -> tuple[int | None, int | None]:
    return (
        None if report.ac_mode is None else int(report.ac_mode),
        None if report.pack_state is None else int(report.pack_state),
    )


def _iso(epoch: float | None) -> str | None:
    return None if epoch is None else datetime.fromtimestamp(epoch, UTC).isoformat(timespec="seconds")


def _close(before: Mapping[str, float], after: Mapping[str, float]) -> bool:
    """Power before and after a gap about the same (20 % or 200 W) for charging and delivering."""
    for key in ("charged", "discharged"):
        b, a = before.get(key, 0.0), after.get(key, 0.0)
        if abs(b - a) > max(200.0, 0.2 * max(b, a)):
            return False
    return True


@dataclass(slots=True)
class Gap:
    """A stretch without good reports longer than HOLD."""

    start: float
    """Epoch time the counting stopped (last good report + HOLD, or the last stored state)."""
    powers: dict[str, float]
    pack_kwh: float | None
    mode: tuple[int | None, int | None]
    restart: bool = False
    pack_at: float | None = None
    """Epoch time of ``pack_kwh`` (the last good report); the held energy since then counts against ΔE."""


@dataclass(slots=True)
class SetCounter:
    """Counters of one set."""

    serial: str
    kwh: dict[str, float] = field(default_factory=lambda: dict.fromkeys(COUNTER_KEYS, 0.0))
    estimated: dict[str, float] = field(default_factory=lambda: dict.fromkeys(COUNTER_KEYS, 0.0))
    has_solar: bool = False
    has_offgrid: bool = False
    last_t: float | None = None
    """Epoch time up to which energy has been counted."""
    last_good: float | None = None
    powers: dict[str, float] = field(default_factory=dict)
    pack_kwh: float | None = None
    capacity_kwh: float | None = None
    mode: tuple[int | None, int | None] = (None, None)
    gap: Gap | None = None
    gaps: list[dict[str, Any]] = field(default_factory=list)
    failed_reads: int = 0
    restored: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "kwh": {k: round(v, 5) for k, v in self.kwh.items()},
            "estimated": {k: round(v, 5) for k, v in self.estimated.items() if v},
            "has_solar": self.has_solar,
            "has_offgrid": self.has_offgrid,
            "last_t": self.last_t,
            "last_good": self.last_good,
            "powers": {k: round(v, 1) for k, v in self.powers.items()},
            "pack_kwh": None if self.pack_kwh is None else round(self.pack_kwh, 4),
            "capacity_kwh": self.capacity_kwh,
            "mode": list(self.mode),
            "gaps": self.gaps[-GAPS_KEPT:],
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
        last_t, last_good = data.get("last_t"), data.get("last_good")
        counter.last_t = None if last_t is None else float(last_t)
        counter.last_good = None if last_good is None else float(last_good)
        counter.powers = {str(k): float(v) for k, v in (data.get("powers") or {}).items()}
        pack, capacity = data.get("pack_kwh"), data.get("capacity_kwh")
        counter.pack_kwh = None if pack is None else float(pack)
        counter.capacity_kwh = None if capacity is None else float(capacity)
        mode = [*(data.get("mode") or []), None, None]
        counter.mode = (mode[0], mode[1])
        counter.restored = counter.last_t is not None
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

    def _credit(self, counter: SetCounter, energy: Mapping[str, float], estimated: bool = False) -> None:
        for key, kwh in energy.items():
            if kwh <= 0:
                continue
            counter.kwh[key] += kwh
            if estimated:
                counter.estimated[key] += kwh
            if key in self.totals:
                self.totals[key] += kwh

    def _add(self, counter: SetCounter, until: float) -> None:
        """Count the held powers from ``last_t`` up to ``until``."""
        if counter.last_t is None or until <= counter.last_t:
            return
        hours = (until - counter.last_t) / 3600
        self._credit(counter, {k: w / 1000 * hours for k, w in counter.powers.items()})
        counter.last_t = until

    def _open_gap(self, counter: SetCounter, start: float) -> None:
        if counter.gap is None:
            counter.gap = Gap(
                start, dict(counter.powers), counter.pack_kwh, counter.mode, restart=counter.restored, pack_at=counter.last_good
            )

    def observe(
        self,
        serial: str,
        report: SetReport | None,
        now: float,
        *,
        good: bool,
        capacities: Mapping[str, float] | None = None,
        daylight: DaylightFn | None = None,
    ) -> dict[str, Any] | None:
        """After every read of a set (``now`` in epoch seconds).

        ``good`` with a fresh ``report``, otherwise a failed read. Returns the log entry of a
        gap that was closed (and filled) by this report, else None.
        """
        counter = self.counter(serial)
        if not good or report is None:
            counter.failed_reads += 1
            if counter.restored and counter.last_t is not None:
                if now - counter.last_t > HOLD:
                    self._open_gap(counter, counter.last_t)
            elif counter.last_good is not None:
                limit = counter.last_good + HOLD
                self._add(counter, min(now, limit))
                if now > limit:
                    self._open_gap(counter, limit)
            return None
        if counter.restored and counter.last_t is not None:
            # First report after a restart: the downtime since the last stored state is a gap.
            if now - counter.last_t > HOLD:
                self._open_gap(counter, counter.last_t)
            else:
                self._add(counter, now)
        elif counter.last_good is not None and now - counter.last_good > HOLD:
            self._add(counter, counter.last_good + HOLD)
            self._open_gap(counter, counter.last_t if counter.last_t is not None else counter.last_good + HOLD)
        else:
            self._add(counter, now)
        new_powers = powers(report)
        new_pack = pack_energy(report, capacities) if capacities is not None else None
        new_mode = _mode(report)
        closed = None
        if counter.gap is not None:
            closed = self._fill(counter, counter.gap, now, new_powers, new_pack, new_mode, daylight)
            counter.gap = None
        counter.restored = False
        counter.last_t = now
        counter.last_good = now
        counter.powers, counter.mode = new_powers, new_mode
        counter.has_solar = counter.has_solar or bool(report.solar_power_inputs)
        counter.has_offgrid = counter.has_offgrid or report.offgrid_power > 0
        if capacities is not None:
            counter.pack_kwh = new_pack
            known = [capacities[p.serial] for p in report.packs if p.serial in capacities]
            counter.capacity_kwh = sum(known) if known and len(known) == len(report.packs) else None
        return closed

    def _fill(
        self,
        counter: SetCounter,
        gap: Gap,
        now: float,
        after: Mapping[str, float],
        pack_after: float | None,
        mode_after: tuple[int | None, int | None],
        daylight: DaylightFn | None,
    ) -> dict[str, Any]:
        """Fill a gap that ends now (SPEC-tellers §5) and log it."""
        seconds = max(now - gap.start, 0.0)
        hours = seconds / 3600
        before = gap.powers
        delta = None if gap.pack_kwh is None or pack_after is None else pack_after - gap.pack_kwh
        # Energy already counted (held) between the last pack reading and the gap, battery side.
        held_hours = max(gap.start - gap.pack_at, 0.0) / 3600 if gap.pack_at is not None else 0.0
        held = (before.get("charged", 0.0) * ETA_IN - before.get("discharged", 0.0) / ETA_OUT) / 1000 * held_hours
        sunny = before.get("solar", 0.0) > 0 or after.get("solar", 0.0) > 0
        light = daylight(gap.start, now) if daylight is not None else sunny
        energy: dict[str, float] = {}
        method = "none"
        if seconds <= INTERPOLATE_MAX and gap.mode == mode_after and before and _close(before, after):
            energy = {k: (before.get(k, 0.0) + after.get(k, 0.0)) / 2 / 1000 * hours for k in COUNTER_KEYS}
            if not light:
                energy["solar"] = 0.0
            method = "interpolate"
            if delta is not None:
                battery_side = held + energy["charged"] * ETA_IN - energy["discharged"] / ETA_OUT
                tolerance = (counter.capacity_kwh or 0.0) * 0.01 + 0.02 * abs(delta)
                if abs(battery_side - delta) > tolerance:
                    energy, method = {}, "none"
        if method == "none" and delta is not None:
            method = "soc"
            rest = delta - held  # what the packs gained beyond the energy already held
            if abs(rest) < (counter.capacity_kwh or 0.0) * 0.01:
                energy = {}  # within the SOC resolution: nothing to fill
            elif rest > 0:
                energy = {"charged": rest / ETA_IN, "dc_charged": rest}
            else:
                energy = {"discharged": -rest * ETA_OUT, "dc_discharged": -rest}
            if light:
                energy["solar"] = before.get("solar", 0.0) / 1000 * hours
            if before.get("offgrid", 0.0) > 0:
                energy["offgrid"] = before["offgrid"] / 1000 * hours
        self._credit(counter, energy, estimated=True)
        entry = {
            "start": _iso(gap.start),
            "end": _iso(now),
            "seconds": round(seconds),
            "method": method,
            "restart": gap.restart,
            "kwh": {k: round(v, 4) for k, v in energy.items() if v > 0},
            "pack_delta_kwh": None if delta is None else round(delta, 4),
        }
        counter.gaps.append(entry)
        counter.gaps = counter.gaps[-GAPS_KEPT:]
        return entry

    def restore(self, data: Mapping[str, Any] | None) -> None:
        """Counter states from the store; the first report afterwards fills the downtime."""
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
                    "estimated": {k: round(v, 3) for k, v in c.estimated.items() if v},
                    "failed_reads": c.failed_reads,
                    "open_gap": None
                    if c.gap is None
                    else {"start": _iso(c.gap.start), "restart": c.gap.restart, "pack_kwh": c.gap.pack_kwh},
                    "gaps": c.gaps[-10:],
                }
                for c in chosen.values()
            ],
        }
