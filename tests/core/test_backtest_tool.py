"""The backtest tool runs on small synthetic files (format of the private data)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from conftest import ROOT

sys.path.insert(0, str(ROOT / "tools"))
import backtest


def _files(tmp: Path) -> tuple[Path, Path, Path]:
    start = datetime(2026, 6, 1, tzinfo=UTC)
    prices, p1, solar = tmp / "prices.csv", tmp / "p1.csv", tmp / "solar.csv"
    with prices.open("w") as fh:
        fh.write("datum_nl;datum_utc;prijs_excl_belastingen\n")
        for k in range(3 * 96):
            t = start + timedelta(minutes=15 * k)
            price = 0.30 if 17 <= t.hour <= 20 else (-0.02 if 10 <= t.hour <= 13 else 0.08)
            decimal_comma = f"{price:.6f}".replace(".", ",")
            fh.write(f'"{t:%Y-%m-%d %H:%M:%S}";"{t:%Y-%m-%d %H:%M:%S}";{decimal_comma}\n')
    with p1.open("w") as fh:
        fh.write("uur_utc,afname_kwh,teruglevering_kwh\n")
        for h in range(72):
            t = start + timedelta(hours=h)
            sun = 2.0 if 8 <= t.hour <= 15 else 0.0
            fh.write(f"{t:%Y-%m-%dT%H:%MZ},{0.0 if sun else 0.5:.3f},{max(sun - 0.5, 0):.3f}\n")
    with solar.open("w") as fh:
        fh.write("entity_id,state,last_changed\n")
        total = 1000.0
        for h in range(73):
            t = start + timedelta(hours=h)
            fh.write(f"sensor.pv,{total:.3f},{t:%Y-%m-%dT%H:%M:%S.000Z}\n")
            total += 2.0 if 8 <= t.hour <= 15 else 0.0
    return prices, p1, solar


def test_backtest_runs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    prices, p1, solar = _files(tmp_path)
    backtest.main(["--prices", str(prices), "--p1", str(p1), "--solar", str(solar), "--capacity", "5"])
    out = capsys.readouterr().out
    assert "planner" in out and "2027" in out
    quarters = backtest.build_quarters(prices, p1, solar, None)
    assert len(quarters) == 71 * 4
    assert sum(q.solar for q in quarters) == pytest.approx(2.0 * 8 * 3 - 2.0, abs=2.1)
