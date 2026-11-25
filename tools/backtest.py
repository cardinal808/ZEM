"""Backtest of the planner on real data (SPEC-planner §12.2).

Usage (data files stay private, B18):

    python tools/backtest.py --prices prijzen.csv --p1 p1-uur.csv --solar zon.csv \
        [--battery accu-uur.csv] [--capacity 9.38] [--supplier zonneplan]

* prices: quarter prices, ``;``-separated with a decimal comma (``datum_nl;datum_utc;prijs_excl_belastingen``);
* p1: grid import/export per hour (``uur_utc,afname_kwh,teruglevering_kwh``);
* solar: Home Assistant history of a production counter (``entity_id,state,last_changed``);
* battery (optional): battery charged/delivered per hour (``uur_utc,geladen_kwh,geleverd_kwh``),
  needed to derive the house consumption while a battery was present.

House consumption per hour = import − export + solar − charged + delivered, spread
evenly over the quarters. The strategies are simulated quarter by quarter with the
same energy model as the planner (``core/planner.step``), with perfect knowledge of
consumption and solar (the yardstick; forecast errors come later, §12.4), and with
the price horizon as in practice: the next day's prices from 13:00 local time,
before that today's pattern as an indicative tomorrow (§2.1).

Each strategy is computed with net metering (2026 rules) and without (2027 rules).
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import sim  # noqa: E402,F401  (loads the core as zephyr_core)
from zephyr_core.costs import Tariffs  # noqa: E402
from zephyr_core.planner import Action, Battery, PlannerSettings, Slot, plan, step  # noqa: E402
from zephyr_core.tariff_table import parse_table  # noqa: E402

TZ = ZoneInfo("Europe/Amsterdam")
Q = timedelta(minutes=15)
H = timedelta(hours=1)


def _utc(text: str) -> datetime:
    text = text.strip().strip('"').replace("Z", "+00:00")
    if "T" not in text:
        text = text.replace(" ", "T")
    value = datetime.fromisoformat(text)
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def read_prices(path: Path) -> dict[datetime, float]:
    out = {}
    with path.open(encoding="utf-8") as fh:
        reader = csv.reader(fh, delimiter=";")
        next(reader)
        for _nl, utc, price in reader:
            out[_utc(utc)] = float(price.replace(",", "."))
    return out


def read_hourly(path: Path) -> dict[datetime, tuple[float, float]]:
    out = {}
    with path.open(encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader)
        for hour, a, b in reader:
            out[_utc(hour)] = (float(a), float(b))
    return out


def read_counter_hourly(path: Path) -> dict[datetime, float]:
    """kWh per hour from a counter history (linear between readings, drops ignored)."""
    points = []
    with path.open(encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader)
        for _entity, state, changed in reader:
            try:
                points.append((_utc(changed), float(state)))
            except ValueError:
                continue
    points.sort()
    at: dict[datetime, float] = {}
    for (t0, v0), (t1, v1) in itertools.pairwise(points):
        if v1 < v0:
            continue
        hour = t0.replace(minute=0, second=0, microsecond=0) + H
        while hour <= t1:
            at[hour] = v0 + (v1 - v0) * (hour - t0).total_seconds() / max((t1 - t0).total_seconds(), 1)
            hour += H
    return {h: at[h + H] - at[h] for h in at if h + H in at and at[h + H] >= at[h]}


@dataclass(slots=True)
class Quarter:
    start: datetime
    market: float
    load: float
    solar: float


def build_quarters(prices: Path, p1: Path, solar: Path, battery: Path | None) -> list[Quarter]:
    price = read_prices(prices)
    grid = read_hourly(p1)
    sun = read_counter_hourly(solar)
    bat = read_hourly(battery) if battery else {}
    first = max(min(grid), min(sun))
    last = min(max(grid), max(sun))
    out: list[Quarter] = []
    hour = first
    while hour <= last:
        if hour in grid and hour in sun:
            imp, exp = grid[hour]
            chg, dis = bat.get(hour, (0.0, 0.0))
            load = max(imp - exp + sun[hour] - chg + dis, 0.0)
            for k in range(4):
                start = hour + k * Q
                if start in price:
                    out.append(Quarter(start, price[start], load / 4, sun[hour] / 4))
        hour += H
    return out


@dataclass(slots=True)
class Result:
    name: str
    cost: float = 0.0
    grid_import: float = 0.0
    grid_export: float = 0.0
    grid_charged: float = 0.0
    charge_starts: int = 0
    saldering_part: float = 0.0
    battery_out: float = 0.0

    def total(self) -> float:
        """Cost including the yearly net-metering correction (export above import loses its netting part)."""
        if self.saldering_part and self.grid_export > self.grid_import:
            return self.cost + (self.grid_export - self.grid_import) / self.grid_export * self.saldering_part
        return self.cost


Strategy = Callable[[list[Quarter], int, float, Action], Action]


def simulate(name: str, quarters: list[Quarter], tariffs: Tariffs, battery: Battery | None, choose: Strategy | None) -> Result:
    res = Result(name)
    energy = battery.capacity_kwh / 2 if battery else 0.0
    prev = Action.DELIVER
    for i, q in enumerate(quarters):
        daylight = q.solar > 0
        buy = tariffs.buy(q.market)
        sell, part = tariffs.sell(q.market, q.start, daylight)
        slot = Slot(0.25, buy, sell, q.load, q.solar)
        if battery is None:
            net = q.load - q.solar
            imp, exp = max(net, 0.0), max(-net, 0.0)
            res.cost += imp * buy - exp * (sell if sell > 0 else 0.0)
        else:
            assert choose is not None
            action = choose(quarters, i, energy, prev)
            r = step(slot, battery, energy, action)
            if action is Action.CHARGE and prev is not Action.CHARGE:
                res.charge_starts += 1
            if action is Action.CHARGE:
                res.grid_charged += max(r.charged - q.solar, 0.0)
            imp, exp = r.grid_import, r.grid_export
            res.cost += r.cost
            res.battery_out += r.delivered
            energy, prev = r.energy_after, action
        res.grid_import += imp
        res.grid_export += exp
        res.saldering_part += exp * part
    return res


def planner_strategy(tariffs: Tariffs, battery: Battery, cfg: PlannerSettings) -> Strategy:
    """Replans when new prices come (13:00 local) and when the plan runs out."""
    cache: dict[str, object] = {"start": -1, "actions": []}

    def horizon(quarters: list[Quarter], i: int) -> list[Slot]:
        now = quarters[i].start.astimezone(TZ)
        known_until = now.date() + timedelta(days=2 if now.hour >= 13 else 1)
        slots: list[Slot] = []
        by_start = {q.start: q for q in quarters[i : i + 200]}
        j = i
        while j < len(quarters) and quarters[j].start.astimezone(TZ).date() < known_until:
            q = quarters[j]
            sell, _ = tariffs.sell(q.market, q.start, q.solar > 0)
            slots.append(Slot(0.25, tariffs.buy(q.market), sell, q.load, q.solar))
            j += 1
        if now.hour < 13:
            # Tomorrow unknown: today's pattern as indicative prices, real consumption and solar.
            while j < len(quarters) and quarters[j].start.astimezone(TZ).date() < known_until + timedelta(days=1):
                q = quarters[j]
                same = by_start.get(q.start - timedelta(days=1))
                market = same.market if same else q.market
                sell, _ = tariffs.sell(market, q.start, q.solar > 0)
                slots.append(Slot(0.25, tariffs.buy(market), sell, q.load, q.solar))
                j += 1
        return slots

    def choose(quarters: list[Quarter], i: int, energy: float, prev: Action) -> Action:
        local = quarters[i].start.astimezone(TZ)
        start = int(cache["start"])  # type: ignore[call-overload]
        actions: list[Action] = cache["actions"]  # type: ignore[assignment]
        if start < 0 or i - start >= len(actions) or (local.hour == 13 and local.minute == 0):
            result = plan(horizon(quarters, i), battery, energy, cfg, prev)
            cache["start"], cache["actions"] = i, result.actions
            start, actions = i, result.actions
        return actions[i - start]

    return choose


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--p1", type=Path, required=True)
    ap.add_argument("--solar", type=Path, required=True)
    ap.add_argument("--battery", type=Path)
    ap.add_argument("--capacity", type=float, default=9.38, help="usable kWh between min and max SOC")
    ap.add_argument("--power", type=float, default=2.4, help="kW charge and deliver")
    ap.add_argument("--eta", type=float, default=0.93, help="efficiency per direction")
    ap.add_argument("--supplier", default="zonneplan")
    args = ap.parse_args(argv)

    quarters = build_quarters(args.prices, args.p1, args.solar, args.battery)
    table = parse_table(json.loads((ROOT / "custom_components/zephyr/data/tariffs.json").read_text(encoding="utf-8")))
    day = quarters[0].start.date()
    base = table.tariffs(args.supplier, max(day, date(2026, 1, 1)))
    assert base is not None, f"supplier {args.supplier} not in the table"
    battery = Battery(args.capacity, args.power, args.power, args.eta, args.eta)
    load = sum(q.load for q in quarters)
    solar = sum(q.solar for q in quarters)
    print(
        f"{quarters[0].start:%Y-%m-%d} – {quarters[-1].start:%Y-%m-%d}: {len(quarters)} quarters, "
        f"house {load:.0f} kWh, solar {solar:.0f} kWh, battery {args.capacity} kWh / {args.power} kW, η {args.eta}"
    )
    rules = {"2026 (net metering)": base, "2027 (no net metering)": replace(base, saldering_until=date(2000, 1, 1))}
    for label, tariffs in rules.items():
        print(f"\n{label}, {base.source}")
        with_x = PlannerSettings(allow_export=True)
        runs = [
            simulate("no battery", quarters, tariffs, None, None),
            simulate("zero meter (N always)", quarters, tariffs, battery, lambda *_: Action.DELIVER),
            simulate("planner", quarters, tariffs, battery, planner_strategy(tariffs, battery, PlannerSettings())),
            simulate("planner + export (X)", quarters, tariffs, battery, planner_strategy(tariffs, battery, with_x)),
        ]
        ref = runs[0].total()
        print(f"  {'strategy':24} {'cost €':>9} {'saving €':>9} {'import':>8} {'export':>8} {'grid→bat':>9} {'bat out':>8} {'starts':>7}")
        for r in runs:
            print(
                f"  {r.name:24} {r.total():9.2f} {ref - r.total():9.2f} {r.grid_import:8.0f} {r.grid_export:8.0f} "
                f"{r.grid_charged:9.0f} {r.battery_out:8.0f} {r.charge_starts:7d}"
            )


if __name__ == "__main__":
    main()
