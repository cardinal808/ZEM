"""Own energy counters per set in Home Assistant (SPEC-tellers, T1).

Listens to every read of every set, feeds ``core.energy_counters`` and keeps the counter
states in a store (``zephyr.<entry>.counters``), saved at most every 5 minutes and on unload.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .core.device_table import pack_info
from .core.energy_counters import EnergyCounters
from .core.models import SetReport

if TYPE_CHECKING:
    from . import ZephyrRuntime
    from .coordinator import SetCoordinator

STORAGE_VERSION = 1
SAVE_EVERY = timedelta(minutes=5)


def capacities(report: SetReport) -> dict[str, float]:
    """Capacity per pack (kWh) by serial number, for the packs ZEPHYR knows."""
    out: dict[str, float] = {}
    for pack in report.packs:
        info = pack_info(report.product, pack.pack_type, pack.serial)
        if info is not None:
            out[pack.serial] = info.capacity_kwh
    return out


class EnergyRecorder:
    """The counters of all sets of one ZEPHYR entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str, runtime: ZephyrRuntime) -> None:
        self.hass = hass
        self.runtime = runtime
        self.counters = EnergyCounters()
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.counters")
        self._seen: dict[str, float | None] = {}
        self._listeners: list[Callable[[], None]] = []

    async def async_start(self) -> Callable[[], None]:
        self.counters.restore(await self._store.async_load())
        unsubs: list[Callable[[], None]] = []
        for coordinator in self.runtime.coordinators.values():
            unsubs.append(coordinator.async_add_listener(self._updated(coordinator)))
        unsubs.append(async_track_time_interval(self.hass, lambda _now: self._save(), SAVE_EVERY))

        def stop() -> None:
            for unsub in unsubs:
                unsub()
            self.hass.async_create_task(self._store.async_save(self.counters.as_dict()))

        return stop

    def _save(self) -> None:
        self._store.async_delay_save(self.counters.as_dict, 1)

    def _updated(self, coordinator: SetCoordinator) -> Callable[[], None]:
        @callback
        def handle() -> None:
            self.observe(coordinator)

        return handle

    def observe(self, coordinator: SetCoordinator) -> None:
        """One read of a set finished: a new ``last_success`` means a good report."""
        data = coordinator.data
        report = data.report if data is not None else None
        last = coordinator.health.last_success
        good = report is not None and last is not None and last != self._seen.get(coordinator.serial)
        self._seen[coordinator.serial] = last
        now = time.monotonic()
        self.counters.observe(
            coordinator.serial,
            report if good else None,
            last if good and last is not None else now,
            good=good,
            wall=dt_util.utcnow().isoformat(timespec="seconds"),
            capacities=capacities(report) if good and report is not None else None,
        )
        for listener in list(self._listeners):
            listener()

    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)

        def remove() -> None:
            self._listeners.remove(listener)

        return remove

    def set_kwh(self, serial: str, key: str) -> float | None:
        counter = self.counters.sets.get(serial)
        return None if counter is None else counter.kwh[key]

    def diagnostics(self) -> dict[str, Any]:
        out = self.counters.diagnostics()
        numbers = {c.serial: c.number for c in self.runtime.coordinators.values()}
        for item, serial in zip(out["sets"], self.counters.sets, strict=False):
            item["set"] = numbers.get(serial)
        return out
