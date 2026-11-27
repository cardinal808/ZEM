"""Consumers in view on the screen *Stroom*: the appliances with a plug (B36) and the airco (B41).

Per consumer: power now and kWh today (``core.devices.DayEnergy`` from the plug's power), and
where it sits in the house picture (floor). The floors are set in the panel
(*Instellingen → Huis in beeld*) and kept in a store with today's energy.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .core.devices import FLOORS, DayEnergy
from .core.solar_now import watts

if TYPE_CHECKING:
    from . import ZephyrRuntime

STORAGE_VERSION = 1
AIRCO = "airco"
DEFAULT_FLOOR = {"washer": "attic", "dryer_heat_pump": "attic", "dryer_condenser": "attic", "dishwasher": "ground", AIRCO: "ground"}


class StroomDevices:
    """Power now and kWh today per consumer in view, and their floors."""

    def __init__(self, hass: HomeAssistant, entry_id: str, runtime: ZephyrRuntime) -> None:
        self.hass = hass
        self.runtime = runtime
        self.energy = DayEnergy()
        self.floors: dict[str, str] = {}
        self.hidden: set[str] = set()
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.house")

    # --- which consumers --------------------------------------------------------------

    def plugs(self) -> list[tuple[str, str, str, str]]:
        """(id, name, kind, power entity) of the appliances with a plug."""
        manager = self.runtime.appliances
        if manager is None:
            return []
        return [(a.id, a.name, a.kind, a.power_entity) for a in manager.appliances.values() if a.power_entity]

    def has_airco(self) -> bool:
        control = self.runtime.control
        return control is not None and control.excluded is not None

    def floor_of(self, device_id: str, kind: str) -> str:
        return self.floors.get(device_id) or DEFAULT_FLOOR.get(kind, "ground")

    # --- start, store -----------------------------------------------------------------

    async def async_start(self) -> Callable[[], None]:
        stored = await self._store.async_load() or {}
        self.floors = {str(k): str(v) for k, v in (stored.get("floors") or {}).items() if v in FLOORS}
        self.hidden = {str(x) for x in stored.get("hidden") or []}
        self.energy.restore(stored.get("energy"), dt_util.now().date())
        unsubs: list[Callable[[], None]] = []
        entities = [p[3] for p in self.plugs()]
        if entities:
            unsubs.append(async_track_state_change_event(self.hass, entities, self._on_plug))
            for device_id, _name, _kind, entity in self.plugs():
                self._observe(device_id, self.hass.states.get(entity))
        unsubs.append(async_track_time_interval(self.hass, self._save, timedelta(minutes=5)))

        def stop() -> None:
            for unsub in unsubs:
                unsub()
            self.hass.async_create_task(self._save(), "zephyr: save the house view")

        return stop

    async def _save(self, _now: Any = None) -> None:
        await self._store.async_save({"floors": self.floors, "hidden": sorted(self.hidden), "energy": self.energy.as_dict()})

    async def async_set_layout(self, floors: dict[str, str], hidden: list[str]) -> None:
        self.floors = {str(k): v for k, v in floors.items() if v in FLOORS}
        self.hidden = {str(x) for x in hidden}
        await self._save()

    @callback
    def _on_plug(self, event: Event[EventStateChangedData]) -> None:
        entity = event.data["entity_id"]
        for device_id, _name, _kind, power_entity in self.plugs():
            if power_entity == entity:
                self._observe(device_id, event.data["new_state"])

    def _observe(self, device_id: str, state: State | None) -> None:
        now = dt_util.now()
        value = None
        if state is not None and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            value = watts(state.state, state.attributes.get("unit_of_measurement"))
        self.energy.observe(device_id, value, time.time(), now.date(), dt_util.start_of_local_day().timestamp())

    # --- view -------------------------------------------------------------------------

    def view(self, airco_today_kwh: float | None) -> list[dict[str, Any]]:
        """Consumers for the panel, plugs first, then the airco (its kWh from the cost log)."""
        now = dt_util.now()
        epoch, midnight = time.time(), dt_util.start_of_local_day().timestamp()
        out: list[dict[str, Any]] = []
        for device_id, name, kind, _entity in self.plugs():
            power = self.energy.power(device_id, epoch)
            out.append(
                {
                    "id": device_id,
                    "name": name,
                    "kind": kind,
                    "floor": self.floor_of(device_id, kind),
                    "shown": device_id not in self.hidden,
                    "power_w": None if power is None else round(power),
                    "today_kwh": round(self.energy.today(device_id, epoch, now.date(), midnight), 3),
                }
            )
        control = self.runtime.control
        if control is not None and control.excluded is not None:
            out.append(
                {
                    "id": AIRCO,
                    "name": None,
                    "kind": AIRCO,
                    "floor": self.floor_of(AIRCO, AIRCO),
                    "shown": AIRCO not in self.hidden,
                    "power_w": round(control.excluded.power(time.monotonic())),
                    "today_kwh": None if airco_today_kwh is None else round(airco_today_kwh, 3),
                }
            )
        return out
