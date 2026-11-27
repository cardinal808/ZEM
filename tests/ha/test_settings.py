"""Settings in the panel (SPEC-ui §3.4, UI-6): one list of fields, in step with the options flow."""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import selector
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.zephyr.settings_schema import BY_KEY, FIELDS, GROUPS, apply_changes, is_modified

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
            assert sel.config["domain"] == [field.domain], key
        elif isinstance(sel, selector.SelectSelector):
            assert field.kind == "select", key
            assert bool(sel.config.get("multiple")) == field.multiple, key


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
    vacation = view["vacation"]
    assert vacation["active"] is False and vacation["until"] is None
    assert vacation["entities"]["switch"].startswith("switch.")
    assert vacation["entities"]["until"].startswith("datetime.")


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


# --- UI-7: changing settings ----------------------------------------------

BASE = {"p1_entity": P1}


@pytest.mark.parametrize(
    ("changes", "error"),
    [
        ({"min_soc": 60}, ("min_soc", "out_of_range")),
        ({"min_soc": 12.5}, ("min_soc", "off_step")),
        ({"min_soc": "veel"}, ("min_soc", "not_a_number")),
        ({"min_soc": True}, ("min_soc", "not_a_number")),
        ({"min_soc": None}, ("min_soc", "required")),
        ({"plan_allow_export": "ja"}, ("plan_allow_export", "not_a_bool")),
        ({"p1_source": "three"}, ("p1_source", "unknown_choice")),
        ({"excluded_hvac_modes": []}, ("excluded_hvac_modes", "choose_one")),
        ({"excluded_hvac_modes": ["heat", "boil"]}, ("excluded_hvac_modes", "unknown_choice")),
        ({"tariff_supplier": "nobody"}, ("tariff_supplier", "unknown_choice")),
        ({"p1_entity": "switch.p1"}, ("p1_entity", "not_an_entity")),
        ({"p1_entity": "sensor.gone"}, ("p1_entity", "entity_missing")),
        ({"excluded_climate_entity": "sensor.living"}, ("excluded_climate_entity", "not_an_entity")),
        ({"nonsense": 1}, ("nonsense", "unknown_key")),
        ({"p1_entity": None}, ("base", "p1_missing")),
        ({"p1_source": "import_export", "p1_import_entity": "sensor.in"}, ("base", "p1_pair_incomplete")),
        ({"p1_source": "import_export", "p1_import_entity": "sensor.in", "p1_export_entity": "sensor.in"}, ("base", "p1_pair_same")),
    ],
)
def test_apply_changes_rejects(changes: dict[str, Any], error: tuple[str, str]) -> None:
    result = apply_changes(BASE, changes, entity_ok=lambda e: e != "sensor.gone")
    assert result.errors == {error[0]: error[1]}
    assert result.options == BASE and result.changed == ()


def test_apply_changes_stores_like_the_options_flow() -> None:
    result = apply_changes(
        {**BASE, "min_price": 0.1, "plan_buffer": 10},
        {"min_soc": "15", "plan_wear_cost": 0.021, "min_price": None, "excluded_hvac_modes": ["cool", "heat", "heat"]},
        reset=["plan_buffer"],
    )
    assert result.errors == {}
    assert result.options == {**BASE, "min_soc": 15.0, "plan_wear_cost": 0.021, "excluded_hvac_modes": ["heat", "cool"]}
    assert set(result.changed) == {"min_soc", "plan_wear_cost", "min_price", "plan_buffer", "excluded_hvac_modes"}
    assert result.reload is True  # the air-conditioner modes are a source setting
    assert apply_changes(BASE, {"min_soc": 15}).reload is False
    assert apply_changes(BASE, {"p1_entity": P1}).changed == ()


