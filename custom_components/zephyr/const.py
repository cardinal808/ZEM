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

SCAN_INTERVAL_IDLE: Final = 5.0
"""Seconds between reads while ZEPHYR is not actively controlling the set."""
SCAN_INTERVAL_ACTIVE: Final = 2.0
"""Seconds between reads while the controller runs."""

MANUFACTURER: Final = "Zendure"

CONF_MIN_SOC = "min_soc"
CONF_MAX_SOC = "max_soc"
