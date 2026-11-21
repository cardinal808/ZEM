"""Mode of the installation."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import ZemConfigEntry, ZemRuntime
from .core.engine import Mode
from .entity import ZemControlEntity

# Dynamic Forecasting follows with the planner (M5).
MODES = [Mode.STANDBY, Mode.ZERO_METER, Mode.FAST_CHARGE, Mode.FAST_DISCHARGE]


async def async_setup_entry(hass: HomeAssistant, entry: ZemConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    async_add_entities([ZemModeSelect(entry.runtime_data, entry)])


class ZemModeSelect(ZemControlEntity, SelectEntity, RestoreEntity):
    _attr_options: list[str] = [m.value for m in MODES]  # noqa: RUF012

    def __init__(self, runtime: ZemRuntime, entry: ZemConfigEntry) -> None:
        super().__init__(runtime, entry, "mode", "select")

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None and last.state in self._attr_options:
            mode = Mode(last.state)
            # A fast mode does not survive a restart: its goal was tied to that moment.
            if mode not in (Mode.FAST_CHARGE, Mode.FAST_DISCHARGE):
                self._control.async_set_mode(mode)

    @property
    def current_option(self) -> str:
        return self._control.engine.mode.value

    async def async_select_option(self, option: str) -> None:
        self._control.async_set_mode(Mode(option))
        self.async_write_ha_state()
