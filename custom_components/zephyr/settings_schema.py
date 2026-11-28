"""The options of an installation as the panel shows them (SPEC-ui §3.4, §4.4; UI-6).

One list of fields with group, type, range, standard value and whether a
change needs a reload. The options flow of Home Assistant asks the same keys
with the same ranges; ``tests/ha/test_settings.py`` keeps the two in step.
Texts (label, short help, more help) live in the panel's translations.

``apply_changes`` checks a change from the panel (UI-7) against the same
rules as the options flow and returns the new options or the errors.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any, Final

from .const import (
    CONF_CALIBRATION_DAYS,
    CONF_COST_EXPORT_COUNTERS,
    CONF_COST_IMPORT_COUNTERS,
    CONF_CURTAIL_INVERTER_W,
    CONF_CURTAIL_MODE,
    CONF_CURTAIL_NUMBER,
    CONF_CURTAIL_SWITCH,
    CONF_EXCLUDED_CLIMATE,
    CONF_EXCLUDED_ENERGY,
    CONF_EXCLUDED_MODES,
    CONF_EXPENSIVE_HOURS,
    CONF_LIVE_OFF_AFTER_RESTART,
    CONF_MAX_SOC,
    CONF_MIN_PRICE,
    CONF_MIN_SOC,
    CONF_P1_ENTITY,
    CONF_P1_EXPORT,
    CONF_P1_IMPORT,
    CONF_P1_SOURCE,
    CONF_PLAN_ALLOW_EXPORT,
    CONF_PLAN_BUFFER,
    CONF_PLAN_GRID_CHARGE_COST,
    CONF_PLAN_LOAD_MARGIN,
    CONF_PLAN_WEAR_COST,
    CONF_PRICE_ENTITY,
    CONF_PRICE_FORECAST_DAYS,
    CONF_PRICE_FORECAST_ENTITY,
    CONF_PRICE_FORECAST_MODE,
    CONF_PRICE_FORECAST_VALUE,
    CONF_RESERVE_SOC,
    CONF_SOLAR_ENERGY,
    CONF_SOLAR_FORECAST,
    CONF_SOLAR_POWER,
    CONF_TARIFF_ENERGY_TAX,
    CONF_TARIFF_FIXED_MONTH,
    CONF_TARIFF_MARKUP_EXPORT,
    CONF_TARIFF_MARKUP_IMPORT,
    CONF_TARIFF_SOLAR_BONUS,
    CONF_TARIFF_SUPPLIER,
    CONF_TARIFF_VAT,
    CONF_VACATION_AWAY,
    CONF_WORKDAY_ENTITY,
    CURTAIL_MODES,
    CURTAIL_OFF,
    CURTAIL_ZEPHYR,
    DEFAULT_EXCLUDED_MODES,
    DEFAULT_EXPENSIVE_HOURS,
    DEFAULT_PLAN_GRID_CHARGE_COST,
    DEFAULT_PLAN_WEAR_COST,
    DEFAULT_RESERVE_SOC,
    HVAC_MODE_CHOICES,
    P1_SOURCE_PAIR,
    P1_SOURCE_SINGLE,
    TARIFF_OWN,
)
from .core.costs import Tariffs
from .core.settings import Settings

GROUPS: Final = ("battery", "sources", "tariffs", "planner", "corrections", "vacation", "house", "zero_meter", "testing")


@dataclass(frozen=True, slots=True)
class Field:
    key: str
    group: str
    kind: str
    """number, bool, select, entity (one sensor) or entities (several)."""
    default: Any = None
    unit: str | None = None
    minimum: float | None = None
    maximum: float | None = None
    step: float | str | None = None
    options: tuple[str, ...] = ()
    device_class: str | None = None
    optional: bool = False
    """May be empty (removed from the options)."""
    reload: bool = False
    """A change needs a reload of the installation (sources): the panel asks first."""
    tariff: bool = False
    """Only used with own tariffs; with a supplier the table's value applies."""
    domain: str = "sensor"
    """Entity domain for entity fields."""
    multiple: bool = False
    """A select with a list value (at least one choice)."""
    show_if: tuple[str, tuple[str, ...]] | None = None
    """Only shown when another field has one of these values ("*" = filled in); hidden values are kept."""
    section: str | None = None
    """Subtab within a long group (panel only); sections appear in the order of their first field."""

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "kind": self.kind,
            "default": self.default,
            "unit": self.unit,
            "min": self.minimum,
            "max": self.maximum,
            "step": self.step,
            "options": list(self.options),
            "device_class": self.device_class,
            "optional": self.optional,
            "reload": self.reload,
            "tariff": self.tariff,
            "domain": self.domain,
            "multiple": self.multiple,
            "show_if": {"key": self.show_if[0], "values": list(self.show_if[1])} if self.show_if else None,
            "section": self.section,
        }


