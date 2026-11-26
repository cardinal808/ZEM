"""Websocket commands for the panel (SPEC-ui §3).

UI-1: ``zephyr/subscribe`` sends a snapshot of *now* and then an update at
most every 2 s while something changes. Units are SI and times ISO (UTC); the
panel formats them. Sign convention: battery + = charging, grid + = import.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any, Final

import voluptuous as vol
from homeassistant.components.websocket_api import async_register_command
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.components.websocket_api.decorators import websocket_command
from homeassistant.components.websocket_api.messages import event_message
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.util import dt as dt_util

from .const import CONF_PLAN_BUFFER, DOMAIN
from .core.engine import Mode
from .core.forecast_plan import ACTION_KEYS, PlanOutcome, reason

if TYPE_CHECKING:
    from . import ZephyrConfigEntry

THROTTLE_S: Final = 2.0
PLAN_MODES: Final = [Mode.STANDBY, Mode.ZERO_METER, Mode.FAST_CHARGE, Mode.FAST_DISCHARGE]


@callback
def async_setup(hass: HomeAssistant) -> None:
    async_register_command(hass, ws_subscribe)
    async_register_command(hass, ws_plan)


def _entry(hass: HomeAssistant) -> ZephyrConfigEntry | None:
    entries = [e for e in hass.config_entries.async_loaded_entries(DOMAIN) if e.runtime_data.control is not None]
    return entries[0] if entries else None


def _iso(moment: datetime | None) -> str | None:
    return None if moment is None else dt_util.as_utc(moment).isoformat()


def _round(value: float | None, digits: int = 1) -> float | None:
    return None if value is None else round(value, digits)


def _plan(hass: HomeAssistant, outcome: PlanOutcome) -> dict[str, Any]:
    tz = dt_util.get_default_time_zone()
    data: dict[str, Any] = {
        "state": str(outcome.state),
        "action": ACTION_KEYS[outcome.action],
        "reason": {"nl": reason(outcome, "nl", tz), "en": reason(outcome, "en", tz)},
        "calculated_at": _iso(outcome.calculated_at),
        "no_prices_since": _iso(outcome.no_prices_since),
        "price_now": None,
        "next": None,
    }
    if outcome.slots:
        first = outcome.slots[0]
        data["price_now"] = {"import": round(first.buy, 4), "export": round(first.sell, 4)}
        nxt = next((b for b in outcome.blocks if b.start > first.start), None)
        if nxt is not None:
            data["next"] = {
                "action": ACTION_KEYS[nxt.action],
                "start": _iso(nxt.start),
                "end": _iso(nxt.end),
                "kwh": round(nxt.kwh, 2),
                "price": round(nxt.price, 4),
                "indicative": nxt.indicative,
            }
    return data


def now_snapshot(hass: HomeAssistant, entry: ZephyrConfigEntry) -> dict[str, Any]:
    """Everything the cards *Nu*, *Accu* and *Volgende stap* need."""
    runtime = entry.runtime_data
    control = runtime.control
    assert control is not None
    totals = runtime.totals()
    result = control.result
    settings = control.engine.settings
    modes = [*PLAN_MODES, Mode.FORECAST] if runtime.planner is not None else list(PLAN_MODES)
    outcome = runtime.planner.outcome if runtime.planner is not None else None
    return {
        "updated_at": dt_util.utcnow().isoformat(),
        "mode": str(control.engine.mode),
        "modes": [str(m) for m in modes],
        "live": not control.shadow,
        "blockers": control.live_blockers(),
        "action": None if result is None else str(result.action),
        "reason": None if result is None else {"nl": result.reason.text("nl"), "en": result.reason.text("en")},
        "reason_code": None if result is None else str(result.reason.code),
        "setpoint_w": None if result is None else result.setpoint,
        "grid_w": None if result is None else _round(result.grid_power, 0),
        "battery_w": _round(totals.power, 0),
        "solar_w": _round(totals.solar_power, 0),
        "soc": _round(totals.soc),
        "energy_kwh": _round(totals.energy_kwh, 2),
        "capacity_kwh": _round(totals.capacity_kwh, 2),
        "min_soc": settings.min_soc,
        "max_soc": settings.max_soc,
        "buffer_pct": float(entry.options.get(CONF_PLAN_BUFFER, 0) or 0),
        "sets_online": totals.sets_online,
        "sets_total": totals.sets_configured,
        "price_entity": bool(control.price_entity),
        "plan": None if outcome is None else _plan(hass, outcome),
    }


@websocket_command({vol.Required("type"): "zephyr/subscribe"})
@callback
def ws_subscribe(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]) -> None:
    """Snapshot of now, then updates (at most every 2 s) until unsubscribed or the installation unloads."""
    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "ZEPHYR is not loaded")
        return
    msg_id: int = msg["id"]
    runtime = entry.runtime_data
    unsubs: list[Callable[[], None]] = []
    state: dict[str, Any] = {"last": 0.0, "timer": None, "open": True}

    @callback
    def send() -> None:
        state["timer"] = None
        if not state["open"]:
            return
        state["last"] = time.monotonic()
        connection.send_message(event_message(msg_id, {"type": "now", "data": now_snapshot(hass, entry)}))

    @callback
    def changed() -> None:
        if not state["open"] or state["timer"] is not None:
            return
        wait = THROTTLE_S - (time.monotonic() - state["last"])
        if wait <= 0:
            send()
            return

        @callback
        def later(_now: datetime) -> None:
            send()

        state["timer"] = async_call_later(hass, wait, later)

    @callback
    def close() -> None:
        state["open"] = False
        timer: CALLBACK_TYPE | None = state["timer"]
        if timer is not None:
            timer()
        for unsub in unsubs:
            unsub()
        unsubs.clear()

    @callback
    def unloaded() -> None:
        # Reload or removal: tell the panel, which subscribes again.
        if state["open"] and msg_id in connection.subscriptions:
            connection.send_message(event_message(msg_id, {"type": "unloaded"}))
        close()

    assert runtime.control is not None
    unsubs.append(runtime.control.async_add_listener(changed))
    if runtime.planner is not None:
        unsubs.append(runtime.planner.async_add_listener(changed))
    for coordinator in runtime.coordinators.values():
        unsubs.append(coordinator.async_add_listener(changed))
    entry.async_on_unload(unloaded)

    connection.subscriptions[msg_id] = close
    connection.send_result(msg_id)
    send()


@websocket_command({vol.Required("type"): "zephyr/plan"})
@callback
def ws_plan(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]) -> None:
    """Prices and plan per quarter, today 00:00 to the end of tomorrow (SPEC-ui §3.2)."""
    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "ZEPHYR is not loaded")
        return
    planner = entry.runtime_data.planner
    if planner is None:
        connection.send_error(msg["id"], "no_price_source", "No price sensor chosen in the options")
        return
    connection.send_result(msg["id"], planner.view())
