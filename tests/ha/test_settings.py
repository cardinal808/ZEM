"""Settings in the panel (SPEC-ui §3.4, UI-6): one list of fields, in step with the options flow."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.zephyr.settings_schema import BY_KEY, FIELDS, GROUPS, is_modified

from .conftest import FakeSets
from .test_shadow import P1, _install_with_p1


def test_every_field_has_a_known_group_and_a_sane_range() -> None:
    assert len(BY_KEY) == len(FIELDS)
    for field in FIELDS:
        assert field.group in GROUPS
        if field.kind == "number":
            assert field.minimum is not None and field.maximum is not None and field.minimum < field.maximum
            if field.default is not None:
                assert field.minimum <= field.default <= field.maximum, field.key


def test_modified() -> None:
    min_soc = BY_KEY["min_soc"]
    assert not is_modified(min_soc, {})
    assert not is_modified(min_soc, {"min_soc": min_soc.default})
    assert is_modified(min_soc, {"min_soc": 15})
    assert not is_modified(BY_KEY["min_price"], {"min_price": None})
    assert is_modified(BY_KEY["plan_allow_export"], {"plan_allow_export": True})


async def test_same_keys_and_ranges_as_the_options_flow(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    """The panel and HA's options flow must ask the same things within the same limits."""
    entry = await _install_with_p1(hass, fake_sets)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    schema = result["data_schema"].schema
    flow: dict[str, Any] = {str(key): value for key, value in schema.items()}
    assert set(flow) == set(BY_KEY)
    for key, sel in flow.items():
        field = BY_KEY[key]
        if isinstance(sel, selector.NumberSelector):
            config = sel.config
            assert field.kind == "number", key
            assert (config["min"], config["max"]) == (field.minimum, field.maximum), key
            assert config["step"] == field.step, key
            assert config.get("unit_of_measurement") == field.unit, key
        elif sel is bool:
            assert field.kind == "bool", key
        elif isinstance(sel, selector.EntitySelector):
            assert field.kind == ("entities" if sel.config.get("multiple") else "entity"), key
        elif isinstance(sel, selector.SelectSelector):
            assert field.kind == "select", key


async def test_settings_get(hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    await hass.config_entries.options.async_configure(result["flow_id"], {"p1_entity": P1, "min_soc": 15, "plan_buffer": 10})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "zephyr/settings/get"})
    msg = await client.receive_json()
    assert msg["success"] is True
    view = msg["result"]
    assert view["can_edit"] is True
    assert [g["key"] for g in view["groups"]] == list(GROUPS)
    fields = {f["key"]: f for g in view["groups"] for f in g["fields"]}
    assert fields["min_soc"]["value"] == 15 and fields["min_soc"]["modified"] is True
    assert fields["max_soc"]["modified"] is False
    assert fields["plan_buffer"]["value"] == 10 and fields["plan_buffer"]["modified"] is True
    battery = next(g for g in view["groups"] if g["key"] == "battery")
    assert battery["modified"] == 1
    assert fields["p1_entity"]["status"]["state"] == "ok"
    assert fields["price_entity"]["status"] == {"state": "unset"}
    assert fields["tariff_supplier"]["choices"][0]["value"] == "own"
    assert fields["tariff_energy_tax"]["active"] is True
    assert fields["tariff_energy_tax"]["in_use"] == fields["tariff_energy_tax"]["value"]
    assert fields["p1_entity"]["reload"] is True and fields["min_soc"]["reload"] is False


async def test_settings_get_read_only_for_other_users(
    hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator, hass_read_only_access_token: str
) -> None:
    await _install_with_p1(hass, fake_sets)
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json_auto_id({"type": "zephyr/settings/get"})
    msg = await client.receive_json()
    assert msg["success"] is True
    assert msg["result"]["can_edit"] is False


def test_panel_has_texts_for_every_field() -> None:
    """Label, help and more text in the panel's translations for every field and group."""
    import json
    from pathlib import Path

    root = Path(__file__).parents[2] / "frontend" / "src" / "locales"
    for lang in ("nl", "en"):
        texts = json.loads((root / f"{lang}.json").read_text(encoding="utf-8"))["settings"]
        assert set(texts["fields"]) == set(BY_KEY), lang
        assert set(texts["groups"]) == set(GROUPS), lang
        for key, field in texts["fields"].items():
            assert field["label"] and field["help"] and field["more"], (lang, key)
