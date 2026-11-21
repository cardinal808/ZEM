"""Constants for the ZEM integration."""

from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "zem"
LOGGER = logging.getLogger(__package__)

SUBENTRY_SET: Final = "set"
MAX_SETS: Final = 3

CONF_HOST: Final = "host"
CONF_SERIAL: Final = "serial"
CONF_PRODUCT: Final = "product"
CONF_NUMBER: Final = "number"
CONF_CAPACITY_OVERRIDE: Final = "capacity_override"

SCAN_INTERVAL_IDLE: Final = 5.0
"""Seconds between reads while ZEM is not actively controlling the set."""

MANUFACTURER: Final = "Zendure"
