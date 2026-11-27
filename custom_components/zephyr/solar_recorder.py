"""Stores the solar forecast and the real production every day (B31, B32).

* 23:00:30 local time: the forecast for tomorrow (day-ahead), from the
  ``detailedForecast`` attribute of the chosen forecast sensor (Solcast), or without one
  from the solar forecast of Home Assistant's Energy dashboard.
* Every full hour: the production counter (kWh), for the production per hour.

Kept in ZEPHYR's own storage (400 days) and shown in the diagnostics.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import CONF_SOLAR_ENERGY, CONF_SOLAR_FORECAST, DOMAIN, LOGGER
from .core.solar_history import ForecastPeriod, SolarHistory, energy_kwh, parse_detailed_forecast, periods_from_wh_hours

STORAGE_VERSION = 1
FORECAST_AT = (23, 0, 30)


ENERGY_REFRESH = timedelta(minutes=30)
"""How often the forecast of the Energy dashboard is read again (the sources update hourly or less)."""


def solar_entities(entity: str | None) -> list[str]:
    """The chosen forecast sensor and its Solcast sibling (today ↔ tomorrow), so the horizon has both days."""
    if not entity:
        return []
    out = [entity]
    for a, b in (("forecast_tomorrow", "forecast_today"), ("forecast_today", "forecast_tomorrow")):
        if entity.endswith(a):
            out.append(entity[: -len(a)] + b)
    return out


class SolarRecorder:
    """Solar history (forecast against production) and the forecast for the planner.

    The forecast comes from the chosen sensor (Solcast, with half-hour detail and the 10/90 %
    bounds), or, without one, from the solar forecast in Home Assistant's Energy dashboard
    (Forecast.Solar, Solcast, Open-Meteo and every other integration that provides one).
    """

    def __init__(self, hass: HomeAssistant, entry_id: str, options: dict[str, Any]) -> None:
        self.hass = hass
        self.forecast_entity: str | None = options.get(CONF_SOLAR_FORECAST)
        self.energy_entity: str | None = options.get(CONF_SOLAR_ENERGY)
        self.history = SolarHistory()
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.solar_history")
        self._energy_periods: list[ForecastPeriod] = []
        self.energy_sources: list[str] = []
        """Integrations whose forecast is used from the Energy dashboard (domains)."""

    @property
    def enabled(self) -> bool:
        return True  # the Energy dashboard may have a forecast even without any setting

    @property
    def source(self) -> str | None:
        """Where the forecast comes from: the sensor, ``energy:<domains>`` or nothing."""
        if self.forecast_entity:
            return self.forecast_entity
        return f"energy:{','.join(self.energy_sources)}" if self._energy_periods else None

    def forecast_periods(self) -> list[ForecastPeriod]:
        if self.forecast_entity:
            periods: list[ForecastPeriod] = []
            for entity in solar_entities(self.forecast_entity):
                state = self.hass.states.get(entity)
                if state is not None:
                    periods += parse_detailed_forecast(state.attributes.get("detailedForecast"))
            return periods
        return list(self._energy_periods)

    async def async_refresh_energy(self, _now: datetime | None = None) -> None:
        """Read the solar forecast of the Energy dashboard (sum over its forecast integrations)."""
        try:
            from homeassistant.components.energy.data import async_get_manager
            from homeassistant.components.energy.websocket_api import async_get_energy_platforms
        except ImportError:  # pragma: no cover - energy not available
            return
        if "energy" not in self.hass.config.components:
            return
        manager = await async_get_manager(self.hass)
        prefs: Mapping[str, Any] = cast(Mapping[str, Any], manager.data or {})
        entries: list[str] = [
            entry_id
            for source in prefs.get("energy_sources", [])
            if source.get("type") == "solar"
            for entry_id in source.get("config_entry_solar_forecast") or []
        ]
        platforms = await async_get_energy_platforms(self.hass)
        total: dict[str, float] = {}
        domains: list[str] = []
        for entry_id in dict.fromkeys(entries):
            entry = self.hass.config_entries.async_get_entry(entry_id)
            if entry is None or entry.domain not in platforms:
                continue
            try:
                forecast = await platforms[entry.domain](self.hass, entry_id)
            except Exception as err:  # one broken source must not stop the others
                LOGGER.debug("Solar forecast of %s failed: %s", entry.domain, err)
                continue
            wh_hours: Mapping[str, Any] = cast(Mapping[str, Any], forecast or {}).get("wh_hours") or {}
            for start, wh in wh_hours.items():
                key = datetime.fromisoformat(start).astimezone(UTC).isoformat()
                total[key] = total.get(key, 0.0) + float(wh or 0.0)
            if entry.domain not in domains:
                domains.append(entry.domain)
        self._energy_periods = periods_from_wh_hours(total)
        self.energy_sources = domains

    async def async_start(self) -> Callable[[], None]:
        self.history = SolarHistory.from_dict(await self._store.async_load())
        unsubs: list[Callable[[], None]] = []
        if self.energy_entity:
            unsubs.append(async_track_time_change(self.hass, self._on_hour, minute=0, second=5))
        hour, minute, second = FORECAST_AT
        unsubs.append(async_track_time_change(self.hass, self._on_evening, hour=hour, minute=minute, second=second))
        if not self.forecast_entity:
            try:
                await self.async_refresh_energy()
            except Exception:  # the forecast is a nice-to-have at start
                LOGGER.exception("Solar forecast from the Energy dashboard failed")
            unsubs.append(async_track_time_interval(self.hass, self._on_refresh, ENERGY_REFRESH))

        def stop() -> None:
            for unsub in unsubs:
                unsub()

        return stop

    @callback
    def _on_hour(self, now: datetime) -> None:
        self.record_counter(dt_util.as_local(now))

    @callback
    def _on_refresh(self, now: datetime) -> None:
        self.hass.async_create_task(self.async_refresh_energy(now), "zephyr: solar forecast from the Energy dashboard")

    @callback
    def _on_evening(self, now: datetime) -> None:
        self.record_forecast(dt_util.as_local(now))

    def record_counter(self, local_now: datetime) -> None:
        assert self.energy_entity is not None
        state = self.hass.states.get(self.energy_entity)
        if state is None:
            return
        try:
            kwh = energy_kwh(float(state.state), state.attributes.get("unit_of_measurement"))
        except ValueError:
            return
        if kwh is None:
            return
        self.history.record_counter(local_now.date().isoformat(), local_now.hour, kwh)
        self._store.async_delay_save(self.history.as_dict, 10)

    def record_forecast(self, local_now: datetime) -> None:
        periods = self.forecast_periods()
        source = self.source
        if not periods or source is None:
            return
        day = (local_now.date() + timedelta(days=1)).isoformat()
        # Only the periods of that day: some sources also list the edges of other days.
        periods = [p for p in periods if dt_util.as_local(datetime.fromisoformat(p.start)).date().isoformat() == day]
        if self.history.record_forecast(day, local_now.isoformat(), source, periods):
            self._store.async_delay_save(self.history.as_dict, 10)
        else:
            LOGGER.debug("No solar forecast for %s in %s", day, source)

    def diagnostics(self) -> dict[str, Any]:
        recent = sorted(self.history.days)[-3:]
        return {
            "forecast_entity": self.forecast_entity,
            "forecast_source": self.source,
            "energy_sources": self.energy_sources,
            "energy_entity": self.energy_entity,
            "days_stored": len(self.history.days),
            "summary": self.history.summary(60),
            "recent": {day: self.history.days[day] for day in recent},
        }
