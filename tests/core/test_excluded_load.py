"""B41 (SPEC-airco): a load the battery may not feed, estimated from a coarse energy counter."""

from __future__ import annotations

import pytest

from zephyr_core.excluded_load import ExcludedLoad, exclusion_for_controller


def _counter_run(load: ExcludedLoad, start: float = 0.0) -> None:
    # Like the air conditioner seen live: +0.25 kWh every 8-9 minutes (~1.8 kW).
    for i, kwh in enumerate((115.0, 115.25, 115.5)):
        load.observe_counter(kwh, start + i * 500)


def test_power_from_counter_steps_and_fading_out() -> None:
    load = ExcludedLoad()
    load.observe_counter(115.0, 0)
    assert load.power(100) == 0  # one reading: nothing measured yet
    _counter_run(load)
    assert load.power(1000) == pytest.approx(1800)
    assert load.power(1300) == pytest.approx(1800)  # within the step interval: keep the estimate
    assert load.power(2000) == pytest.approx(900)  # no step for 1000 s: at most 0.25 kWh / 1000 s
    load.observe_counter(115.5, 2100)  # an equal reading is no step
    assert load.power(2100) == pytest.approx(0.25 * 3_600_000 / 1100)


def test_climate_mode_and_action_switch_at_once() -> None:
    load = ExcludedLoad(blocked_modes=("heat",), has_climate=True)
    load.observe_climate("heat", "heating", 0)
    _counter_run(load)
    assert load.power(1000) == pytest.approx(1800)
    load.observe_climate("heat", "idle", 1010)
    assert load.power(1010) == 0  # stopped: no waiting for the counter
    load.observe_climate("heat", "heating", 3000)
    assert load.power(3000) == pytest.approx(1800)  # start: power of the previous run
    load.observe_counter(115.75, 3450)  # first step measured from the start, not from the idle time
    assert load.power(3450) == pytest.approx(2000)
    load.observe_climate("cool", "cooling", 3500)
    assert load.power(3500) == 0  # cooling may come from the battery
    assert not load.active()


def test_without_climate_always_active_and_counter_reset_is_reference() -> None:
    load = ExcludedLoad()
    assert load.active()
    _counter_run(load)
    load.observe_counter(0.1, 1100)  # counter reset
    assert load.power(1100) == pytest.approx(1800)  # keeps the estimate, fades from the reset
    load.observe_counter(0.35, 1110)  # too close: noise, not a measurement
    assert load.power(1110) <= 4000


def test_exclusion_never_exceeds_the_house_demand() -> None:
    # Delivering 760 W, 300 W import: demand 1060 W.
    assert exclusion_for_controller(500, 300, -760) == 500
    assert exclusion_for_controller(2000, 300, -760) == 1060
    # Charging from solar: no demand, the surplus is untouched.
    assert exclusion_for_controller(2000, -200, 500) == 0


def test_energy_total_counts_only_while_excluded() -> None:
    load = ExcludedLoad(blocked_modes=("heat",), has_climate=True)
    load.observe_counter(10.0, 0)
    load.observe_climate("heat", "heating", 0)
    load.observe_counter(10.25, 500)
    load.observe_climate("cool", "cooling", 600)
    load.observe_counter(10.5, 1000)  # cooling: may come from the battery
    assert load.energy_total == pytest.approx(0.25)


def test_solar_for_the_planner_with_an_excluded_load() -> None:
    from datetime import UTC, datetime

    from zephyr_core.forecast_plan import HorizonSlot, solar_for_planner

    def slot(solar: float, excluded: float) -> HorizonSlot:
        return HorizonSlot(datetime(2026, 11, 26, tzinfo=UTC), 0.1, 0.3, 0.3, 0.2, solar, False, excluded)

    # Rest of the house 0.2 kWh, air conditioner 0.4 kWh in this quarter.
    assert solar_for_planner(slot(0.1, 0.4)) == pytest.approx(0.1)  # all solar for the rest
    assert solar_for_planner(slot(0.5, 0.4)) == pytest.approx(0.2)  # rest covered, no surplus for the battery
    assert solar_for_planner(slot(0.9, 0.4)) == pytest.approx(0.5)  # surplus once the air conditioner is covered
    assert solar_for_planner(slot(0.5, 0.0)) == pytest.approx(0.5)


def test_history_hour_and_blocked_share() -> None:
    from datetime import UTC, datetime, timedelta

    from zephyr_core.load_profile import HourEnergy, blocked_share, profile_from_history

    t0 = datetime(2026, 11, 25, 12, tzinfo=UTC)
    hour = HourEnergy(t0, import_kwh=2.5, export_kwh=0.0, solar_kwh=0.3, battery_kwh=0.0, excluded_kwh=1.8)
    assert hour.house_kwh == pytest.approx(1.0)
    assert profile_from_history([hour], excluded=True).expected("workday", 12) == pytest.approx(1.8)
    changes = [(t0 - timedelta(hours=1), "heat"), (t0 + timedelta(minutes=45), "off")]
    assert blocked_share(changes, t0, t0 + timedelta(hours=1), ["heat"]) == pytest.approx(0.75)
    assert blocked_share(changes, t0, t0 + timedelta(hours=1), ["cool"]) == 0
