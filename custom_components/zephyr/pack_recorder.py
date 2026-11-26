"""Keeps the cell balance per pack per day and when a set was last full (UI-4).

Listens to the set coordinators; saves at most every 5 minutes in
``zephyr.<entry>.packs``. Serial numbers stay in Home Assistant's storage.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .core.packs import PackHistory, cell_delta_mv

if TYPE_CHECKING:
    from . import ZephyrRuntime

STORAGE_VERSION: Final = 1
SAVE_DELAY_S: Final = 300


class PackRecorder:
    def __init__(self, hass: HomeAssistant, entry_id: str, runtime: ZephyrRuntime) -> None:
        self.hass = hass
        self.runtime = runtime
        self.history = PackHistory()
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.packs")

    async def async_start(self) -> Callable[[], None]:
        self.history = PackHistory.from_dict(await self._store.async_load())
        self.history.prune(dt_util.now().date())
        unsubs = [c.async_add_listener(self._on_update) for c in self.runtime.coordinators.values()]

        def stop() -> None:
            for unsub in unsubs:
                unsub()
            self._store.async_delay_save(self.history.as_dict, 0)

        return stop

    @callback
    def _on_update(self) -> None:
        now = dt_util.now()
        today = now.date()
        changed = False
        for coordinator in self.runtime.coordinators.values():
            data = coordinator.data
            if data is None or data.report is None or not data.online:
                continue
            report = data.report
            changed |= self.history.note_set_full(report.serial, dt_util.as_utc(now).isoformat(), report.soc)
            for pack in report.packs:
                delta = cell_delta_mv(pack.cell_voltage_min, pack.cell_voltage_max)
                changed |= self.history.note_pack(pack.serial, today, pack.soc, delta)
        if changed:
            self._store.async_delay_save(self.history.as_dict, SAVE_DELAY_S)
