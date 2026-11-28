"""Energy balance and price check for the diagnostics (TOETS-besparing voorstel 4 and 6)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from zephyr_core.cost_checks import energy_balance, price_check


def _quarters(day: str, charge: float, deliver: float, socs: list[float]) -> list[dict]:
    start = datetime.fromisoformat(f"{day}T00:00:00+00:00")
    n = len(socs)
    return [
        {"start": (start + timedelta(minutes=15 * i)).isoformat(), "charge_kwh": charge / n, "discharge_kwh": deliver / n, "soc": soc}
        for i, soc in enumerate(socs)
    ]


def test_balance_matches_and_flags_missing_energy() -> None:
    # 10 kWh capacity, charged 2.15 kWh (× 0.93 = 2.0) → SOC +20 %: fine.
    ok = _quarters("2026-11-26", 2.15, 0.0, [10.0, 20.0, 30.0])
    # The next day the SOC rose 30 % (3 kWh) but only 1 kWh was counted: suspect.
    bad = _quarters("2026-11-27", 1.0, 0.0, [40.0, 50.0, 60.0])
    days = energy_balance(ok + bad, 10.0, 0.93, 0.93, UTC)
    assert days[0]["suspect"] is False
    assert days[1]["suspect"] is True and days[1]["difference_kwh"] < -1.5


def test_price_check_flags_a_wrong_slot() -> None:
    hour = datetime(2025, 11, 25, 22, 0, tzinfo=UTC)
    records = [{"start": (hour + timedelta(minutes=15 * i)).isoformat(), "market": 0.20} for i in range(3)]
    records.append({"start": (hour + timedelta(minutes=45)).isoformat(), "market": 0.379})  # 25-11 23:45
    found = price_check(records, {hour: 0.208})  # one quarter far off: flagged
    assert found and found[0]["energyzero"] == 0.208
    normal = [{**r, "market": 0.20 + 0.02 * i} for i, r in enumerate(records)]  # 0.20–0.26 within the hour
    assert price_check(normal, {hour: 0.23}) == []
    interpolated = [{**r, "price_source": "interpolated"} for r in records]
    assert price_check(interpolated, {hour: 0.208}) == []