def _example(hass: HomeAssistant, key: str, suppliers: list[str]) -> dict[str, Any]:
    """A valid value for every field that differs from what is set (plus what it needs)."""
    field = BY_KEY[key]
    energy = {"device_class": "energy", "unit_of_measurement": "kWh"}
    hass.states.async_set("sensor.p1_in", "1", {"device_class": "power"})
    hass.states.async_set("sensor.p1_out", "0", {"device_class": "power"})
    hass.states.async_set("sensor.counter", "12.5", energy)
    hass.states.async_set("climate.living", "heat", {"hvac_action": "heating"})
    if field.kind == "number":
        assert field.minimum is not None and field.maximum is not None
        return {key: field.maximum if field.default in (None, field.minimum) else field.minimum}
    if field.kind == "bool":
        return {key: not field.default}
    if field.kind == "select":
        if field.multiple:
            return {key: ["cool"]}
        if key == "tariff_supplier":
            return {key: suppliers[1]}
        return {key: next(o for o in field.options if o != field.default)} | (
            {"p1_import_entity": "sensor.p1_in", "p1_export_entity": "sensor.p1_out"} if key == "p1_source" else {}
        )
    if field.domain == "binary_sensor":
        hass.states.async_set("binary_sensor.workday_sensor", "on")
        return {key: "binary_sensor.workday_sensor"}
    if field.domain == "number":
        hass.states.async_set("number.inverter_limit", "100")
        return {key: "number.inverter_limit"}
    if field.domain == "switch":
        hass.states.async_set("switch.export_limit", "off")
        return {key: "switch.export_limit"}
    if key == "excluded_climate_entity":
        return {key: "climate.living", "excluded_energy_entity": "sensor.counter"}
    if field.kind == "entities":
        return {key: ["sensor.p1_in" if field.device_class == "power" else "sensor.counter"]}
    return {key: "sensor.p1_in" if field.device_class == "power" else "sensor.counter"}


@pytest.mark.parametrize("key", list(BY_KEY))
async def test_settings_set_every_key(hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator, key: str) -> None:
    """Live fields change without a reload; sources reload ZEPHYR (SPEC-ui §3.4)."""
    entry = await _install_with_p1(hass, fake_sets)
    runtime = entry.runtime_data
    assert runtime.tariffs is not None and runtime.tariffs.table is not None
    suppliers = ["own", *(k for k, _n in runtime.tariffs.table.choices())]
    changes = _example(hass, key, suppliers)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "zephyr/settings/set", "changes": changes})
    msg = await client.receive_json()
    assert msg["success"] is True, msg
    assert msg["result"]["ok"] is True, msg["result"]
    assert key in msg["result"]["changed"]
    assert msg["result"]["reload"] is BY_KEY[key].reload
    await hass.async_block_till_done()
    for k, v in changes.items():
        assert entry.options[k] == v, k
    if BY_KEY[key].reload:
        assert entry.runtime_data is not runtime
    else:
        assert entry.runtime_data is runtime
        assert runtime.options == dict(entry.options)


async def test_live_settings_reach_engine_planner_and_tariffs(
    hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    runtime = entry.runtime_data
    control, tariffs = runtime.control, runtime.tariffs
    assert control is not None and tariffs is not None
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "zephyr/settings/set",
            "changes": {"min_soc": 20, "max_soc": 90, "reserve_soc": 40, "expensive_hours": 3, "min_price": 0.25, "tariff_vat": 9},
        }
    )
    assert (await client.receive_json())["result"]["ok"] is True
    await hass.async_block_till_done()
    assert (control.engine.settings.min_soc, control.engine.settings.max_soc) == (20, 90)
    assert (control.reserve_soc, control.expensive_hours, control.min_price) == (40, 3, 0.25)
    assert tariffs.own.vat == 9
    await client.send_json_auto_id({"type": "zephyr/settings/set", "reset": ["min_soc", "min_price"]})
    assert (await client.receive_json())["result"]["changed"] == ["min_soc", "min_price"]
    await hass.async_block_till_done()
    assert control.engine.settings.min_soc == BY_KEY["min_soc"].default
    assert control.min_price is None
    assert entry.runtime_data is runtime


