"""Curtail surplus solar at a negative export price (PLANNING 1.1/1.2).

Every quarter the export price of that quarter (market price with the tariffs, as in the cost
log) decides: below zero, surplus solar should not be exported. With mode *ZEPHYR* this blocks
export of the sets' own PV (``gridReverse``, via the engine) and turns on the chosen switch
for the inverter; otherwise nothing is written.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_time_change
from homeassistant.helpers.sun import is_up
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CURTAIL_INVERTER_W,
    CONF_CURTAIL_MODE,
    CONF_CURTAIL_NUMBER,
    CONF_CURTAIL_SWITCH,
    CONF_PRICE_ENTITY,
    CURTAIL_EXTERNAL,
    CURTAIL_OFF,
    CURTAIL_ZEPHYR,
    LOGGER,
)
from .core.curtail_limit import should_write, wanted_percent
from .prices import price_state

if TYPE_CHECKING:
    from . import ZephyrRuntime


def planner_curtails(options: Mapping[str, Any]) -> bool:
    """Does the planner count surplus at a negative price as curtailed?"""
    mode = options.get(CONF_CURTAIL_MODE, CURTAIL_OFF)
    inverter = bool(options.get(CONF_CURTAIL_SWITCH)) or (
        bool(options.get(CONF_CURTAIL_NUMBER)) and bool(options.get(CONF_CURTAIL_INVERTER_W))
    )
    return mode == CURTAIL_EXTERNAL or (mode == CURTAIL_ZEPHYR and inverter)


class CurtailManager:
    """Decides per quarter whether export is blocked, and drives the switch."""

    def __init__(self, hass: HomeAssistant, options: Mapping[str, Any], runtime: ZephyrRuntime) -> None:
        self.hass = hass
        self.runtime = runtime
        self.mode: str = options.get(CONF_CURTAIL_MODE, CURTAIL_OFF)
        self.switch: str | None = options.get(CONF_CURTAIL_SWITCH) or None
        self.price_entity: str | None = options.get(CONF_PRICE_ENTITY)
        self.negative = False
        self.sell: float | None = None
        self.checked_at: str | None = None
        self._switch_set: bool | None = None
        self.number: str | None = options.get(CONF_CURTAIL_NUMBER) or None
        rated = options.get(CONF_CURTAIL_INVERTER_W)
        self.rated_w: float | None = float(rated) if rated else None
        self.limit_written: int | None = None
        self.last_error: str | None = None

    @property
    def export_blocked(self) -> bool | None:
        """For the engine: block / allow ``gridReverse``; None = ZEPHYR leaves it alone."""
        return self.negative if self.mode == CURTAIL_ZEPHYR else None

    async def async_start(self) -> Callable[[], None]:
        unsub = async_track_time_change(self.hass, self._on_quarter, minute=[0, 15, 30, 45], second=5)
        cancel = async_call_later(self.hass, 10, self._on_quarter)
        unsub_limit = async_track_time_change(self.hass, self._on_limit_tick, second=list(range(0, 60, 10)))

        def stop() -> None:
            unsub()
            cancel()
            unsub_limit()

        return stop

    @callback
    def _on_quarter(self, _now: datetime | None = None) -> None:
        self.hass.async_create_task(self.async_check(), "zephyr: curtail check")

    def sell_now(self, now: datetime | None = None) -> float | None:
        """Export price of the current quarter (€/kWh), as the cost log applies it."""
        from .cost_recorder import market_price, quarter_floor

        now = now or dt_util.utcnow()
        start = quarter_floor(now)
        if not self.price_entity or self.runtime.tariffs is None:
            return None
        market = market_price(price_state(self.hass, self.price_entity), start)
        if market is None:
            return None
        tariffs = self.runtime.tariffs.tariffs_for(dt_util.as_local(start).date())
        sell, _ = tariffs.sell(market, start, is_up(self.hass, start + timedelta(minutes=7, seconds=30)))
        return sell

    async def async_check(self) -> None:
        self.sell = self.sell_now()
        negative = self.sell is not None and self.sell < 0
        if negative != self.negative:
            LOGGER.info("Export price %s: export of surplus solar %s", self.sell, "blocked" if negative else "allowed")
        self.negative = negative
        self.checked_at = dt_util.utcnow().isoformat(timespec="seconds")
        if self.mode == CURTAIL_ZEPHYR and self.switch:
            await self._drive(negative)
        if self.mode == CURTAIL_ZEPHYR and self.number and self.rated_w:
            await self.async_limit()

    @callback
    def _on_limit_tick(self, _now: datetime) -> None:
        if self.mode == CURTAIL_ZEPHYR and self.number and self.rated_w:
            self.hass.async_create_task(self.async_limit(), "zephyr: inverter limit")

    async def async_limit(self) -> None:
        """Keep the inverter at what the house and the battery take while the price is negative."""
        if not self.number or not self.rated_w:
            return
        state = self.hass.states.get(self.number)
        try:
            current = None if state is None else float(state.state)
        except ValueError:
            current = None
        if self.negative:
            control = self.runtime.control
            solar, _ = control.external_solar() if control is not None else (None, False)
            grid = control.engine.p1_now if control is not None else None
            if solar is None or grid is None:
                return
            # Leave room for the batteries to charge from the surplus first (the controller
            # takes it as soon as it sees export).
            wanted = wanted_percent(solar + self._charge_room(), grid, self.rated_w)
        else:
            wanted = 100
        if not should_write(current, wanted):
            return
        try:
            await self.hass.services.async_call("number", "set_value", {"entity_id": self.number, "value": wanted}, blocking=True)
        except Exception as err:
            self.last_error = f"{type(err).__name__}: {err}"
            LOGGER.warning("Curtail number %s: %s", self.number, err)
            return
        self.limit_written = wanted
        self.last_error = None

    def _charge_room(self) -> float:
        """W the online sets could still charge on top of what they charge now (not when full)."""
        control = self.runtime.control
        max_soc = control.engine.settings.max_soc if control is not None else 100.0
        room = 0.0
        for coordinator in self.runtime.coordinators.values():
            data = coordinator.data
            report = data.report if data is not None else None
            if report is None or not coordinator.health.online or report.soc >= max_soc - 1:
                continue
            room += max(float(report.charge_max_limit or 2400) - max(report.charge_power_ac, 0.0), 0.0)
        return room

    async def _drive(self, on: bool) -> None:
        state = self.hass.states.get(self.switch) if self.switch else None
        current = None if state is None else state.state == "on"
        if current is on and self._switch_set is on:
            return
        try:
            await self.hass.services.async_call(
                "switch", SERVICE_TURN_ON if on else SERVICE_TURN_OFF, {"entity_id": self.switch}, blocking=True
            )
        except Exception as err:
            self.last_error = f"{type(err).__name__}: {err}"
            LOGGER.warning("Curtail switch %s: %s", self.switch, err)
            return
        self._switch_set = on
        self.last_error = None

    def view(self) -> dict[str, Any]:
        """For the panel (SPEC-ui-planner §4.3): is ZEPHYR curtailing now, and how."""
        active = self.mode == CURTAIL_ZEPHYR and self.negative
        return {
            "mode": self.mode,
            "negative": self.negative,
            "active": active,
            "percent": self.limit_written if active and self.number is not None else None,
            "switch_on": self._switch_set if active and self.switch is not None else None,
            "export_blocked": bool(self.export_blocked),
        }

    def diagnostics(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "switch_set": self.switch is not None,
            "number_set": self.number is not None,
            "rated_w": self.rated_w,
            "limit_written": self.limit_written,
            "sell_now": self.sell,
            "negative": self.negative,
            "export_blocked": self.export_blocked,
            "checked_at": self.checked_at,
            "last_error": self.last_error,
        }
