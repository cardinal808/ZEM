"""ZEPHYR: Home Assistant integration for Zendure home batteries.

Shadow mode by default (ZEPHYR computes what it would do); live control with
``switch.zephyr_control`` (M4b).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, SUBENTRY_SET
from .coordinator import SetCoordinator
from .core.totals import Totals, compute_totals

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.SELECT, Platform.SWITCH]

if TYPE_CHECKING:
    from .control import ZephyrControl
    from .cost_recorder import CostRecorder
    from .pack_recorder import PackRecorder
    from .planner_runner import PlanRunner
    from .solar_recorder import SolarRecorder
    from .tariff_provider import TariffProvider


@dataclass(slots=True)
class ZephyrRuntime:
    """Runtime objects of one ZEPHYR installation."""

    coordinators: dict[str, SetCoordinator] = field(default_factory=dict)
    control: ZephyrControl | None = None
    solar: SolarRecorder | None = None
    costs: CostRecorder | None = None
    tariffs: TariffProvider | None = None
    planner: PlanRunner | None = None
    packs: PackRecorder | None = None
    options: dict[str, Any] = field(default_factory=dict)
    """The options in use; a change of only live fields is applied without a reload (UI-7)."""

    def totals(self) -> Totals:
        return compute_totals((c.snapshot() for c in self.coordinators.values()), time.monotonic())


type ZephyrConfigEntry = ConfigEntry[ZephyrRuntime]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_TEST_COMMAND = "test_command"
TEST_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required("power"): vol.All(vol.Coerce(int), vol.Range(min=-2400, max=2400)),
        vol.Optional("duration", default=60): vol.All(vol.Coerce(float), vol.Range(min=1, max=60)),
    }
)

SERVICE_EXPORT_COSTS = "export_costs"
EXPORT_COSTS_SCHEMA = vol.Schema({vol.Optional("start"): cv.date, vol.Optional("end"): cv.date})

SERVICE_RECALCULATE = "recalculate"
SERVICE_RESET_PROFILE = "reset_profile"
RESET_PROFILE_SCHEMA = vol.Schema({vol.Optional("refill", default=True): cv.boolean})
SERVICE_GET_PLAN = "get_plan"


def _planners(hass: HomeAssistant) -> list[PlanRunner]:
    planners = [
        e.runtime_data.planner
        for e in hass.config_entries.async_loaded_entries(DOMAIN)
        if e.runtime_data.planner is not None and e.runtime_data.planner.enabled
    ]
    if not planners:
        raise ServiceValidationError(translation_domain=DOMAIN, translation_key="no_planner")
    return planners


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Actions of ZEPHYR (registered once, act on the loaded installation)."""

    async def test_command(call: ServiceCall) -> None:
        entries = [e for e in hass.config_entries.async_loaded_entries(DOMAIN) if e.runtime_data.control is not None]
        if not entries:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_loaded")
        for entry in entries:
            control = entry.runtime_data.control
            assert control is not None
            await control.async_test_command(call.data["power"], call.data["duration"])

    hass.services.async_register(DOMAIN, SERVICE_TEST_COMMAND, test_command, schema=TEST_COMMAND_SCHEMA)

    async def export_costs(call: ServiceCall) -> ServiceResponse:
        """All stored quarters of the period as CSV in config/zephyr/ (default: this month)."""
        entries = [e for e in hass.config_entries.async_loaded_entries(DOMAIN) if e.runtime_data.costs is not None]
        if not entries:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="not_loaded")
        costs = entries[0].runtime_data.costs
        assert costs is not None
        end: date = call.data.get("end") or costs.period("today")[1]
        start: date = call.data.get("start") or end.replace(day=1)
        if start > end:
            raise ServiceValidationError(translation_domain=DOMAIN, translation_key="export_period")
        result = await costs.async_export(start, end)
        return {"path": str(result["path"]), "rows": int(result["rows"])}

    hass.services.async_register(
        DOMAIN, SERVICE_EXPORT_COSTS, export_costs, schema=EXPORT_COSTS_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )

    async def recalculate(call: ServiceCall) -> None:
        """Make a new plan now (the panel and automations; otherwise every quarter)."""
        for planner in _planners(hass):
            planner.async_request()

    hass.services.async_register(DOMAIN, SERVICE_RECALCULATE, recalculate)

    async def reset_profile(call: ServiceCall) -> ServiceResponse:
        """Forget the learned consumption (PT9); by default fill it again from the recorder."""
        result: dict[str, Any] = {}
        for planner in _planners(hass):
            result = await planner.async_reset_profile(call.data["refill"])
        return result

    hass.services.async_register(
        DOMAIN, SERVICE_RESET_PROFILE, reset_profile, schema=RESET_PROFILE_SCHEMA, supports_response=SupportsResponse.OPTIONAL
    )

    async def get_plan(call: ServiceCall) -> ServiceResponse:
        """The current plan (blocks, quarters, figures) for automations and templates."""
        response: ServiceResponse = _planners(hass)[0].plan_response()
        return response

    hass.services.async_register(DOMAIN, SERVICE_GET_PLAN, get_plan, supports_response=SupportsResponse.ONLY)
    from .websocket_api import async_setup as async_setup_websocket

    async_setup_websocket(hass)
    return True


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
    runtime = ZephyrRuntime(options=dict(entry.options))
    for subentry in entry.subentries.values():
        if subentry.subentry_type != SUBENTRY_SET:
            continue
        coordinator = SetCoordinator(hass, entry, subentry)
        await coordinator.async_refresh()  # never raises; an unreachable set starts offline
        runtime.coordinators[subentry.subentry_id] = coordinator
    from .control import ZephyrControl

    runtime.control = ZephyrControl(hass, entry, runtime)
    from .cost_recorder import CostRecorder
    from .tariff_provider import TariffProvider

    runtime.tariffs = TariffProvider(hass, entry.entry_id, dict(entry.options))
    runtime.costs = CostRecorder(hass, entry.entry_id, dict(entry.options), runtime, runtime.tariffs)
    from .planner_runner import PlanRunner

    planner = PlanRunner(hass, entry.entry_id, dict(entry.options), runtime)
    runtime.planner = planner if planner.enabled else None
    entry.runtime_data = runtime
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(runtime.control.async_start())
    entry.async_on_unload(await runtime.tariffs.async_start())
    entry.async_on_unload(await runtime.costs.async_start())
    from .pack_recorder import PackRecorder

    runtime.packs = PackRecorder(hass, entry.entry_id, runtime)
    entry.async_on_unload(await runtime.packs.async_start())
    from .solar_recorder import SolarRecorder

    runtime.solar = SolarRecorder(hass, entry.entry_id, dict(entry.options))
    if runtime.solar.enabled:
        entry.async_on_unload(await runtime.solar.async_start())
    if runtime.planner is not None:
        entry.async_on_unload(await runtime.planner.async_start())
    from .panel import async_register_panel

    await async_register_panel(hass, entry.entry_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ZephyrConfigEntry) -> bool:
    from .panel import async_remove_panel

    async_remove_panel(hass, entry.entry_id, final=entry.disabled_by is not None)
    if entry.runtime_data.costs is not None:
        await entry.runtime_data.costs.async_save()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ZephyrConfigEntry) -> None:
    from .panel import async_remove_panel

    async_remove_panel(hass, entry.entry_id, final=True)


async def _async_options_updated(hass: HomeAssistant, entry: ZephyrConfigEntry) -> None:
    """Apply settings live; reload only for sources or anything that is not a known live setting (SPEC-ui §3.4)."""
    from .settings_schema import BY_KEY

    runtime = entry.runtime_data
    new = dict(entry.options)
    changed = {k for k in set(new) | set(runtime.options) if new.get(k) != runtime.options.get(k)}
    if not changed or any(k not in BY_KEY or BY_KEY[k].reload for k in changed):
        # No option changed (a set was added or renamed) or a source changed: start again.
        await hass.config_entries.async_reload(entry.entry_id)
        return
    runtime.options = new
    if runtime.control is not None:
        runtime.control.apply_options(new)
    if runtime.tariffs is not None:
        runtime.tariffs.apply_options(new)
    if runtime.planner is not None:
        runtime.planner.apply_options(new)
