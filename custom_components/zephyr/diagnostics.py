"""Diagnostics download: state of every set, with serial numbers and IP addresses hidden."""

from __future__ import annotations

import dataclasses
import time
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import ZephyrConfigEntry
from .const import CONF_HOST, CONF_SERIAL
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
            "p1_filter": {"step_holds": control.engine.grid_filter.holds},
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
            "decisions": list(control.log)[-200:],
        }
    solar = runtime.solar.diagnostics() if runtime.solar is not None and runtime.solar.enabled else None
    costs = runtime.costs.diagnostics() if runtime.costs is not None else None
    planner = runtime.planner.diagnostics() if runtime.planner is not None else None
    return {
        "totals": dataclasses.asdict(runtime.totals()),
        "sets": sets,
        "control": control_info,
        "solar": solar,
        "costs": costs,
        "planner": planner,
    }
