"""Which tariffs the cost log (and later the planner) uses (B28).

* Own tariffs from the options, or a supplier from the tariff table.
* The table ships with ZEPHYR (``data/tariffs.json``). ZEPHYR fetches the newest
  version from GitHub once a month, at startup when that is due, and when the
  chosen supplier changes. It keeps the last fetched table in its own storage.
  Without a connection it uses the newest of the stored and the shipped table.
* No scraping of supplier websites (P2): the table is maintained with pull requests.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_TARIFF_ENERGY_TAX,
    CONF_TARIFF_FIXED_MONTH,
    CONF_TARIFF_MARKUP_EXPORT,
    CONF_TARIFF_MARKUP_IMPORT,
    CONF_TARIFF_SOLAR_BONUS,
    CONF_TARIFF_SUPPLIER,
    CONF_TARIFF_VAT,
    DOMAIN,
    LOGGER,
    TARIFF_OWN,
)
from .core.costs import Tariffs
from .core.tariff_table import TableError, TariffTable, newest, parse_table

TABLE_URL = "https://raw.githubusercontent.com/cardinal808/ZEPHYR/main/custom_components/zephyr/data/tariffs.json"
SHIPPED = Path(__file__).parent / "data" / "tariffs.json"
REFRESH_AFTER = timedelta(days=30)
FIRST_FETCH_DELAY = 60.0
"""s after startup before a due fetch (startup stays fast)."""
STORAGE_VERSION = 1


def tariffs_from_options(options: Mapping[str, Any]) -> Tariffs:
    defaults = Tariffs()
    return Tariffs(
        energy_tax=float(options.get(CONF_TARIFF_ENERGY_TAX, defaults.energy_tax)),
        vat=float(options.get(CONF_TARIFF_VAT, defaults.vat)),
        markup_import=float(options.get(CONF_TARIFF_MARKUP_IMPORT, defaults.markup_import)),
        markup_export=float(options.get(CONF_TARIFF_MARKUP_EXPORT, defaults.markup_export)),
        solar_bonus=float(options.get(CONF_TARIFF_SOLAR_BONUS) or 0.0),
        fixed_month=float(options.get(CONF_TARIFF_FIXED_MONTH) or 0.0),
        source="own",
    )


def load_shipped() -> TariffTable | None:
    """The table shipped with this version (blocking: call in the executor)."""
    try:
        return parse_table(json.loads(SHIPPED.read_text(encoding="utf-8")))
    except (OSError, ValueError) as err:
        LOGGER.error("Shipped tariff table cannot be read: %s", err)
        return None


class TariffProvider:
    def __init__(self, hass: HomeAssistant, entry_id: str, options: Mapping[str, Any]) -> None:
        self.hass = hass
        self.supplier: str = options.get(CONF_TARIFF_SUPPLIER) or TARIFF_OWN
        self.own = tariffs_from_options(options)
        self.shipped: TariffTable | None = None
        self.fetched: TariffTable | None = None
        self.fetched_at: datetime | None = None
        self.fetched_for: str | None = None
        self.attempted_at: datetime | None = None
        self.last_error: str | None = None
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.tariff_table")

    @property
    def table(self) -> TariffTable | None:
        return newest(self.fetched, self.shipped)

    @property
    def origin(self) -> str | None:
        table = self.table
        if table is None:
            return None
        return "github" if table is self.fetched else "shipped"

    async def async_start(self) -> Callable[[], None]:
        self.shipped = await self.hass.async_add_executor_job(load_shipped)
        stored = await self._store.async_load() or {}
        if stored.get("data"):
            try:
                self.fetched = parse_table(stored["data"])
                self.fetched_at = dt_util.parse_datetime(str(stored.get("fetched_at") or ""))
                self.fetched_for = stored.get("supplier")
            except TableError as err:
                self.last_error = f"stored table: {err}"
        unsubs: list[Callable[[], None]] = [async_track_time_interval(self.hass, self._on_day, timedelta(days=1))]
        if self._fetch_due():
            unsubs.append(async_call_later(self.hass, FIRST_FETCH_DELAY, self._on_day))

        def stop() -> None:
            for unsub in unsubs:
                unsub()

        return stop

    def _fetch_due(self) -> bool:
        now = dt_util.utcnow()
        if self.attempted_at is not None and now - self.attempted_at < timedelta(hours=23):
            return False  # at most one attempt a day
        if self.fetched_at is None:
            return True
        if self.supplier != TARIFF_OWN and self.supplier != self.fetched_for:
            return True  # the choice changed (B28)
        return now - self.fetched_at >= REFRESH_AFTER

    @callback
    def _on_day(self, _now: datetime) -> None:
        if self._fetch_due():
            self.hass.async_create_background_task(self.async_fetch(), "zephyr: fetch tariff table")

    async def async_fetch(self) -> bool:
        """Fetch the table from GitHub. False (and the reason in the diagnostics) when it fails."""
        session = async_get_clientsession(self.hass)
        self.attempted_at = dt_util.utcnow()
        try:
            async with session.get(TABLE_URL, timeout=aiohttp.ClientTimeout(total=20)) as response:
                response.raise_for_status()
                data = json.loads(await response.text())
            table = parse_table(data)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            self.last_error = f"{type(err).__name__}: {err}"
            LOGGER.info("Tariff table not fetched: %s", self.last_error)
            return False
        self.fetched, self.fetched_at, self.fetched_for, self.last_error = table, dt_util.utcnow(), self.supplier, None
        await self._store.async_save({"fetched_at": self.fetched_at.isoformat(), "supplier": self.supplier, "data": data})
        return True

    def tariffs_for(self, day: date) -> Tariffs:
        """The tariffs that apply on ``day``: the chosen supplier, or own tariffs."""
        if self.supplier != TARIFF_OWN and self.table is not None:
            tariffs = self.table.tariffs(self.supplier, day, fixed_month=self.own.fixed_month)
            if tariffs is not None:
                return tariffs
        return self.own

    def diagnostics(self) -> dict[str, Any]:
        table = self.table
        today = dt_util.now().date()
        return {
            "supplier": self.supplier,
            "in_use": self.tariffs_for(today).as_dict(),
            "supplier_missing": self.supplier != TARIFF_OWN and self.tariffs_for(today) is self.own,
            "table": None if table is None else {"updated": table.updated.isoformat(), "origin": self.origin},
            "shipped_updated": None if self.shipped is None else self.shipped.updated.isoformat(),
            "fetched_at": None if self.fetched_at is None else self.fetched_at.isoformat(),
            "last_error": self.last_error,
        }
