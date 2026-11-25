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
