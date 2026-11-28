"""Hand-over of the running control from one setup of the entry to the next (reload).

A reload (a setting that needs one, a set added) used to leave the sets at 0 W and start again
from nothing: the relay opened, the new control waited for the P1 and went live with a new
``acMode`` (a relay switch), and the house drew from the grid meanwhile. Now the unload leaves
the sets at their last command and parks the engine here; the next setup takes it over within
``HANDOVER_FOR`` and goes on as if nothing happened.

Nobody takes it over in time (the setup failed, the entry was removed): the sets go to 0 W
then, as before. Disabling the entry still writes 0 W at once (control.py).
"""

from __future__ import annotations

import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Final

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from .core.engine import ZephyrEngine
    from .writer import SetWriter

HANDOVER_FOR: Final = 120.0
"""s the next setup has to take over; after that the sets go to 0 W."""
KEY: Final = f"{DOMAIN}_handover"


@dataclass
class Handover:
    engine: ZephyrEngine
    live: bool
    live_since: float | None
    p1_watts: float | None
    p1_at: float | None
    p1_gaps: list[tuple[float, float]]
    writers: dict[str, SetWriter]
    live_history: list[dict[str, Any]]
    zero: Callable[[], Coroutine[Any, Any, None]]
    """Leaves the sets at 0 W (the old control's writers): when nobody takes over."""
    at: float = field(default_factory=time.monotonic)
    cancel: Callable[[], None] | None = None


def _parked(hass: HomeAssistant) -> dict[str, Handover]:
    parked: dict[str, Handover] = hass.data.setdefault(KEY, {})
    return parked


@callback
def park(hass: HomeAssistant, entry_id: str, handover: Handover) -> None:
    """Keep the control for the next setup; 0 W after ``HANDOVER_FOR`` when nobody takes it."""
    old = _parked(hass).pop(entry_id, None)
    if old is not None and old.cancel is not None:
        old.cancel()

    @callback
    def expire(_now: Any) -> None:
        if _parked(hass).get(entry_id) is not handover:
            return
        del _parked(hass)[entry_id]
        if handover.live:
            LOGGER.warning("ZEPHYR did not start again within %d s after the reload: the sets go to 0 W", HANDOVER_FOR)
            hass.async_create_background_task(handover.zero(), "zephyr: hand-over expired, sets to 0 W")

    handover.cancel = async_call_later(hass, HANDOVER_FOR, expire)
    _parked(hass)[entry_id] = handover


@callback
def take(hass: HomeAssistant, entry_id: str) -> Handover | None:
    """The parked control of this entry, if still valid; it is no longer parked afterwards."""
    handover = _parked(hass).pop(entry_id, None)
    if handover is None:
        return None
    if handover.cancel is not None:
        handover.cancel()
        handover.cancel = None
    if time.monotonic() - handover.at > HANDOVER_FOR:
        if handover.live:
            hass.async_create_background_task(handover.zero(), "zephyr: hand-over expired, sets to 0 W")
        return None
    return handover
