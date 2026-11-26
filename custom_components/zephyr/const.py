"""Constants for the ZEPHYR integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "zephyr"
LOGGER = logging.getLogger(__package__)

SUBENTRY_SET: Final = "set"
MAX_SETS: Final = 3

CONF_HOST: Final = "host"
CONF_SERIAL: Final = "serial"
CONF_PRODUCT: Final = "product"
CONF_NUMBER: Final = "number"
CONF_CAPACITY_OVERRIDE: Final = "capacity_override"
CONF_P1_ENTITY: Final = "p1_entity"
CONF_P1_SOURCE: Final = "p1_source"
CONF_P1_IMPORT: Final = "p1_import_entity"
CONF_P1_EXPORT: Final = "p1_export_entity"
P1_SOURCE_SINGLE: Final = "single"
P1_SOURCE_PAIR: Final = "import_export"
CONF_SOLAR_FORECAST: Final = "solar_forecast_entity"
CONF_SOLAR_ENERGY: Final = "solar_energy_entity"
CONF_PRICE_ENTITY: Final = "price_entity"
CONF_EXCLUDED_ENERGY: Final = "excluded_energy_entity"
CONF_VACATION_AWAY: Final = "vacation_when_away"
CONF_WORKDAY_ENTITY: Final = "workday_entity"
"""Workday binary sensor: holidays count as weekend days in the consumption profile."""
"""B42: vacation on by itself when nobody is home (zone.home = 0) for 24 h."""
"""B41: energy counter of a load the battery may not feed (the air conditioner)."""
CONF_EXCLUDED_CLIMATE: Final = "excluded_climate_entity"
CONF_EXCLUDED_MODES: Final = "excluded_hvac_modes"
DEFAULT_EXCLUDED_MODES: Final = ["heat"]
HVAC_MODE_CHOICES: Final = ["heat", "cool", "dry", "fan_only", "heat_cool", "auto"]
CONF_EXPENSIVE_HOURS: Final = "expensive_hours"
CONF_RESERVE_SOC: Final = "reserve_soc"
CONF_MIN_PRICE: Final = "min_price"
DEFAULT_EXPENSIVE_HOURS: Final = 4
DEFAULT_RESERVE_SOC: Final = 20
CONF_LIVE_OFF_AFTER_RESTART: Final = "live_off_after_restart"
"""Test phase (PLAN-M4b L5): live control stays off after a restart until the user switches it on."""

SCAN_INTERVAL_IDLE: Final = 5.0
"""Seconds between reads while ZEPHYR is not actively controlling the set."""
SCAN_INTERVAL_ACTIVE: Final = 2.0
"""Seconds between reads while the controller runs."""

MANUFACTURER: Final = "Zendure"

CONF_MIN_SOC = "min_soc"
CONF_MAX_SOC = "max_soc"

# Cost log (B38): own tariffs, €/kWh excl. VAT. The tariff table (B28) follows.
CONF_TARIFF_ENERGY_TAX: Final = "tariff_energy_tax"
CONF_TARIFF_VAT: Final = "tariff_vat"
CONF_TARIFF_MARKUP_IMPORT: Final = "tariff_markup_import"
CONF_TARIFF_MARKUP_EXPORT: Final = "tariff_markup_export"
CONF_TARIFF_FIXED_MONTH: Final = "tariff_fixed_month"
CONF_TARIFF_SOLAR_BONUS: Final = "tariff_solar_bonus"
CONF_TARIFF_SUPPLIER: Final = "tariff_supplier"
TARIFF_OWN: Final = "own"
"""Supplier choice: own tariffs from the options instead of the tariff table (B28)."""
CONF_COST_IMPORT_COUNTERS: Final = "cost_import_counters"
CONF_COST_EXPORT_COUNTERS: Final = "cost_export_counters"

# Planner (M5, SPEC-planner §2.5)
CONF_PLAN_WEAR_COST: Final = "plan_wear_cost"
CONF_PLAN_ALLOW_EXPORT: Final = "plan_allow_export"
CONF_PLAN_LOAD_MARGIN: Final = "plan_load_margin"
CONF_PLAN_BUFFER: Final = "plan_buffer"
CONF_PLAN_GRID_CHARGE_COST: Final = "plan_grid_charge_cost"
DEFAULT_PLAN_WEAR_COST: Final = 0.03
"""€ per kWh out of the battery (B39)."""
DEFAULT_PLAN_GRID_CHARGE_COST: Final = 0.01
"""€ per kWh charged from the grid that grid charging must win (B40, BACKTEST-1 §grid charge)."""
