"""Surplus solar at a negative export price (PLANNING 1.1/1.2)."""

from __future__ import annotations

from datetime import datetime, timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.zephyr.curtail import planner_curtails
from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics
from custom_components.zephyr.websocket_api import events_view, now_snapshot

from .conftest import FakeSets
from .test_costs import P1, PRICE, _run
from .test_live import _switch
from .test_shadow import _install_with_p1

SWITCH = "switch.export_limiter"
NUMBER = "number.solaredge_active_power_limit"


def _prices(hass: HomeAssistant, value: float) -> None:
    start = dt_util.now().replace(hour=0, minute=0, second=0, microsecond=0)
    raw = [{"start": start + timedelta(hours=h), "end": start + timedelta(hours=h + 1), "value": value} for h in range(24)]
    hass.states.async_set(PRICE, str(value), {"raw_today": raw, "raw_tomorrow": [], "unit": "kWh"})


def test_planner_counts_surplus_as_curtailed_only_when_something_curtails() -> None:
    assert not planner_curtails({})
    assert not planner_curtails({"curtail_negative": "curtail_off"})
    assert planner_curtails({"curtail_negative": "curtail_external"})
    assert not planner_curtails({"curtail_negative": "curtail_zephyr"})  # only the sets' own panels
    assert planner_curtails({"curtail_negative": "curtail_zephyr", "curtail_switch": SWITCH})


async def test_zephyr_blocks_export_and_turns_the_switch_on(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory
) -> None:
    calls: list[tuple[str, str]] = []

    async def record(call: ServiceCall) -> None:
        calls.append((call.service, call.data["entity_id"]))
        hass.states.async_set(SWITCH, "on" if call.service == "turn_on" else "off")

    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 25, 11, 59, 50, tzinfo=dt_util.get_default_time_zone()))
    entry = await _install_with_p1(hass, fake_sets)
    _prices(hass, -0.50)  # even with saldering below zero
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"], {"p1_entity": P1, "price_entity": PRICE, "curtail_negative": "curtail_zephyr", "curtail_switch": SWITCH}
    )
    await hass.async_block_till_done()
    await _run(hass, freezer, 10)  # P1 reporting
    await _switch(hass, True)  # live: ZEPHYR may write
    # Then a fake inverter switch (the switch services of HA would otherwise handle it).
    hass.services.async_register("switch", "turn_on", record)
    hass.services.async_register("switch", "turn_off", record)
    hass.states.async_set(SWITCH, "off")
    await _run(hass, freezer, 30)
    curtail = entry.runtime_data.curtail
    assert curtail.negative and curtail.export_blocked is True and curtail.sell is not None and curtail.sell < 0
    assert ("turn_on", SWITCH) in calls, (curtail.switch, curtail.last_error)
    await _run(hass, freezer, 20)
    assert any(props.get("gridReverse") == 2 for _, props in fake_sets.writes), fake_sets.writes

    # The next quarter has a positive price again: switch off, export allowed.
    _prices(hass, 0.10)
    freezer.move_to(datetime(2026, 11, 25, 12, 15, 4, tzinfo=dt_util.get_default_time_zone()))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await _run(hass, freezer, 10)
    assert not curtail.negative and curtail.export_blocked is False
    assert calls[-1] == ("turn_off", SWITCH)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["curtail"]["mode"] == "curtail_zephyr" and diag["curtail"]["switch_set"] is True


async def test_zephyr_limits_the_inverter_power(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    values: list[float] = []

    async def set_value(call: ServiceCall) -> None:
        values.append(call.data["value"])
        hass.states.async_set(NUMBER, str(call.data["value"]))

    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 25, 11, 59, 50, tzinfo=dt_util.get_default_time_zone()))
    entry = await _install_with_p1(hass, fake_sets)
    hass.states.async_set("sensor.inverter_power", "3000", {"unit_of_measurement": "W"})
    _prices(hass, -0.50)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "p1_entity": P1,
            "price_entity": PRICE,
            "solar_power_entities": ["sensor.inverter_power"],
            "curtail_negative": "curtail_zephyr",
            "curtail_number": NUMBER,
            "curtail_inverter_w": 5000,
        },
    )
    await hass.async_block_till_done()
    hass.services.async_register("number", "set_value", set_value)
    hass.states.async_set(NUMBER, "100")
    await _run(hass, freezer, 30, watts=-1000.0)
    assert entry.runtime_data.curtail.negative
    room = entry.runtime_data.curtail._charge_room()
    assert room > 0  # the set is not full: it may still charge from the surplus
    assert values and values[-1] == round((3000 + room - 1000 - 50) / 5000 * 100)
    assert planner_curtails(dict(entry.options))
    now = now_snapshot(hass, entry)["curtail"]
    assert now["active"] and now["negative"] and now["export_blocked"] and now["percent"] == values[-1] and now["switch_on"] is None
    events = events_view(entry)
    assert [p["day"] for p in events["peaks"]] == ["2026-11-25"] and set(events["peaks"][0]) == {"day", "kwh", "holds"}
    _prices(hass, 0.10)
    freezer.move_to(datetime(2026, 11, 25, 12, 15, 4, tzinfo=dt_util.get_default_time_zone()))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await _run(hass, freezer, 20, watts=-1000.0)
    assert values[-1] == 100
    now = now_snapshot(hass, entry)["curtail"]
    assert not now["active"] and now["percent"] is None and now["mode"] == "curtail_zephyr"
