"""Planned appliances (B36)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from zephyr_core.appliances import (
    DISHWASHER,
    DRYER_CONDENSER,
    DRYER_HEAT_PUMP,
    WASHER,
    PlannedRun,
    Run,
    default_profile,
    detect_runs,
    learned_profile,
    place_runs,
    profile_kwh,
    quarter_energy,
)

T0 = datetime(2026, 11, 28, 8, 0, tzinfo=UTC)


def test_default_profiles_match_the_spec() -> None:
    assert profile_kwh(default_profile(DISHWASHER)) == pytest.approx(1.0, abs=0.1)
    assert profile_kwh(default_profile(WASHER)) == pytest.approx(0.8, abs=0.1)
    assert profile_kwh(default_profile(DRYER_HEAT_PUMP)) == pytest.approx(1.2, abs=0.05)
    assert profile_kwh(default_profile(DRYER_CONDENSER)) == pytest.approx(2.5, abs=0.05)
    assert len(default_profile(DRYER_CONDENSER)) == 105


def _series(parts: list[tuple[int, float]], start: datetime = T0) -> list[tuple[datetime, float]]:
    """State changes: (minutes, W) parts."""
    out, at = [], start
    for minutes, watts in parts:
        out.append((at, watts))
        at += timedelta(minutes=minutes)
    out.append((at, 0.0))
    return out


def test_detect_runs_skips_short_pulses_and_splits_runs() -> None:
    # A 1-minute tap pulse, a washing run of 60 min, a pause of 30 min, a second run of 40 min.
    series = _series([(1, 2000.0), (20, 0.0), (20, 2000.0), (40, 150.0), (30, 0.0), (40, 600.0), (20, 0.0)])
    runs = detect_runs(series)
    assert [r.minutes for r in runs] == [60, 40]
    assert runs[0].start == T0 + timedelta(minutes=21)
    assert runs[0].kwh == pytest.approx(2.0 * 20 / 60 + 0.15 * 40 / 60, abs=0.01)
    assert runs[1].kwh == pytest.approx(0.6 * 40 / 60, abs=0.01)


def test_a_short_dip_does_not_split_a_run() -> None:
    series = _series([(30, 1500.0), (3, 0.0), (30, 1500.0), (10, 0.0)])
    assert [r.minutes for r in detect_runs(series)] == [63]


def test_learned_profile_after_three_runs() -> None:
    def run(watts: float, minutes: int) -> Run:
        return Run(T0, minutes, watts * minutes / 60000, tuple([watts] * minutes))

    assert learned_profile([run(1000, 60), run(1200, 70)]) is None
    profile = learned_profile([run(1000, 60), run(1200, 70), run(1100, 65)])
    assert profile is not None and len(profile) == 65 and profile[0] == 1100


def test_quarter_energy() -> None:
    parts = quarter_energy(default_profile(WASHER), T0 + timedelta(minutes=5))
    assert sum(parts.values()) == pytest.approx(profile_kwh(default_profile(WASHER)))
    assert min(parts) == T0 and parts[T0] == pytest.approx(2.0 * 10 / 60)


def _price(at: datetime) -> float:
    """Expensive morning, cheap from 12:00 to 15:00."""
    return 0.10 if 12 <= at.hour < 15 else 0.40


def _cost(extra: dict[datetime, float]) -> float:
    return sum(kwh * _price(q) for q, kwh in extra.items())


def test_best_start_in_the_cheap_hours_and_dryer_after_washer() -> None:
    washer = PlannedRun("Wasmachine", T0, T0 + timedelta(hours=12))
    dryer = PlannedRun("Droger", T0, T0 + timedelta(hours=12), after="Wasmachine")
    profiles = {"Wasmachine": default_profile(WASHER), "Droger": default_profile(DRYER_CONDENSER)}
    extra = place_runs([dryer, washer], profiles, T0, _cost)
    assert washer.best_start is not None and dryer.best_start is not None
    assert 12 <= washer.best_start.hour < 15
    assert dryer.best_start >= washer.best_start + timedelta(minutes=120)
    assert washer.details["saving"] > 0.05
    assert sum(extra.values()) == pytest.approx(profile_kwh(profiles["Wasmachine"]) + profile_kwh(profiles["Droger"]))


def test_no_gain_keeps_the_earliest_start() -> None:
    run = PlannedRun("Vaatwasser", T0, T0 + timedelta(hours=10))
    place_runs([run], {"Vaatwasser": default_profile(DISHWASHER)}, T0, lambda extra: 1.0)
    assert run.best_start == T0


def test_fixed_start_and_round_trip() -> None:
    run = PlannedRun("Wasmachine", T0, T0 + timedelta(hours=4), fixed_start=T0 + timedelta(hours=1))
    place_runs([run], {}, T0, _cost)
    assert run.best_start == T0 + timedelta(hours=1)
    assert PlannedRun.from_dict(run.as_dict()).fixed_start == run.fixed_start


def test_plan_places_the_washer_on_the_sun_when_export_pays_little() -> None:
    """2027-like prices: export earns 0.05, import costs 0.30; solar 1.5 kWh/quarter from 11 to 14."""
    from zephyr_core.forecast_plan import BatteryInput, HorizonSlot, plan_appliances, with_appliances
    from zephyr_core.planner import PlannerSettings

    slots = []
    for q in range(48):  # 08:00–20:00
        start = T0 + timedelta(minutes=15 * q)
        sun = 1.5 if 11 <= start.hour < 14 else 0.0
        slots.append(HorizonSlot(start, 0.2, 0.30, 0.05, 0.1, sun, False))
    empty = BatteryInput(capacity_kwh=11.04, soc=10.0, min_soc=10.0, max_soc=95.0, charge_kw=2.4, deliver_kw=2.4)
    run = PlannedRun("Wasmachine", T0, T0 + timedelta(hours=12))
    extra = plan_appliances(slots, empty, T0, PlannerSettings(), [run], {"Wasmachine": default_profile(WASHER)})
    assert run.best_start is not None and 11 <= run.best_start.hour < 13
    assert run.details["saving"] > 0
    loaded = with_appliances(slots, extra)
    assert sum(s.appliance_kwh for s in loaded) == pytest.approx(profile_kwh(default_profile(WASHER)))


def test_two_washes_one_after_the_other() -> None:
    runs = [PlannedRun("Wasmachine", T0, T0 + timedelta(hours=12)) for _ in range(2)]
    place_runs(runs, {"Wasmachine": default_profile(WASHER)}, T0, _cost)
    first, second = sorted(r.best_start for r in runs if r.best_start)
    assert second >= first + timedelta(minutes=120)


def test_standard_windows() -> None:
    from zoneinfo import ZoneInfo

    from zephyr_core.appliances import standard_window

    tz = ZoneInfo("Europe/Amsterdam")
    evening = datetime(2026, 11, 28, 21, 30, tzinfo=tz)
    # Dishwasher: from now, done by 07:00 (next morning).
    assert standard_window(evening, "", "07:00") == (evening, datetime(2026, 11, 29, 7, 0, tzinfo=tz))
    # Washer 08:00–20:00: at 21:30 it is tomorrow's window; at 10:00 from now.
    assert standard_window(evening, "08:00", "20:00") == (datetime(2026, 11, 29, 8, tzinfo=tz), datetime(2026, 11, 29, 20, tzinfo=tz))
    morning = datetime(2026, 11, 28, 10, 0, tzinfo=tz)
    assert standard_window(morning, "08:00", "20:00") == (morning, datetime(2026, 11, 28, 20, tzinfo=tz))


def test_run_cost_is_its_own_share_not_the_whole_plan() -> None:
    """The panel shows what one run costs: the plan's cost with the run minus without it."""
    washer = PlannedRun("Wasmachine", T0, T0 + timedelta(hours=12))
    profiles = {"Wasmachine": default_profile(WASHER)}
    place_runs([washer], profiles, T0, lambda extra: 5.0 + _cost(dict(extra)))  # 5.0: rest of the plan
    assert washer.best_start is not None
    own = sum(kwh * _price(q) for q, kwh in quarter_energy(profiles["Wasmachine"], washer.best_start).items())
    assert washer.details["cost"] == pytest.approx(own, abs=0.001)
    assert washer.details["cost_now"] - washer.details["cost"] == pytest.approx(washer.details["saving"], abs=0.001)
