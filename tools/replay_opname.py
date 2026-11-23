"""Replay a recording (Home Assistant history CSV) through the simulator.

The house load without battery is rebuilt from the recording:
    load = P1 (corrected) + battery delivering − battery charging
and ZEPHYR controls a simulated set against it. The result is compared with
the recorded grid power of the existing system over the same seconds.

Usage (the CSV stays on your own machine; never commit it):
    python tools/replay_opname.py history.csv --start 2026-11-12T16:00 --hours 6

Entity ids of the recorded system can be changed with the options.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sim  # noqa: F401
from sim.device import SimSet
from sim.runner import Simulation, energy_wh, share_within, writes


def load_series(path: Path, entities: set[str]) -> dict[str, tuple[list[float], list[float]]]:
    raw: dict[str, list[tuple[float, float]]] = {e: [] for e in entities}
    with path.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            e = row["entity_id"]
            if e not in raw:
                continue
            try:
                v = float(row["state"])
            except ValueError:
                continue
            t = dt.datetime.fromisoformat(row["last_changed"].replace("Z", "+00:00")).timestamp()
            raw[e].append((t, v))
    out = {}
    for e, pts in raw.items():
        pts.sort()
        out[e] = ([p[0] for p in pts], [p[1] for p in pts])
    return out


def at(series: tuple[list[float], list[float]], t: float) -> float:
    ts, vs = series
    i = bisect.bisect_right(ts, t) - 1
    return vs[i] if i >= 0 else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", type=Path)
    ap.add_argument("--start", required=True, help="UTC start, e.g. 2026-11-12T16:00")
    ap.add_argument("--hours", type=float, default=6)
    ap.add_argument("--p1", default="sensor.p1_aansturing_vermogen")
    ap.add_argument("--deliver", default="sensor.zendure_2400_ac_vermogen_naar_huis")
    ap.add_argument("--charge", default="sensor.zendure_2400_ac_vermogen_van_huis")
    ap.add_argument("--soc", default="sensor.zendure_2400_ac_laadpercentage")
    ap.add_argument("--battery", help="one signed battery sensor (+ charging) instead of --deliver/--charge")
    ap.add_argument("--max-deliver", type=int, default=2400)
    ap.add_argument("--compare-filters", action="store_true", help="run without filters, step filter only, both, and hold times")
    args = ap.parse_args()

    wanted = {args.p1, args.soc} | ({args.battery} if args.battery else {args.deliver, args.charge})
    series = load_series(args.csv, wanted)
    t0 = dt.datetime.fromisoformat(args.start).replace(tzinfo=dt.UTC).timestamp()
    t1 = t0 + args.hours * 3600

    def battery_rec(t: float) -> float:
        """Recorded battery power, + charging."""
        if args.battery:
            return at(series[args.battery], t0 + t)
        return at(series[args.charge], t0 + t) - at(series[args.deliver], t0 + t)

    def load(t: float) -> float:
        return at(series[args.p1], t0 + t) - battery_rec(t)

    if args.compare_filters:
        compare_filters(load, at(series[args.soc], t0) or 50.0, t1 - t0, args.max_deliver)
        return

    soc0 = at(series[args.soc], t0) or 50.0
    sim_ = Simulation(load=load, sets=[SimSet(soc=soc0)], dt=0.25)
    sim_.settings = sim_.settings.with_changes(max_deliver_power=args.max_deliver)
    sim_.engine.update_settings(sim_.settings)
    tr = sim_.run(t1 - t0)

    # Compare only seconds where both systems were delivering (actively regulating).
    zephyr_g, rec_g = [], []
    for t, g, b in zip(tr.t, tr.grid, tr.battery, strict=True):
        rec_deliver = -battery_rec(t)
        if b < -20 and rec_deliver > 20:
            zephyr_g.append(g)
            rec_g.append(at(series[args.p1], t0 + t))

    def stats(name: str, vals: list[float]) -> None:
        vals = sorted(vals)
        n = len(vals)
        if not n:
            print(f"{name}: no data")
            return
        q = lambda p: vals[int(p * (n - 1))]  # noqa: E731
        within = sum(1 for v in vals if abs(v - 15) <= 50 or abs(v) <= 50) / n
        imp = sum(1 for v in vals if v > 100) / n
        exp = sum(1 for v in vals if v < -20) / n
        print(
            f"{name:>10}: n={n:6d}  p5 {q(0.05):6.0f}  p50 {q(0.5):6.0f}  p95 {q(0.95):6.0f}  "
            f"within ±50 W {within:5.1%}  import>100 {imp:5.1%}  export<-20 {exp:5.1%}"
        )

    print(f"Window {args.start} UTC, {args.hours} h; delivering both: {len(zephyr_g) * sim_.dt / 3600:.1f} h")
    stats("recorded", rec_g)
    stats("ZEPHYR", zephyr_g)
    print(f"ZEPHYR writes: {sum(len(s.writes) for s in sim_.sets)}; overall within ±50 W: {share_within(tr, 15, 50):.1%}")


def compare_filters(load: Callable[[float], float], soc0: float, duration: float, max_deliver: int) -> None:
    """Same recording, different P1 filter settings: grid energy, writes and accuracy."""
    variants = [
        ("no filters", {"step_threshold": 0, "noise_band": 0}),
        ("noise only", {"step_threshold": 0}),
        ("step 10 s only", {"noise_band": 0}),
        ("both, step 10 s", {}),
        ("both, step 6 s", {"step_hold": 6}),
        ("both, step 15 s", {"step_hold": 15}),
        ("both, step 1200 W", {"step_threshold": 1200}),
    ]
    print(f"{'variant':>18} {'import Wh':>10} {'export Wh':>10} {'writes':>7} {'±50 W':>7} {'holds':>6}")
    for name, changes in variants:
        sim_ = Simulation(load=load, sets=[SimSet(soc=soc0)], dt=0.25)
        sim_.settings = sim_.settings.with_changes(max_deliver_power=max_deliver, **changes)
        sim_.engine.update_settings(sim_.settings)
        tr = sim_.run(duration)
        print(
            f"{name:>18} {energy_wh(tr, 1):10.0f} {energy_wh(tr, -1):10.0f} {writes(sim_):7d} "
            f"{share_within(tr, 15, 50):7.1%} {sim_.engine.grid_filter.holds:6d}"
        )


if __name__ == "__main__":
    main()