async def test_settings_set_reports_errors_and_changes_nothing(
    hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    before = dict(entry.options)
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "zephyr/settings/set", "changes": {"min_soc": 70, "max_soc": 95}})
    msg = await client.receive_json()
    assert msg["result"] == {"ok": False, "errors": {"min_soc": "out_of_range"}}
    assert dict(entry.options) == before


async def test_settings_set_only_for_administrators(
    hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator, hass_read_only_access_token: str
) -> None:
    await _install_with_p1(hass, fake_sets)
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json_auto_id({"type": "zephyr/settings/set", "changes": {"min_soc": 15}})
    msg = await client.receive_json()
    assert msg["success"] is False and msg["error"]["code"] == "unauthorized"


async def test_air_conditioner_status_next_to_the_fields(
    hass: HomeAssistant, fake_sets: FakeSets, hass_ws_client: WebSocketGenerator
) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    hass.states.async_set("sensor.counter", "12.5", {"device_class": "energy", "unit_of_measurement": "kWh"})
    hass.states.async_set("climate.living", "heat", {"hvac_action": "heating"})
    client = await hass_ws_client(hass)
    await client.send_json_auto_id(
        {
            "type": "zephyr/settings/set",
            "changes": {"excluded_energy_entity": "sensor.counter", "excluded_climate_entity": "climate.living"},
        }
    )
    assert (await client.receive_json())["result"]["reload"] is True
    await hass.async_block_till_done()
    assert entry.runtime_data.control is not None and entry.runtime_data.control.excluded is not None
    await client.send_json_auto_id({"type": "zephyr/settings/get"})
    fields = {f["key"]: f for g in (await client.receive_json())["result"]["groups"] for f in g["fields"]}
    assert fields["excluded_climate_entity"]["status"] == {"state": "ok", "mode": "heat", "action": "heating"}
    assert fields["excluded_energy_entity"]["status"] == {"state": "ok", "no_step": True}
    assert fields["excluded_hvac_modes"]["multiple"] is True
    hass.states.async_set("climate.living", "unavailable")
    await client.send_json_auto_id({"type": "zephyr/settings/get"})
    fields = {f["key"]: f for g in (await client.receive_json())["result"]["groups"] for f in g["fields"]}
    assert fields["excluded_climate_entity"]["status"] == {"state": "unavailable"}


async def test_options_flow_needs_the_counter_for_a_climate_entity(hass: HomeAssistant, fake_sets: FakeSets) -> None:
    entry = await _install_with_p1(hass, fake_sets)
    hass.states.async_set("climate.living", "heat")
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"p1_entity": P1, "excluded_climate_entity": "climate.living"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "excluded_needs_counter"}


def test_show_if_points_at_real_fields_and_choices() -> None:
    """Every condition names an existing field and one of its choices ("*" = an entity filled in)."""
    from custom_components.zephyr.settings_schema import BY_KEY, FIELDS

    conditional = [f for f in FIELDS if f.show_if]
    assert {f.key for f in conditional} >= {
        "p1_entity",
        "p1_import_entity",
        "p1_export_entity",
        "curtail_switch",
        "curtail_number",
        "curtail_inverter_w",
        "excluded_climate_entity",
        "excluded_hvac_modes",
    }
    for field in conditional:
        key, values = field.show_if  # type: ignore[misc]
        other = BY_KEY[key]
        assert other.show_if is None, field.key  # no chains
        for value in values:
            assert value in other.options if value != "*" else other.kind in ("entity", "entities"), field.key
        assert field.as_dict()["show_if"] == {"key": key, "values": list(values)}


def test_climate_without_counter_is_kept_not_refused() -> None:
    """Hidden in the panel and not used by control.py; the options flow still asks for the counter."""
    result = apply_changes(BASE, {"excluded_climate_entity": "climate.living"}, entity_ok=lambda e: True)
    assert result.errors == {}
