"""Settings that use entities of another Zendure integration: repair issue and diagnostics."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from custom_components.zephyr.const import DOMAIN
from custom_components.zephyr.diagnostics import async_get_config_entry_diagnostics
from custom_components.zephyr.foreign import ISSUE_ID

from .conftest import FakeSets
from .test_costs import P1
from .test_shadow import _install_with_p1


async def _options(hass: HomeAssistant, entry_id: str, **options: object) -> None:
    result = await hass.config_entries.options.async_init(entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": P1, **options})
    await hass.async_block_till_done()


async def test_entities_of_another_zendure_integration_are_reported(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    registry = er.async_get(hass)
    other = registry.async_get_or_create("sensor", "zendure_ha", "abc_solar", suggested_object_id="set_solar_power")
    for entity_id in (other.entity_id, "sensor.zendure_2400_solar_input_power", "sensor.inverter_power"):
        hass.states.async_set(entity_id, "100", {"unit_of_measurement": "W", "device_class": "power"})
    entry = await _install_with_p1(hass, fake_sets)
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_ID) is None

    await _options(
        hass, entry.entry_id, solar_power_entities=[other.entity_id, "sensor.zendure_2400_solar_input_power", "sensor.inverter_power"]
    )
    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_ID)
    assert issue is not None and "sensor.zendure_2400_solar_input_power" in issue.translation_placeholders["entities"]
    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert [f["entity"] for f in diag["foreign_entities"]] == [other.entity_id, "sensor.zendure_2400_solar_input_power"]
    assert {f["advice"] for f in diag["foreign_entities"]} == {"remove"}
    assert diag["options"]["solar_power_entities"][-1] == "sensor.inverter_power"

    # Only the inverter left (a live setting, no reload): the issue goes away.
    await _options(hass, entry.entry_id, solar_power_entities=["sensor.inverter_power"])
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_ID) is None
