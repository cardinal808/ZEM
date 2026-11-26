"""Totals over all sets: one virtual battery (SPEC-meerdere-sets §3)."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from .models import SetReport

KEEP_OFFLINE_ENERGY_SECONDS: Final = 300.0
"""An offline set keeps counting for SOC and capacity this long (V6)."""


@dataclass(frozen=True, slots=True)
class SetSnapshot:
    """What the totals need from one set."""

    report: SetReport | None
    capacity_kwh: float
    online: bool
    enabled: bool = True
    offline_since: float | None = None
    last_success: float | None = None
    """Monotonic time of the last good report (for the cost log's hold, B44 T0)."""


@dataclass(frozen=True, slots=True)
class Totals:
    """Totals as the planner and the entities see them. None = unknown."""

    soc: float | None
    """Capacity-weighted state of charge in %."""
    capacity_kwh: float | None
    energy_kwh: float | None
    power: float
    """Net battery power of the online sets: + charging, − delivering."""
    charge_power: float
    discharge_power: float
    solar_power: float
    sets_online: int
    sets_configured: int


def _counts_for_energy(s: SetSnapshot, now: float) -> bool:
    if not s.enabled or s.report is None or s.capacity_kwh <= 0:
        return False
    if s.online:
        return True
    return s.offline_since is not None and now - s.offline_since <= KEEP_OFFLINE_ENERGY_SECONDS


def compute_totals(sets: Iterable[SetSnapshot], now: float) -> Totals:
    """Combine the sets. Totals are unknown when no set counts (never 0)."""
    sets = list(sets)
    energy_sets = [s for s in sets if _counts_for_energy(s, now)]
    power_sets = [s for s in sets if s.online and s.report is not None]

    capacity = sum(s.capacity_kwh for s in energy_sets)
    if energy_sets and capacity > 0:
        energy = sum(s.capacity_kwh * s.report.soc / 100 for s in energy_sets if s.report is not None)
        soc: float | None = round(100 * energy / capacity, 1)
        capacity_out: float | None = round(capacity, 3)
        energy_out: float | None = round(energy, 3)
    else:
        soc = capacity_out = energy_out = None

    power = sum(s.report.battery_power_ac for s in power_sets if s.report is not None)
    charge = sum(max(s.report.battery_power_ac, 0.0) for s in power_sets if s.report is not None)
    discharge = sum(max(-s.report.battery_power_ac, 0.0) for s in power_sets if s.report is not None)
    solar = sum(s.report.solar_power for s in power_sets if s.report is not None)
    return Totals(
        soc=soc,
        capacity_kwh=capacity_out,
        energy_kwh=energy_out,
        power=round(power, 1),
        charge_power=round(charge, 1),
        discharge_power=round(discharge, 1),
        solar_power=round(solar, 1),
        sets_online=len(power_sets),
        sets_configured=len(sets),
    )


COST_HOLD_SECONDS: Final = 60.0
"""The cost log keeps counting a set's last power this long after its last good report (B44 HOLD)."""


@dataclass(frozen=True, slots=True)
class CostFlows:
    """Power flows of the sets as the cost log integrates them (B44 T0), W ≥ 0."""

    charge: float
    """Σ ``outputPackPower``: AC power into the batteries."""
    deliver: float
    """Σ ``packInputPower``: AC power out of the batteries."""
    solar: float
    """Σ ``solarInputPower``: the sets' own PV inputs."""
    complete: bool
    """Every enabled set counted (none beyond the hold)."""


def cost_flows(sets: Iterable[SetSnapshot], now: float, hold: float = COST_HOLD_SECONDS) -> CostFlows | None:
    """Battery and set-PV flows for the cost log; None when no set counts.

    Battery energy comes from the pack powers (``outputPackPower`` / ``packInputPower``), not
    from the set's net exchange with the house: that one includes the set's own PV, which
    the cost log counts as solar (otherwise it is counted twice). A set that cannot be read
    keeps its last values for ``hold`` seconds after its last good report.
    """
    enabled = [s for s in sets if s.enabled]
    counted = [s for s in enabled if s.report is not None and (s.online or (s.last_success is not None and now - s.last_success <= hold))]
    if not counted:
        return None
    return CostFlows(
        charge=sum(max(s.report.charge_power_ac, 0.0) for s in counted if s.report is not None),
        deliver=sum(max(s.report.deliver_power_ac, 0.0) for s in counted if s.report is not None),
        solar=sum(max(s.report.solar_power, 0.0) for s in counted if s.report is not None),
        complete=len(counted) == len(enabled),
    )
