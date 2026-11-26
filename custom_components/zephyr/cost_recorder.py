"""Cost log in Home Assistant (B38, SPEC-kosten).

Every second (with the control loop) the P1 value and the battery power of the
sets are integrated; at every quarter (:00, :15, :30, :45) the quarter is closed
with the meter counters (optional), the solar counter and the market price that
applied at its start. Quarters are stored per month (24 months), day totals
without limit. Also in shadow mode: then it shows the costs of the current system.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Mapping
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.sun import is_up
from homeassistant.util import dt as dt_util

from .const import (
    CONF_COST_EXPORT_COUNTERS,
    CONF_COST_IMPORT_COUNTERS,
    CONF_PRICE_ENTITY,
    CONF_SOLAR_ENERGY,
    DOMAIN,
    LOGGER,
)
from .core import plan_check
from .core.costs import (
    QUARTER_SECONDS,
    Pools,
    QuarterInput,
    QuarterMeter,
    Summary,
    add_to_day,
    counter_delta,
    evaluate,
    summarize,
    to_csv,
)
from .core.price_window import parse_nordpool_raw
from .core.solar_history import energy_kwh

if TYPE_CHECKING:
    from . import ZephyrRuntime
    from .tariff_provider import TariffProvider

STORAGE_VERSION = 1
KEEP_MONTHS = 24
P1_FRESH = 10.0
"""s; an older P1 value is not integrated (a gap in the quarter)."""


def _number(state: State | None) -> float | None:
    if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
        return None
    try:
        return float(state.state)
    except ValueError:
        return None


def _counter_kwh(state: State | None) -> float | None:
    value = _number(state)
    if value is None or state is None:
        return None
    return energy_kwh(value, state.attributes.get("unit_of_measurement"))


def market_price(state: State | None, start: datetime) -> float | None:
    """Bare market price (€/kWh) of the slot that contains ``start``, from a Nord Pool sensor."""
    if state is None:
        return None
    slots = parse_nordpool_raw(state.attributes.get("raw_today")) + parse_nordpool_raw(state.attributes.get("raw_tomorrow"))
    slot = next((s for s in slots if s.start <= start < s.end), None)
    if slot is None:
        return None
    unit = str(state.attributes.get("unit") or state.attributes.get("unit_of_measurement") or "")
    value = slot.price
    if "MWh" in unit:
        value /= 1000
    if state.attributes.get("price_in_cents") is True:
        value /= 100
    return value


def quarter_floor(moment: datetime) -> datetime:
    utc = dt_util.as_utc(moment)
    return utc.replace(minute=utc.minute - utc.minute % 15, second=0, microsecond=0)


def _month_key(start: datetime) -> str:
    return dt_util.as_local(start).strftime("%Y-%m")


def _months_back(month: str, count: int) -> str:
    year, mon = (int(x) for x in month.split("-"))
    index = year * 12 + mon - 1 - count
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def _days_in_month(day: date) -> int:
    nxt = date(day.year + (day.month == 12), day.month % 12 + 1, 1)
    return (nxt - date(day.year, day.month, 1)).days


class CostRecorder:
    def __init__(
        self, hass: HomeAssistant, entry_id: str, options: Mapping[str, Any], runtime: ZephyrRuntime, tariffs: TariffProvider
    ) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.runtime = runtime
        self.tariffs = tariffs
        self.price_entity: str | None = options.get(CONF_PRICE_ENTITY)
        self.solar_entity: str | None = options.get(CONF_SOLAR_ENERGY)
        self.import_counters: list[str] = list(options.get(CONF_COST_IMPORT_COUNTERS) or [])
        self.export_counters: list[str] = list(options.get(CONF_COST_EXPORT_COUNTERS) or [])
        self.meter = QuarterMeter()
        self.days: dict[str, dict[str, float]] = {}
        self.pools = Pools()
        self.counters: dict[str, list[Any]] = {}
        """entity → [boundary (ISO UTC), kWh]: the reading at the last quarter boundary."""
        self._excluded_total: float | None = None
        """B41: the excluded load's energy total at the last quarter close (None until the first close)."""
        self.months: list[str] = []
        self.current: list[dict[str, Any]] = []
        self.current_month: str | None = None
        self.open_start: datetime | None = None
        self.open_market: float | None = None
        self._main: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.costs")
        self._listeners: list[Callable[[], None]] = []
        self._summaries: dict[str, Summary] = {}
        self._stores: dict[str, Store[dict[str, Any]]] = {}

    # --- lifecycle ---------------------------------------------------------------

    def _month_store(self, month: str) -> Store[dict[str, Any]]:
        if month not in self._stores:
            self._stores[month] = Store(self.hass, STORAGE_VERSION, f"{DOMAIN}.{self.entry_id}.costs.{month}")
        return self._stores[month]

    async def async_save(self) -> None:
        """Write everything now (unload, reload): delayed saves only flush when HA stops."""
        if self.current_month is not None:
            await self._month_store(self.current_month).async_save({"quarters": self.current})
        await self._main.async_save(self._main_data())

    async def async_start(self) -> Callable[[], None]:
        data = await self._main.async_load() or {}
        self.days = {k: dict(v) for k, v in (data.get("days") or {}).items()}
        self.pools = Pools.from_dict(data.get("pools"))
        self.counters = dict(data.get("counters") or {})
        self.months = list(data.get("months") or [])
        now = dt_util.utcnow()
        await self._load_month(_month_key(now))
        self._open(quarter_floor(now))
        unsubs: list[Callable[[], None]] = [
            async_track_time_change(self.hass, self._on_boundary, minute=[0, 15, 30, 45], second=0),
        ]
        if self.runtime.control is not None:
            unsubs.append(self.runtime.control.async_add_listener(self._sample))
        self._summaries.clear()
        for listener in list(self._listeners):  # the sensors were added before the history was loaded
            listener()

        def stop() -> None:
            for unsub in unsubs:
                unsub()

        return stop

    async def _load_month(self, month: str) -> None:
        if month == self.current_month:
            return
        stored = await self._month_store(month).async_load() or {}
        self.current = list(stored.get("quarters") or [])
        self.current_month = month
        if month not in self.months:
            self.months.append(month)
            for old in [m for m in self.months if m <= _months_back(month, KEEP_MONTHS)]:
                self.months.remove(old)
                await self._month_store(old).async_remove()
                self._stores.pop(old, None)

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    # --- measuring ----------------------------------------------------------------

    @callback
    def _sample(self) -> None:
        now = time.monotonic()
        control = self.runtime.control
        grid: float | None = None
        if control is not None and control.p1_at is not None and now - control.p1_at <= P1_FRESH:
            grid = control.p1_watts
        totals = self.runtime.totals()
        battery = totals.power if totals.sets_online else None
        self.meter.sample(now, grid, battery, totals.solar_power)

    def _open(self, start: datetime) -> None:
        self.open_start = start
        self.open_market = market_price(self.hass.states.get(self.price_entity), start) if self.price_entity else None

    @callback
    def _on_boundary(self, now: datetime) -> None:
        self.hass.async_create_task(self.async_close(quarter_floor(now)), "zephyr: close cost quarter")

    def _counter_sum(self, entities: Iterable[str], boundary: datetime, previous: datetime) -> float | None:
        """Sum of the counter deltas since ``previous``; None when one is unknown. Stores the new readings."""
        total: float | None = 0.0
        for entity in entities:
            reading = _counter_kwh(self.hass.states.get(entity))
            stored = self.counters.get(entity)
            delta = counter_delta(stored[1], reading) if stored and stored[0] == previous.isoformat() else None
            if reading is not None:
                self.counters[entity] = [boundary.isoformat(), reading]
            else:
                self.counters.pop(entity, None)
            total = None if total is None or delta is None else total + delta
        return total

    async def async_close(self, boundary: datetime) -> dict[str, Any] | None:
        """Close the quarter that ends at ``boundary`` and open the next one."""
        mono = time.monotonic()
        measured = self.meter.take(mono)
        start = boundary - timedelta(seconds=QUARTER_SECONDS)
        market = self.open_market if self.open_start == start else None
        if market is None and self.price_entity:
            market = market_price(self.hass.states.get(self.price_entity), start)
        imp, exp = measured.import_kwh, measured.export_kwh
        coverage = measured.grid_seconds / QUARTER_SECONDS
        if self.import_counters and self.export_counters:
            counted_imp = self._counter_sum(self.import_counters, boundary, start)
            counted_exp = self._counter_sum(self.export_counters, boundary, start)
            if counted_imp is not None and counted_exp is not None:
                imp, exp, coverage = counted_imp, counted_exp, 1.0
        solar: float | None = None
        if self.solar_entity:
            ext = self._counter_sum([self.solar_entity], boundary, start)
            solar = None if ext is None else ext + measured.set_solar_kwh
        if self.runtime.coordinators:
            coverage = min(coverage, measured.battery_seconds / QUARTER_SECONDS)
        totals = self.runtime.totals()
        local_start = dt_util.as_local(start)
        record = evaluate(
            QuarterInput(
                start=start,
                minutes=QUARTER_SECONDS / 60,
                import_kwh=imp,
                export_kwh=exp,
                charge_kwh=measured.charge_kwh,
                discharge_kwh=measured.discharge_kwh,
                solar_kwh=solar,
                market=market,
                coverage=coverage,
                stored_kwh=totals.energy_kwh,
                daylight=is_up(self.hass, start + timedelta(seconds=QUARTER_SECONDS / 2)),
            ),
            self.tariffs.tariffs_for(local_start.date()),
            self.pools,
            _days_in_month(local_start.date()),
        )
        record["soc"] = None if totals.soc is None else round(totals.soc, 1)
        if self.runtime.vacation is not None and self.runtime.vacation.was(start):
            record["vacation"] = True  # B42: filter vacations out of overviews; the planner learns apart
        excluded = self.runtime.control.excluded if self.runtime.control is not None else None
        if excluded is not None:
            # B41: use of the load the battery may not feed (the air conditioner), from its counter.
            total = excluded.energy_total
            previous = self._excluded_total if self._excluded_total is not None else total
            record["excluded_kwh"] = round(max(total - previous, 0.0), 3)
            self._excluded_total = total
        if self.runtime.planner is not None:
            record.update(self.runtime.planner.quarter_closed(start, record, self.solar_entity is not None))
        self._open(boundary)
        await self._load_month(_month_key(start))
        self.current.append(record)
        add_to_day(self.days.setdefault(local_start.date().isoformat(), {}), record)
        self._summaries.clear()
        assert self.current_month is not None
        month_store, quarters = self._month_store(self.current_month), self.current
        month_store.async_delay_save(lambda: {"quarters": quarters}, 30)
        self._main.async_delay_save(self._main_data, 30)
        LOGGER.debug("Cost quarter %s: %s", start.isoformat(), record)
        for listener in list(self._listeners):
            listener()
        return record

    def records_since(self, start: datetime) -> dict[datetime, dict[str, Any]]:
        """Stored quarters of the current month from ``start`` on, by start time (UTC); for the panel."""
        out: dict[datetime, dict[str, Any]] = {}
        for record in self.current:
            moment = dt_util.as_utc(datetime.fromisoformat(record["start"]))
            if moment >= start:
                out[moment] = record
        return out

    def _main_data(self) -> dict[str, Any]:
        return {"days": self.days, "pools": self.pools.as_dict(), "counters": self.counters, "months": self.months}

    # --- reading --------------------------------------------------------------------

    def period(self, name: str) -> tuple[date, date]:
        today = dt_util.now().date()
        if name == "today":
            return today, today
        if name == "month":
            return today.replace(day=1), today
        return today.replace(month=1, day=1), today

    def summary(self, name: str) -> Summary:
        if name not in self._summaries:
            first, last = self.period(name)
            self._summaries[name] = summarize(self.days, first, last, self.tariffs.tariffs_for(first))
        return self._summaries[name]

    async def async_records(self, first: date, last: date) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for month in sorted(self.months):
            if month < first.strftime("%Y-%m") or month > last.strftime("%Y-%m"):
                continue
            if month == self.current_month:
                quarters = self.current
            else:
                quarters = list((await self._month_store(month).async_load() or {}).get("quarters") or [])
            for record in quarters:
                day = dt_util.as_local(datetime.fromisoformat(record["start"])).date()
                if first <= day <= last:
                    out.append(record)
        return out

    async def async_export(self, first: date, last: date) -> dict[str, Any]:
        records = await self.async_records(first, last)
        path = Path(self.hass.config.path(DOMAIN, f"costs_{first.isoformat()}_{last.isoformat()}.csv"))
        text = to_csv(records)

        def write() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        await self.hass.async_add_executor_job(write)
        return {"path": str(path), "rows": len(records)}

    def plan_check(self, days: int = 14) -> dict[str, Any]:
        """Plan against reality (B38) for the last ``days`` local days, today included."""
        today = dt_util.now().date()
        items = plan_check.checks(self.days, today - timedelta(days=days - 1), today)
        return {"days": items, "summary": plan_check.summary([i for i in items if i["date"] < today.isoformat()])}

    def diagnostics(self) -> dict[str, Any]:
        return {
            "tariffs": self.tariffs.diagnostics(),
            "price_entity": self.price_entity,
            "solar_entity": self.solar_entity,
            "import_counters": self.import_counters,
            "export_counters": self.export_counters,
            "open_quarter": None if self.open_start is None else self.open_start.isoformat(),
            "open_market": self.open_market,
            "pools": self.pools.as_dict(),
            "days_stored": len(self.days),
            "months_stored": self.months,
            "today": self.summary("today").as_dict(),
            "month": self.summary("month").as_dict(),
            "last_quarters": self.current[-8:],
            "plan_check": self.plan_check(7),
        }
