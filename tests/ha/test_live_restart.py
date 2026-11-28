"""Live control after a restart: shadow mode for a new installation, live stays live."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    mock_restore_cache,
    mock_restore_cache_with_extra_data,
)

from custom_components.zephyr import async_migrate_entry
from custom_components.zephyr.const import DOMAIN

from .conftest import FakeSets
from .test_shadow import P1, _install_with_p1

SWITCH = "switch.zephyr_control"


async def _restart(hass: HomeAssistant, entry: Any, state: str = "on") -> None:
    """Unload, put the switch's last state in the restore cache (as after a restart), set up again."""
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    mock_restore_cache(hass, [State(SWITCH, state)])
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _run(hass: HomeAssistant, freezer: FrozenDateTimeFactory, seconds: int) -> None:
    for _ in range(seconds // 5):
        freezer.tick(timedelta(seconds=5))
        hass.states.async_set(P1, "300", {"device_class": "power", "unit_of_measurement": "W"}, force_update=True)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()


async def test_new_installation_starts_in_shadow_mode(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    await _run(hass, freezer, 30)
    assert hass.states.get(SWITCH).state == "off"
    assert entry.runtime_data.control.shadow


async def test_live_stays_live_after_a_restart(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    await _restart(hass, entry)
    await _run(hass, freezer, 30)  # as soon as the P1 reports and the set is online
    assert not entry.runtime_data.control.shadow
    assert hass.states.get(SWITCH).state == "on"


async def test_test_phase_setting_keeps_it_off(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    hass.config_entries.async_update_entry(entry, options={**entry.options, "live_off_after_restart": True})
    await hass.async_block_till_done()
    await _restart(hass, entry)
    await _run(hass, freezer, 30)
    assert entry.runtime_data.control.shadow
    assert ir.async_get(hass).async_get_issue(DOMAIN, "live_off_after_restart") is not None


async def test_not_resumed_when_the_set_stays_away(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    fake_sets.fail("10.0.0.10")
    await _restart(hass, entry)
    await _run(hass, freezer, 11 * 60)
    assert entry.runtime_data.control.shadow
    assert ir.async_get(hass).async_get_issue(DOMAIN, "live_not_resumed") is not None


async def test_resume_goes_on_after_ten_minutes(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    # 28-11: the set stayed away longer than 10 minutes after a restart; ZEPHYR gave up and the
    # switch stayed off, also after the next restart. Now it keeps trying and goes live by itself.
    entry = await _install_with_p1(hass, fake_sets)
    answer = fake_sets.answers["10.0.0.10"]
    fake_sets.fail("10.0.0.10")
    await _restart(hass, entry)
    await _run(hass, freezer, 11 * 60)
    control = entry.runtime_data.control
    assert control.shadow and control.wanted_live
    assert control.live_history[-1]["event"] == "not_resumed"
    fake_sets.answers["10.0.0.10"] = answer
    await _run(hass, freezer, 90)
    assert not control.shadow
    assert hass.states.get(SWITCH).state == "on"
    assert ir.async_get(hass).async_get_issue(DOMAIN, "live_not_resumed") is None
    assert control.live_history[-1]["reason"] == "resumed"


async def test_wish_survives_a_restart_while_resuming(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    # The state was off (still resuming), but the user wanted live: the next start resumes.
    entry = await _install_with_p1(hass, fake_sets)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    mock_restore_cache_with_extra_data(hass, [(State(SWITCH, "off"), {"wanted_live": True})])
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _run(hass, freezer, 30)
    assert not entry.runtime_data.control.shadow


async def test_switched_off_stays_off(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    mock_restore_cache_with_extra_data(hass, [(State(SWITCH, "on"), {"wanted_live": False})])
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await _run(hass, freezer, 30)
    assert entry.runtime_data.control.shadow


async def test_live_history_is_kept_over_a_restart(hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    await _run(hass, freezer, 10)
    await hass.services.async_call("switch", "turn_on", {"entity_id": SWITCH}, blocking=True)
    await hass.services.async_call("switch", "turn_off", {"entity_id": SWITCH}, blocking=True)
    await hass.async_block_till_done()
    state = hass.states.get(SWITCH)
    assert state.attributes["last_shadow_reason"] == "user"
    assert state.attributes["wanted_live"] is False
    await _restart(hass, entry, "off")
    history = entry.runtime_data.control.live_history
    assert [(e["event"], e["reason"]) for e in history][-2:] == [("live", "user"), ("shadow", "user")]


async def test_migration_turns_the_test_phase_setting_off(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, version=1, minor_version=1, options={"live_off_after_restart": True, "p1_entity": P1})
    entry.add_to_hass(hass)
    assert await async_migrate_entry(hass, entry)
    assert entry.minor_version == 2 and entry.options["live_off_after_restart"] is False and entry.options["p1_entity"] == P1
