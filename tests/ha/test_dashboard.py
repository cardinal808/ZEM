"""The test dashboard (PLAN-M4b §2.9) is valid YAML and refers only to ZEPHYR entities that exist."""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from homeassistant.core import HomeAssistant

from .conftest import FakeSets
from .test_shadow import _install_with_p1

DASHBOARD = Path(__file__).parents[2] / "dashboards" / "zephyr-test.yaml"
ENTITY = re.compile(r"\b(?:switch|select|sensor|binary_sensor)\.zephyr_[a-z0-9_]+")


async def test_dashboard_entities_exist(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    text = DASHBOARD.read_text(encoding="utf-8")
    config = yaml.safe_load(text)
    assert config["views"][0]["cards"]
    entry = await _install_with_p1(hass, fake_sets)
    # The plan entities exist with a price sensor (SPEC-planner §4).
    hass.states.async_set("sensor.nordpool_test", "0.1", {"raw_today": [], "raw_tomorrow": []})
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(
        result["flow_id"], {"p1_entity": "sensor.p1_meter_power", "price_entity": "sensor.nordpool_test"}
    )
    await hass.async_block_till_done()
    missing = sorted({e for e in ENTITY.findall(text) if hass.states.get(e) is None})
    assert not missing, missing
    services = set(re.findall(r"perform_action: (\w+\.\w+)", text))
    for service in services:
        domain, name = service.split(".")
        assert hass.services.has_service(domain, name), service
