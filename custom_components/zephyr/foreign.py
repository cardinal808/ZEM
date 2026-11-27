"""Settings that use an entity of another Zendure integration (repair issue and diagnostics).

ZEPHYR reads the sets itself and has its own counters (B44). An entity of another Zendure
integration in a setting either duplicates what ZEPHYR measures (PV of the set counted twice)
or stops working when that integration is removed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Final

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import issue_registry as ir

from .const import (
    CONF_COST_EXPORT_COUNTERS,
    CONF_COST_IMPORT_COUNTERS,
    CONF_P1_ENTITY,
    CONF_P1_EXPORT,
    CONF_P1_IMPORT,
    CONF_SOLAR_ENERGY,
    CONF_SOLAR_POWER,
    DOMAIN,
)
from .settings_schema import FIELDS

ISSUE_ID: Final = "foreign_entities"

ADVICE: Final[dict[str, str]] = {
    CONF_SOLAR_POWER: "remove",
    CONF_SOLAR_ENERGY: "inverter_counter",
    CONF_P1_ENTITY: "p1_meter",
    CONF_P1_IMPORT: "p1_meter",
    CONF_P1_EXPORT: "p1_meter",
    CONF_COST_IMPORT_COUNTERS: "p1_meter",
    CONF_COST_EXPORT_COUNTERS: "p1_meter",
}
"""What to do instead; anything else: a ZEPHYR entity or a source outside the sets."""


def _is_zendure(hass: HomeAssistant, entity_id: str) -> bool:
    """An entity of another Zendure integration: by its integration, device maker or name."""
    entry = er.async_get(hass).async_get(entity_id)
    if entry is not None:
        if entry.platform == DOMAIN:
            return False
        if "zendure" in entry.platform.lower():
            return True
        if entry.device_id:
            device = dr.async_get(hass).async_get(entry.device_id)
            if device is not None and "zendure" in (device.manufacturer or "").lower():
                return True
    return "zendure" in entity_id.split(".", 1)[-1].lower()


def foreign_entities(hass: HomeAssistant, options: Mapping[str, Any]) -> list[dict[str, str]]:
    """Every setting that points to an entity of another Zendure integration."""
    found: list[dict[str, str]] = []
    for field in FIELDS:
        if field.kind not in ("entity", "entities"):
            continue
        value = options.get(field.key)
        ids = value if isinstance(value, list) else [value] if isinstance(value, str) and value else []
        for entity_id in ids:
            if _is_zendure(hass, entity_id):
                found.append({"setting": field.key, "entity": entity_id, "advice": ADVICE.get(field.key, "replace")})
    return found


def check(hass: HomeAssistant, options: Mapping[str, Any]) -> list[dict[str, str]]:
    """Create or remove the repair issue; returns what was found."""
    found = foreign_entities(hass, options)
    if not found:
        ir.async_delete_issue(hass, DOMAIN, ISSUE_ID)
        return found
    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_ID,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_ID,
        translation_placeholders={"entities": "\n".join(f"- {f['setting']}: {f['entity']}" for f in found)},
    )
    return found
