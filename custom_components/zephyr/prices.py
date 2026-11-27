"""Prices from the Nord Pool integration of Home Assistant itself (not only the HACS one).

ZEPHYR reads the day's prices from the price sensor's ``raw_today`` / ``raw_tomorrow``
attributes, as the Nord Pool custom integration (HACS) gives them. The Nord Pool integration
that ships with Home Assistant has no such attributes; its prices come from the action
``nordpool.get_prices_for_date`` (bare market price per MWh). For a price sensor of that
integration, :class:`CoreNordPool` fetches today and tomorrow and :func:`price_state`
adds them to the sensor's state as ``raw_today`` / ``raw_tomorrow`` (€/kWh), so every reader
keeps working unchanged.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta
from typing import Any, Final

from homeassistant.core import Event, EventStateChangedData, HomeAssistant, State, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import DOMAIN, LOGGER

NORDPOOL: Final = "nordpool"
REFRESH: Final = timedelta(minutes=15)
"""How often a missing day is asked for (tomorrow appears around 13:00)."""
_CACHE: Final = "core_nordpool"


def core_nordpool(hass: HomeAssistant, entity: str | None) -> tuple[str, str] | None:
    """(config entry, area) when ``entity`` is a price sensor of HA's own Nord Pool integration."""
    if not entity:
        return None
    state = hass.states.get(entity)
    if state is not None and "raw_today" in state.attributes:
        return None  # the HACS integration (same domain): it has the prices itself
    reg = er.async_get(hass).async_get(entity)
    if reg is None or reg.platform != NORDPOOL or reg.config_entry_id is None or "-" not in (reg.unique_id or ""):
        return None
    return reg.config_entry_id, reg.unique_id.split("-", 1)[0]


def _days(hass: HomeAssistant, entity: str) -> dict[str, list[dict[str, Any]]] | None:
    cache: dict[str, dict[str, list[dict[str, Any]]]] = hass.data.get(DOMAIN, {}).get(_CACHE, {})
    return cache.get(entity)


def price_state(hass: HomeAssistant, entity: str | None) -> State | None:
    """The price sensor's state, with ``raw_today``/``raw_tomorrow`` added for HA's own Nord Pool."""
    state = hass.states.get(entity) if entity else None
    if state is None or entity is None or "raw_today" in state.attributes:
        return state
    days = _days(hass, entity)
    if not days:
        return state
    today = dt_util.now().date()
    extra = {
        "raw_today": days.get(today.isoformat(), []),
        "raw_tomorrow": days.get((today + timedelta(days=1)).isoformat(), []),
        "unit": "EUR/kWh",
        "price_in_cents": False,
    }
    return State(state.entity_id, state.state, {**state.attributes, **extra}, state.last_changed, state.last_updated)


def raw_from_response(response: Mapping[str, Any] | None, area: str) -> list[dict[str, Any]]:
    """The action's answer (``{area: [{start, end, price}]}``, per MWh) as ``raw_today`` items in €/kWh."""
    out: list[dict[str, Any]] = []
    for item in (response or {}).get(area) or []:
        if not isinstance(item, Mapping) or item.get("price") is None:
            continue
        out.append({"start": item["start"], "end": item["end"], "value": round(float(item["price"]) / 1000, 6)})
    return out


class CoreNordPool:
    """Fetches today and tomorrow from HA's own Nord Pool integration for one price sensor."""

    def __init__(self, hass: HomeAssistant, entity: str | None, on_new: Callable[[], None]) -> None:
        self.hass = hass
        self.entity = entity
        self._on_new = on_new
        self.source: tuple[str, str] | None = None
        self.last_error: str | None = None
        self._asked: datetime | None = None

    async def async_start(self) -> Callable[[], None]:
        self.source = core_nordpool(self.hass, self.entity)
        if self.source is None or self.entity is None:
            return lambda: None
        self.hass.data.setdefault(DOMAIN, {}).setdefault(_CACHE, {}).setdefault(self.entity, {})
        await self.async_fetch()
        unsubs = [
            async_track_time_interval(self.hass, self._on_interval, REFRESH),
            # Nord Pool may load after ZEPHYR: ask again when its sensor comes (or updates).
            async_track_state_change_event(self.hass, [self.entity], self._on_sensor),
        ]

        def stop() -> None:
            for unsub in unsubs:
                unsub()
            self.hass.data.get(DOMAIN, {}).get(_CACHE, {}).pop(self.entity, None)

        return stop

    @callback
    def _on_sensor(self, _event: Event[EventStateChangedData]) -> None:
        days = _days(self.hass, self.entity) if self.entity else None
        today = dt_util.now().date().isoformat()
        now = dt_util.utcnow()
        if days is not None and not days.get(today) and (self._asked is None or now - self._asked >= timedelta(minutes=1)):
            self._asked = now
            self.hass.async_create_task(self.async_fetch(), "zephyr: Nord Pool prices")

    @callback
    def _on_interval(self, _now: datetime) -> None:
        self.hass.async_create_task(self.async_fetch(), "zephyr: Nord Pool prices")

    async def async_fetch(self) -> None:
        """Ask for every day of today and tomorrow that is not known yet."""
        if self.source is None or self.entity is None:
            return
        entry_id, area = self.source
        days = _days(self.hass, self.entity)
        if days is None:
            return
        today = dt_util.now().date()
        new = False
        for day in (today, today + timedelta(days=1)):
            if days.get(day.isoformat()):
                continue
            items = await self._fetch_day(entry_id, area, day)
            if items:
                days[day.isoformat()] = items
                new = True
        for old in [d for d in days if d < (today - timedelta(days=1)).isoformat()]:
            del days[old]
        if new:
            self._on_new()

    async def _fetch_day(self, entry_id: str, area: str, day: date) -> list[dict[str, Any]]:
        try:
            response = await self.hass.services.async_call(
                NORDPOOL,
                "get_prices_for_date",
                {"config_entry": entry_id, "date": day, "areas": [area]},
                blocking=True,
                return_response=True,
            )
        except Exception as err:  # tomorrow is not published yet, or the service is away
            self.last_error = f"{day}: {err}"
            LOGGER.debug("Nord Pool prices for %s: %s", day, err)
            return []
        self.last_error = None
        return raw_from_response(response, area)

    def diagnostics(self) -> dict[str, Any]:
        days = _days(self.hass, self.entity) if self.entity else None
        return {
            "core_nordpool": self.source is not None,
            "area": None if self.source is None else self.source[1],
            "days": {day: len(items) for day, items in (days or {}).items()},
            "last_error": self.last_error,
        }