# Fields that only apply with a certain choice (OPDRACHT-ui-velden-voorwaarde).
_P1_SINGLE: Final = (CONF_P1_SOURCE, (P1_SOURCE_SINGLE,))
_P1_PAIR: Final = (CONF_P1_SOURCE, (P1_SOURCE_PAIR,))
_ZEPHYR_CURTAILS: Final = (CONF_CURTAIL_MODE, (CURTAIL_ZEPHYR,))
_HAS_COUNTER: Final = (CONF_EXCLUDED_ENERGY, ("*",))
_HAS_FORECAST: Final = (CONF_PRICE_FORECAST_ENTITY, ("*",))

_S = Settings()
_T = Tariffs()

FIELDS: Final[tuple[Field, ...]] = (
    Field(CONF_MIN_SOC, "battery", "number", _S.min_soc, "%", 5, 50, 1),
    Field(CONF_MAX_SOC, "battery", "number", _S.max_soc, "%", 70, 100, 1),
    Field(CONF_P1_SOURCE, "sources", "select", P1_SOURCE_SINGLE, options=(P1_SOURCE_SINGLE, P1_SOURCE_PAIR), reload=True, section="meter"),
    Field(CONF_P1_ENTITY, "sources", "entity", device_class="power", optional=True, reload=True, show_if=_P1_SINGLE, section="meter"),
    Field(CONF_P1_IMPORT, "sources", "entity", device_class="power", optional=True, reload=True, show_if=_P1_PAIR, section="meter"),
    Field(CONF_P1_EXPORT, "sources", "entity", device_class="power", optional=True, reload=True, show_if=_P1_PAIR, section="meter"),
    Field(CONF_PRICE_ENTITY, "sources", "entity", optional=True, reload=True, section="prices"),
    Field(CONF_SOLAR_FORECAST, "sources", "entity", optional=True, reload=True, section="solar"),
    Field(CONF_PRICE_FORECAST_ENTITY, "sources", "entity", optional=True, reload=True, domain="sensor", section="prices"),
    Field(
        CONF_PRICE_FORECAST_MODE,
        "sources",
        "select",
        "indicative",
        options=("off", "indicative", "use"),
        show_if=_HAS_FORECAST,
        section="prices",
    ),
    Field(CONF_PRICE_FORECAST_DAYS, "sources", "number", 1, "d", 0, 2, 1, show_if=_HAS_FORECAST, section="prices"),
    Field(CONF_PRICE_FORECAST_VALUE, "sources", "select", "low", options=("low", "mid"), show_if=_HAS_FORECAST, section="prices"),
    Field(CONF_SOLAR_ENERGY, "sources", "entity", device_class="energy", optional=True, reload=True, section="solar"),
    Field(CONF_SOLAR_POWER, "sources", "entities", device_class="power", optional=True, section="solar"),
    Field(CONF_EXCLUDED_ENERGY, "corrections", "entity", device_class="energy", optional=True, reload=True),
    Field(CONF_EXCLUDED_CLIMATE, "corrections", "entity", optional=True, reload=True, domain="climate", show_if=_HAS_COUNTER),
    Field(
        CONF_EXCLUDED_MODES,
        "corrections",
        "select",
        tuple(DEFAULT_EXCLUDED_MODES),
        options=tuple(HVAC_MODE_CHOICES),
        reload=True,
        multiple=True,
        show_if=_HAS_COUNTER,
    ),
    Field(CONF_COST_IMPORT_COUNTERS, "sources", "entities", device_class="energy", optional=True, reload=True, section="counters"),
    Field(CONF_COST_EXPORT_COUNTERS, "sources", "entities", device_class="energy", optional=True, reload=True, section="counters"),
    Field(CONF_TARIFF_SUPPLIER, "tariffs", "select", TARIFF_OWN),
    Field(CONF_TARIFF_ENERGY_TAX, "tariffs", "number", _T.energy_tax, "€/kWh", 0, 1, "any", tariff=True),
    Field(CONF_TARIFF_MARKUP_IMPORT, "tariffs", "number", _T.markup_import, "€/kWh", -1, 1, "any", tariff=True),
    Field(CONF_TARIFF_MARKUP_EXPORT, "tariffs", "number", _T.markup_export, "€/kWh", -1, 1, "any", tariff=True),
    Field(CONF_TARIFF_VAT, "tariffs", "number", _T.vat, "%", 0, 30, 0.1, tariff=True),
    Field(CONF_TARIFF_SOLAR_BONUS, "tariffs", "number", _T.solar_bonus, "%", 0, 50, 0.1, tariff=True),
    Field(CONF_TARIFF_FIXED_MONTH, "tariffs", "number", None, "€", -200, 500, 0.01, optional=True),
    Field(CONF_PLAN_WEAR_COST, "planner", "number", DEFAULT_PLAN_WEAR_COST, "€/kWh", 0, 0.5, 0.001, section="plan"),
    Field(CONF_PLAN_GRID_CHARGE_COST, "planner", "number", DEFAULT_PLAN_GRID_CHARGE_COST, "€/kWh", 0, 0.5, 0.001, section="plan"),
    Field(CONF_PLAN_ALLOW_EXPORT, "planner", "bool", False, section="plan"),
    Field(CONF_PLAN_LOAD_MARGIN, "planner", "number", 0, "%", 0, 50, 1, section="plan"),
    Field(CONF_PLAN_BUFFER, "planner", "number", 0, "%", 0, 50, 1, section="plan"),
    Field(CONF_CALIBRATION_DAYS, "battery", "number", 21, "d", 0, 90, 1),
    Field(CONF_WORKDAY_ENTITY, "sources", "entity", optional=True, reload=True, domain="binary_sensor", section="counters"),
    Field(CONF_CURTAIL_MODE, "planner", "select", CURTAIL_OFF, options=CURTAIL_MODES, reload=True, section="curtail"),
    Field(
        CONF_CURTAIL_SWITCH, "planner", "entity", optional=True, reload=True, domain="switch", show_if=_ZEPHYR_CURTAILS, section="curtail"
    ),
    Field(
        CONF_CURTAIL_NUMBER, "planner", "entity", optional=True, reload=True, domain="number", show_if=_ZEPHYR_CURTAILS, section="curtail"
    ),
    Field(CONF_CURTAIL_INVERTER_W, "planner", "number", 0, "W", 0, 100000, 100, reload=True, show_if=_ZEPHYR_CURTAILS, section="curtail"),
    Field(CONF_VACATION_AWAY, "vacation", "bool", False, reload=True),
    Field(CONF_EXPENSIVE_HOURS, "zero_meter", "number", DEFAULT_EXPENSIVE_HOURS, "h", 1, 12, 1),
    Field(CONF_RESERVE_SOC, "zero_meter", "number", DEFAULT_RESERVE_SOC, "%", 0, 80, 1),
    Field(CONF_MIN_PRICE, "zero_meter", "number", None, "€/kWh", -1, 2, 0.01, optional=True),
    Field(CONF_LIVE_OFF_AFTER_RESTART, "testing", "bool", False),
)

