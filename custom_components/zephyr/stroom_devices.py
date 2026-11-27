"""Consumers in view on the screen *Stroom*: the appliances with a plug (B36) and the airco (B41).

Per consumer: power now and kWh today (``core.devices.DayEnergy`` from the plug's power), and
where it sits in the house picture (floor). The floors are set in the panel
(*Instellingen → Huis in beeld*) and kept in a store with today's energy.
"""

from __future__ import annotations

import os
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
# Items of the house picture: each can get a box and a spot on an own picture.
PICTURE_ITEMS = ("roof", "shed_solar", "battery", "grid", "ev", "home", "attic", "first", "ground", "shed")
PICTURE_MAX_BYTES = 3_000_000
_MAGIC = ((b"\xff\xd8\xff", "image/jpeg"), (b"\x89PNG", "image/png"))


def picture_mime(data: bytes) -> str | None:
    """The image type from its first bytes: JPEG, PNG or WebP, else None."""
    for magic, mime in _MAGIC:
        if data.startswith(magic):
            return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _fraction(value: Any) -> float:
    return min(1.0, max(0.0, float(value)))


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
        # Own picture (Instellingen → Apparaten): the image itself in a file next to the store.
        self.picture_path = hass.config.path(".storage", f"{DOMAIN}.{entry_id}.house_picture")
        self.picture: dict[str, Any] = self._empty_picture()

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
        self.picture = self._clean_picture(stored.get("picture"))
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
        await self._store.async_save(
            {"floors": self.floors, "hidden": sorted(self.hidden), "energy": self.energy.as_dict(), "picture": self.picture}
        )

    # --- own picture --------------------------------------------------------------------

    @staticmethod
    def _empty_picture() -> dict[str, Any]:
        return {"custom": False, "version": 0, "mime": None, "width": 0, "height": 0, "items": {}, "hidden": []}

    def _clean_picture(self, raw: Any) -> dict[str, Any]:
        out = self._empty_picture()
        if not isinstance(raw, dict):
            return out
        out["version"] = int(raw.get("version") or 0)
        out["mime"] = raw.get("mime") if raw.get("mime") in ("image/jpeg", "image/png", "image/webp") else None
        out["width"], out["height"] = int(raw.get("width") or 0), int(raw.get("height") or 0)
        out["custom"] = bool(raw.get("custom")) and out["mime"] is not None
        out["items"] = self._clean_items(raw.get("items"))
        out["hidden"] = [x for x in raw.get("hidden") or [] if x in PICTURE_ITEMS]
        return out

    @staticmethod
    def _clean_items(raw: Any) -> dict[str, dict[str, list[float]]]:
        items: dict[str, dict[str, list[float]]] = {}
        for key, value in (raw or {}).items():
            if key not in PICTURE_ITEMS or not isinstance(value, dict):
                continue
            try:
                items[key] = {part: [_fraction(value[part][0]), _fraction(value[part][1])] for part in ("box", "point") if part in value}
            except (TypeError, ValueError, IndexError, KeyError):
                continue
        return items

    def picture_view(self) -> dict[str, Any]:
        """The own picture for the panel; ``has_image`` says whether one was uploaded."""
        p = self.picture
        return {
            "custom": p["custom"],
            "has_image": p["mime"] is not None,
            "version": p["version"],
            "width": p["width"],
            "height": p["height"],
            "items": p["items"],
            "hidden": p["hidden"],
        }

    async def async_set_picture_image(self, data: bytes, width: int, height: int) -> None:
        """Store an uploaded picture (already scaled down in the panel) and switch to it."""
        mime = picture_mime(data)
        if mime is None:
            raise ValueError("not_an_image")
        if len(data) > PICTURE_MAX_BYTES:
            raise ValueError("too_large")
        await self.hass.async_add_executor_job(self._write_picture, data)
        self.picture.update(custom=True, version=self.picture["version"] + 1, mime=mime, width=max(1, width), height=max(1, height))
        await self._save()

    def _write_picture(self, data: bytes) -> None:
        os.makedirs(os.path.dirname(self.picture_path), exist_ok=True)
        tmp = f"{self.picture_path}.tmp"
        with open(tmp, "wb") as handle:
            handle.write(data)
        os.replace(tmp, self.picture_path)

    async def async_set_picture(self, custom: bool, items: dict[str, Any], hidden: list[str]) -> None:
        """Own picture on or off, and where each item's box and spot are (fractions of the picture)."""
        self.picture["custom"] = custom and self.picture["mime"] is not None
        self.picture["items"] = self._clean_items(items)
        self.picture["hidden"] = [x for x in hidden if x in PICTURE_ITEMS]
        await self._save()

    async def async_clear_picture(self) -> None:
        """Remove the own picture; the default house returns."""
        await self.hass.async_add_executor_job(self._remove_picture)
        self.picture = {**self._empty_picture(), "version": self.picture["version"] + 1}
        await self._save()

    def _remove_picture(self) -> None:
        if os.path.exists(self.picture_path):
            os.remove(self.picture_path)

    async def async_read_picture(self) -> tuple[bytes, str] | None:
        """The stored picture and its type, or None."""
        mime = self.picture["mime"]
        if mime is None:
            return None

        def read() -> bytes | None:
            if not os.path.exists(self.picture_path):
                return None
            with open(self.picture_path, "rb") as handle:
                return handle.read()

        data = await self.hass.async_add_executor_job(read)
        return None if data is None else (data, mime)

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
