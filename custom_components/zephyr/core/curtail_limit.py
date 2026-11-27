"""Inverter power limit at a negative export price (PLANNING 1.2, number entity in %).

The inverter should produce what the house and the battery take, not more: export at a
negative price costs money, while turning it off fully would make the house import (the
import price is often still positive then). Every few seconds:

    wanted production = solar now + grid power (P1, + import) − margin

so the grid settles at a small import (``MARGIN_W``). As a percentage of the inverter's
rated power, rounded, only written on a change of at least ``MIN_STEP`` %, or back to 100 %
when the price is no longer negative.
"""

from __future__ import annotations

from typing import Final

MARGIN_W: Final = 50.0
"""Aim for this small import instead of exactly zero (no export by overshoot)."""
MIN_STEP: Final = 2
"""Smallest change of the limit worth a write (%)."""


def wanted_percent(solar_w: float, grid_w: float, rated_w: float, margin_w: float = MARGIN_W) -> int:
    """Limit (%) for the inverter so the grid stays at a small import."""
    if rated_w <= 0:
        return 100
    target = max(solar_w + grid_w - margin_w, 0.0)
    return max(0, min(100, round(target / rated_w * 100)))


def should_write(current: float | None, wanted: int) -> bool:
    """Write when the limit is unknown, moves at least MIN_STEP, or must go to 0 / 100."""
    if current is None:
        return True
    if wanted in (0, 100):
        return round(current) != wanted
    return abs(current - wanted) >= MIN_STEP
