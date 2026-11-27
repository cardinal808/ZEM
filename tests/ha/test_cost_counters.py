"""Cost log on the own energy counters, corrected after a filled gap (SPEC-tellers T3)."""

from __future__ import annotations

from datetime import datetime

import pytest
from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets
from .test_costs import P1, PRICE, _prices, _run
from .test_shadow import _install_with_p1

HOST = "10.0.0.10"
KW = 2.386  # outputPackPower of the fixture


async def _charging(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory):  # type: ignore[no-untyped-def]
    await hass.config.async_set_time_zone("Europe/Amsterdam")
    freezer.move_to(datetime(2026, 11, 25, 11, 59, 50, tzinfo=dt_util.get_default_time_zone()))
    entry = await _install_with_p1(hass, fake_sets, "charge_2400")
    _prices(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": P1, "price_entity": PRICE})
    await hass.async_block_till_done()
    return entry


async def test_quarters_from_the_counters_and_a_gap_corrected(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory
) -> None:
    entry = await _charging(hass, fake_sets, freezer)
    costs = entry.runtime_data.costs
    await _run(hass, freezer, 10)  # 12:00 closes the partial quarter (meter: no counter reading before)
    await _run(hass, freezer, 900)  # 12:15 closes a whole quarter from the counters
    whole = costs.current[-1]
    assert whole["battery_source"] == "counters"
    assert whole["charge_kwh"] == pytest.approx(KW / 4, abs=0.01)
    assert "pools" in whole and "daylight" in whole

    # 12:25–12:35 the set cannot be read; meanwhile the packs filled up.
    await _run(hass, freezer, 600)
    answer = fake_sets.answers[HOST]
    fake_sets.fail(HOST)
    await _run(hass, freezer, 600)  # 12:30 closes a quarter with only the hold counted
    gap_quarter = costs.current[-1]
    assert gap_quarter["charge_kwh"] < KW / 4 - 0.05
    assert isinstance(answer, dict)
    for pack in answer["packData"]:
        pack["socLevel"] += 4  # ≈ 0.44 kWh in the packs over ~10 minutes of charging
    fake_sets.answers[HOST] = answer
    await _run(hass, freezer, 300)  # back at 12:35; 12:45 closes the next quarter
    await _run(hass, freezer, 300)
    corrected = next(r for r in costs.current if r["start"] == gap_quarter["start"])
    assert corrected.get("estimated") is True
    assert corrected["charge_kwh"] > gap_quarter["charge_kwh"] + 0.1
    after = costs.current[-1]
    assert after["charge_kwh"] == pytest.approx(KW / 4, abs=0.03)  # no jump: the fill went to the gap quarter

    # The day equals what the counters counted from the first boundary on (12:00).
    day = costs.days["2026-11-25"]
    from_counters = sum(r["charge_kwh"] for r in costs.current if r["battery_source"] == "counters")
    assert day["charge_kwh"] == pytest.approx(sum(r["charge_kwh"] for r in costs.current), abs=0.001)
    total = entry.runtime_data.energy.counters.totals["charged"]
    first_reading = KW * 10 / 3600  # energy before 12:00 (10 s)
    assert from_counters == pytest.approx(total - first_reading, abs=0.02)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["costs"]["gap_corrections"][-1]["corrected"] is True
