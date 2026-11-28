"""Diagnostics download: state of every set, with serial numbers and IP addresses hidden."""

from __future__ import annotations

import dataclasses
import time
from collections.abc import Sequence
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import ZephyrConfigEntry
from .const import CONF_COST_IMPORT_COUNTERS, CONF_HOST, CONF_SERIAL
from .coordinator import unknown_pack_details

TO_REDACT = {"sn", CONF_SERIAL, CONF_HOST, "serial"}


def _redact_report(raw: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = async_redact_data(raw, TO_REDACT)
    packs = report.get("packData")
    if isinstance(packs, list):
        # Keep the first letter of pack serials: it identifies the pack type.
        report["packData"] = [
            {**async_redact_data(p, TO_REDACT), "sn_prefix": str(p.get("sn", ""))[:1]}
            for p in raw.get("packData", [])
            if isinstance(p, dict)
        ]
    return report


def _dsmr_version(hass: HomeAssistant, control: Any, counters: Sequence[str] = ()) -> str | None:
    """The DSMR version of the smart meter, if a meter reader reports it (diagnostics).

    Looked for on the device of the P1 sensor, then on the device of the meter counters for the
    cost log (a P1 power sensor may be a template, the counters are the reader's own), and last
    as the one sensor whose id ends in ``dsmr_version`` (none or several: unknown).
    """
    registry = er.async_get(hass)
    sources = [control.p1_entity, *(control.p1_pair or ()), *counters]
    seen: set[str] = set()
    for entity in sources:
        reg = registry.async_get(entity) if entity else None
        if reg is None or reg.device_id is None or reg.device_id in seen:
            continue
        seen.add(reg.device_id)
        for other in er.async_entries_for_device(registry, reg.device_id):
            if "dsmr_version" in other.entity_id or "dsmr_version" in (other.unique_id or ""):
                state = hass.states.get(other.entity_id)
                return None if state is None else state.state
    named = [st for st in hass.states.async_all("sensor") if st.entity_id.endswith("dsmr_version")]
    return named[0].state if len(named) == 1 else None


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ZephyrConfigEntry) -> dict[str, Any]:
    runtime = entry.runtime_data
    sets: list[dict[str, Any]] = []
    for coordinator in runtime.coordinators.values():
        data = coordinator.data
        health = coordinator.health
        sets.append(
            {
                "number": coordinator.number,
                "product": coordinator.product,
                "config": async_redact_data(dict(entry.subentries[coordinator.subentry_id].data), TO_REDACT),
                "online": data.online if data else False,
                "status": data.status.value if data else None,
                "health": {
                    "consecutive_failures": health.consecutive_failures,
                    "offline_episodes": health.episodes_offline,
                    "last_error": health.last_error,
                },
                "capacity": {
                    "capacity_kwh": data.capacity.capacity_kwh,
                    "unknown_pack_count": len(data.capacity.unknown_packs),
                    "unknown_packs": unknown_pack_details(data.report, data.capacity) if data.report else [],
                }
                if data and data.capacity
                else None,
                "report": _redact_report(dict(data.raw)) if data and data.raw else None,
            }
        )
    control = runtime.control
    control_info: dict[str, Any] | None = None
    if control is not None:
        result = control.result
        control_info = {
            "shadow": control.shadow,
            "live": {
                "since_s": None if control.live_since is None else round(time.monotonic() - control.live_since),
                "blockers": control.live_blockers() if control.shadow else [],
                "writes": {
                    str(control.runtime.coordinators[key].number): w.stats.snapshot(time.monotonic()) for key, w in control.writers.items()
                },
                "test": control.test,
                "wanted": control.wanted_live,
                "history": list(control.live_history),
            },
            "price": None
            if control.price_entity is None
            else {
                "entity": control.price_entity,
                "expensive_hours": control.expensive_hours,
                "reserve_soc": control.reserve_soc,
                "min_price": control.min_price,
                "decision": None if control.price is None else control.price.as_dict(),
            },
            "p1_entity": control.p1_description,
            "mode": control.engine.mode.value,
            "settings": dataclasses.asdict(control.engine.settings),
            "last": {
                "setpoint": result.setpoint,
                "action": result.action.value,
                "reason": result.reason.code.value,
                "p1_ok": result.p1_ok,
                "p1_interval": result.p1_interval,
            }
            if result
            else None,
            "p1_profile": control.engine.p1_profile_view(time.monotonic())
            | {
                "timestamps": "last_reported",
                "dsmr_version": _dsmr_version(hass, control, list(entry.options.get(CONF_COST_IMPORT_COUNTERS, []))),
            },
            "p1_filter": {
                "step_holds": control.engine.grid_filter.holds,
                "peak_kwh": round(control.engine.peak_kwh, 4),
                "days": control.peak_days,
            },
            "twin": control.engine.twin_summary(),
            "excluded_load": None
            if control.excluded is None
            else {
                "energy_entity_set": True,
                "climate_entity_set": control.excluded_climate is not None,
                **control.excluded.diagnostics(time.monotonic()),
                "excluded_now_w": round(control.engine.excluded_now),
            },
            "counters": {
                runtime.coordinators[key].number: counts
                for key, counts in control.engine.counters(time.monotonic()).items()
                if key in runtime.coordinators
            },
            "decisions": list(control.log),
            "log": {"since": control.log_file.since, "lines": len(control.log), "from_before_start": control.log_file.restored},
        }
    solar = runtime.solar.diagnostics() if runtime.solar is not None and runtime.solar.enabled else None
    costs = runtime.costs.diagnostics() if runtime.costs is not None else None
    planner = runtime.planner.diagnostics() if runtime.planner is not None else None
    from .foreign import foreign_entities

    return {
        "options": async_redact_data(dict(entry.options), TO_REDACT),
        "foreign_entities": foreign_entities(hass, entry.options),
        "prices": runtime.prices.diagnostics() if runtime.prices is not None else None,
        "totals": dataclasses.asdict(runtime.totals()),
        "sets": sets,
        "control": control_info,
        "solar": solar,
        "costs": costs,
        "energy_counters": runtime.energy.diagnostics() if runtime.energy is not None else None,
        "curtail": runtime.curtail.diagnostics() if runtime.curtail is not None else None,
        "appliances": runtime.appliances.diagnostics() if runtime.appliances is not None else None,
        "planner": planner,
    }
