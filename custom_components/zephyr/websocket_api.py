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
from homeassistant.components.websocket_api.decorators import async_response, require_admin, websocket_command
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
    from .control import ZephyrControl

THROTTLE_S: Final = 2.0
PLAN_MODES: Final = [Mode.STANDBY, Mode.ZERO_METER, Mode.FAST_CHARGE, Mode.FAST_DISCHARGE]


@callback
def async_setup(hass: HomeAssistant) -> None:
    async_register_command(hass, ws_subscribe)
    async_register_command(hass, ws_plan)
    async_register_command(hass, ws_sets)
    async_register_command(hass, ws_settings_get)
    async_register_command(hass, ws_settings_set)
    async_register_command(hass, ws_events)
    async_register_command(hass, ws_savings)
    async_register_command(hass, ws_plan_check)
    async_register_command(hass, ws_savings_backfill)
    async_register_command(hass, ws_stroom)


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


def _excluded(control: Any) -> dict[str, Any] | None:
    """The air conditioner that may not run on the battery (B41, SPEC-ui-airco §2.1); None when not set up."""
    load = control.excluded
    if load is None:
        return None
    now = time.monotonic()
    diag = load.diagnostics(now)
    since = diag["seconds_since_step"]
    interval = diag["mean_step_interval_s"]
    active = bool(diag["active"])
    if not diag["has_climate"]:
        quality = "no_climate"
    elif active and not diag["last_step_kwh"]:
        quality = "starting"  # running, no counter step since the start: power of the previous run
    elif since is not None and interval and since > 2 * interval:
        quality = "fading"  # the counter is late: the estimate drops
    else:
        quality = "ok"
    return {
        "active": active,
        "power_w": round(load.power(now)),
        "excluded_w": round(control.engine.excluded_now),
        "mode": diag["mode"],
        "action": diag["action"],
        "blocked_modes": diag["blocked_modes"],
        "has_climate": diag["has_climate"],
        "seconds_since_step": since,
        "mean_step_interval_s": interval,
        "last_step_kwh": diag["last_step_kwh"],
        "quality": quality,
    }


def _control_entities(hass: HomeAssistant, entry: ZephyrConfigEntry) -> dict[str, str | None]:
    """Entity ids of the mode select and the live switch: the panel controls ZEPHYR through them (SPEC-ui §3)."""
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    return {
        "mode": registry.async_get_entity_id("select", DOMAIN, f"{entry.entry_id}_mode"),
        "live": registry.async_get_entity_id("switch", DOMAIN, f"{entry.entry_id}_control"),
    }


def _solar_now(control: ZephyrControl, sets_solar: float) -> dict[str, Any]:
    """Solar now: PV on the sets plus inverters the sets do not see (power sensors or the counter's estimate)."""
    external, estimated = control.external_solar()
    return {
        "solar_w": _round(sets_solar + (external or 0.0), 0),
        "solar_sets_w": _round(sets_solar, 0),
        "solar_external_w": _round(external, 0),
        "solar_estimated": bool(estimated and external is not None),
    }


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
        "previous_mode": str(control.previous_mode),
        "entities": _control_entities(hass, entry),
        "live": not control.shadow,
        "blockers": control.live_blockers(),
        "action": None if result is None else str(result.action),
        "reason": None if result is None else {"nl": result.reason.text("nl"), "en": result.reason.text("en")},
        "reason_code": None if result is None else str(result.reason.code),
        "setpoint_w": None if result is None else result.setpoint,
        "grid_w": None if result is None else _round(result.grid_power, 0),
        "battery_w": _round(totals.power, 0),
        **_solar_now(control, totals.solar_power),
        "soc": _round(totals.soc),
        "energy_kwh": _round(totals.energy_kwh, 2),
        "capacity_kwh": _round(totals.capacity_kwh, 2),
        "min_soc": settings.min_soc,
        "max_soc": settings.max_soc,
        "buffer_pct": float(entry.options.get(CONF_PLAN_BUFFER, 0) or 0),
        "sets_online": totals.sets_online,
        "sets_total": totals.sets_configured,
        "price_entity": bool(control.price_entity),
        "excluded": _excluded(control),
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
    from .const import CONF_EXCLUDED_CLIMATE, CONF_EXCLUDED_ENERGY, CONF_P1_ENTITY, CONF_P1_EXPORT, CONF_P1_IMPORT, CONF_PRICE_ENTITY

    if not value:
        return {"state": "unset"}
    ids = value if isinstance(value, list) else [value]
    missing = [e for e in ids if hass.states.get(e) is None]
    if missing:
        return {"state": "missing", "entities": missing}
    runtime = entry.runtime_data
    if key == CONF_EXCLUDED_CLIMATE:
        climate = hass.states.get(value)
        assert climate is not None
        if climate.state in ("unavailable", "unknown"):
            return {"state": "unavailable"}
        return {"state": "ok", "mode": climate.state, "action": climate.attributes.get("hvac_action")}
    if key == CONF_EXCLUDED_ENERGY and runtime.control is not None and runtime.control.excluded is not None:
        diag = runtime.control.excluded.diagnostics(time.monotonic())
        if not diag["mean_step_interval_s"]:
            return {"state": "ok", "no_step": True}
        return {"state": "ok", "step_kwh": diag["last_step_kwh"], "step_interval_s": diag["mean_step_interval_s"]}
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
            if field.group in ("sources", "corrections") and field.kind in ("entity", "entities"):
                item["status"] = _source_status(hass, entry, field.key, value)
            fields.append(item)
        groups.append({"key": group, "fields": fields, "modified": sum(1 for f in fields if f["modified"])})
    return {"groups": groups, "supplier": supplier, "tariffs_source": in_use.get("source"), "vacation": _vacation(hass, entry)}


