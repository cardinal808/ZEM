"""Planner: one action per price slot, lowest total cost over the horizon (SPEC-planner §1, §3).

Dynamic programming backwards over the slots, with the energy in the battery in
``steps`` steps (linear interpolation between them) and the previous action as
state (for the switching costs). Then a forward pass from the real energy gives
the plan. Pure Python, no Home Assistant; the HA layer and the backtest feed it.

Actions (§1):

* ``L`` charge from the grid at full power (solar surplus goes in too);
* ``H`` hold: the battery does not deliver, the house takes from the grid
  (solar surplus still goes in);
* ``N`` deliver what the house needs (zero on the meter);
* ``X`` deliver at full power, the rest to the grid (only when allowed).

Not yet in this version: calibration penalty (§3.5), efficiency per power band
(§6, a fixed efficiency per direction is used), PU1, PU2, PU4–PU6 (§12). PU3 (wear
cost per kWh) is a setting, off by default until the backtest justifies a value.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final


class Action(StrEnum):
    CHARGE = "L"
    HOLD = "H"
    DELIVER = "N"
    EXPORT = "X"


GROUPS: Final = (Action.CHARGE, Action.HOLD, Action.DELIVER)
"""Previous-action states: X counts as N for the switching costs (§3.4)."""


def _group(action: Action) -> Action:
    return Action.DELIVER if action is Action.EXPORT else action


@dataclass(frozen=True, slots=True)
class Slot:
    hours: float
    """Duration (h)."""
    buy: float
    """All-in import price (€/kWh)."""
    sell: float
    """Export price (€/kWh), may be negative."""
    load_kwh: float
    """House consumption in the slot (without separately counted loads)."""
    solar_kwh: float


@dataclass(frozen=True, slots=True)
class Battery:
    capacity_kwh: float
    """Usable energy between min_SOC (0) and max_SOC (capacity)."""
    charge_kw: float
    deliver_kw: float
    eta_in: float = 0.93
    eta_out: float = 0.93
    reserve_kwh: float = 0.0
    """Buffer (B37): the bottom part of ``capacity_kwh`` the planner never plans to deliver from.
    Charging into it is allowed; energy in it is worth the mean buy price (``plan``), so it is
    refilled when that is cheaper than buying the shortfall later."""


@dataclass(frozen=True, slots=True)
class PlannerSettings:
    steps: int = 40
    charge_start_cost: float = 0.02
    hold_start_cost: float = 0.005
    allow_export: bool = False
    """Action X (B12: off by default)."""
    load_margin: float = 0.0
    """Plan with this share more consumption when choosing (not in the costs)."""
    wear_cost: float = 0.0
    """€ per kWh delivered by the battery (PU3): weighs wear in the choice, not in the grid costs.
    Keeps the planner from cycling the battery for a few cents (especially with X)."""
    grid_charge_cost: float = 0.0
    """€ per kWh charged from the grid (L), in the choice only: grid charging must win at least
    this much per kWh. Keeps the planner from buying at an expensive moment for a cent of gain
    that rests on a forecast (e.g. topping up before the sun to export the solar with a bonus)."""
    curtail: bool = False
    """Surplus solar is curtailed when the export price is negative (the inverter is limited, by
    ZEPHYR or another system). Without that the surplus is exported and pays the negative price,
    so the planner makes room in the battery before such hours."""


@dataclass(frozen=True, slots=True)
class Step:
    """The result of one action in one slot."""

    energy_after: float
    grid_import: float
    grid_export: float
    cost: float
    charged: float
    """kWh into the battery (AC side)."""
    delivered: float
    """kWh out of the battery (AC side)."""
    grid_charged: float = 0.0
    """kWh from the grid into the battery (L, AC side)."""
    spill: float = 0.0
    """Solar surplus that fits neither the house nor the battery (exported, or curtailed at a negative price)."""


def step(slot: Slot, battery: Battery, energy: float, action: Action, load_margin: float = 0.0, curtail: bool = False) -> Step:
    """Energy flows and cost of ``action`` in ``slot`` from ``energy`` (§3.2)."""
    load = slot.load_kwh * (1 + load_margin)
    direct = min(load, slot.solar_kwh)
    need = load - direct
    surplus = slot.solar_kwh - direct
    # Solar surplus goes into the battery first; what does not fit is exported.
    room = battery.capacity_kwh - energy
    into = min(surplus, room / battery.eta_in) if room > 0 else 0.0
    s1 = energy + into * battery.eta_in
    spill = surplus - into
    charged, delivered, grid_charged = into, 0.0, 0.0
    imp, exp = need, spill
    if action is Action.CHARGE:
        extra = min(battery.charge_kw * slot.hours, (battery.capacity_kwh - s1) / battery.eta_in)
        extra = max(extra, 0.0)
        s1 += extra * battery.eta_in
        imp += extra
        charged += extra
        grid_charged = extra
    elif action is Action.DELIVER:
        out = min(need, max(s1 - battery.reserve_kwh, 0.0) * battery.eta_out, battery.deliver_kw * slot.hours)
        s1 -= out / battery.eta_out
        imp -= out
        delivered = out
    elif action is Action.EXPORT:
        out = min(max(s1 - battery.reserve_kwh, 0.0) * battery.eta_out, battery.deliver_kw * slot.hours)
        s1 -= out / battery.eta_out
        house = min(need, out)
        imp -= house
        exp += out - house
        delivered = out
    # A negative export price: surplus solar is either curtailed (earns nothing) or exported and
    # pays the negative price. Battery export (X) always pays the price it gets.
    if slot.sell >= 0 or not curtail:
        cost = imp * slot.buy - exp * slot.sell
    else:
        battery_export = exp - spill if action is Action.EXPORT else 0.0
        cost = imp * slot.buy - battery_export * slot.sell
        exp = battery_export
    return Step(max(min(s1, battery.capacity_kwh), 0.0), imp, exp, cost, charged, delivered, grid_charged, spill)


@dataclass(slots=True)
class Plan:
    actions: list[Action] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    cost: float = 0.0
    """Expected net cost over the horizon (grid only, without switching costs or end value)."""


def _choice(cfg: PlannerSettings, r: Step) -> float:
    """Costs that only steer the choice (not in the grid costs): wear and the grid-charge threshold."""
    return cfg.wear_cost * r.delivered + cfg.grid_charge_cost * r.grid_charged


def _interp(values: list[float], energy: float, capacity: float, n: int) -> float:
    if capacity <= 0:
        return values[0]
    x = max(0.0, min(energy / capacity * n, float(n)))
    i = min(int(x), n - 1)
    frac = x - i
    return values[i] * (1 - frac) + values[i + 1] * frac


def plan(
    slots: Sequence[Slot],
    battery: Battery,
    energy_now: float,
    settings: PlannerSettings | None = None,
    previous: Action = Action.DELIVER,
) -> Plan:
    """The cheapest action per slot from ``energy_now`` (kWh above min_SOC)."""
    cfg = settings or PlannerSettings()
    n = cfg.steps
    cap = battery.capacity_kwh
    if not slots:
        return Plan()
    actions = [Action.CHARGE, Action.HOLD, Action.DELIVER] + ([Action.EXPORT] if cfg.allow_export else [])
    grid = [cap * i / n for i in range(n + 1)]
    # End value: what is left is worth the cheapest price in the horizon (§3.3).
    end_price = min(s.buy for s in slots) * (1.0 if cfg.allow_export else battery.eta_out)
    # B37: energy in the buffer is worth what a shortfall would cost later (mean buy price).
    reserve = min(battery.reserve_kwh, cap)
    reserve_price = max(sum(s.buy for s in slots) / len(slots) * battery.eta_out, end_price)

    def end_value(e: float) -> float:
        return -(min(e, reserve) * reserve_price + max(e - reserve, 0.0) * end_price)

    future: dict[Action, list[float]] = {g: [end_value(e) for e in grid] for g in GROUPS}

    def switch(prev: Action, action: Action) -> float:
        if action is Action.CHARGE and prev is not Action.CHARGE:
            return cfg.charge_start_cost
        if action is Action.HOLD and prev is not Action.HOLD:
            return cfg.hold_start_cost
        return 0.0

    tables: list[dict[Action, list[float]]] = [future]
    for slot in reversed(slots):
        options = [a for a in actions if not (a is Action.EXPORT and slot.sell <= 0)]
        # Per energy step: cost + value after, per action (independent of the previous action).
        after: list[list[tuple[Action, float]]] = []
        for e in grid:
            row = []
            for a in options:
                r = step(slot, battery, e, a, cfg.load_margin, cfg.curtail)
                row.append((a, r.cost + _choice(cfg, r) + _interp(future[_group(a)], r.energy_after, cap, n)))
            after.append(row)
        current = {prev: [min(v + switch(prev, a) for a, v in row) for row in after] for prev in GROUPS}
        tables.append(current)
        future = current
    tables.reverse()  # tables[t] = value from slot t onwards; tables[len] = end value

    result = Plan()
    energy, prev = energy_now, _group(previous)
    for t, slot in enumerate(slots):
        options = [a for a in actions if not (a is Action.EXPORT and slot.sell <= 0)]
        best: tuple[float, Action, Step] | None = None
        for a in options:
            r = step(slot, battery, energy, a, cfg.load_margin, cfg.curtail)
            total = r.cost + _choice(cfg, r) + switch(prev, a) + _interp(tables[t + 1][_group(a)], r.energy_after, cap, n)
            if best is None or total < best[0] - 1e-12:
                best = (total, a, r)
        assert best is not None
        _, a, r = best
        # The real costs use the real load (the margin only steers the choice).
        real = step(slot, battery, energy, a, curtail=cfg.curtail) if cfg.load_margin else r
        result.actions.append(a)
        result.steps.append(real)
        result.cost += real.cost
        energy, prev = real.energy_after, _group(a)
    return result
