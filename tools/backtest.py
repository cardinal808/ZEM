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
from zephyr_core.load_profile import WEEKEND, WORKDAY, LoadProfile  # noqa: E402
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


class Forecaster:
    """What the planner knows about consumption and solar (SPEC-planner §2.2, §2.3).

    * ``perfect``: the real values (yardstick);
    * ``learned`` load: the learned profile per hour (workday/weekend) with steering, learned online;
    * ``yesterday`` solar: the solar of the same quarter one day earlier (a simple, pessimistic stand-in
      for a forecast; a real forecast such as Solcast should do better).
    """

    def __init__(self, quarters: list[Quarter], load: str, solar: str) -> None:
        self.quarters = quarters
        self.load_mode, self.solar_mode = load, solar
        self.profile = LoadProfile()
        self.by_start = {q.start: q for q in quarters}
        self._learned_until = 0
        self._hour_kwh = 0.0

    @property
    def perfect(self) -> bool:
        return self.load_mode == "perfect" and self.solar_mode == "perfect"

    @staticmethod
    def day_type(local: datetime) -> str:
        return WEEKEND if local.weekday() >= 5 else WORKDAY

    def learn_until(self, i: int) -> None:
        """Feed the measured quarters before ``i`` into the profile (per full hour)."""
        while self._learned_until < i:
            q = self.quarters[self._learned_until]
            self._hour_kwh += q.load
            local = q.start.astimezone(TZ)
            if local.minute == 45:
                self.profile.learn(self.day_type(local), local.hour, self._hour_kwh)
                self._hour_kwh = 0.0
            self._learned_until += 1

    def load(self, i: int, j: int) -> float:
        q = self.quarters[j]
        if self.load_mode == "perfect":
            return q.load
        local = q.start.astimezone(TZ)
        ahead = (q.start - self.quarters[i].start).total_seconds() / 3600
        return self.profile.forecast(self.day_type(local), local.hour, ahead) / 4

    def solar(self, i: int, j: int) -> float:
        q = self.quarters[j]
        if self.solar_mode == "perfect" or j == i:
            return q.solar  # the running quarter: the controller follows the real solar
        yesterday = self.by_start.get(q.start - timedelta(days=1))
        return yesterday.solar if yesterday else q.solar


def planner_strategy(tariffs: Tariffs, battery: Battery, cfg: PlannerSettings, forecaster: Forecaster | None = None) -> Strategy:
    """Replans when new prices come (13:00 local), when the plan runs out and, with forecasts, every hour."""
    cache: dict[str, object] = {"start": -1, "actions": []}

    def horizon(quarters: list[Quarter], i: int) -> list[Slot]:
        now = quarters[i].start.astimezone(TZ)
        known_until = now.date() + timedelta(days=2 if now.hour >= 13 else 1)
        slots: list[Slot] = []
        by_start = {q.start: q for q in quarters[max(i - 100, 0) : i + 200]}

        def known(j: int) -> tuple[float, float]:
            if forecaster is None:
                return quarters[j].load, quarters[j].solar
            return forecaster.load(i, j), forecaster.solar(i, j)

        j = i
        while j < len(quarters) and quarters[j].start.astimezone(TZ).date() < known_until:
            q = quarters[j]
            load, sun = known(j)
            sell, _ = tariffs.sell(q.market, q.start, sun > 0)
            slots.append(Slot(0.25, tariffs.buy(q.market), sell, load, sun))
            j += 1
        if now.hour < 13:
            # Tomorrow unknown: today's pattern as indicative prices.
            while j < len(quarters) and quarters[j].start.astimezone(TZ).date() < known_until + timedelta(days=1):
                q = quarters[j]
                same = by_start.get(q.start - timedelta(days=1))
                market = same.market if same else q.market
                load, sun = known(j)
                sell, _ = tariffs.sell(market, q.start, sun > 0)
                slots.append(Slot(0.25, tariffs.buy(market), sell, load, sun))
                j += 1
        return slots

    def choose(quarters: list[Quarter], i: int, energy: float, prev: Action) -> Action:
        local = quarters[i].start.astimezone(TZ)
        if forecaster is not None:
            forecaster.learn_until(i)
        start = int(cache["start"])  # type: ignore[call-overload]
        actions: list[Action] = cache["actions"]  # type: ignore[assignment]
        hourly = forecaster is not None and not forecaster.perfect and local.minute == 0
        if start < 0 or i - start >= len(actions) or (local.hour == 13 and local.minute == 0) or hourly:
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
    ap.add_argument("--load", choices=["perfect", "learned"], default="perfect", help="consumption the planner knows")
    ap.add_argument("--sun", choices=["perfect", "yesterday"], default="perfect", help="solar the planner knows")
    ap.add_argument("--rules", choices=["both", "2026", "2027"], default="both")
    ap.add_argument("--quick", action="store_true", help="only no battery, zero meter and the planner with wear")
    ap.add_argument(
        "--wear", type=float, default=0.03, help="€ per kWh out of the battery (PU3), for the 'incl. wear' column and the wear runs"
    )
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
    if args.rules != "both":
        rules = {k: v for k, v in rules.items() if k.startswith(args.rules)}
    print(f"planner knows: consumption {args.load}, solar {args.sun}")
    for label, tariffs in rules.items():
        print(f"\n{label}, {base.source}")
        w = args.wear

        def run(name: str, cfg: PlannerSettings, tariffs: Tariffs = tariffs) -> Result:
            forecaster = Forecaster(quarters, args.load, args.sun)
            return simulate(name, quarters, tariffs, battery, planner_strategy(tariffs, battery, cfg, forecaster))

        runs = [
            simulate("no battery", quarters, tariffs, None, None),
            simulate("zero meter (N always)", quarters, tariffs, battery, lambda *_: Action.DELIVER),
        ]
        if not args.quick:
            runs.append(run("planner", PlannerSettings()))
        runs.append(run(f"planner, wear {w}", PlannerSettings(wear_cost=w)))
        if not args.quick:
            runs.append(run("planner + X", PlannerSettings(allow_export=True)))
            runs.append(run(f"planner + X, wear {w}", PlannerSettings(allow_export=True, wear_cost=w)))
        ref = runs[0].total()
        print(
            f"  {'strategy':24} {'cost €':>9} {'saving €':>9} {'+wear €':>9} {'import':>8} {'export':>8} "
            f"{'grid→bat':>9} {'bat out':>8} {'starts':>7}"
        )
        for r in runs:
            print(
                f"  {r.name:24} {r.total():9.2f} {ref - r.total():9.2f} {r.total() + w * r.battery_out:9.2f} "
                f"{r.grid_import:8.0f} {r.grid_export:8.0f} "
                f"{r.grid_charged:9.0f} {r.battery_out:8.0f} {r.charge_starts:7d}"
            )


if __name__ == "__main__":
    main()
