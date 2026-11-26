"""Websocket commands for the panel (SPEC-ui §3).

UI-1: ``zephyr/subscribe`` sends a snapshot of *now* and then an update at
most every 2 s while something changes. Units are SI and times ISO (UTC); the
panel formats them. Sign convention: battery + = charging, grid + = import.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import datetime, timedelta
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
from .core.device_table import pack_info
from .core.engine import Mode
from .core.forecast_plan import ACTION_KEYS, PlanOutcome, reason
from .core.packs import PackHistory, cell_delta_mv, cell_status, judged
from .core.plan_view import past_action

if TYPE_CHECKING:
    from . import ZephyrConfigEntry

THROTTLE_S: Final = 2.0
PLAN_MODES: Final = [Mode.STANDBY, Mode.ZERO_METER, Mode.FAST_CHARGE, Mode.FAST_DISCHARGE]


@callback
def async_setup(hass: HomeAssistant) -> None:
    async_register_command(hass, ws_subscribe)
    async_register_command(hass, ws_plan)
    async_register_command(hass, ws_sets)
    async_register_command(hass, ws_settings_get)


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


def _activity(entry: ZephyrConfigEntry) -> list[dict[str, Any]]:
    """What the battery did in the last 24 hours, from the cost log, as segments (start, end, action)."""
    costs = entry.runtime_data.costs
    if costs is None:
        return []
    since = dt_util.utcnow() - timedelta(hours=24)
    segments: list[dict[str, Any]] = []
    for start, record in sorted(costs.records_since(since).items()):
        action = past_action(record)
        end = start + timedelta(minutes=15)
        last = segments[-1] if segments else None
        if last is not None and last["action"] == action and last["end"] == end - timedelta(minutes=15):
            last["end"] = end
        else:
            segments.append({"action": action, "start": start, "end": end})
    return [{**s, "start": _iso(s["start"]), "end": _iso(s["end"])} for s in segments]


def sets_view(hass: HomeAssistant, entry: ZephyrConfigEntry) -> dict[str, Any]:
    """Sets with their packs, cell balance and history (SPEC-ui §3.3). No serial numbers (B18)."""
    runtime = entry.runtime_data
    control = runtime.control
    assert control is not None
    counters = control.engine.counters(time.monotonic())
    history = runtime.packs.history if runtime.packs is not None else PackHistory()
    today = dt_util.now().date()
    sets: list[dict[str, Any]] = []
    for key, coordinator in sorted(runtime.coordinators.items(), key=lambda kv: kv[1].number):
        data = coordinator.data
        report = data.report if data is not None else None
        capacity = data.capacity.capacity_kwh if data is not None and data.capacity is not None else None
        packs: list[dict[str, Any]] = []
        names: dict[str, int] = {}
        for index, pack in enumerate(report.packs if report is not None else ()):
            info = pack_info(report.product, pack.pack_type, pack.serial) if report is not None else None
            model = info.name if info is not None else None
            names[model or "?"] = names.get(model or "?", 0) + 1
            delta = cell_delta_mv(pack.cell_voltage_min, pack.cell_voltage_max)
            is_judged = judged(pack.soc, pack.cell_voltage_max, pack.power, info.capacity_kwh if info else None)
            packs.append(
                {
                    "index": index,
                    "model": model,
                    "built_in": bool(model and model.startswith("Built-in")),
                    "number": names[model or "?"],
                    "capacity_kwh": None if info is None else info.capacity_kwh,
                    "soc": pack.soc,
                    "energy_kwh": None if info is None else round(info.capacity_kwh * pack.soc / 100, 2),
                    "power_w": round(pack.power),
                    "temp": pack.max_temperature,
                    "cell_min_v": pack.cell_voltage_min,
                    "cell_max_v": pack.cell_voltage_max,
                    "cell_delta_mv": delta,
                    "cell_judged": is_judged,
                    "cell_status": cell_status(delta, is_judged),
                    "history": history.last_days(pack.serial, today),
                }
            )
        relays = counters.get(key, {}).get("relay_24h")
        sets.append(
            {
                "id": key,
                "number": coordinator.number,
                "model": coordinator.model_name,
                "online": bool(data is not None and data.online),
                "status": None if data is None else str(data.status),
                "soc": None if report is None else report.soc,
                "capacity_kwh": capacity,
                "energy_kwh": None if report is None or capacity is None else round(capacity * report.soc / 100, 2),
                "power_w": None if report is None else round(report.battery_power_ac),
                "solar_w": None if report is None else round(report.solar_power),
                "enclosure_temp": None if report is None else report.enclosure_temperature,
                "limits": None if report is None else {"min": report.min_soc, "max": report.max_soc},
                "last_full": None if report is None else history.sets_full.get(report.serial),
                "relays_24h": relays,
                "packs": packs,
            }
        )
    return {"now": dt_util.utcnow().isoformat(), "sets": sets, "activity_24h": _activity(entry)}


@websocket_command({vol.Required("type"): "zephyr/sets"})
@callback
def ws_sets(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]) -> None:
    """Sets and their batteries for the screen Accu/Sets (SPEC-ui §4.3)."""
    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "ZEPHYR is not loaded")
        return
    connection.send_result(msg["id"], sets_view(hass, entry))


def _source_status(hass: HomeAssistant, entry: ZephyrConfigEntry, key: str, value: Any) -> dict[str, Any] | None:
    """How a source is doing, for the line under it (e.g. "every 1 s", "96 quarter prices")."""
    from .const import CONF_P1_ENTITY, CONF_P1_EXPORT, CONF_P1_IMPORT, CONF_PRICE_ENTITY

    if not value:
        return {"state": "unset"}
    ids = value if isinstance(value, list) else [value]
    missing = [e for e in ids if hass.states.get(e) is None]
    if missing:
        return {"state": "missing", "entities": missing}
    runtime = entry.runtime_data
    if key in (CONF_P1_ENTITY, CONF_P1_IMPORT, CONF_P1_EXPORT) and runtime.control is not None:
        result = runtime.control.result
        interval = None if result is None else result.p1_interval
        return {"state": "ok", "interval_s": None if interval is None else round(interval, 1)}
    if key == CONF_PRICE_ENTITY and runtime.planner is not None:
        return {"state": "ok", "price_slots": runtime.planner.inputs.get("price_slots")}
    return {"state": "ok"}


def settings_view(hass: HomeAssistant, entry: ZephyrConfigEntry) -> dict[str, Any]:
    """Groups, fields, values and source status for the screen Instellingen (SPEC-ui §3.4)."""
    from .const import CONF_TARIFF_SUPPLIER, TARIFF_OWN
    from .settings_schema import FIELDS, GROUPS, is_modified

    options = dict(entry.options)
    runtime = entry.runtime_data
    provider = runtime.tariffs
    supplier = options.get(CONF_TARIFF_SUPPLIER, TARIFF_OWN)
    suppliers = [{"value": TARIFF_OWN, "label": None}]
    in_use: dict[str, Any] = {}
    if provider is not None:
        if provider.table is not None:
            suppliers += [{"value": key, "label": name} for key, name in provider.table.choices()]
        in_use = provider.tariffs_for(dt_util.now().date()).as_dict()
    groups: list[dict[str, Any]] = []
    for group in GROUPS:
        fields = []
        for field in (f for f in FIELDS if f.group == group):
            value = options.get(field.key, field.default)
            item = field.as_dict() | {"value": value, "modified": is_modified(field, options)}
            if field.key == CONF_TARIFF_SUPPLIER:
                item["choices"] = suppliers
            if field.tariff:
                item["active"] = supplier == TARIFF_OWN
                item["in_use"] = in_use.get(field.key.removeprefix("tariff_"))
            if field.group == "sources" and field.kind in ("entity", "entities"):
                item["status"] = _source_status(hass, entry, field.key, value)
            fields.append(item)
        groups.append({"key": group, "fields": fields, "modified": sum(1 for f in fields if f["modified"])})
    return {"groups": groups, "supplier": supplier, "tariffs_source": in_use.get("source")}


@websocket_command({vol.Required("type"): "zephyr/settings/get"})
@callback
def ws_settings_get(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]) -> None:
    """Settings of the installation; everyone may read them, only administrators change them (UI-7)."""
    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "ZEPHYR is not loaded")
        return
    view = settings_view(hass, entry)
    view["can_edit"] = bool(connection.user is not None and connection.user.is_admin)
    connection.send_result(msg["id"], view)
