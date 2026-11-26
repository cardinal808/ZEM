"""The options of an installation as the panel shows them (SPEC-ui §3.4, §4.4; UI-6).

One list of fields with group, type, range, standard value and whether a
change needs a reload. The options flow of Home Assistant asks the same keys
with the same ranges; ``tests/ha/test_settings.py`` keeps the two in step.
Texts (label, short help, more help) live in the panel's translations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from .const import (
    CONF_COST_EXPORT_COUNTERS,
    CONF_COST_IMPORT_COUNTERS,
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
    CONF_RESERVE_SOC,
    CONF_SOLAR_ENERGY,
    CONF_SOLAR_FORECAST,
    CONF_TARIFF_ENERGY_TAX,
    CONF_TARIFF_FIXED_MONTH,
    CONF_TARIFF_MARKUP_EXPORT,
    CONF_TARIFF_MARKUP_IMPORT,
    CONF_TARIFF_SOLAR_BONUS,
    CONF_TARIFF_SUPPLIER,
    CONF_TARIFF_VAT,
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

GROUPS: Final = ("battery", "sources", "tariffs", "planner", "corrections", "zero_meter", "testing")


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
        }


_S = Settings()
_T = Tariffs()

FIELDS: Final[tuple[Field, ...]] = (
    Field(CONF_MIN_SOC, "battery", "number", _S.min_soc, "%", 5, 50, 1),
    Field(CONF_MAX_SOC, "battery", "number", _S.max_soc, "%", 70, 100, 1),
    Field(CONF_P1_SOURCE, "sources", "select", P1_SOURCE_SINGLE, options=(P1_SOURCE_SINGLE, P1_SOURCE_PAIR), reload=True),
    Field(CONF_P1_ENTITY, "sources", "entity", device_class="power", optional=True, reload=True),
    Field(CONF_P1_IMPORT, "sources", "entity", device_class="power", optional=True, reload=True),
    Field(CONF_P1_EXPORT, "sources", "entity", device_class="power", optional=True, reload=True),
    Field(CONF_PRICE_ENTITY, "sources", "entity", optional=True, reload=True),
    Field(CONF_SOLAR_FORECAST, "sources", "entity", optional=True, reload=True),
    Field(CONF_SOLAR_ENERGY, "sources", "entity", device_class="energy", optional=True, reload=True),
    Field(CONF_EXCLUDED_ENERGY, "corrections", "entity", device_class="energy", optional=True, reload=True),
    Field(CONF_EXCLUDED_CLIMATE, "corrections", "entity", optional=True, reload=True),
    Field(CONF_EXCLUDED_MODES, "corrections", "select", tuple(DEFAULT_EXCLUDED_MODES), options=tuple(HVAC_MODE_CHOICES), reload=True),
    Field(CONF_COST_IMPORT_COUNTERS, "sources", "entities", device_class="energy", optional=True, reload=True),
    Field(CONF_COST_EXPORT_COUNTERS, "sources", "entities", device_class="energy", optional=True, reload=True),
    Field(CONF_TARIFF_SUPPLIER, "tariffs", "select", TARIFF_OWN),
    Field(CONF_TARIFF_ENERGY_TAX, "tariffs", "number", _T.energy_tax, "€/kWh", 0, 1, "any", tariff=True),
    Field(CONF_TARIFF_MARKUP_IMPORT, "tariffs", "number", _T.markup_import, "€/kWh", -1, 1, "any", tariff=True),
    Field(CONF_TARIFF_MARKUP_EXPORT, "tariffs", "number", _T.markup_export, "€/kWh", -1, 1, "any", tariff=True),
    Field(CONF_TARIFF_VAT, "tariffs", "number", _T.vat, "%", 0, 30, 0.1, tariff=True),
    Field(CONF_TARIFF_SOLAR_BONUS, "tariffs", "number", _T.solar_bonus, "%", 0, 50, 0.1, tariff=True),
    Field(CONF_TARIFF_FIXED_MONTH, "tariffs", "number", None, "€", -200, 500, 0.01, optional=True),
    Field(CONF_PLAN_WEAR_COST, "planner", "number", DEFAULT_PLAN_WEAR_COST, "€/kWh", 0, 0.5, 0.001),
    Field(CONF_PLAN_GRID_CHARGE_COST, "planner", "number", DEFAULT_PLAN_GRID_CHARGE_COST, "€/kWh", 0, 0.5, 0.001),
    Field(CONF_PLAN_ALLOW_EXPORT, "planner", "bool", False),
    Field(CONF_PLAN_LOAD_MARGIN, "planner", "number", 0, "%", 0, 50, 1),
    Field(CONF_PLAN_BUFFER, "planner", "number", 0, "%", 0, 50, 1),
    Field(CONF_EXPENSIVE_HOURS, "zero_meter", "number", DEFAULT_EXPENSIVE_HOURS, "h", 1, 12, 1),
    Field(CONF_RESERVE_SOC, "zero_meter", "number", DEFAULT_RESERVE_SOC, "%", 0, 80, 1),
    Field(CONF_MIN_PRICE, "zero_meter", "number", None, "€/kWh", -1, 2, 0.01, optional=True),
    Field(CONF_LIVE_OFF_AFTER_RESTART, "testing", "bool", True),
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
