"""The control log over 48 hours, kept over a restart (log_file.py)."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics
from custom_components.zephyr.log_file import append_lines, read_lines

from .conftest import FakeSets
from .test_shadow import _install_with_p1, _p1


async def test_log_survives_a_restart(
    hass: HomeAssistant, fake_sets: FakeSets, freezer: FrozenDateTimeFactory, log_dir_in_tmp: Path
) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    for watts in (300, 800, 1500):
        await _p1(hass, freezer, watts, seconds=5)
    before = list(entry.runtime_data.control.log)
    assert before
    freezer.tick(timedelta(minutes=1))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    await hass.async_block_till_done(wait_background_tasks=True)
    assert list(log_dir_in_tmp.rglob("*.jsonl"))

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    control = hass.config_entries.async_get_entry(entry.entry_id).runtime_data.control
    assert list(control.log)[: len(before)] == before
    assert control.log_file.restored >= len(before)
    diag: dict[str, Any] = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["control"]["log"]["from_before_start"] >= len(before)
    assert len(diag["control"]["decisions"]) == len(control.log)


def test_files_older_than_48_hours_are_removed(tmp_path: Path) -> None:
    append_lines(tmp_path, [{"time": "2026-11-25T10:00:00+00:00", "event": "live"}], "2026-11-25T00:00:00+00:00")
    append_lines(tmp_path, [{"time": "2026-11-28T10:00:05+00:00", "event": "shadow"}], "2026-11-26T10:00:00+00:00")
    assert sorted(p.name for p in tmp_path.iterdir()) == ["2026-11-28T10.jsonl"]
    (tmp_path / "2026-11-28T10.jsonl").write_text(
        (tmp_path / "2026-11-28T10.jsonl").read_text() + "not json\n" + json.dumps({"time": "2026-11-26T09:00:00+00:00"}) + "\n"
    )
    assert read_lines(tmp_path, "2026-11-26T10:00:00+00:00") == [{"time": "2026-11-28T10:00:05+00:00", "event": "shadow"}]
