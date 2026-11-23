"""Stores the solar forecast and the real production every day (B31, B32).

* 23:00:30 local time: the forecast for tomorrow (day-ahead), from the
  ``detailedForecast`` attribute of the chosen forecast sensor (Solcast).
* Every full hour: the production counter (kWh), for the production per hour.

Kept in ZEPHYR's own storage (400 days) and shown in the diagnostics.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import CONF_SOLAR_ENERGY, CONF_SOLAR_FORECAST, DOMAIN, LOGGER
from .core.solar_history import SolarHistory, energy_kwh, parse_detailed_forecast

STORAGE_VERSION = 1
FORECAST_AT = (23, 0, 30)


class SolarRecorder:
    def __init__(self, hass: HomeAssistant, entry_id: str, options: dict[str, Any]) -> None:
        self.hass = hass
        self.forecast_entity: str | None = options.get(CONF_SOLAR_FORECAST)
        self.energy_entity: str | None = options.get(CONF_SOLAR_ENERGY)
        self.history = SolarHistory()
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.solar_history")

    @property
    def enabled(self) -> bool:
        return bool(self.forecast_entity or self.energy_entity)

    async def async_start(self) -> Callable[[], None]:
        self.history = SolarHistory.from_dict(await self._store.async_load())
        unsubs: list[Callable[[], None]] = []
        if self.energy_entity:
            unsubs.append(async_track_time_change(self.hass, self._on_hour, minute=0, second=5))
        if self.forecast_entity:
            hour, minute, second = FORECAST_AT
            unsubs.append(async_track_time_change(self.hass, self._on_evening, hour=hour, minute=minute, second=second))

        def stop() -> None:
            for unsub in unsubs:
                unsub()

        return stop

    @callback
    def _on_hour(self, now: datetime) -> None:
        self.record_counter(dt_util.as_local(now))

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
        assert self.forecast_entity is not None
        state = self.hass.states.get(self.forecast_entity)
        if state is None:
            return
        periods = parse_detailed_forecast(state.attributes.get("detailedForecast"))
        day = (local_now.date() + timedelta(days=1)).isoformat()
        # Only the periods of that day: some sources also list the edges of other days.
        periods = [p for p in periods if dt_util.as_local(datetime.fromisoformat(p.start)).date().isoformat() == day]
        if self.history.record_forecast(day, local_now.isoformat(), self.forecast_entity, periods):
            self._store.async_delay_save(self.history.as_dict, 10)
        else:
            LOGGER.debug("No solar forecast for %s in %s", day, self.forecast_entity)

    def diagnostics(self) -> dict[str, Any]:
        recent = sorted(self.history.days)[-3:]
        return {
            "forecast_entity": self.forecast_entity,
            "energy_entity": self.energy_entity,
            "days_stored": len(self.history.days),
            "summary": self.history.summary(60),
            "recent": {day: self.history.days[day] for day in recent},
        }