def _vacation(hass: HomeAssistant, entry: ZephyrConfigEntry) -> dict[str, Any] | None:
    """Vacation now (B42) and the entities the panel switches it with (one path, like automations)."""
    from homeassistant.helpers import entity_registry as er

    vacation = entry.runtime_data.vacation
    if vacation is None:
        return None
    state = vacation.state
    registry = er.async_get(hass)

    def iso(moment: Any) -> str | None:
        return None if moment is None else dt_util.as_local(moment).isoformat()

    return {
        "active": vacation.active(),
        "manual": state.manual,
        "auto": state.auto,
        "until": iso(state.until),
        "started": iso(state.started),
        "entities": {
            "switch": registry.async_get_entity_id("switch", DOMAIN, f"{entry.entry_id}_vacation"),
            "until": registry.async_get_entity_id("datetime", DOMAIN, f"{entry.entry_id}_vacation_until"),
        },
    }


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


@websocket_command(
    {
        vol.Required("type"): "zephyr/settings/set",
        vol.Optional("changes", default={}): {str: vol.Any(None, bool, int, float, str, [str])},
        vol.Optional("reset", default=[]): [str],
    }
)
@require_admin
@async_response
async def ws_settings_set(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]) -> None:
    """Change settings (UI-7). Sources reload ZEPHYR; the rest goes live without a reload."""
    from .const import TARIFF_OWN
    from .settings_schema import apply_changes

    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "ZEPHYR is not loaded")
        return
    provider = entry.runtime_data.tariffs
    suppliers = [TARIFF_OWN]
    if provider is not None and provider.table is not None:
        suppliers += [key for key, _name in provider.table.choices()]
    result = apply_changes(
        entry.options,
        msg["changes"],
        msg["reset"],
        suppliers=suppliers,
        entity_ok=lambda entity_id: hass.states.get(entity_id) is not None,
    )
    if result.errors:
        connection.send_result(msg["id"], {"ok": False, "errors": result.errors})
        return
    if result.changed:
        hass.config_entries.async_update_entry(entry, options=result.options)
    connection.send_result(msg["id"], {"ok": True, "changed": list(result.changed), "reload": result.reload})


def events_view(entry: ZephyrConfigEntry) -> dict[str, Any]:
    """Recent events and today's write counters for the screen Diagnose (SPEC-ui §4.5)."""
    from .core.events import events_from_log

    runtime = entry.runtime_data
    control = runtime.control
    assert control is not None
    now = time.monotonic()
    counts = control.engine.counters(now)
    sets = []
    for key, coordinator in sorted(runtime.coordinators.items(), key=lambda kv: kv[1].number):
        c = counts.get(key, {})
        writer = control.writers.get(key)
        w = writer.stats.snapshot(now) if writer is not None else {}
        sets.append(
            {
                "number": coordinator.number,
                "ram_24h": c.get("ram_24h", 0),
                "flash_24h": c.get("flash_24h", 0),
                "relay_24h": c.get("relay_24h"),
                "failed_24h": w.get("failed_24h", 0),
                "last_error": w.get("last_error"),
            }
        )
    # In shadow mode the engine counts what it would send; nothing reaches the set.
    return {
        "entry_id": entry.entry_id,
        "shadow": control.shadow,
        "events": events_from_log(control.log),
        "sets": sets,
        "profile": _profile(runtime.planner),
    }


