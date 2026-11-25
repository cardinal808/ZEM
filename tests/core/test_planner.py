"""Planner (SPEC-planner §3, §10): near the brute-force optimum, sensible plans."""

from __future__ import annotations

import itertools
import random
import time

import pytest

from zephyr_core.planner import Action, Battery, PlannerSettings, Slot, plan, step

BAT = Battery(capacity_kwh=4.0, charge_kw=2.4, deliver_kw=2.4, eta_in=0.92, eta_out=0.92)
Q = 0.25


def objective(slots: list[Slot], actions: tuple[Action, ...], battery: Battery, energy: float, cfg: PlannerSettings) -> float:
    """Grid cost + switching costs − end value, as the planner weighs it."""
    total, prev = 0.0, Action.DELIVER
    for slot, a in zip(slots, actions, strict=True):
        if a is Action.EXPORT and slot.sell <= 0:
            return float("inf")
        group = Action.DELIVER if a is Action.EXPORT else a
        if group is Action.CHARGE and prev is not Action.CHARGE:
            total += cfg.charge_start_cost
        if group is Action.HOLD and prev is not Action.HOLD:
            total += cfg.hold_start_cost
        r = step(slot, battery, energy, a)
        total += r.cost + cfg.wear_cost * r.delivered
        energy, prev = r.energy_after, group
    end_price = min(s.buy for s in slots) * (1.0 if cfg.allow_export else battery.eta_out)
    return total - energy * end_price


def brute_force(slots: list[Slot], battery: Battery, energy: float, cfg: PlannerSettings) -> float:
    actions = [Action.CHARGE, Action.HOLD, Action.DELIVER] + ([Action.EXPORT] if cfg.allow_export else [])
    return min(objective(slots, combo, battery, energy, cfg) for combo in itertools.product(actions, repeat=len(slots)))


def _random_slots(rng: random.Random, n: int) -> list[Slot]:
    out = []
    for _ in range(n):
        buy = rng.uniform(0.05, 0.45)
        solar = rng.choice([0.0, 0.0, rng.uniform(0, 1.0)])
        out.append(Slot(Q, buy, buy - 0.12 + rng.uniform(-0.02, 0.02), rng.uniform(0.05, 0.6), solar))
    return out


@pytest.mark.parametrize(("allow_export", "wear"), [(False, 0.0), (True, 0.0), (True, 0.04)])
def test_within_half_a_cent_of_brute_force(allow_export: bool, wear: float) -> None:
    rng = random.Random(7)
    cfg = PlannerSettings(steps=100, allow_export=allow_export, wear_cost=wear)
    for _ in range(12):
        slots = _random_slots(rng, 6 if allow_export else 7)
        energy = rng.uniform(0, BAT.capacity_kwh)
        result = plan(slots, BAT, energy, cfg)
        got = objective(slots, tuple(result.actions), BAT, energy, cfg)
        assert got <= brute_force(slots, BAT, energy, cfg) + 0.005


def test_charges_cheap_and_delivers_expensive() -> None:
    slots = [Slot(1.0, 0.10, 0.0, 0.3, 0.0)] * 4 + [Slot(1.0, 0.40, 0.2, 0.8, 0.0)] * 4
    result = plan(slots, Battery(4.0, 2.4, 2.4), 0.0)
    assert Action.CHARGE in result.actions[:4]
    assert result.actions[4:] == [Action.DELIVER] * 4
    assert all(s.grid_import == pytest.approx(0.0, abs=1e-9) for s in result.steps[4:6])


def test_no_charging_when_spread_does_not_cover_losses() -> None:
    slots = [Slot(1.0, 0.20, 0.0, 0.3, 0.0)] * 4 + [Slot(1.0, 0.21, 0.0, 0.3, 0.0)] * 4
    result = plan(slots, Battery(4.0, 2.4, 2.4), 0.0)
    assert Action.CHARGE not in result.actions


def test_holds_for_the_evening_peak() -> None:
    # Battery full; a mild price now and a high one later: keep the energy for later.
    slots = [Slot(1.0, 0.22, 0.0, 1.0, 0.0)] * 4 + [Slot(1.0, 0.45, 0.0, 1.0, 0.0)] * 4
    result = plan(slots, Battery(4.0, 2.4, 2.4), 4.0)
    assert result.actions[:4] == [Action.HOLD] * 4
    assert result.actions[4:] == [Action.DELIVER] * 4


def test_negative_export_price_never_exports() -> None:
    slots = [Slot(Q, -0.05, -0.10, 0.1, 1.0)] * 8
    result = plan(slots, BAT, 3.0, PlannerSettings(allow_export=True))
    assert Action.EXPORT not in result.actions
    assert all(s.cost >= -1e-9 or s.grid_export == 0 for s in result.steps)


def test_two_days_of_quarters_in_under_a_second() -> None:
    rng = random.Random(1)
    slots = _random_slots(rng, 192)
    start = time.perf_counter()
    plan(slots, Battery(9.4, 2.4, 2.4), 5.0, PlannerSettings(steps=40))
    assert time.perf_counter() - start < 1.0


def test_wear_cost_stops_cycling_for_a_small_spread() -> None:
    # Spread 0.10 → 0.30: worth cycling without wear, not with €0.25/kWh wear.
    slots = [Slot(1.0, 0.10, 0.0, 0.3, 0.0)] * 4 + [Slot(1.0, 0.30, 0.15, 0.8, 0.0)] * 4
    assert Action.CHARGE in plan(slots, Battery(4.0, 2.4, 2.4), 0.0).actions
    assert Action.CHARGE not in plan(slots, Battery(4.0, 2.4, 2.4), 0.0, PlannerSettings(wear_cost=0.25)).actions
