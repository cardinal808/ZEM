"""ZEPHYR: Home Assistant integration for Zendure home batteries.

Milestone M3: reading and shadow mode. ZEPHYR computes what it would do but
does not write to the sets yet.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, SUBENTRY_SET
from .coordinator import SetCoordinator
from .core.totals import Totals, compute_totals

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SELECT]

if TYPE_CHECKING:
    from .control import ZephyrControl
    from .solar_recorder import SolarRecorder


@dataclass(slots=True)
class ZephyrRuntime:
    """Runtime objects of one ZEPHYR installation."""

    coordinators: dict[str, SetCoordinator] = field(default_factory=dict)
    control: ZephyrControl | None = None
    solar: SolarRecorder | None = None

    def totals(self) -> Totals:
        return compute_totals((c.snapshot() for c in self.coordinators.values()), time.monotonic())


type ZephyrConfigEntry = ConfigEntry[ZephyrRuntime]


async def async_setup_entry(hass: HomeAssistant, entry: ZephyrConfigEntry) -> bool:
    """Set up ZEPHYR: one reader per set, then the entities."""
    # The installation device must exist before set devices refer to it.
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="ZEPHYR",
        manufacturer="ZEPHYR",
        model="Installation",
    )
    runtime = ZephyrRuntime()
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_SET:
            continue
        coordinator = SetCoordinator(hass, entry, subentry)
        await coordinator.async_refresh()  # never raises; an unreachable set starts offline
        runtime.coordinators[subentry.subentry_id] = coordinator
    from .control import ZephyrControl

    runtime.control = ZephyrControl(hass, entry, runtime)
    entry.runtime_data = runtime
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(runtime.control.async_start())
    from .solar_recorder import SolarRecorder

    runtime.solar = SolarRecorder(hass, entry.entry_id, dict(entry.options))
    if runtime.solar.enabled:
        entry.async_on_unload(await runtime.solar.async_start())
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ZephyrConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: ZephyrConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