BY_KEY: Final = {f.key: f for f in FIELDS}


def is_modified(field: Field, options: dict[str, Any]) -> bool:
    """The user changed this field (it is in the options and differs from the standard value)."""
    if field.key not in options:
        return False
    value = options[field.key]
    if field.kind == "number" and value is not None and field.default is not None:
        return abs(float(value) - float(field.default)) > 1e-9
    return bool(value != field.default and not (field.optional and value in (None, "", [])))


_ENTITY_ID: Final = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")
_EMPTY: Final[tuple[Any, ...]] = (None, "", [])


def _number(field: Field, value: Any) -> tuple[float | None, str | None]:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return None, "not_a_number"
    try:
        number = float(value)
    except ValueError:
        return None, "not_a_number"
    if not math.isfinite(number):
        return None, "not_a_number"
    if (field.minimum is not None and number < field.minimum - 1e-9) or (field.maximum is not None and number > field.maximum + 1e-9):
        return None, "out_of_range"
    if isinstance(field.step, int | float) and field.step > 0:
        base = field.minimum or 0.0
        steps = (number - base) / field.step
        if abs(steps - round(steps)) > 1e-6:
            return None, "off_step"
        number = round(base + round(steps) * field.step, 6)
    return number, None


def _check(field: Field, value: Any, suppliers: Iterable[str], entity_ok: Callable[[str], bool]) -> tuple[Any, str | None]:
    """The value to store for one field, or an error code."""
    if field.kind == "number":
        return _number(field, value)
    if field.kind == "bool":
        return (value, None) if isinstance(value, bool) else (None, "not_a_bool")
    if field.kind == "select":
        allowed = set(field.options) if field.options else set(suppliers)
        if field.multiple:
            if not isinstance(value, list) or not value:
                return None, "choose_one"
            if any(not isinstance(v, str) or v not in allowed for v in value):
                return None, "unknown_choice"
            return [o for o in field.options if o in value], None
        return (value, None) if isinstance(value, str) and value in allowed else (None, "unknown_choice")
    ids = value if field.kind == "entities" else [value]
    if not isinstance(ids, list) or any(not isinstance(e, str) for e in ids):
        return None, "not_an_entity"
    for entity_id in ids:
        if not _ENTITY_ID.match(entity_id) or entity_id.split(".", 1)[0] != field.domain:
            return None, "not_an_entity"
        if not entity_ok(entity_id):
            return None, "entity_missing"
    if field.kind == "entities":
        return list(dict.fromkeys(ids)), None
    return value, None


