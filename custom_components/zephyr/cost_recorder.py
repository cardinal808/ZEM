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
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_change
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
from .core.cost_correction import MAX_AGE as MAX_CORRECTION_AGE
from .core.cost_correction import day_delta, gap_shares, reevaluate
from .core.costs import (
    QUARTER_SECONDS,
    Pools,
    QuarterInput,
    QuarterMeter,
    Summary,
    add_to_day,
    counter_delta,
    evaluate,
    quarter_status,
    refresh_content,
    summarize,
    to_csv,
)
from .core.energy_counters import TOTAL_KEYS as ENERGY_TOTAL_KEYS
from .core.price_window import parse_nordpool_raw
from .core.quarter_fill import (
    FULL_SHARE,
    Part,
    QuarterFill,
    fill_gap,
    fill_part,
    history_mean,
    interpolate,
    neighbour_value,
    scale_to,
)
from .core.solar_history import energy_kwh
from .prices import price_state

if TYPE_CHECKING:
    from . import ZephyrRuntime
    from .tariff_provider import TariffProvider

STORAGE_VERSION = 1
KEEP_MONTHS = 24
P1_FRESH = 10.0
"""s; an older P1 value is not integrated (a gap in the quarter)."""
FILL_VERSION = 2
"""Version of the one-off work on the stored history: 1 fills it (OPDRACHT-onvolledige-kwartieren
eis 5), 2 adds the solar savings split (OPDRACHT-besparing-zon)."""
MAX_GAP_QUARTERS = 31 * 96
"""A longer interruption is not filled with quarters (a month of guesses helps nobody)."""


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
        self.days: dict[str, dict[str, Any]] = {}
        self.pools = Pools()
        self.counters: dict[str, list[Any]] = {}
        """entity → [boundary (ISO UTC), kWh]: the reading at the last quarter boundary."""
        self._corrections_log: list[dict[str, Any]] = []
        self._gap_here = False
        self._excluded_total: float | None = None
        """B41: the excluded load's energy total at the last quarter close (None until the first close)."""
        self.months: list[str] = []
        self.current: list[dict[str, Any]] = []
        self.current_month: str | None = None
        self.open_start: datetime | None = None
        self.open_market: float | None = None
        self.last_closed: datetime | None = None
        """Start of the last closed quarter: quarters after it up to the next close were missed."""
        self._gap_log: list[dict[str, Any]] = []
        self.fill_version = FILL_VERSION
        self.repaired: dict[str, Any] | None = None
        self._ez_cache: dict[str, dict[datetime, float]] = {}
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
        if "grid_value" not in (data.get("pools") or {"grid_value": 0}) and self.pools.grid_kwh > 0:
            # Before 0.8.83 the pools did not keep what the grid energy cost: start at the mean
            # buy price of the last week (only the energy now in the battery).
            week = summarize(
                self.days, dt_util.now().date() - timedelta(days=7), dt_util.now().date(), self.tariffs.tariffs_for(dt_util.now().date())
            )
            mean = week.as_dict().get("mean_buy_price")
            self.pools.grid_value = self.pools.grid_kwh * float(mean or 0.0)
        self.counters = dict(data.get("counters") or {})
        self.months = list(data.get("months") or [])
        now = dt_util.utcnow()
        await self._load_month(_month_key(now))
        self.last_closed = self._find_last_closed(data.get("last_closed"))
        self.fill_version = int(data.get("fill_version") or 0)
        if self.fill_version < FILL_VERSION:
            if self.fill_version < 1:
                self._repair_history()
            await self._add_solar_values()
            self.fill_version = FILL_VERSION
            await self.async_save()
        self._open(quarter_floor(now))
        unsubs: list[Callable[[], None]] = [
            async_track_time_change(self.hass, self._on_boundary, minute=[0, 15, 30, 45], second=0),
        ]
        if self.runtime.control is not None:
            unsubs.append(self.runtime.control.async_add_listener(self._sample))
        if self.price_entity:
            unsubs.append(async_track_state_change_event(self.hass, [self.price_entity], self._on_price))
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
        flows = self.runtime.cost_flows()
        if flows is None:
            self.meter.sample(now, grid, None)
        else:
            self.meter.sample(now, grid, flows.charge, flows.deliver, flows.solar, flows.complete)

    def _open(self, start: datetime) -> None:
        self.open_start = start
        self.open_market = market_price(price_state(self.hass, self.price_entity), start) if self.price_entity else None

    @callback
    def _on_price(self, _event: Any) -> None:
        self.hass.async_create_task(self._retry_prices(), "zephyr: retry interpolated prices")

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
            market = market_price(price_state(self.hass, self.price_entity), start)
        price_source = "nordpool" if market is not None else None
        missed = self._missed(start)
        since = missed[0] if missed else None
        gap_totals: dict[str, float | None] = {}
        if since is not None and self.import_counters and self.export_counters:
            # The meter counted on while HA was off: from the last boundary before up to now.
            gap_totals["import_kwh"] = self._counter_since(self.import_counters, boundary, since)
            gap_totals["export_kwh"] = self._counter_since(self.export_counters, boundary, since)
        if since is not None and self.solar_entity:
            gap_totals["solar_ext_kwh"] = self._counter_since([self.solar_entity], boundary, since)
        imp, exp = measured.import_kwh, measured.export_kwh
        grid_share = measured.grid_seconds / QUARTER_SECONDS
        if self.import_counters and self.export_counters:
            counted_imp = self._counter_sum(self.import_counters, boundary, start)
            counted_exp = self._counter_sum(self.export_counters, boundary, start)
            if counted_imp is not None and counted_exp is not None:
                imp, exp, grid_share = counted_imp, counted_exp, 1.0
        charge, discharge, set_solar = measured.charge_kwh, measured.discharge_kwh, measured.set_solar_kwh
        corrections, filled = self._gap_corrections(start)
        own = self._own_counters(boundary, start)
        # The coverage follows the source: the own energy counters count the whole quarter, also
        # when the power readings of the set had a gap (0.8.79; before, such a quarter counted
        # as incomplete although its energy was right).
        battery_share = 1.0 if own is not None or not self.runtime.coordinators else measured.battery_seconds / QUARTER_SECONDS
        if own is not None:
            # SPEC-tellers T3: the own energy counters, without what they filled for earlier quarters.
            charge = max(own["charged"] - filled["charged"], 0.0)
            discharge = max(own["discharged"] - filled["discharged"], 0.0)
            set_solar = max(own["solar"] - filled["solar"], 0.0)
        ext: float | None = None
        if self.solar_entity:
            ext = self._counter_sum([self.solar_entity], boundary, start)
        totals = self.runtime.totals()
        local_start = dt_util.as_local(start)
        daylight = is_up(self.hass, start + timedelta(seconds=QUARTER_SECONDS / 2))
        fill = QuarterFill()
        if missed:
            # HA was off: make the missed quarters and fill them (step 2); a counter total over
            # the gap also sets this quarter's part of it.
            rates = {
                "import_kwh": imp / grid_share if grid_share > 0.05 else None,
                "export_kwh": exp / grid_share if grid_share > 0.05 else None,
                "solar_ext_kwh": None if ext is None else ext,
            }
            if self.runtime.energy is None:
                rates["charge_kwh"] = charge / battery_share if battery_share > 0.05 else None
                rates["discharge_kwh"] = discharge / battery_share if battery_share > 0.05 else None
            here = await self._fill_missed(missed, rates, gap_totals)
            for name, kwh in here.items():
                if name == "import_kwh":
                    imp, grid_share = kwh, 1.0
                elif name == "export_kwh":
                    exp = kwh
                elif name == "solar_ext_kwh":
                    ext = kwh
                fill.methods[name] = "scaled"
                fill.added[name] = kwh
            if here:
                fill.causes.append("ha_off")
        if market is None and self.price_entity:
            # No price yet (step 3): between the last and the next known price; replaced by a real
            # one as soon as Nord Pool or EnergyZero has it (``_retry_prices``).
            market, price_source = self._price_for(start)
        # Fill what was not measured (OPDRACHT-onvolledige-kwartieren): neighbours, own rate, history.
        prev = self._record_at(start - timedelta(seconds=QUARTER_SECONDS))
        parts = {
            "import_kwh": (Part(imp, grid_share), "p1", True),
            "export_kwh": (Part(exp, grid_share), "p1", True),
            "charge_kwh": (Part(charge, battery_share), "set", True),
            "discharge_kwh": (Part(discharge, battery_share), "set", True),
        }
        if self.solar_entity:
            parts["solar_ext_kwh"] = (Part(ext or 0.0, 0.0 if ext is None else 1.0), "solar_counter", daylight)
        for name in list(fill.methods):
            parts.pop(name, None)  # set from a counter total over the interruption
        values: dict[str, float] = {"import_kwh": imp, "export_kwh": exp, "charge_kwh": charge, "discharge_kwh": discharge}
        if self.solar_entity and ext is not None:
            values["solar_ext_kwh"] = ext
        basis: dict[str, list[float]] = {}
        for name, (part, cause, allowed) in parts.items():
            done = fill_part(part, neighbour_value(prev, name), None, self._history(start, name), allowed)
            if done is None:
                values[name] = part.kwh
                continue
            values[name] = done.kwh
            fill.methods[name] = done.method
            fill.added[name] = done.added
            fill.causes.append(cause)
            basis[name] = [round(part.kwh, 5), round(part.share, 4)]
        if own is not None and self._gap_here:
            # The set was unreadable for a while: the own counters filled that part (SPEC-tellers T2).
            for name in ("charge_kwh", "discharge_kwh"):
                fill.methods.setdefault(name, "counter")
            fill.causes.append("set")
        imp, exp = values["import_kwh"], values["export_kwh"]
        charge, discharge = values["charge_kwh"], values["discharge_kwh"]
        solar: float | None = None
        if self.solar_entity:
            ext = values["solar_ext_kwh"]
            solar = ext + set_solar
        measured_share = min(grid_share, battery_share, 1.0 if ext is not None or not self.solar_entity else 0.0)
        coverage = measured_share if fill.status == "missing" else 1.0
        pools_before = self.pools.as_dict()
        record = evaluate(
            QuarterInput(
                start=start,
                minutes=QUARTER_SECONDS / 60,
                import_kwh=imp,
                export_kwh=exp,
                charge_kwh=charge,
                discharge_kwh=discharge,
                solar_kwh=solar,
                market=market,
                coverage=coverage,
                stored_kwh=totals.energy_kwh,
                daylight=daylight,
            ),
            self.tariffs.tariffs_for(local_start.date()),
            self.pools,
            _days_in_month(local_start.date()),
        )
        # Inputs kept for a later correction (T3): pools before, energy stored, daylight, coverage.
        record.update(
            {
                "pools": pools_before,
                "stored_kwh": None if totals.energy_kwh is None else round(totals.energy_kwh, 4),
                "daylight": daylight,
                "coverage": round(coverage, 3),
                "measured_share": round(measured_share, 3),
                "battery_source": "counters" if own is not None else "meter",
                **fill.as_record(),
            }
        )
        if self.solar_entity:
            record["solar_ext_kwh"] = None if ext is None else round(ext, 4)
        if price_source is not None:
            record["price_source"] = price_source
            if price_source == "interpolated":
                record.setdefault("fill_causes", [])
                record["fill_causes"] = sorted({*record["fill_causes"], "price"})
        if basis:
            record["fill_basis"] = basis  # to refine the fill once the next quarter is known
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
        self.last_closed = start
        add_to_day(self.days.setdefault(local_start.date().isoformat(), {}), record)
        refine, updates = self._refine_previous(record)
        for quarter, extra in refine.items():
            target = corrections.setdefault(quarter, {})
            for key, kwh in extra.items():
                target[key] = target.get(key, 0.0) + kwh
        if corrections:
            self._correct(corrections, updates)
        self._summaries.clear()
        assert self.current_month is not None
        month_store, quarters = self._month_store(self.current_month), self.current
        month_store.async_delay_save(lambda: {"quarters": quarters}, 30)
        self._main.async_delay_save(self._main_data, 30)
        LOGGER.debug("Cost quarter %s: %s", start.isoformat(), record)
        for listener in list(self._listeners):
            listener()
        if self.price_entity:
            self.hass.async_create_task(self._retry_prices(), "zephyr: retry interpolated prices")
        return record

    # --- filling (OPDRACHT-onvolledige-kwartieren) -----------------------------------------

    async def _add_solar_values(self) -> None:
        """Once: the solar savings split (direct, export, bonus) for the stored quarters, from
        their stored prices and kWh; the day totals get the sums (OPDRACHT-besparing-zon)."""
        from .core.costs import SOLAR_VALUE_FIELDS

        added = 0
        for month in sorted(self.months):
            quarters = (
                self.current
                if month == self.current_month
                else list((await self._month_store(month).async_load() or {}).get("quarters") or [])
            )
            changed = False
            for record in quarters:
                if record.get("cost_no_solar") is None or "solar_direct_value" in record:
                    continue
                buy, sell, market = record.get("buy"), record.get("sell"), record.get("market")
                if buy is None or sell is None or market is None:
                    continue
                local = dt_util.as_local(datetime.fromisoformat(record["start"])).date()
                tariffs = self.tariffs.tariffs_for(local)
                exp_nb = float(record.get("export_no_battery_kwh") or 0.0)
                values = {
                    "solar_direct_value": round(float(record.get("solar_direct_kwh") or 0.0) * float(buy), 5),
                    "solar_export_value": round(exp_nb * float(sell), 5),
                    "solar_bonus_value": round(exp_nb * tariffs.bonus(float(market), bool(record.get("daylight"))), 5),
                }
                record.update(values)
                day = self.days.get(local.isoformat())
                if day is not None and day.get("source") is None:
                    for name in SOLAR_VALUE_FIELDS:
                        day[name] = round(day.get(name, 0.0) + values[name], 5)
                changed = True
                added += 1
            if changed and month != self.current_month:
                await self._month_store(month).async_save({"quarters": quarters})
        if added:
            self._summaries.clear()
            LOGGER.info("Cost log: solar savings split added to %d stored quarters", added)

    def _repair_history(self) -> None:
        """Once (eis 5): fill the stored quarters of this month that were incomplete, make the
        quarters missing between them, and evaluate the month again from the first one touched."""
        records = self.current
        if len(records) < 2 or "pools" not in records[0]:
            return
        step = timedelta(seconds=QUARTER_SECONDS)
        flows = ("import_kwh", "export_kwh", "charge_kwh", "discharge_kwh")
        out: list[dict[str, Any]] = []
        touched: dict[str, dict[str, float]] = {}
        made = filled = 0
        for index, record in enumerate(records):
            if out:
                prev_start = datetime.fromisoformat(out[-1]["start"])
                here = datetime.fromisoformat(record["start"])
                count = int((here - prev_start).total_seconds() // QUARTER_SECONDS) - 1
                if 0 < count <= MAX_GAP_QUARTERS:
                    missed = [prev_start + step * (i + 1) for i in range(count)]
                    daylight = [is_up(self.hass, q + step / 2) for q in missed]
                    after = {f: neighbour_value(record, f) for f in flows}
                    for quarter, fill, day in zip(missed, fill_gap(out[-1], after, count, {}, daylight), daylight, strict=True):
                        new = {
                            "start": quarter.isoformat(),
                            "minutes": QUARTER_SECONDS / 60,
                            **{f: round(fill.values.get(f, 0.0), 4) for f in flows},
                            "solar_kwh": None,
                            "market": None,
                            "pools": record.get("pools"),
                            "stored_kwh": None,
                            "daylight": day,
                            "coverage": 1.0,
                            "measured_share": 0.0,
                            "battery_source": "meter",
                            "soc": None,
                            **fill.as_record(),
                        }
                        prices = interpolate(out[-1].get("market"), record.get("market"), 1)
                        if prices:
                            new["price_source"] = "interpolated"
                        out.append(new)
                        touched[new["start"]] = {"market": prices[0]} if prices else {}
                        made += 1
            if quarter_status(record) == "missing" and "pools" in record and "coverage" in record:
                share = float(record.get("coverage") or 0.0)
                nxt = records[index + 1] if index + 1 < len(records) else None
                prev = out[-1] if out else None
                extra: dict[str, float] = {}
                fields: dict[str, Any] = {}
                fill = QuarterFill(causes=["history"])
                for flow, key in zip(flows, ("import", "export", "charged", "discharged"), strict=True):
                    done = fill_part(Part(float(record.get(flow) or 0.0), share), neighbour_value(prev, flow), neighbour_value(nxt, flow))
                    if done is None or not done.added:
                        continue
                    extra[key] = done.added
                    fill.methods[flow] = done.method
                    fill.added[flow] = done.added
                if extra:
                    fields = {**fill.as_record(), "coverage": 1.0}
                    record = {**record, **fields}
                    touched[record["start"]] = extra
                    filled += 1
            if record.get("market") is None and "pools" in record and "coverage" in record:
                nxt_price = next((r.get("market") for r in records[index + 1 : index + 9] if r.get("market") is not None), None)
                prev_price = next((r.get("market") for r in reversed(out[-8:]) if r.get("market") is not None), None)
                prices = interpolate(prev_price, nxt_price, 1)
                if prices:
                    record = {**record, "price_source": "interpolated"}
                    record["fill_causes"] = sorted({*(record.get("fill_causes") or []), "price"})
                    touched.setdefault(record["start"], {})["market"] = prices[0]
                    filled += 1
            out.append(record)
        if not touched:
            return
        tz = dt_util.get_default_time_zone()
        result = reevaluate(out, touched, self.tariffs.tariffs_for, _days_in_month, tz, dt_util.utcnow().isoformat(timespec="seconds"))
        if result is None:
            LOGGER.debug("Cost log: history fill not possible (quarters from before 0.8.31)")
            return
        self.pools = result[0]
        self.current[:] = out
        days: dict[str, dict[str, Any]] = {}
        for record in out:
            add_to_day(days.setdefault(dt_util.as_local(datetime.fromisoformat(record["start"])).date().isoformat(), {}), record)
        self.days.update(days)
        self.repaired = {"made": made, "filled": filled, "from": min(touched)}
        LOGGER.info("Cost log: history filled once: %d quarters made, %d filled", made, filled)

    def _save_month(self, month: str, quarters: list[dict[str, Any]]) -> None:
        def data() -> dict[str, Any]:
            return {"quarters": quarters}

        self._month_store(month).async_delay_save(data, 30)

    def _price_for(self, start: datetime) -> tuple[float | None, str | None]:
        """A price for a quarter Nord Pool has no price for (step 3): between the last known
        price before and the next one after (the sensor, up to 2 h ahead), else the mean of the
        same quarter over 7 days."""
        before: float | None = None
        for back in range(1, 9):
            record = self._record_at(start - timedelta(seconds=QUARTER_SECONDS * back))
            if record is not None and record.get("market") is not None:
                before = float(record["market"])
                break
        state = price_state(self.hass, self.price_entity) if self.price_entity else None
        after = next(
            (p for p in (market_price(state, start + timedelta(seconds=QUARTER_SECONDS * i)) for i in range(1, 9)) if p is not None),
            None,
        )
        values = interpolate(before, after, 1)
        if values:
            return values[0], "interpolated"
        history = [self._record_at(start - timedelta(days=d)) for d in range(1, 8)]
        known = [float(r["market"]) for r in history if r is not None and r.get("market") is not None]
        if known:
            return sum(known) / len(known), "interpolated"
        return None, None

    async def _retry_prices(self, _event: Any = None) -> None:
        """Replace interpolated prices by real ones: Nord Pool, after an hour EnergyZero (step 3)."""
        now = dt_util.utcnow()
        oldest = (now - MAX_CORRECTION_AGE).isoformat()
        waiting = [r for r in self.current if r.get("price_source") == "interpolated" and r.get("start", "") >= oldest]
        if not waiting:
            return
        state = price_state(self.hass, self.price_entity) if self.price_entity else None
        corrections: dict[str, dict[str, float]] = {}
        updates: dict[str, dict[str, Any]] = {}
        for record in waiting:
            start = datetime.fromisoformat(record["start"])
            price, source = market_price(state, start), "nordpool"
            if price is None and now - start >= timedelta(hours=1):
                price, source = await self._energyzero_hour(start), "energyzero"
            if price is None:
                continue
            corrections[record["start"]] = {"market": price}
            causes = [c for c in record.get("fill_causes") or [] if c != "price"]
            updates[record["start"]] = {"price_source": source, "fill_causes": causes}
        if corrections and self._correct(corrections, updates):
            self._summaries.clear()
            assert self.current_month is not None
            self._save_month(self.current_month, self.current)
            self._main.async_delay_save(self._main_data, 30)
            LOGGER.debug("Cost log: %d interpolated prices replaced", len(corrections))
            for listener in list(self._listeners):
                listener()

    async def _energyzero_hour(self, start: datetime) -> float | None:
        """EnergyZero's price for the hour of ``start`` (one request per day and hour of the clock)."""
        tz = dt_util.get_default_time_zone()
        day = dt_util.as_local(start).date()
        key = f"{day.isoformat()}@{dt_util.utcnow().strftime('%Y-%m-%dT%H')}"
        if key not in self._ez_cache:
            self._ez_cache = {k: v for k, v in self._ez_cache.items() if k.startswith(day.isoformat())}
            prices, _failed = await self._energyzero(day, day + timedelta(days=1), tz)
            self._ez_cache[key] = prices
        hour = dt_util.as_utc(start).replace(minute=0)
        return self._ez_cache[key].get(hour)

    def _missed(self, start: datetime) -> list[datetime]:
        """Quarter starts between the last closed quarter and ``start`` (HA was off)."""
        if self.last_closed is None:
            return []
        first = self.last_closed + timedelta(seconds=QUARTER_SECONDS)
        count = int((start - first).total_seconds() // QUARTER_SECONDS)
        if count <= 0:
            return []
        if count > MAX_GAP_QUARTERS:
            LOGGER.warning("Cost log: %d quarters missed (more than a month): not filled", count)
            self._gap_log.append({"start": first.isoformat(), "quarters": count, "filled": False})
            return []
        return [first + timedelta(seconds=QUARTER_SECONDS * i) for i in range(count)]

    def _counter_since(self, entities: Iterable[str], boundary: datetime, since: datetime) -> float | None:
        """Counter difference from the boundary ``since`` (stored before HA went off) up to now."""
        total = 0.0
        for entity in entities:
            stored = self.counters.get(entity)
            reading = _counter_kwh(self.hass.states.get(entity))
            if not stored or stored[0] != since.isoformat() or reading is None:
                return None
            delta = counter_delta(stored[1], reading)
            if delta is None:
                return None
            total += delta
        return total

    async def _fill_missed(
        self, missed: list[datetime], rates: Mapping[str, float | None], totals: Mapping[str, float | None]
    ) -> dict[str, float]:
        """Make the quarters HA missed, filled (step 2), and return this quarter's share of a counter
        total over the interruption (which runs up to the end of this quarter)."""
        count = len(missed)
        before = self._record_at(missed[0] - timedelta(seconds=QUARTER_SECONDS))
        daylight = [is_up(self.hass, q + timedelta(seconds=QUARTER_SECONDS / 2)) for q in missed]
        here: dict[str, float] = {}
        gap_totals: dict[str, float | None] = {}
        for flow, total in totals.items():
            if total is None:
                continue
            spread = interpolate(neighbour_value(before, flow), rates.get(flow), count) or [0.0] * count
            last = rates.get(flow)
            last = spread[-1] if last is None and spread else (last or 0.0)
            if flow == "solar_ext_kwh":
                spread = [v if day else 0.0 for v, day in zip(spread, daylight, strict=True)]
            shares = scale_to([*spread, last], total)
            gap_totals[flow], here[flow] = sum(shares[:-1]), shares[-1]
        after = {flow: rates.get(flow) for flow in ("import_kwh", "export_kwh", "charge_kwh", "discharge_kwh", "solar_ext_kwh")}
        if self.runtime.energy is not None:
            # The own counters fill the battery over a restart (T2); their gap lands in these quarters.
            after.pop("charge_kwh")
            after.pop("discharge_kwh")
        if not self.solar_entity:
            after.pop("solar_ext_kwh")
        history = [{f: self._history(q, f) for f in after} for q in missed]
        fills = fill_gap(before, after, count, gap_totals, daylight, history)
        state = price_state(self.hass, self.price_entity) if self.price_entity else None
        for quarter, fill, day in zip(missed, fills, daylight, strict=True):
            v = fill.values
            if self.runtime.energy is not None:
                fill.methods.setdefault("charge_kwh", "counter")
                fill.methods.setdefault("discharge_kwh", "counter")
            ext = v.get("solar_ext_kwh") if self.solar_entity else None
            local = dt_util.as_local(quarter)
            market = market_price(state, quarter)
            source = "nordpool" if market is not None else None
            if market is None and self.price_entity:
                market, source = self._price_for(quarter)
            pools_before = self.pools.as_dict()
            record = evaluate(
                QuarterInput(
                    start=quarter,
                    minutes=QUARTER_SECONDS / 60,
                    import_kwh=v.get("import_kwh", 0.0),
                    export_kwh=v.get("export_kwh", 0.0),
                    charge_kwh=v.get("charge_kwh", 0.0),
                    discharge_kwh=v.get("discharge_kwh", 0.0),
                    solar_kwh=ext,
                    market=market,
                    coverage=0.0 if fill.status == "missing" else 1.0,
                    stored_kwh=None,
                    daylight=day,
                ),
                self.tariffs.tariffs_for(local.date()),
                self.pools,
                _days_in_month(local.date()),
            )
            record.update(
                {
                    "pools": pools_before,
                    "stored_kwh": None,
                    "daylight": day,
                    "coverage": 0.0 if fill.status == "missing" else 1.0,
                    "measured_share": 0.0,
                    "battery_source": "counters" if self.runtime.energy is not None else "meter",
                    "soc": None,
                    **fill.as_record(),
                }
            )
            if self.solar_entity:
                record["solar_ext_kwh"] = None if ext is None else round(ext, 4)
            if source is not None:
                record["price_source"] = source
            await self._load_month(_month_key(quarter))
            self.current.append(record)
            add_to_day(self.days.setdefault(local.date().isoformat(), {}), record)
            self._save_month(_month_key(quarter), self.current)
            self.last_closed = quarter
        self._gap_log.append({"start": missed[0].isoformat(), "quarters": count, "filled": True, "counters": sorted(gap_totals)})
        self._gap_log = self._gap_log[-20:]
        LOGGER.info("Cost log: %d quarters missed while Home Assistant was off, filled", count)
        return here

    def _record_at(self, start: datetime) -> dict[str, Any] | None:
        """The stored quarter that starts at ``start`` (current month, searched from the end)."""
        key = dt_util.as_utc(start).isoformat()
        low, high = 0, len(self.current)
        while low < high:  # the quarters are in time order
            mid = (low + high) // 2
            if str(self.current[mid].get("start", "")) < key:
                low = mid + 1
            else:
                high = mid
        if low < len(self.current) and self.current[low].get("start") == key:
            found: dict[str, Any] = self.current[low]
            return found
        return None

    def _history(self, start: datetime, flow: str) -> float | None:
        """Mean of a flow at the same time of day over the last 7 days (guess without neighbours)."""
        records = [self._record_at(start - timedelta(days=d)) for d in range(1, 8)]
        return history_mean([r for r in records if r is not None], flow)

    def _refine_previous(self, record: Mapping[str, Any]) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, Any]]]:
        """The quarter before ``record`` was filled with its own rate standing in for the next
        quarter; now that is known: fill it again between its real neighbours. Returns the
        corrections (kWh to add per flow) for ``reevaluate`` and the fill fields to set afterwards."""
        start = datetime.fromisoformat(record["start"])
        prev = self._record_at(start - timedelta(seconds=QUARTER_SECONDS))
        if prev is None or not prev.get("fill_basis"):
            return {}, {}
        before = self._record_at(start - timedelta(seconds=2 * QUARTER_SECONDS))
        keys = {"import_kwh": "import", "export_kwh": "export", "charge_kwh": "charged", "discharge_kwh": "discharged"}
        out: dict[str, float] = {}
        fill_kwh = dict(prev.get("fill_kwh") or {})
        methods = dict(prev.get("fill") or {})
        fields: dict[str, Any] = {}
        for name, (kwh, share) in prev["fill_basis"].items():
            if share >= FULL_SHARE or prev.get("fill", {}).get(name) not in ("interpolated", "own_rate"):
                continue
            rates = interpolate(neighbour_value(before, name), neighbour_value(record, name), 1)
            if not rates:
                continue
            if name == "solar_ext_kwh" and not prev.get("daylight"):
                continue
            new_total = float(kwh) + max(rates[0], 0.0) * (1.0 - float(share))
            old_total = float(prev.get(name) or 0.0)
            delta = new_total - old_total
            if abs(delta) < 1e-4:
                continue
            out[keys.get(name, "solar")] = delta
            fill_kwh[name] = round(new_total - float(kwh), 4)
            if name == "solar_ext_kwh":
                fields["solar_ext_kwh"] = round(new_total, 4)
            methods[name] = "interpolated"
        prev.pop("fill_basis", None)  # refined once
        if not out:
            return {}, {}
        fields.update({"fill_kwh": fill_kwh, "fill": methods})
        return {prev["start"]: out}, {prev["start"]: fields}

    # --- own energy counters and corrections (SPEC-tellers T3) ---------------------------

    def _own_counters(self, boundary: datetime, previous: datetime) -> dict[str, float] | None:
        """Deltas of the installation's own energy counters since ``previous``; None without a reading then."""
        energy = self.runtime.energy
        if energy is None:
            return None
        out: dict[str, float] | None = {}
        for key in ENERGY_TOTAL_KEYS:
            reading = energy.counters.totals[key]
            stored = self.counters.get(f"zephyr:{key}")
            self.counters[f"zephyr:{key}"] = [boundary.isoformat(), reading]
            if out is None or not stored or stored[0] != previous.isoformat():
                out = None
                continue
            out[key] = max(reading - float(stored[1]), 0.0)
        return out

    def _gap_corrections(self, start: datetime) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
        """Spread the gaps filled since the last close over their quarters.

        Returns the extra kWh per closed quarter (ISO start; only gaps that began less than
        48 h ago) and the total filled for quarters before ``start`` (taken out of this
        quarter's counter delta, also for older gaps).
        """
        corrections: dict[str, dict[str, float]] = {}
        filled = dict.fromkeys(ENERGY_TOTAL_KEYS, 0.0)
        self._gap_here = False
        energy = self.runtime.energy
        if energy is None:
            return corrections, filled
        for gap in energy.take_gaps():
            if not gap.get("start") or not gap.get("end"):
                continue
            gap_start, gap_end = datetime.fromisoformat(gap["start"]), datetime.fromisoformat(gap["end"])
            recent = start - gap_start <= MAX_CORRECTION_AGE
            for quarter, share in gap_shares(gap_start, gap_end).items():
                if quarter >= start:
                    self._gap_here = True  # this quarter: the counter delta already holds it (estimated)
                    continue
                for key in ENERGY_TOTAL_KEYS:
                    kwh = float(gap["kwh"].get(key, 0.0)) * share
                    if kwh <= 0:
                        continue
                    filled[key] += kwh
                    if recent:
                        extra = corrections.setdefault(quarter.isoformat(), {})
                        extra[key] = extra.get(key, 0.0) + kwh
            self._corrections_log.append(
                {"start": gap["start"], "end": gap["end"], "method": gap.get("method"), "kwh": gap["kwh"], "corrected": recent}
            )
        self._corrections_log = self._corrections_log[-20:]
        return corrections, filled

    def _correct(self, corrections: dict[str, dict[str, float]], updates: Mapping[str, Mapping[str, Any]]) -> bool:
        """Evaluate again with ``corrections`` and then set ``updates`` (fields per quarter)."""
        if not self._apply_corrections(corrections):
            return False
        for quarter, fields in updates.items():
            stored = self._record_at(datetime.fromisoformat(quarter))
            if stored is None:
                continue
            before = dict(stored)
            stored.update(fields)
            stored.pop("fill_basis", None)
            day = dt_util.as_local(datetime.fromisoformat(quarter)).date().isoformat()
            day_delta(self.days.setdefault(day, {}), before, stored)
        return True

    def _apply_corrections(self, corrections: dict[str, dict[str, float]]) -> bool:
        """Evaluate the current month again from the first corrected quarter; update days and pools."""
        tz = dt_util.get_default_time_zone()
        result = reevaluate(
            self.current,
            corrections,
            self.tariffs.tariffs_for,
            _days_in_month,
            tz,
            dt_util.utcnow().isoformat(timespec="seconds"),
        )
        if result is None:
            LOGGER.debug("Cost log: gap correction not possible (quarters missing or from before 0.8.31): %s", corrections)
            return False
        self.pools, changes = result
        touched: set[str] = set()
        for old, new in changes:
            day = dt_util.as_local(datetime.fromisoformat(new["start"])).date().isoformat()
            day_delta(self.days.setdefault(day, {}), old, new)
            touched.add(day)
        for day in touched:  # the battery's content at the day's start and end (0.8.83)
            refresh_content(
                self.days[day],
                (r for r in self.current if dt_util.as_local(datetime.fromisoformat(r["start"])).date().isoformat() == day),
            )
        LOGGER.debug("Cost log: %d quarters evaluated again after a gap", len(changes))
        return True

    def records_since(self, start: datetime) -> dict[datetime, dict[str, Any]]:
        """Stored quarters of the current month from ``start`` on, by start time (UTC); for the panel."""
        out: dict[datetime, dict[str, Any]] = {}
        for record in self.current:
            moment = dt_util.as_utc(datetime.fromisoformat(record["start"]))
            if moment >= start:
                out[moment] = record
        return out

    def _main_data(self) -> dict[str, Any]:
        return {
            "days": self.days,
            "pools": self.pools.as_dict(),
            "counters": self.counters,
            "months": self.months,
            "last_closed": None if self.last_closed is None else self.last_closed.isoformat(),
            "fill_version": self.fill_version,
        }

    def _find_last_closed(self, stored: Any) -> datetime | None:
        """The last closed quarter: stored (0.8.80), else the last quarter of the month, else the
        last counter boundary (an interruption over the turn of a month)."""
        if isinstance(stored, str):
            return dt_util.as_utc(datetime.fromisoformat(stored))
        if self.current:
            return dt_util.as_utc(datetime.fromisoformat(self.current[-1]["start"]))
        boundaries = [v[0] for v in self.counters.values() if isinstance(v, list) and v and isinstance(v[0], str)]
        if boundaries:
            return dt_util.as_utc(datetime.fromisoformat(max(boundaries))) - timedelta(seconds=QUARTER_SECONDS)
        return None

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

    # --- savings before the cost log (from hourly statistics) ------------------------

    @property
    def measured_since(self) -> str | None:
        """First day the cost log measured itself (not worked out afterwards)."""
        measured = [k for k, v in self.days.items() if v.get("source") is None]
        return min(measured) if measured else None

    async def async_backfill(
        self, first: date, charge_entity: str, discharge_entity: str, solar_entity: str | None, price_entity: str | None
    ) -> dict[str, Any]:
        """Work out the days from ``first`` up to the cost log again from hourly statistics (replaces an earlier run)."""
        from .core.backfill import PRICE_ENERGYZERO, SOURCE_HOURLY, backfill_days, series_to_hours
        from .planner_runner import hourly_statistics

        tz = dt_util.get_default_time_zone()
        since = self.measured_since
        end_day = date.fromisoformat(since) if since else dt_util.now().date()
        if first >= end_day:
            return {"days": 0, "hours": 0, "skipped": 0, "priced_hours": 0, "first": None, "last": None}
        start = datetime.combine(first, datetime.min.time(), tz)
        end = datetime.combine(end_day, datetime.min.time(), tz)
        counters = [*self.import_counters, *self.export_counters, charge_entity, discharge_entity]
        from_sensor = price_entity if price_entity and price_entity != PRICE_ENERGYZERO else None
        ids = [*counters, *([solar_entity] if solar_entity else []), *([from_sensor] if from_sensor else [])]
        stats = await hourly_statistics(self.hass, start, end, list(dict.fromkeys(ids)))

        series: dict[str, dict[datetime, float]] = {}
        for entity in ids:
            field = "mean" if entity == price_entity else "change"
            rows: dict[datetime, float] = {}
            for row in stats.get(entity, []):
                value, begin = row.get(field), row.get("start")
                if value is None or begin is None:
                    continue
                moment = begin if isinstance(begin, datetime) else datetime.fromtimestamp(float(begin), UTC)
                rows[dt_util.as_utc(moment)] = float(value)
            series[entity] = rows
        failed_days = 0
        if price_entity == PRICE_ENERGYZERO:
            series[PRICE_ENERGYZERO], failed_days = await self._energyzero(first, end_day, tz)

        starts = []
        t = dt_util.as_utc(start)
        while t < dt_util.as_utc(end):
            starts.append(t)
            t += timedelta(hours=1)
        hours = series_to_hours(
            starts,
            series,
            self.import_counters,
            self.export_counters,
            lambda moment: series[charge_entity].get(moment),
            lambda moment: series[discharge_entity].get(moment),
            solar_entity,
            price_entity,
        )
        result = backfill_days(hours, self.tariffs.tariffs_for, tz)
        self.days = {k: v for k, v in self.days.items() if v.get("source") != SOURCE_HOURLY}
        for key, day in result.days.items():
            if since is None or key < since:
                self.days[key] = day
        self._summaries.clear()
        await self._main.async_save(self._main_data())
        keys = sorted(result.days)
        return {
            "days": len(keys),
            "hours": result.hours,
            "skipped": result.skipped,
            "priced_hours": sum(1 for h in hours if h.market is not None and h.import_kwh is not None),
            "first": keys[0] if keys else None,
            "last": keys[-1] if keys else None,
            "price_failed_days": failed_days,
        }

    async def _energyzero(self, first: date, end_day: date, tz: Any) -> tuple[dict[datetime, float], int]:
        """Market prices per hour from EnergyZero, one request per day (small, and one bad day does not stop the rest)."""
        import aiohttp
        from homeassistant.helpers.aiohttp_client import async_get_clientsession

        from .core.backfill import ENERGYZERO_URL, energyzero_params, energyzero_prices

        session = async_get_clientsession(self.hass)
        prices: dict[datetime, float] = {}
        failed = 0
        day = first
        while day < end_day:
            start = datetime.combine(day, datetime.min.time(), tz)
            stop = datetime.combine(day + timedelta(days=1), datetime.min.time(), tz) - timedelta(milliseconds=1)
            try:
                async with session.get(
                    ENERGYZERO_URL, params=energyzero_params(start, stop), timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    response.raise_for_status()
                    found = energyzero_prices(await response.json(content_type=None))
            except (aiohttp.ClientError, TimeoutError, ValueError) as err:
                LOGGER.warning("EnergyZero prices for %s not available: %s", day, err)
                found = {}
            if not found:
                failed += 1
            prices.update(found)
            day += timedelta(days=1)
        return prices, failed

    async def async_clear_backfill(self) -> int:
        """Remove the days worked out afterwards."""
        from .core.backfill import SOURCE_HOURLY

        before = len(self.days)
        self.days = {k: v for k, v in self.days.items() if v.get("source") != SOURCE_HOURLY}
        self._summaries.clear()
        await self._main.async_save(self._main_data())
        return before - len(self.days)

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

    def _fill_by_day(self, count: int) -> dict[str, dict[str, Any]]:
        """Per day: quarters measured, estimated and missing, by cause and method, and the kWh added."""
        out: dict[str, dict[str, Any]] = {}
        for key in sorted(self.days)[-count:]:
            day = self.days[key]
            quarters = int(day.get("quarters", 0))
            estimated, missing = int(day.get("estimated", 0)), int(day.get("incomplete", 0))
            out[key] = {
                "measured": quarters - estimated - missing,
                "estimated": estimated,
                "missing": missing,
                "without_price": int(day.get("no_price", 0)),
                "price_interpolated": int(day.get("price_interpolated", 0)),
                "causes": {k[6:]: v for k, v in day.items() if k.startswith("cause_")},
                "methods": {k[7:]: v for k, v in day.items() if k.startswith("method_")},
                "filled_kwh": {k[7:]: round(v, 3) for k, v in day.items() if k.startswith("filled_")},
            }
        return out

    def energy_balance(self, days: int = 7) -> list[dict[str, Any]]:
        """Per day: charged × η − delivered against the change of the battery's energy (diagnostics)."""
        from .core.cost_checks import energy_balance

        tz = dt_util.get_default_time_zone()
        first = (dt_util.now().date() - timedelta(days=days - 1)).isoformat()
        records = [r for r in self.current if dt_util.as_local(datetime.fromisoformat(r["start"])).date().isoformat() >= first]
        totals = self.runtime.totals()
        eta_in = eta_out = 0.93
        planner = self.runtime.planner
        battery = (planner.inputs or {}).get("battery") if planner is not None else None
        if isinstance(battery, Mapping):
            eta_in, eta_out = float(battery.get("eta_in", eta_in)), float(battery.get("eta_out", eta_out))
        return energy_balance(records, totals.capacity_kwh, eta_in, eta_out, tz)

    async def async_price_check(self, days: int = 2) -> dict[str, Any]:
        """Quarter prices of the last days against EnergyZero's hour prices (diagnostics)."""
        from .core.cost_checks import price_check

        tz = dt_util.get_default_time_zone()
        today = dt_util.now().date()
        first = today - timedelta(days=days - 1)
        records = [r for r in self.current if dt_util.as_local(datetime.fromisoformat(r["start"])).date() >= first]
        key = f"check@{dt_util.utcnow().strftime('%Y-%m-%dT%H')}"
        if key not in self._ez_cache:
            self._ez_cache = {k: v for k, v in self._ez_cache.items() if not k.startswith("check@")}
            self._ez_cache[key], _failed = await self._energyzero(first, today + timedelta(days=1), tz)
        hourly = self._ez_cache[key]
        return {"hours_compared": len(hourly), "deviations": price_check(records, hourly)}

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
            "gap_corrections": self._corrections_log[-10:],
            "fill_by_day": self._fill_by_day(7),
            "energy_balance": self.energy_balance(7),
            "missed_quarters": self._gap_log[-10:],
            "history_filled": self.repaired,
            "last_closed": None if self.last_closed is None else self.last_closed.isoformat(),
            "plan_check": self.plan_check(7),
        }
