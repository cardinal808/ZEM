"""ZEM: Home Assistant integration for Zendure home batteries.

Milestone M2: reading only. ZEM does not write to the sets yet.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, SUBENTRY_SET
from .coordinator import SetCoordinator
from .core.totals import Totals, compute_totals

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


@dataclass(slots=True)
class ZemRuntime:
    """Runtime objects of one ZEM installation."""

    coordinators: dict[str, SetCoordinator] = field(default_factory=dict)

    def totals(self) -> Totals:
        return compute_totals((c.snapshot() for c in self.coordinators.values()), time.monotonic())


type ZemConfigEntry = ConfigEntry[ZemRuntime]


async def async_setup_entry(hass: HomeAssistant, entry: ZemConfigEntry) -> bool:
    """Set up ZEM: one reader per set, then the entities."""
    # The installation device must exist before set devices refer to it.
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="ZEM",
        manufacturer="ZEM",
        model="Installation",
    )
    runtime = ZemRuntime()
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_SET:
            continue
        coordinator = SetCoordinator(hass, entry, subentry)
        await coordinator.async_refresh()  # never raises; an unreachable set starts offline
        runtime.coordinators[subentry.subentry_id] = coordinator
    entry.runtime_data = runtime
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ZemConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: ZemConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
