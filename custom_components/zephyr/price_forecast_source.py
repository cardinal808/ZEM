"""The jeroen.nl price forecast in Home Assistant (OPDRACHT-prijsvoorspelling-jeroen).

Reads the sensor of ha-jeroen-nl (chosen by the user; nothing is fetched from jeroen.nl by
ZEPHYR), extends the planner's horizon with it (``core/price_forecast.py``), keeps one forecast
run a day for the backtest (private: only in ZEPHYR's own storage, never in diagnostics or
exports) and works out its quality against the real prices.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta, tzinfo
from typing import Any, Final

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_PRICE_FORECAST_DAYS,
    CONF_PRICE_FORECAST_ENTITY,
    CONF_PRICE_FORECAST_MODE,
    CONF_PRICE_FORECAST_VALUE,
    DOMAIN,
    LOGGER,
)
from .core.price_forecast import (
    MODE_INDICATIVE,
    MODE_OFF,
    MODES,
    VALUE_LOW,
    VALUES,
    Extension,
    Forecast,
    extend_markets,
    parse_forecast,
)

ISSUE_FORMAT: Final = "price_forecast_format"
KEEP_RUNS: Final = timedelta(days=120)
SAVE_AFTER_HOUR: Final = 6
SOURCE: Final = {"name": "jeroen.nl", "url": "https://jeroen.nl"}


RUN_VERSION = 2
"""2: the band is bare like ``market`` (before 0.8.96 it was kept all-in, OPDRACHT-band-prijsverwachting)."""


def _repair_run(run: dict[str, Any]) -> dict[str, Any]:
    """A run kept before 0.8.96: its band was all-in and cannot be turned back (the sensor's
    line is not kept), so ``market`` stands in for it; the error per day ahead stays right."""
    if run.get("v", 1) >= RUN_VERSION:
        return run
    slots = []
    for slot in run.get("slots", []):
        start, market, low, high = slot
        slots.append([start, market, low, high] if low <= market <= high else [start, market, market, market])
    return {**run, "slots": slots, "v": RUN_VERSION}


class PriceForecastSource:
    def __init__(self, hass: HomeAssistant, entry_id: str, options: Mapping[str, Any]) -> None:
        self.hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}.{entry_id}.price_forecast")
        self.runs: list[dict[str, Any]] = []
        self._loaded = False
        self.last: Extension | None = None
        self.forecast: Forecast | None = None
        self.compare: dict[str, Any] | None = None
        self.apply_options(options)

    def apply_options(self, options: Mapping[str, Any]) -> None:
        self.entity: str | None = options.get(CONF_PRICE_FORECAST_ENTITY) or None
        mode = options.get(CONF_PRICE_FORECAST_MODE, MODE_INDICATIVE)
        self.mode: str = mode if mode in MODES else MODE_INDICATIVE
        if not self.entity:
            self.mode = MODE_OFF
        self.days: int = int(options.get(CONF_PRICE_FORECAST_DAYS, 1))
        value = options.get(CONF_PRICE_FORECAST_VALUE, VALUE_LOW)
        self.value: str = value if value in VALUES else VALUE_LOW

    @property
    def active(self) -> bool:
        return self.mode != MODE_OFF and bool(self.entity)

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.runs = [_repair_run(r) for r in data.get("runs", []) if isinstance(r, dict)]
        self._loaded = True

    def extend(self, markets: Sequence[tuple[datetime, float, bool]], now: datetime, tz: tzinfo) -> Extension | None:
        """The horizon with the forecast, or None when the source is off."""
        if not self.active or self.entity is None:
            self.last = None
            return None
        state = self.hass.states.get(self.entity)
        forecast = parse_forecast(None if state is None else state.state, {} if state is None else state.attributes)
        self.forecast = forecast
        if not forecast.readable:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                ISSUE_FORMAT,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_FORMAT,
                translation_placeholders={"entity": self.entity},
            )
        else:
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_FORMAT)
        self.last = extend_markets(markets, forecast, now, tz, self.days, self.value)
        self._keep_run(forecast, now)
        return self.last

    # --- runs for the backtest (§3.6) ---------------------------------------------------

    def _keep_run(self, forecast: Forecast, now: datetime) -> None:
        if not self._loaded or not forecast.slots or dt_util.as_local(now).hour < SAVE_AFTER_HOUR:
            return
        made = (forecast.made or forecast.slots[0].start).isoformat()
        day = dt_util.as_local(now).date().isoformat()
        if any(r.get("day") == day for r in self.runs):
            return  # one run a day
        self.runs.append(
            {
                "day": day,
                "made": made,
                "v": RUN_VERSION,
                "slots": [[s.start.isoformat(), round(s.market, 6), round(s.low, 6), round(s.high, 6)] for s in forecast.slots],
            }
        )
        oldest = (dt_util.as_local(now).date() - KEEP_RUNS).isoformat()
        self.runs = [r for r in self.runs if r.get("day", "") >= oldest]
        self._store.async_delay_save(self._data, 10)
        LOGGER.debug("Price forecast: run of %s kept (%d quarters)", made, len(forecast.slots))

    def _data(self) -> dict[str, Any]:
        return {"runs": self.runs}

    def quality(self, actual: Callable[[datetime], float | None], days: int = 30) -> dict[str, Any]:
        """Per day ahead: mean absolute error (€/kWh, bare) and the share inside the band."""
        since = (dt_util.now().date() - timedelta(days=days)).isoformat()
        stats: dict[int, list[tuple[float, bool]]] = {}
        for run in self.runs:
            if run.get("day", "") < since:
                continue
            run_day = datetime.fromisoformat(run["day"]).date()
            for start, market, low, high in run.get("slots", []):
                moment = datetime.fromisoformat(start)
                real = actual(moment)
                if real is None:
                    continue
                ahead = (dt_util.as_local(moment).date() - run_day).days
                stats.setdefault(ahead, []).append((abs(market - real), low <= real <= high))
        return {
            str(ahead): {
                "quarters": len(rows),
                "mean_error": round(sum(e for e, _ in rows) / len(rows), 4),
                "inside_band": round(sum(1 for _, inside in rows if inside) / len(rows), 3),
            }
            for ahead, rows in sorted(stats.items())
        }

    def diagnostics(self, actual: Callable[[datetime], float | None]) -> dict[str, Any]:
        """Summaries only: the raw forecast stays private (jeroen.nl terms)."""
        ext, forecast = self.last, self.forecast
        return {
            "entity": self.entity,
            "mode": self.mode,
            "days": self.days,
            "value": self.value,
            "used_slots": 0 if ext is None else len(ext.used),
            "first": None if ext is None or not ext.used else ext.used[0].start.isoformat(),
            "last": None if ext is None or not ext.used else ext.used[-1].start.isoformat(),
            "made": None if forecast is None or forecast.made is None else forecast.made.isoformat(),
            "reason": None if ext is None else ext.reason,
            "issues": [] if forecast is None else forecast.issues,
            "band_all_in": 0 if forecast is None else forecast.band_all_in,
            "compare": self.compare,
            "runs_stored": len(self.runs),
            "quality": self.quality(actual),
        }

    def chart(self) -> dict[str, Any] | None:
        """The forecast quarters used, with the band, for the panel's price chart (§3.5)."""
        ext = self.last
        if ext is None or not ext.used:
            return None
        return {
            "source": SOURCE,
            "value": self.value,
            "slots": [{"start": s.start.isoformat(), "market": s.market, "low": s.low, "high": s.high} for s in ext.used],
        }