def cross_errors(options: Mapping[str, Any]) -> str | None:
    """Rules over several fields, the same as the options flow (and B41: a climate entity needs the counter)."""
    if options.get(CONF_P1_SOURCE, P1_SOURCE_SINGLE) == P1_SOURCE_PAIR:
        if not (options.get(CONF_P1_IMPORT) and options.get(CONF_P1_EXPORT)):
            return "p1_pair_incomplete"
        if options[CONF_P1_IMPORT] == options[CONF_P1_EXPORT]:
            return "p1_pair_same"
    elif not options.get(CONF_P1_ENTITY):
        return "p1_missing"
    # A climate entity without the counter is hidden in the panel and not used (control.py), so it is
    # kept rather than refused; the options flow of HA still asks for the counter.
    return None


@dataclass(frozen=True, slots=True)
class ChangeResult:
    options: dict[str, Any]
    errors: dict[str, str]
    """Per field key, or ``base`` for a rule over several fields."""
    changed: tuple[str, ...]

    @property
    def reload(self) -> bool:
        return any(BY_KEY[k].reload for k in self.changed)


def apply_changes(
    options: Mapping[str, Any],
    changes: Mapping[str, Any],
    reset: Iterable[str] = (),
    *,
    suppliers: Iterable[str] = (TARIFF_OWN,),
    entity_ok: Callable[[str], bool] = lambda _e: True,
) -> ChangeResult:
    """New options after ``changes`` (key → value) and ``reset`` (keys back to the standard value).

    An empty value of an optional field removes it, like the options flow does.
    """
    data = dict(options)
    errors: dict[str, str] = {}
    supplier_keys = list(suppliers)
    for key in reset:
        if key not in BY_KEY:
            errors[key] = "unknown_key"
        else:
            data.pop(key, None)
    for key, value in changes.items():
        field = BY_KEY.get(key)
        if field is None:
            errors[key] = "unknown_key"
            continue
        if value in _EMPTY and not (field.kind == "select" and field.multiple):
            if field.optional:
                data.pop(key, None)
            else:
                errors[key] = "required"
            continue
        stored, error = _check(field, value, supplier_keys, entity_ok)
        if error is not None:
            errors[key] = error
        else:
            data[key] = stored
    if not errors and (base := cross_errors(data)) is not None:
        errors["base"] = base
    changed = tuple(k for k in BY_KEY if data.get(k) != options.get(k))
    return ChangeResult(data if not errors else dict(options), errors, changed if not errors else ())
