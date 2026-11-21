"""Install ZEM, read sets, entities, offline handling, diagnostics."""

from __future__ import annotations

from datetime import timedelta
from ipaddress import IPv4Address
from typing import Any

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.zem.const import DOMAIN
from custom_components.zem.diagnostics import async_get_config_entry_diagnostics

from .conftest import FakeSets

SERIAL_1 = "EEB4AEXAMPLE001"
SERIAL_2 = "EEB4AEXAMPLE002"


async def _install(hass: HomeAssistant, host: str = "10.0.0.10") -> config_entries.ConfigEntry[Any]:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": host})
    assert result["type"] is FlowResultType.CREATE_ENTRY, result
    await hass.async_block_till_done()
    return hass.config_entries.async_entries(DOMAIN)[0]


async def _tick(hass: HomeAssistant, seconds: float = 5.5) -> None:
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=seconds))
    await hass.async_block_till_done()


async def test_install_creates_entities(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    fake_sets.add("10.0.0.10", "deliver_760")
    entry = await _install(hass)
    assert entry.title == "ZEM"
    assert len(entry.subentries) == 1

    assert float(hass.states.get("sensor.zem_set_1_state_of_charge").state) == 54
    assert float(hass.states.get("sensor.zem_set_1_power").state) == -760  # + = charging (B16)
    assert float(hass.states.get("sensor.zem_set_1_discharge_power").state) == 760
    assert float(hass.states.get("sensor.zem_set_1_charge_power").state) == 0
    assert hass.states.get("sensor.zem_set_1_status").state == "discharging"
    assert float(hass.states.get("sensor.zem_set_1_capacity").state) == pytest.approx(11.04)
    assert hass.states.get("binary_sensor.zem_set_1_online").state == "on"
    assert hass.states.get("binary_sensor.zem_set_1_fault").state == "off"

    assert float(hass.states.get("sensor.zem_state_of_charge").state) == 54
    assert float(hass.states.get("sensor.zem_capacity").state) == pytest.approx(11.04)
    assert float(hass.states.get("sensor.zem_power").state) == -760
    assert hass.states.get("sensor.zem_sets_online").state == "1"


async def test_nothing_is_written(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    fake_sets.add("10.0.0.10", "deliver_760")
    await _install(hass)
    await _tick(hass)
    await _tick(hass)
    assert fake_sets.writes == []
    assert fake_sets.reads["10.0.0.10"] >= 3


async def test_cannot_connect(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": "10.0.0.99"})
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_second_set_via_user_flow_becomes_subentry(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    fake_sets.add("10.0.0.10", "deliver_760")
    fake_sets.add("10.0.0.11", "charge_2400", serial=SERIAL_2, electricLevel=20)
    entry = await _install(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"host": "10.0.0.11"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "set_added"
    await hass.async_block_till_done()
    assert len(entry.subentries) == 2
    assert float(hass.states.get("sensor.zem_set_2_state_of_charge").state) == 20
    # Totals: capacity-weighted SOC, net power of both sets.
    assert float(hass.states.get("sensor.zem_capacity").state) == pytest.approx(22.08)
    assert float(hass.states.get("sensor.zem_state_of_charge").state) == pytest.approx(37.0)
    assert float(hass.states.get("sensor.zem_power").state) == pytest.approx(-760 + 2386)


async def test_subentry_flow_and_limit(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    fake_sets.add("10.0.0.10", "standby")
    for i, host in enumerate(("10.0.0.11", "10.0.0.12", "10.0.0.13"), start=2):
        fake_sets.add(host, "standby", serial=f"EEB4AEXAMPLE00{i}")
    entry = await _install(hass)
    for host in ("10.0.0.11", "10.0.0.12"):
        result = await hass.config_entries.subentries.async_init((entry.entry_id, "set"), context={"source": config_entries.SOURCE_USER})
        result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"host": host})
        assert result["type"] is FlowResultType.CREATE_ENTRY
        await hass.async_block_till_done()
    assert len(entry.subentries) == 3
    result = await hass.config_entries.subentries.async_init((entry.entry_id, "set"), context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "max_sets"


async def test_subentry_flow_rejects_known_set(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    fake_sets.add("10.0.0.10", "standby")
    fake_sets.add("10.0.0.20", "standby")  # same serial number, other address
    entry = await _install(hass)
    result = await hass.config_entries.subentries.async_init((entry.entry_id, "set"), context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {"host": "10.0.0.20"})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


def _zeroconf(host: str) -> ZeroconfServiceInfo:
    return ZeroconfServiceInfo(
        ip_address=IPv4Address(host),
        ip_addresses=[IPv4Address(host)],
        port=80,
        hostname="zendure.local.",
        type="_zendure._tcp.local.",
        name="Zendure._zendure._tcp.local.",
        properties={},
    )


async def test_zeroconf_discovery_installs(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    fake_sets.add("10.0.0.10", "standby")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=_zeroconf("10.0.0.10")
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert result["description_placeholders"]["model"] == "SolarFlow 2400 Pro"
    assert result["description_placeholders"]["serial"] == "…E001"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_zeroconf_follows_new_ip_address(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    fake_sets.add("10.0.0.10", "standby")
    entry = await _install(hass)
    fake_sets.add("10.0.0.50", "standby")  # same set, new address
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=_zeroconf("10.0.0.50")
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    await hass.async_block_till_done()
    sub = next(iter(entry.subentries.values()))
    assert sub.data["host"] == "10.0.0.50"


async def test_offline_after_three_failed_reads(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    fake_sets.add("10.0.0.10", "deliver_760")
    await _install(hass)
    fake_sets.fail("10.0.0.10")
    await _tick(hass)
    await _tick(hass)
    assert hass.states.get("binary_sensor.zem_set_1_online").state == "on"
    await _tick(hass)
    assert hass.states.get("binary_sensor.zem_set_1_online").state == "off"
    assert hass.states.get("sensor.zem_set_1_status").state == "offline"
    assert hass.states.get("sensor.zem_set_1_power").state == "unavailable"
    # Energy totals keep the last known values for five minutes.
    assert float(hass.states.get("sensor.zem_capacity").state) == pytest.approx(11.04)
    assert hass.states.get("sensor.zem_sets_online").state == "0"

    fake_sets.add("10.0.0.10", "deliver_760")
    await _tick(hass)
    assert hass.states.get("binary_sensor.zem_set_1_online").state == "off"  # needs two good reads
    await _tick(hass)
    assert hass.states.get("binary_sensor.zem_set_1_online").state == "on"


async def test_unreachable_set_does_not_block_setup(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    fake_sets.add("10.0.0.10", "standby")
    entry = await _install(hass)
    fake_sets.fail("10.0.0.10")
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert hass.states.get("binary_sensor.zem_set_1_online").state == "off"


async def test_other_serial_at_address_raises_issue(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    fake_sets.add("10.0.0.10", "standby")
    await _install(hass)
    fake_sets.add("10.0.0.10", "standby", serial="OTHERSET0000001")
    for _ in range(3):
        await _tick(hass)
    assert hass.states.get("binary_sensor.zem_set_1_online").state == "off"
    assert ir.async_get(hass).async_get_issue(
        DOMAIN, f"serial_mismatch_{next(iter(hass.config_entries.async_entries(DOMAIN)[0].subentries))}"
    )


async def test_diagnostics_hide_serials_and_addresses(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    fake_sets.add("10.0.0.10", "deliver_760")
    entry = await _install(hass)
    diag = await async_get_config_entry_diagnostics(hass, entry)
    text = str(diag)
    assert SERIAL_1 not in text
    assert "EXAMPLE000" not in text  # pack serials
    assert "10.0.0.10" not in text
    pack = diag["sets"][0]["report"]["packData"][0]
    assert pack["sn_prefix"] == "J"
    assert diag["sets"][0]["capacity"]["capacity_kwh"] == pytest.approx(11.04)
    assert diag["totals"]["power"] == -760
