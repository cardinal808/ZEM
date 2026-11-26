"""The planner in Home Assistant, shadow only (SPEC-planner §4, §5; PT1, PT2, PT5, PT8, PT11)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.zephyr.const import DOMAIN
from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets
from .test_shadow import P1, _install_with_p1

PRICE = "sensor.nordpool_test"
SOLCAST_TOMORROW = "sensor.solcast_pv_forecast_forecast_tomorrow"
SOLCAST_TODAY = "sensor.solcast_pv_forecast_forecast_today"
DAY = [0.05] * 6 + [0.15] * 11 + [0.40] * 4 + [0.15] * 3


@pytest.fixture(autouse=True)
async def _test_day(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    """Every test starts on 26-11-2026 in Amsterdam, so prices set before `_setup` are for that day (not the real one)."""
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 26, 0, 0, 0, tzinfo=dt_util.get_default_time_zone()))


def _raw(day_offset: int, prices: list[float]) -> list[dict[str, Any]]:
    start = dt_util.start_of_local_day() + timedelta(days=day_offset)
    return [{"start": start + timedelta(hours=h), "end": start + timedelta(hours=h + 1), "value": v} for h, v in enumerate(prices)]


def _set_prices(hass: HomeAssistant, today: int = 0, tomorrow: bool = True) -> None:
    hass.states.async_set(
        PRICE,
        "0.1",
        {"raw_today": _raw(today, DAY), "raw_tomorrow": _raw(today + 1, DAY) if tomorrow else [], "unit": "kWh"},
    )


async def _tick(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: int, step: int = 5) -> None:
    for _ in range(seconds // step):
        freezer.tick(timedelta(seconds=step))
        hass.states.async_set(P1, "300", {"device_class": "power", "unit_of_measurement": "W"}, force_update=True)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()


async def _setup(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, at: tuple[int, int], **options: Any) -> Any:
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 26, *at, 0, tzinfo=dt_util.get_default_time_zone()))
    entry = await _install_with_p1(hass, fake_sets)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": P1, **options})
    await hass.async_block_till_done()
    return entry


async def test_plan_in_shadow_mode(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 26, 1, 0, 0, tzinfo=dt_util.get_default_time_zone()))
    _set_prices(hass)
    half_hours = [
        {"period_start": dt_util.start_of_local_day() + timedelta(days=1, hours=12, minutes=30 * i), "pv_estimate": 1.0} for i in range(4)
    ]
    hass.states.async_set(SOLCAST_TOMORROW, "4", {"detailedForecast": half_hours})
    entry = await _setup(hass, fake_sets, freezer, (1, 0), price_entity=PRICE, solar_forecast_entity=SOLCAST_TOMORROW)
    writes = len(fake_sets.writes)
    await _tick(hass, freezer, 10)

    action = hass.states.get("sensor.zephyr_plan_action")
    assert action is not None
    assert action.state in ("charge", "hold", "deliver")
    assert action.attributes["code"] in ("L", "H", "N")
    assert action.attributes["shadow"] is True
    assert len(action.attributes["timeline"]) == 23 * 4 + 96  # 01:00 today to the end of tomorrow
    assert hass.states.get("sensor.zephyr_plan_state").state == "active"
    reason = hass.states.get("sensor.zephyr_plan_reason").state
    assert reason and reason != "unknown"
    assert float(hass.states.get("sensor.zephyr_planned_grid_charge").state) >= 0
    assert hass.states.get("sensor.zephyr_planned_export").state == "0.0"
    assert hass.states.get("sensor.zephyr_plan_calculated_at").state not in ("unknown", "unavailable")
    # Shadow: the plan writes nothing to the set.
    assert len(fake_sets.writes) == writes

    diag = await async_get_config_entry_diagnostics(hass, entry)
    planner = diag["planner"]
    assert planner["settings"]["wear_cost"] == 0.03  # B39
    assert planner["inputs"]["solar_source"] == "forecast"
    assert planner["inputs"]["solar_entities"] == [SOLCAST_TOMORROW, SOLCAST_TODAY]
    assert planner["outcome"]["state"] == "active"
    assert len(planner["snapshots"]) == 1
    noon_tomorrow = dt_util.start_of_local_day() + timedelta(days=1, hours=12)
    noon = [row for row in planner["timeline"] if datetime.fromisoformat(row["start"]) == noon_tomorrow]
    assert noon and noon[0]["solar"] == pytest.approx(0.25)

    # The cost log gets the plan of the quarter (B38).
    await _tick(hass, freezer, 900)
    costs = entry.runtime_data.costs
    record = costs.current[-1]
    assert record["start"] == dt_util.as_utc(datetime(2026, 11, 26, 1, 0, tzinfo=dt_util.get_default_time_zone())).isoformat()
    assert record["plan_action"] in ("L", "H", "N")
    assert isinstance(record["plan_cost"], float)


async def test_pt8_start_without_prices_then_plan(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    """The price sensor is not there yet: No prices (N), no error; a plan within a minute once it comes."""
    await _setup(hass, fake_sets, freezer, (14, 3), price_entity=PRICE)
    await _tick(hass, freezer, 10)
    assert hass.states.get("sensor.zephyr_plan_state").state == "no_prices"
    assert hass.states.get("sensor.zephyr_plan_action").state == "deliver"
    assert hass.states.get("sensor.zephyr_plan_reason").state.startswith("No price for this quarter")
    assert ir.async_get(hass).async_get_issue(DOMAIN, "price_format") is None
    _set_prices(hass)
    await _tick(hass, freezer, 5)
    assert hass.states.get("sensor.zephyr_plan_state").state == "active"


async def test_pt1_prices_of_yesterday_after_midnight(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    """At 00:30 the source still shows yesterday as 'today': No prices, never a plan on old prices."""
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 26, 0, 30, 0, tzinfo=dt_util.get_default_time_zone()))
    _set_prices(hass, today=-1, tomorrow=False)
    await _setup(hass, fake_sets, freezer, (0, 30), price_entity=PRICE)
    await _tick(hass, freezer, 10)
    assert hass.states.get("sensor.zephyr_plan_state").state == "no_prices"
    since = hass.states.get("sensor.zephyr_plan_state").attributes["no_prices_since"]
    # The source moves on: the next minute check plans again; "since" stayed put meanwhile.
    await _tick(hass, freezer, 60)
    assert hass.states.get("sensor.zephyr_plan_state").attributes["no_prices_since"] == since
    _set_prices(hass)
    await _tick(hass, freezer, 60)
    assert hass.states.get("sensor.zephyr_plan_state").state == "active"


async def test_pt5_unreadable_prices_raise_a_repair(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    hass.states.async_set(PRICE, "0.23", {"prices": [0.1, 0.2]})
    await _setup(hass, fake_sets, freezer, (10, 0), price_entity=PRICE)
    await _tick(hass, freezer, 10)
    assert hass.states.get("sensor.zephyr_plan_state").state == "no_prices"
    assert ir.async_get(hass).async_get_issue(DOMAIN, "price_format") is not None
    _set_prices(hass)
    await _tick(hass, freezer, 5)
    assert ir.async_get(hass).async_get_issue(DOMAIN, "price_format") is None


async def test_pt11_no_price_sensor_no_plan_entities(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _setup(hass, fake_sets, freezer, (10, 0))
    await _tick(hass, freezer, 10)
    assert entry.runtime_data.planner is None
    assert hass.states.get("sensor.zephyr_plan_action") is None


async def test_profile_learns_from_the_cost_log(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    """A whole hour of cost quarters becomes one hour in the profile (without a solar counter: no solar)."""
    _set_prices(hass)
    entry = await _setup(hass, fake_sets, freezer, (9, 59), price_entity=PRICE)
    planner = entry.runtime_data.planner
    assert planner.profile.mean_count == 0
    await _tick(hass, freezer, 60 + 3600)  # 10:00-11:00 complete
    assert planner.profile.mean_count == 1
    # House: 300 W import + 760 W from the battery ≈ 1.06 kWh in the hour.
    assert planner.profile.mean == pytest.approx(1.06, abs=0.03)


async def test_mode_dynamic_forecasting_follows_the_plan_in_shadow(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory
) -> None:
    """The mode exists only with a price sensor; in shadow mode the engine follows the plan, nothing is sent."""
    _set_prices(hass)
    entry = await _setup(hass, fake_sets, freezer, (1, 0), price_entity=PRICE)
    options = hass.states.get("select.zephyr_mode").attributes["options"]
    assert "dynamic_forecasting" in options
    fake_sets.answers["10.0.0.10"]["properties"]["electricLevel"] = 15  # nearly empty before the cheap night
    await _tick(hass, freezer, 10)
    writes = len(fake_sets.writes)
    await hass.services.async_call(
        "select", "select_option", {"entity_id": "select.zephyr_mode", "option": "dynamic_forecasting"}, blocking=True
    )
    await _tick(hass, freezer, 10, step=1)
    assert hass.states.get("select.zephyr_mode").state == "dynamic_forecasting"
    plan = hass.states.get("sensor.zephyr_plan_action").attributes["code"]
    control = entry.runtime_data.control
    assert control.runtime.planner.action_at(dt_util.utcnow()).value == plan
    result = control.result
    # Cheap night, expensive evening: charge from the grid at full power.
    assert plan == "L"
    assert result.reason.code.value == "plan_charge"
    assert result.setpoint == 2400
    assert hass.states.get("sensor.zephyr_action").state == "charge"
    assert len(fake_sets.writes) == writes  # shadow: nothing sent


async def test_no_forecast_mode_without_price_sensor(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    await _setup(hass, fake_sets, freezer, (10, 0))
    assert "dynamic_forecasting" not in hass.states.get("select.zephyr_mode").attributes["options"]


async def test_profile_first_fill_from_the_recorder(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With meter counters the profile starts from the recorder's hourly statistics, not from a few night hours."""
    from custom_components.zephyr import planner_runner

    imp, exp, solar = "sensor.meter_import", "sensor.meter_export", "sensor.solar_energy"
    asked: list[list[str]] = []

    async def fake_stats(hass: HomeAssistant, start: datetime, end: datetime, ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        asked.append(ids)
        rows: dict[str, list[dict[str, Any]]] = {i: [] for i in ids}
        t = start
        while t < end:
            local = dt_util.as_local(t)
            evening = 17 <= local.hour < 22
            ts = dt_util.as_utc(t).timestamp()
            rows[imp].append({"start": ts, "change": 0.2 if evening else 0.3})
            rows[exp].append({"start": ts, "change": 0.0})
            rows[solar].append({"start": ts, "change": 0.0})
            rows["sensor.zephyr_power"].append({"start": ts, "mean": -1000.0 if evening else 0.0})
            t += timedelta(hours=1)
        return rows

    monkeypatch.setattr(planner_runner, "hourly_statistics", fake_stats)
    hass.config.components.add("recorder")
    _set_prices(hass)
    entry = await _setup(
        hass,
        fake_sets,
        freezer,
        (7, 30),
        price_entity=PRICE,
        cost_import_counters=[imp],
        cost_export_counters=[exp],
        solar_energy_entity=solar,
    )
    planner = entry.runtime_data.planner
    assert asked and set(asked[-1]) == {imp, exp, solar, "sensor.zephyr_power"}
    assert planner.profile_source.startswith("recorder")
    assert planner.profile.expected("workday", 18) == pytest.approx(1.2)
    assert planner.profile.expected("workday", 3) == pytest.approx(0.3)
    await _tick(hass, freezer, 10)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["planner"]["inputs"]["profile_source"].startswith("recorder")


async def test_pt2_pt6_pt12_night_with_price_reserve(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, caplog: pytest.LogCaptureFixture
) -> None:
    """22:00–03:00: the source does not move on at midnight and then goes empty; ZEPHYR plans on the
    saved prices (Price reserve), also after a restart, and is back on the source as soon as it is."""
    entry = await _setup(hass, fake_sets, freezer, (22, 0), price_entity=PRICE)
    _set_prices(hass)
    await _tick(hass, freezer, 10)
    assert hass.states.get("sensor.zephyr_plan_state").state == "active"
    planner = entry.runtime_data.planner
    assert len(planner.reserve) >= 24

    # 23:59 the source drops tomorrow and keeps "today" = yesterday after midnight (PT1/PT12).
    await _tick(hass, freezer, 2 * 3600 - 60, step=30)
    _set_prices(hass, tomorrow=False)
    await _tick(hass, freezer, 60 + 600, step=30)
    assert hass.states.get("sensor.zephyr_plan_state").state == "price_reserve"
    assert hass.states.get("sensor.zephyr_plan_reason").state.startswith("Saved prices")
    assert hass.states.get("sensor.zephyr_plan_action").attributes["timeline"]

    # The source goes empty (PT2) and HA restarts (PT6): the reserve comes from the storage.
    hass.states.async_set(PRICE, "unavailable", {})
    await _tick(hass, freezer, 30)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    await _tick(hass, freezer, 20)
    assert hass.states.get("sensor.zephyr_plan_state").state == "price_reserve"
    assert entry.runtime_data.planner.inputs["price_source"] == "reserve"

    # 00:45: the source has today's prices again → plan on the source within a minute.
    _set_prices(hass, tomorrow=False)  # start_of_local_day is now the new day
    await _tick(hass, freezer, 60)
    assert hass.states.get("sensor.zephyr_plan_state").state == "active"
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["planner"]["snapshots"]
    assert not [r for r in caplog.records if r.levelname in ("ERROR", "CRITICAL") and "zephyr" in r.name]


async def test_b41_profile_without_the_air_conditioner(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """B41: the first fill takes the air conditioner out of the house while it was heating; it is learned apart."""
    from custom_components.zephyr import planner_runner

    imp, exp, airco, climate = "sensor.meter_import", "sensor.meter_export", "sensor.airco_energy", "climate.airco"

    async def fake_stats(hass: HomeAssistant, start: datetime, end: datetime, ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        rows: dict[str, list[dict[str, Any]]] = {i: [] for i in ids}
        t = start
        while t < end:
            midday = 11 <= dt_util.as_local(t).hour < 15
            ts = dt_util.as_utc(t).timestamp()
            rows[imp].append({"start": ts, "change": 2.2 if midday else 0.3})
            rows[exp].append({"start": ts, "change": 0.0})
            rows[airco].append({"start": ts, "change": 1.8 if midday else 0.0})
            rows["sensor.zephyr_power"].append({"start": ts, "mean": 0.0})
            t += timedelta(hours=1)
        return rows

    async def fake_climate(hass: HomeAssistant, start: datetime, end: datetime, entity: str) -> list[tuple[datetime, str | None]]:
        assert entity == climate
        return [(start, "heat")]

    monkeypatch.setattr(planner_runner, "hourly_statistics", fake_stats)
    monkeypatch.setattr(planner_runner, "climate_history", fake_climate)
    hass.config.components.add("recorder")
    _set_prices(hass)
    entry = await _setup(
        hass,
        fake_sets,
        freezer,
        (7, 30),
        price_entity=PRICE,
        cost_import_counters=[imp],
        cost_export_counters=[exp],
        excluded_energy_entity=airco,
        excluded_climate_entity=climate,
    )
    planner = entry.runtime_data.planner
    assert planner.profile.expected("workday", 12) == pytest.approx(0.4)  # 2.2 − 1.8
    assert planner.excluded_profile.expected("workday", 12) == pytest.approx(1.8)
    assert planner.excluded_profile.expected("workday", 3) == pytest.approx(0.0)

    # Live: a cost hour with 0.45 kWh air conditioner per quarter is learned without it.
    start = datetime(2026, 11, 26, 12, 0, tzinfo=dt_util.get_default_time_zone())
    for q in range(4):
        planner.quarter_closed(start + timedelta(minutes=15 * q), {"complete": True, "house_kwh": 0.55, "excluded_kwh": 0.45}, True)
    assert planner.profile.recent[-1][0] == pytest.approx(0.4)
    assert planner.excluded_profile.recent[-1][0] == pytest.approx(1.8)

    await _tick(hass, freezer, 10)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["planner"]["excluded_profile"] is not None
    assert all("excluded" in q for q in diag["planner"]["timeline"])


async def test_b41_existing_profile_is_filled_again_when_the_air_conditioner_is_added(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A profile learned with the air conditioner in it (Bjorn: 64 h) is replaced once the counter is set."""
    from custom_components.zephyr import planner_runner

    imp, exp, airco = "sensor.meter_import", "sensor.meter_export", "sensor.airco_energy"

    async def fake_stats(hass: HomeAssistant, start: datetime, end: datetime, ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        rows: dict[str, list[dict[str, Any]]] = {i: [] for i in ids}
        t = start
        while t < end:
            ts = dt_util.as_utc(t).timestamp()
            rows[imp].append({"start": ts, "change": 2.0})
            rows[exp].append({"start": ts, "change": 0.0})
            if airco in rows:
                rows[airco].append({"start": ts, "change": 1.5})
            rows["sensor.zephyr_power"].append({"start": ts, "mean": 0.0})
            t += timedelta(hours=1)
        return rows

    monkeypatch.setattr(planner_runner, "hourly_statistics", fake_stats)
    hass.config.components.add("recorder")
    _set_prices(hass)
    options = {"price_entity": PRICE, "cost_import_counters": [imp], "cost_export_counters": [exp]}
    entry = await _setup(hass, fake_sets, freezer, (7, 30), **options)
    planner = entry.runtime_data.planner
    assert planner.profile.mean_count >= 48 and planner.profile.expected("workday", 12) == pytest.approx(2.0)
    await planner._store.async_save(planner._data())  # as after a day of running

    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": P1, **options, "excluded_energy_entity": airco})
    await hass.async_block_till_done()
    planner = entry.runtime_data.planner
    assert planner.profile.expected("workday", 12) == pytest.approx(0.5)  # without a climate entity: always aside
    assert planner.excluded_profile.expected("workday", 12) == pytest.approx(1.5)
