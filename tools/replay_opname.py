"""Replay a recording (Home Assistant history CSV) through the simulator.

The house load without battery is rebuilt from the recording:
    load = P1 (corrected) + battery delivering − battery charging
and ZEM controls a simulated set against it. The result is compared with
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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sim  # noqa: F401
from sim.device import SimSet
from sim.runner import Simulation, share_within


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
    ap.add_argument("--max-deliver", type=int, default=2400)
    args = ap.parse_args()

    series = load_series(args.csv, {args.p1, args.deliver, args.charge, args.soc})
    t0 = dt.datetime.fromisoformat(args.start).replace(tzinfo=dt.UTC).timestamp()
    t1 = t0 + args.hours * 3600

    def load(t: float) -> float:
        return at(series[args.p1], t0 + t) + at(series[args.deliver], t0 + t) - at(series[args.charge], t0 + t)

    soc0 = at(series[args.soc], t0) or 50.0
    sim_ = Simulation(load=load, sets=[SimSet(soc=soc0)], dt=0.25)
    sim_.settings = sim_.settings.with_changes(max_deliver_power=args.max_deliver)
    sim_.engine.update_settings(sim_.settings)
    tr = sim_.run(t1 - t0)

    # Compare only seconds where both systems were delivering (actively regulating).
    zem_g, rec_g = [], []
    for t, g, b in zip(tr.t, tr.grid, tr.battery, strict=True):
        rec_deliver = at(series[args.deliver], t0 + t)
        if b < -20 and rec_deliver > 20:
            zem_g.append(g)
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

    print(f"Window {args.start} UTC, {args.hours} h; delivering both: {len(zem_g) * sim_.dt / 3600:.1f} h")
    stats("recorded", rec_g)
    stats("ZEM", zem_g)
    print(f"ZEM writes: {sum(len(s.writes) for s in sim_.sets)}; overall within ±50 W: {share_within(tr, 15, 50):.1%}")


if __name__ == "__main__":
    main()