def _profile(planner: Any) -> dict[str, Any] | None:
    """The learned use per hour the planner works with (house, and the air conditioner apart; B41)."""
    from .core.load_profile import MIN_COUNT, WEEKEND, WORKDAY

    if planner is None:
        return None
    house, airco = planner.profile, planner.excluded_profile

    def day(kind: str) -> dict[str, Any]:
        return {
            "house": [round(v, 3) for v in house.values[kind]],
            "airco": [round(v, 3) for v in airco.values[kind]] if planner.excluded_entity else [],
            "counts": list(house.counts[kind]),
            "min_count": MIN_COUNT[kind],
        }

    return {
        "source": planner.profile_source,
        "hours": house.mean_count,
        "mean": round(house.mean, 3),
        "workday": day(WORKDAY),
        "weekend": day(WEEKEND),
    }


@websocket_command({vol.Required("type"): "zephyr/events"})
@callback
def ws_events(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]) -> None:
    """The last 100 events from the decision log and the counters of the last 24 hours."""
    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "ZEPHYR is not loaded")
        return
    connection.send_result(msg["id"], events_view(entry))


SAVINGS_DAYS = 30


def _backfill_price(costs: Any) -> str:
    """Price for the backfill: the price sensor only if HA keeps statistics of it (state_class), otherwise EnergyZero."""
    from .core.backfill import PRICE_ENERGYZERO

    state = costs.hass.states.get(costs.price_entity) if costs.price_entity else None
    return costs.price_entity if state is not None and state.attributes.get("state_class") else PRICE_ENERGYZERO


def savings_view(entry: ZephyrConfigEntry) -> dict[str, Any]:
    """What the battery saved: today, this week, month and year, and the last 30 days (cost log, B38)."""
    from datetime import timedelta as _td

    from .core.costs import Summary, summarize

    costs = entry.runtime_data.costs
    assert costs is not None
    today = dt_util.now().date()
    tariffs = costs.tariffs.tariffs_for(today)
    week_start = today - _td(days=today.weekday())

    def period(summary: Summary) -> dict[str, Any]:
        d = summary.as_dict()
        keys = ("cost", "cost_no_battery", "savings_battery", "savings_solar_via_battery", "savings_trade", "charge_kwh", "discharge_kwh")
        gaps = d["incomplete_quarters"] + d["quarters_without_price"]
        return {**{k: d[k] for k in keys}, "days": summary.days, "quarters": d["quarters"], "incomplete_quarters": gaps}

    days: list[dict[str, Any]] = []
    stored = costs.days
    since = min(stored) if stored else None
    for i in range(SAVINGS_DAYS - 1, -1, -1):
        day = today - _td(days=i)
        key = day.isoformat()
        if since is None or key < since:
            continue
        totals = stored.get(key)
        if totals is None:
            days.append({"day": key, "savings_battery": None, "incomplete": True})
            continue
        saved = Summary(days=1, totals=dict(totals)).savings_battery
        gaps = bool(totals.get("incomplete") or totals.get("no_price"))
        # Today is still running; an earlier day with fewer than 92 quarters (the shortest day) misses some.
        short = day != today and totals.get("quarters", 0) < 92
        days.append(
            {
                "day": key,
                "savings_battery": None if saved is None else round(saved, 2),
                "incomplete": gaps or short,
                "hourly": totals.get("source") is not None,
            }
        )
    return {
        "periods": {
            "today": period(costs.summary("today")),
            "week": period(summarize(stored, week_start, today, tariffs)),
            "month": period(costs.summary("month")),
            "year": period(costs.summary("year")),
        },
        "days": days,
        "since": since,
        "measured_since": costs.measured_since,
        "backfilled_days": sum(1 for v in stored.values() if v.get("source") is not None),
        "can_backfill": bool(costs.import_counters and costs.export_counters),
        "defaults": {"solar_entity": costs.solar_entity, "price_entity": _backfill_price(costs)},
        "saldering_until": tariffs.saldering_until.isoformat() if tariffs.saldering_until > today else None,
    }


