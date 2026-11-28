"""Cost log (B38): quarters closed on the clock, sensors, export, kept over a reload."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.zephyr.const import DOMAIN
from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets
from .test_shadow import P1, _install_with_p1

PRICE = "sensor.nordpool_test"
IMPORT = ("sensor.meter_energy_consumed_tariff_1", "sensor.meter_energy_consumed_tariff_2")
EXPORT = ("sensor.meter_energy_produced_tariff_1", "sensor.meter_energy_produced_tariff_2")
ENERGY = {"device_class": "energy", "state_class": "total_increasing", "unit_of_measurement": "kWh"}


def _prices(hass: HomeAssistant) -> None:
    start = dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)
    raw = [{"start": start + timedelta(hours=h), "end": start + timedelta(hours=h + 1), "value": 0.10} for h in range(24)]
    hass.states.async_set(PRICE, "0.1", {"raw_today": raw, "raw_tomorrow": [], "unit": "kWh"})


async def _run(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: int, watts: float = 400.0) -> None:
    for _ in range(seconds // 5):
        freezer.tick(timedelta(seconds=5))
        hass.states.async_set(P1, str(watts), {"device_class": "power", "unit_of_measurement": "W"}, force_update=True)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()


async def _setup(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, **options: object):  # type: ignore[no-untyped-def]
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 25, 11, 59, 50, tzinfo=dt_util.get_default_time_zone()))
    entry = await _install_with_p1(hass, fake_sets)
    _prices(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {"p1_entity": P1, "price_entity": PRICE, "tariff_markup_import": 0.0165, "tariff_fixed_month": 30.0, **options},
    )
    await hass.async_block_till_done()
    return entry


async def test_quarter_costs_and_sensors(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, tmp_path: Path) -> None:
    entry = await _setup(hass, fake_sets, freezer)
    await _run(hass, freezer, 10)  # 12:00:00 closes the (partial) quarter 11:45–12:00
    await _run(hass, freezer, 900)  # 12:15:00 closes a whole quarter
    costs = entry.runtime_data.costs
    first, record = costs.current[-2:]
    assert first["complete"] is False
    assert record["start"] == "2026-11-25T11:00:00+00:00"
    assert record["complete"] is True
    # House imports 400 W while the set (fixture) delivers 760 W.
    assert record["import_kwh"] == pytest.approx(0.1, abs=0.002)
    assert record["discharge_kwh"] == pytest.approx(0.19, abs=0.003)
    buy = (0.10 + 0.0165 + 0.09161) * 1.21
    assert record["buy"] == pytest.approx(buy, abs=1e-5)
    assert record["cost"] == pytest.approx(record["import_kwh"] * buy, abs=1e-4)
    # Without the battery the house would have drawn 400 + 760 W.
    assert record["cost_no_battery"] == pytest.approx((record["import_kwh"] + record["discharge_kwh"]) * buy, abs=1e-4)
    assert record["cost_no_solar"] is None  # no solar counter configured

    today = hass.states.get("sensor.zephyr_costs_today")
    assert float(today.state) == pytest.approx(sum(r["cost"] for r in costs.current), abs=0.01)
    assert today.attributes["unit_of_measurement"] == "EUR"
    assert today.attributes["state_class"] == "total"
    assert today.attributes["includes_solar"] is False
    assert today.attributes["incomplete_quarters"] == 1
    assert float(hass.states.get("sensor.zephyr_savings_today").state) == pytest.approx(0.19 * buy, abs=0.01)
    assert hass.states.get("sensor.zephyr_costs_year").state == today.state

    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["costs"]["tariffs"]["in_use"]["markup_import"] == 0.0165
    assert diag["costs"]["tariffs"]["supplier"] == "own"
    assert len(diag["costs"]["last_quarters"]) == 2

    hass.config.config_dir = str(tmp_path)
    response = await hass.services.async_call(DOMAIN, "export_costs", {}, blocking=True, return_response=True)
    assert response["rows"] == 2
    lines = Path(str(response["path"])).read_text(encoding="utf-8").strip().split("\n")
    assert lines[0].startswith("start,") and len(lines) == 3

    # A reload keeps the day totals and the quarters.
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert len(entry.runtime_data.costs.current) == 2
    assert hass.states.get("sensor.zephyr_costs_today").state == today.state


async def test_meter_counters_win(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    for entity in (*IMPORT, *EXPORT):
        hass.states.async_set(entity, "100.0", ENERGY)
    entry = await _setup(hass, fake_sets, freezer, cost_import_counters=list(IMPORT), cost_export_counters=list(EXPORT))
    await _run(hass, freezer, 10)
    hass.states.async_set(IMPORT[0], "100.05", ENERGY)
    hass.states.async_set(IMPORT[1], "100.02", ENERGY)
    hass.states.async_set(EXPORT[1], "100.01", ENERGY)
    await _run(hass, freezer, 900)
    record = entry.runtime_data.costs.current[-1]
    assert record["import_kwh"] == pytest.approx(0.07)
    assert record["export_kwh"] == pytest.approx(0.01)
    assert record["complete"] is True


async def test_savings_view_for_the_panel(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, hass_ws_client: WebSocketGenerator
) -> None:
    """Screen Besparing: periods from the cost log, the last 30 days, incomplete days marked."""
    client = await hass_ws_client(hass)
    entry = await _setup(hass, fake_sets, freezer)
    await _run(hass, freezer, 10)
    await _run(hass, freezer, 900)
    costs = entry.runtime_data.costs
    # Two earlier days: a whole one and one where HA was off for a while.
    whole = {**costs.days["2026-11-25"], "quarters": 96, "incomplete": 0, "no_price": 0}
    costs.days["2026-11-23"] = whole
    costs.days["2026-11-24"] = {**whole, "quarters": 60}
    costs._summaries.clear()
    await client.send_json_auto_id({"type": "zephyr/savings"})
    msg = await client.receive_json()
    assert msg["success"] is True
    view = msg["result"]
    assert view["since"] == "2026-11-23"
    assert [d["day"] for d in view["days"]] == ["2026-11-23", "2026-11-24", "2026-11-25"]
    assert [d["incomplete"] for d in view["days"]] == [False, True, True]  # today has an open quarter
    today = view["periods"]["today"]
    assert today["savings_battery"] == pytest.approx(today["cost_no_battery"] - today["cost"], abs=0.01)
    assert today["savings_battery"] > 0
    assert view["periods"]["week"]["days"] == 3  # Monday 23-11 to Wednesday 25-11
    assert view["periods"]["month"]["days"] == 3
    assert set(today) >= {"savings_solar_via_battery", "savings_trade", "charge_kwh", "discharge_kwh", "incomplete_quarters"}


async def test_savings_before_the_cost_log_from_hourly_statistics(
    hass: HomeAssistant,
    fake_sets: FakeSets,
    freezer: FrozenDateTimeFactory,
    hass_ws_client: WebSocketGenerator,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bjorn, 26-11 (choice 2): days before the cost log are worked out again per hour, with the same method."""
    from custom_components.zephyr import planner_runner

    charge, discharge = "sensor.set_energy_in", "sensor.set_energy_out"
    calls: list[tuple[datetime, datetime, list[str]]] = []

    async def fake_stats(hass: HomeAssistant, start: datetime, end: datetime, ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        calls.append((start, end, ids))
        rows: dict[str, list[dict[str, Any]]] = {i: [] for i in ids}
        t = start
        while t < end:
            hour = dt_util.as_local(t).hour
            evening = 17 <= hour < 21
            for entity, value in (
                (IMPORT[0], 0.1 if evening else 0.6),
                (IMPORT[1], 0.0),
                (EXPORT[0], 0.0),
                (EXPORT[1], 0.0),
                (charge, 0.0),
                (discharge, 0.5 if evening else 0.0),
            ):
                rows[entity].append({"start": t, "change": value})
            rows[PRICE].append({"start": dt_util.as_utc(t).timestamp(), "mean": 0.30 if evening else 0.20})
            t += timedelta(hours=1)
        return rows

    monkeypatch.setattr(planner_runner, "hourly_statistics", fake_stats)
    for entity in (*IMPORT, *EXPORT, charge, discharge):
        hass.states.async_set(entity, "100.0", ENERGY)
    client = await hass_ws_client(hass)
    entry = await _setup(hass, fake_sets, freezer, cost_import_counters=list(IMPORT), cost_export_counters=list(EXPORT))
    await _run(hass, freezer, 10)
    costs = entry.runtime_data.costs
    assert costs.measured_since == "2026-11-25"

    msg_base = {"type": "zephyr/savings/backfill", "first": "2026-11-20", "charge_entity": charge, "discharge_entity": discharge}
    await client.send_json_auto_id({**msg_base, "price_entity": PRICE})
    result = (await client.receive_json())["result"]
    assert result["ok"] is True
    assert (result["first"], result["last"], result["days"]) == ("2026-11-20", "2026-11-24", 5)
    assert result["hours"] == 120 and result["skipped"] == 0 and result["priced_hours"] == 120
    # Statistics are asked up to the first measured day, not into it.
    assert dt_util.as_local(calls[-1][1]).date().isoformat() == "2026-11-25"

    await client.send_json_auto_id({"type": "zephyr/savings"})
    view = (await client.receive_json())["result"]
    assert view["measured_since"] == "2026-11-25" and view["since"] == "2026-11-20"
    assert view["backfilled_days"] == 5 and view["can_backfill"] is True
    hourly = [d for d in view["days"] if d["hourly"]]
    assert [d["day"] for d in hourly] == ["2026-11-20", "2026-11-21", "2026-11-22", "2026-11-23", "2026-11-24"]
    assert all(not d["incomplete"] for d in hourly)
    tariffs = costs.tariffs.tariffs_for(date(2026, 11, 22))
    assert hourly[0]["savings_battery"] == pytest.approx(4 * 0.5 * tariffs.buy(0.30), abs=0.01)
    assert not view["days"][-1]["hourly"]

    # A second run replaces the first; clearing removes only the worked-out days.
    await client.send_json_auto_id({**msg_base, "first": "2026-11-23", "price_entity": PRICE})
    assert (await client.receive_json())["result"]["days"] == 2
    assert sorted(k for k, v in costs.days.items() if v.get("source")) == ["2026-11-23", "2026-11-24"]
    await client.send_json_auto_id({"type": "zephyr/savings/backfill", "clear": True})
    assert (await client.receive_json())["result"] == {"ok": True, "removed": 2}
    assert list(costs.days) == ["2026-11-25"]

    # Without battery counters or with an unknown entity: an error, nothing changes.
    await client.send_json_auto_id({"type": "zephyr/savings/backfill", "first": "2026-11-20"})
    assert (await client.receive_json())["result"] == {"ok": False, "error": "no_battery_counters"}
    await client.send_json_auto_id({**msg_base, "charge_entity": "sensor.gone"})
    assert (await client.receive_json())["result"]["error"] == "entity_missing"


async def test_backfill_with_energyzero_prices(
    hass: HomeAssistant,
    fake_sets: FakeSets,
    freezer: FrozenDateTimeFactory,
    hass_ws_client: WebSocketGenerator,
    monkeypatch: pytest.MonkeyPatch,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """A price sensor without statistics (Bjorn's Nord Pool): prices per hour from EnergyZero instead."""
    from custom_components.zephyr import planner_runner

    charge, discharge = "sensor.set_energy_in", "sensor.set_energy_out"

    async def fake_stats(hass: HomeAssistant, start: datetime, end: datetime, ids: list[str]) -> dict[str, list[dict[str, Any]]]:
        assert PRICE not in ids  # the sensor is not asked
        rows: dict[str, list[dict[str, Any]]] = {i: [] for i in ids}
        t = start
        while t < end:
            evening = 17 <= dt_util.as_local(t).hour < 21
            for entity, value in ((IMPORT[0], 0.6), (IMPORT[1], 0.0), (EXPORT[0], 0.0), (EXPORT[1], 0.0), (charge, 0.0)):
                rows[entity].append({"start": t, "change": value})
            rows[discharge].append({"start": t, "change": 0.5 if evening else 0.0})
            t += timedelta(hours=1)
        return rows

    def day_prices(day: str) -> dict[str, Any]:
        start = datetime.fromisoformat(f"{day}T00:00:00").replace(tzinfo=dt_util.get_default_time_zone())
        hours = [dt_util.as_utc(start + timedelta(hours=h)) for h in range(24)]
        return {"Prices": [{"readingDate": h.strftime("%Y-%m-%dT%H:%M:%SZ"), "price": 0.30} for h in hours]}

    url = "https://api.energyzero.nl/v1/energyprices"
    query = {"interval": "4", "usageType": "1", "inclBtw": "false"}
    first = {"fromDate": "2026-11-22T23:00:00.000Z", "tillDate": "2026-11-23T22:59:59.000Z", **query}
    second = {"fromDate": "2026-11-23T23:00:00.000Z", "tillDate": "2026-11-24T22:59:59.000Z", **query}
    aioclient_mock.get(url, params=first, json=day_prices("2026-11-23"))
    aioclient_mock.get(url, params=second, status=500)
    monkeypatch.setattr(planner_runner, "hourly_statistics", fake_stats)
    for entity in (*IMPORT, *EXPORT, charge, discharge):
        hass.states.async_set(entity, "100.0", ENERGY)
    client = await hass_ws_client(hass)
    await _setup(hass, fake_sets, freezer, cost_import_counters=list(IMPORT), cost_export_counters=list(EXPORT))
    await _run(hass, freezer, 10)

    await client.send_json_auto_id({"type": "zephyr/savings"})
    assert (await client.receive_json())["result"]["defaults"]["price_entity"] == "energyzero"  # no state_class on the test sensor
    await client.send_json_auto_id(
        {
            "type": "zephyr/savings/backfill",
            "first": "2026-11-23",
            "charge_entity": charge,
            "discharge_entity": discharge,
            "price_entity": "energyzero",
        }
    )
    result = (await client.receive_json())["result"]
    assert result["ok"] is True and result["days"] == 2
    assert result["priced_hours"] == 24 and result["price_failed_days"] == 1
    assert aioclient_mock.call_count == 2


async def test_unmeasured_part_is_filled_and_refined(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    # OPDRACHT-onvolledige-kwartieren: P1 away for 5 of 15 minutes, no meter counters. The
    # missing part is filled (first with the quarter's own rate as the next neighbour, then,
    # once the next quarter closed, between the real neighbours) and the quarter is estimated.
    entry = await _setup(hass, fake_sets, freezer)
    await _run(hass, freezer, 10)  # 11:45–12:00: 10 s measured, nothing to fill with
    costs = entry.runtime_data.costs
    assert costs.current[-1]["status"] == "missing"
    await _run(hass, freezer, 900, 400.0)  # 12:00–12:15 at 400 W: measured
    assert costs.current[-1]["status"] == "measured"
    await _run(hass, freezer, 600, 400.0)  # 12:15–12:30: 10 min at 400 W ...
    for _ in range(60):  # ... then 5 min without a P1 value
        freezer.tick(timedelta(seconds=5))
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
    gap = costs.current[-1]
    assert gap["status"] == "estimated" and gap["fill"]["import_kwh"] == "interpolated"
    assert "p1" in gap["fill_causes"] and gap["complete"] is True
    assert gap["import_kwh"] == pytest.approx(0.1, abs=0.004)  # 400 W on both sides
    await _run(hass, freezer, 900, 600.0)  # 12:30–12:45 at 600 W: the gap is filled again at ~500 W
    gap = costs.current[-2]
    assert gap["import_kwh"] == pytest.approx(0.0667 + 0.0417, abs=0.004)
    assert gap["estimated"] is True and "fill_basis" not in gap
    today = hass.states.get("sensor.zephyr_costs_today")
    assert today.attributes["estimated_quarters"] == 1
    assert today.attributes["missing_quarters"] == 1
    diag = await async_get_config_entry_diagnostics(hass, entry)
    day = next(iter(diag["costs"]["fill_by_day"].values()))
    assert day["estimated"] == 1 and day["missing"] == 1 and day["causes"]["p1"] == 1
    assert day["filled_kwh"]["import_kwh"] == pytest.approx(0.0417, abs=0.004)
    total = sum(r["import_kwh"] for r in costs.current)
    assert costs.days[next(iter(costs.days))]["import_kwh"] == pytest.approx(total, abs=1e-4)


async def test_quarters_while_ha_was_off_are_made_and_filled(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory
) -> None:
    # OPDRACHT-onvolledige-kwartieren step 2: HA off 12:22:30–13:07:30. The quarters 12:15, 12:30
    # and 12:45 get a record; the meter counted 0.80 kWh from 12:15 to 13:15, which sets the sum;
    # the spread rises from the quarter before (0.10) to the rate after (1200 W = 0.30).
    for entity in (*IMPORT, *EXPORT):
        hass.states.async_set(entity, "100.0", ENERGY)
    entry = await _setup(hass, fake_sets, freezer, cost_import_counters=list(IMPORT), cost_export_counters=list(EXPORT))
    await _run(hass, freezer, 10)
    hass.states.async_set(IMPORT[0], "100.10", ENERGY)
    await _run(hass, freezer, 900)  # 12:15 closes 12:00–12:15: 0.10 kWh from the counters
    costs = entry.runtime_data.costs
    assert costs.current[-1]["import_kwh"] == pytest.approx(0.10)
    await _run(hass, freezer, 450)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    freezer.tick(timedelta(minutes=45))
    hass.states.async_set(IMPORT[0], "100.90", ENERGY)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _run(hass, freezer, 450, 1200.0)  # 13:15 closes 13:00–13:15
    costs = entry.runtime_data.costs
    starts = [r["start"][11:16] for r in costs.current]
    assert starts[-5:] == ["11:00", "11:15", "11:30", "11:45", "12:00"]  # UTC
    gap = costs.current[-4:-1]
    assert all(r["status"] == "estimated" and r["fill"]["import_kwh"] == "scaled" for r in gap)
    assert all("ha_off" in r["fill_causes"] for r in gap)
    assert gap[0]["import_kwh"] < gap[1]["import_kwh"] < gap[2]["import_kwh"]
    assert sum(r["import_kwh"] for r in costs.current[-4:]) == pytest.approx(0.80, abs=1e-3)
    assert costs.current[-1]["status"] == "estimated"
    assert all(r["cost"] is not None for r in gap)  # priced from the Nord Pool sensor of that day
    day = costs.days["2026-11-25"]
    assert day["import_kwh"] == pytest.approx(sum(r["import_kwh"] for r in costs.current), abs=1e-3)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["costs"]["missed_quarters"][-1]["quarters"] == 3


async def test_history_filled_once_after_the_update(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    # Eis 5: once, the stored month is filled: a quarter that was missing gets a record, an
    # incomplete one is filled, and the month is evaluated again; day totals follow.
    entry = await _setup(hass, fake_sets, freezer)
    await _run(hass, freezer, 10)
    for _ in range(5):
        await _run(hass, freezer, 900, 400.0)
    costs = entry.runtime_data.costs
    records = costs.current
    assert len(records) == 6
    del records[3]  # a quarter HA never closed (before 0.8.80)
    half = records[3]
    half.update({"import_kwh": 0.05, "complete": False, "coverage": 0.5})
    half.pop("status", None)
    costs.fill_version = 0
    await costs.async_save()
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    costs = entry.runtime_data.costs
    assert len(costs.current) == 6 and costs.fill_version == 3
    made, filled = costs.current[3], costs.current[4]
    assert made["status"] == "estimated" and made["import_kwh"] == pytest.approx(0.1, abs=0.005)
    assert filled["status"] == "estimated" and filled["import_kwh"] == pytest.approx(0.1, abs=0.005)
    day = costs.days["2026-11-25"]
    assert day["import_kwh"] == pytest.approx(sum(r["import_kwh"] for r in costs.current), abs=1e-3)
    assert day["quarters"] == 6
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["costs"]["history_filled"]["made"] == 1 and diag["costs"]["history_filled"]["filled"] >= 1


def _quarter_prices(hass: HomeAssistant, prices: dict[str, float], default: float = 0.10, hole: str | None = None) -> None:
    """Quarter prices for today (local HH:MM → €/kWh); ``hole`` leaves one quarter out."""
    start = dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)
    raw = []
    for q in range(96):
        begin = start + timedelta(minutes=15 * q)
        key = begin.strftime("%H:%M")
        if key == hole:
            continue
        raw.append({"start": begin, "end": begin + timedelta(minutes=15), "value": prices.get(key, default)})
    hass.states.async_set(PRICE, "0.1", {"raw_today": raw, "raw_tomorrow": [], "unit": "kWh"})


async def test_missing_price_is_interpolated_then_replaced(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory
) -> None:
    # Step 3: no price for 12:15–12:30 at closing: between 0.10 (before) and 0.20 (after) → 0.15,
    # counted at once; when Nord Pool has it (0.12) it replaces the guess and the day follows.
    entry = await _setup(hass, fake_sets, freezer)
    _quarter_prices(hass, {"12:30": 0.20}, hole="12:15")
    await _run(hass, freezer, 10)
    await _run(hass, freezer, 900)
    await _run(hass, freezer, 900)
    costs = entry.runtime_data.costs
    guess = costs.current[-1]
    assert guess["price_source"] == "interpolated" and guess["market"] == pytest.approx(0.15)
    assert guess["cost"] is not None and "price" in guess["fill_causes"]
    assert hass.states.get("sensor.zephyr_costs_today").attributes["price_interpolated_quarters"] == 1
    _quarter_prices(hass, {"12:30": 0.20, "12:15": 0.12})
    await hass.async_block_till_done()
    real = next(r for r in costs.current if r["start"] == guess["start"])
    assert real["price_source"] == "nordpool" and real["market"] == pytest.approx(0.12)
    day = costs.days["2026-11-25"]
    assert day["cost"] == pytest.approx(sum(r["cost"] for r in costs.current if r["cost"] is not None), abs=1e-4)
    assert not day.get("price_interpolated")


async def test_price_from_energyzero_when_nord_pool_stays_away(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, aioclient_mock: AiohttpClientMocker
) -> None:
    hour = datetime(2026, 11, 25, 11, 0, tzinfo=dt_util.UTC)  # 12:00 local
    aioclient_mock.get(
        "https://api.energyzero.nl/v1/energyprices",
        json={"Prices": [{"readingDate": hour.isoformat().replace("+00:00", "Z"), "price": 0.177}]},
    )
    entry = await _setup(hass, fake_sets, freezer)
    _quarter_prices(hass, {}, hole="12:15")
    await _run(hass, freezer, 10)
    await _run(hass, freezer, 900)
    await _run(hass, freezer, 900)  # 12:15 interpolated
    await _run(hass, freezer, 3600)  # an hour on: EnergyZero
    costs = entry.runtime_data.costs
    record = next(r for r in costs.current if r["start"] == "2026-11-25T11:15:00+00:00")
    assert record["price_source"] == "energyzero" and record["market"] == pytest.approx(0.177)


async def test_prices_around_midnight(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    # TOETS-besparing bevinding 3: the Nord Pool sensor rolls raw_today over at midnight. 23:45
    # keeps the price it had when it opened; 00:00–00:45 get the new day's prices.
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    tz = dt_util.get_default_time_zone()
    freezer.move_to(datetime(2026, 11, 25, 23, 29, 50, tzinfo=tz))
    entry = await _install_with_p1(hass, fake_sets)
    today = datetime(2026, 11, 25, tzinfo=tz)
    tomorrow = today + timedelta(days=1)

    def raw(day: datetime, value: float) -> list[dict[str, Any]]:
        return [{"start": day + timedelta(minutes=15 * q), "end": day + timedelta(minutes=15 * (q + 1)), "value": value} for q in range(96)]

    hass.states.async_set(PRICE, "0.2", {"raw_today": raw(today, 0.21), "raw_tomorrow": raw(tomorrow, 0.30), "unit": "kWh"})
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": P1, "price_entity": PRICE})
    await hass.async_block_till_done()
    await _run(hass, freezer, 10)  # 23:30
    await _run(hass, freezer, 900)  # 23:45 closes 23:30
    await _run(hass, freezer, 895)
    hass.states.async_set(PRICE, "0.3", {"raw_today": raw(tomorrow, 0.30), "raw_tomorrow": [], "unit": "kWh"})
    await _run(hass, freezer, 5)  # 00:00 closes 23:45 after the roll-over
    for _ in range(3):
        await _run(hass, freezer, 900)
    costs = entry.runtime_data.costs
    by_start = {dt_util.as_local(datetime.fromisoformat(r["start"])).strftime("%H:%M"): r for r in costs.current}
    assert by_start["23:45"]["market"] == pytest.approx(0.21) and by_start["23:45"]["price_source"] == "nordpool"
    assert [by_start[k]["market"] for k in ("00:00", "00:15", "00:30")] == pytest.approx([0.30, 0.30, 0.30])


async def test_solar_savings_split(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    # OPDRACHT-besparing-zon: with a solar counter the saving splits into solar (direct + export,
    # with the solar bonus) and battery; direct + export = Z0 − Z1.
    solar = "sensor.solar_total"
    hass.states.async_set(solar, "50.0", ENERGY)
    entry = await _setup(hass, fake_sets, freezer, solar_energy_entity=solar, tariff_solar_bonus=10.0)
    await _run(hass, freezer, 10)
    hass.states.async_set(solar, "50.3", ENERGY)  # 0.3 kWh solar in the quarter, house imports 400 W
    await _run(hass, freezer, 900, -200.0)
    costs = entry.runtime_data.costs
    q = costs.current[-1]
    assert q["solar_direct_value"] is not None
    assert q["solar_direct_value"] + q["solar_export_value"] == pytest.approx(q["cost_no_solar"] - q["cost_no_battery"], abs=1e-4)
    assert q["solar_bonus_value"] >= 0
    state = hass.states.get("sensor.zephyr_savings_today")
    assert state.attributes["battery"] == state.attributes["savings_battery"]
    assert "solar" in state.attributes and "total" in state.attributes
    client_view = costs.summary("today").as_dict()
    assert "self_consumption" in client_view and "savings_total" in client_view


async def test_older_months_filled_once(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    # 0.8.89: the months before the current one are filled once too (each on its own).
    entry = await _setup(hass, fake_sets, freezer)
    await _run(hass, freezer, 10)
    for _ in range(4):
        await _run(hass, freezer, 900, 400.0)
    costs = entry.runtime_data.costs
    old = [dict(r) for r in costs.current]
    del old[2]  # a quarter missing in the older month
    await costs._month_store("2026-10").async_save({"quarters": old})
    costs.months = sorted({*costs.months, "2026-10"})
    costs.fill_version = 2
    await costs.async_save()
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    costs = entry.runtime_data.costs
    stored = (await costs._month_store("2026-10").async_load())["quarters"]
    assert len(stored) == len(old) + 1 and stored[2]["status"] == "estimated"
    assert costs.repaired["older_months"]["2026-10"]["made"] == 1
