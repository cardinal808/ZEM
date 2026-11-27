"""B42 in Home Assistant: vacation switch with an end, automatic when away, planner and cost log."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.zephyr.const import DOMAIN
from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets
from .test_planner import PRICE, _set_prices, _setup, _test_day, _tick  # noqa: F401 (_test_day: autouse, fixed test day)


async def _on(hass: HomeAssistant, entity: str, service: str = "turn_on", **data: Any) -> None:
    domain = entity.split(".")[0]
    await hass.services.async_call(domain, service, {"entity_id": entity, **data}, blocking=True)
    await hass.async_block_till_done()


async def test_vacation_switch_end_and_plan(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    _set_prices(hass)
    entry = await _setup(hass, fake_sets, freezer, (9, 0), price_entity=PRICE)
    planner = entry.runtime_data.planner
    for hour in range(24):
        for _ in range(3):
            planner.profile.learn("workday", hour, 0.25 if hour < 6 else 1.0)
    assert hass.states.get("switch.zephyr_vacation").state == "off"

    end = dt_util.now().replace(hour=18, minute=0)
    await _on(hass, "datetime.zephyr_vacation_until", "set_value", datetime=end.isoformat())
    await _on(hass, "switch.zephyr_vacation")
    state = hass.states.get("switch.zephyr_vacation")
    assert state.state == "on" and state.attributes["until"] == dt_util.as_utc(end).isoformat()
    await _tick(hass, freezer, 10)
    timeline = planner.outcome.timeline()
    by_time = {datetime.fromisoformat(q["start"]): q["load"] for q in timeline}
    at = dt_util.as_utc(dt_util.now().replace(hour=12, minute=0, second=0, microsecond=0))
    after = dt_util.as_utc(dt_util.now().replace(hour=19, minute=0, second=0, microsecond=0))
    assert by_time[at] == pytest.approx(0.25 / 4, abs=0.001)  # standby use while away
    assert by_time[after] == pytest.approx(1.0 / 4, abs=0.01)  # back home: the normal profile
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["planner"]["inputs"]["vacation"] is True and diag["planner"]["vacation"]["manual"] is True

    # Learning: a whole hour while away goes into the vacation profile, not the normal one.
    start = dt_util.now().replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    before = planner.profile.mean_count
    for q in range(4):
        planner.quarter_closed(start + timedelta(minutes=15 * q), {"complete": True, "house_kwh": 0.05, "vacation": True}, True)
    assert planner.profile.mean_count == before
    assert planner.vacation_profile.expected("workday", start.hour) == pytest.approx(0.2)

    # The end passes: off by itself, the period is kept.
    freezer.move_to(end + timedelta(minutes=2))
    await _tick(hass, freezer, 60)
    assert hass.states.get("switch.zephyr_vacation").state == "off"
    assert entry.runtime_data.vacation.state.periods


async def test_vacation_when_nobody_home(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    hass.states.async_set("zone.home", "0")
    entry = await _setup(hass, fake_sets, freezer, (9, 0), vacation_when_away=True)
    vacation = entry.runtime_data.vacation
    hass.states.async_set("zone.home", "1")
    await hass.async_block_till_done()
    hass.states.async_set("zone.home", "0")
    await hass.async_block_till_done()
    assert not vacation.active()
    freezer.tick(timedelta(hours=24, minutes=1))
    await _tick(hass, freezer, 60)
    assert vacation.active() and vacation.state.auto
    assert hass.states.get("switch.zephyr_vacation").attributes["automatic"] is True
    hass.states.async_set("zone.home", "2")
    await hass.async_block_till_done()
    assert not vacation.active() and len(vacation.state.periods) == 1


async def test_cost_quarter_is_marked(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _setup(hass, fake_sets, freezer, (9, 0))
    await _on(hass, "switch.zephyr_vacation")
    costs = entry.runtime_data.costs
    boundary = dt_util.now().replace(second=0, microsecond=0) + timedelta(minutes=15)
    freezer.move_to(boundary)
    record = await costs.async_close(boundary)
    assert record is not None and record["vacation"] is True
    assert DOMAIN