@websocket_command({vol.Required("type"): "zephyr/savings"})
@callback
def ws_savings(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]) -> None:
    """Screen Besparing (M6 part 2)."""
    entry = _entry(hass)
    if entry is None or entry.runtime_data.costs is None:
        connection.send_error(msg["id"], "not_loaded", "ZEPHYR is not loaded")
        return
    connection.send_result(msg["id"], savings_view(entry))


@websocket_command({vol.Required("type"): "zephyr/plan_check", vol.Optional("days", default=14): vol.All(int, vol.Range(min=1, max=400))})
@callback
def ws_plan_check(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]) -> None:
    """Plan against reality per day: the day-ahead plan next to what was measured (B38)."""
    entry = _entry(hass)
    if entry is None or entry.runtime_data.costs is None:
        connection.send_error(msg["id"], "not_loaded", "ZEPHYR is not loaded")
        return
    connection.send_result(msg["id"], entry.runtime_data.costs.plan_check(msg["days"]))


def stroom_view(entry: ZephyrConfigEntry) -> dict[str, Any]:
    """Screen Stroom: energy per route and airco today (closed quarters), and the zero score."""
    from .core import stroom

    runtime = entry.runtime_data
    start = dt_util.as_utc(dt_util.start_of_local_day())
    records = list(runtime.costs.records_since(start).values()) if runtime.costs is not None else []
    control = runtime.control
    return {
        "today": stroom.routes(records),
        "zero": control.zero.view() if control is not None else None,
        "live": control is not None and not control.shadow,
        "airco_set": control is not None and control.excluded is not None,
    }


@websocket_command({vol.Required("type"): "zephyr/stroom"})
@callback
def ws_stroom(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]) -> None:
    """Energy per route and how well the meter stayed at zero, today (screen Stroom)."""
    entry = _entry(hass)
    if entry is None:
        connection.send_error(msg["id"], "not_loaded", "ZEPHYR is not loaded")
        return
    connection.send_result(msg["id"], stroom_view(entry))


@websocket_command(
    {
        vol.Required("type"): "zephyr/savings/backfill",
        vol.Optional("clear", default=False): bool,
        vol.Optional("first"): str,
        vol.Optional("charge_entity"): str,
        vol.Optional("discharge_entity"): str,
        vol.Optional("solar_entity"): vol.Any(None, str),
        vol.Optional("price_entity"): vol.Any(None, str),
    }
)
@require_admin
@async_response
async def ws_savings_backfill(hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]) -> None:
    """Work out the savings before the cost log from hourly statistics (or remove that again)."""
    from datetime import date as _date

    entry = _entry(hass)
    if entry is None or entry.runtime_data.costs is None:
        connection.send_error(msg["id"], "not_loaded", "ZEPHYR is not loaded")
        return
    costs = entry.runtime_data.costs
    if msg["clear"]:
        connection.send_result(msg["id"], {"ok": True, "removed": await costs.async_clear_backfill()})
        return
    if not (costs.import_counters and costs.export_counters):
        connection.send_result(msg["id"], {"ok": False, "error": "no_counters"})
        return
    try:
        first = _date.fromisoformat(msg.get("first", ""))
    except ValueError:
        connection.send_result(msg["id"], {"ok": False, "error": "bad_date"})
        return
    entities = {k: msg.get(k) for k in ("charge_entity", "discharge_entity", "solar_entity", "price_entity")}
    if not entities["charge_entity"] or not entities["discharge_entity"]:
        connection.send_result(msg["id"], {"ok": False, "error": "no_battery_counters"})
        return
    missing = [e for e in entities.values() if e and e != "energyzero" and hass.states.get(e) is None]
    if missing:
        connection.send_result(msg["id"], {"ok": False, "error": "entity_missing", "entities": missing})
        return
    result = await costs.async_backfill(
        first, entities["charge_entity"], entities["discharge_entity"], entities["solar_entity"], entities["price_entity"]
    )
    connection.send_result(msg["id"], {"ok": True, **result})
