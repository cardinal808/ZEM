"""Cell balance per pack and its short history (SPEC-celbalans.md)."""

from __future__ import annotations

from datetime import date

import pytest

from zephyr_core.packs import PackHistory, cell_delta_mv, cell_status, judged, label, rest_power_w


def test_delta_in_mv() -> None:
    assert cell_delta_mv(3.36, 3.48) == 120
    assert cell_delta_mv(3.35, 3.40) == 50
    assert cell_delta_mv(None, 3.4) is None
    assert cell_delta_mv(3.5, 3.4) is None


def test_rest_power_is_a_tenth_c() -> None:
    assert rest_power_w(2.88) == pytest.approx(288)
    assert rest_power_w(2.40) == pytest.approx(240)
    assert rest_power_w(None) == 200


@pytest.mark.parametrize(
    ("soc", "vmax", "power", "capacity", "expected"),
    [
        (100.0, 3.48, 0.0, 2.88, True),  # diagnostics 26-11: full and at rest
        (96.0, 3.38, -150.0, 2.88, True),
        (80.0, 3.41, 100.0, 2.88, True),  # top of the curve by voltage
        (100.0, 3.48, 900.0, 2.88, False),  # charging hard: the current distorts
        (75.0, 3.33, 0.0, 2.88, False),  # middle of the curve says little
        (100.0, 3.45, 250.0, None, False),  # unknown type: at most 200 W
    ],
)
def test_judged_only_near_full_with_a_small_current(soc: float, vmax: float, power: float, capacity: float | None, expected: bool) -> None:
    assert judged(soc, vmax, power, capacity) is expected


@pytest.mark.parametrize(
    ("delta", "status"), [(0, "good"), (30, "good"), (40, "balancing"), (100, "balancing"), (110, "imbalance"), (None, None)]
)
def test_labels(delta: int | None, status: str | None) -> None:
    assert label(delta) == status
    assert cell_status(delta, True) == status
    assert cell_status(delta, False) is None


def test_diagnostics_26_11() -> None:
    """All four packs full and at rest: 50, 120, 70 and 40 mV."""
    assert [label(mv) for mv in (50, 120, 70, 40)] == ["balancing", "imbalance", "balancing", "balancing"]


def test_history_keeps_the_largest_judged_difference_and_full_days() -> None:
    h = PackHistory()
    d1, d2 = date(2026, 11, 25), date(2026, 11, 26)
    assert h.note_pack("G1", d1, 100.0, 50, True)
    assert h.note_pack("G1", d1, 100.0, 120, True)
    assert not h.note_pack("G1", d1, 100.0, 70, True)  # smaller: no change
    assert not h.note_pack("G1", d1, 60.0, 200, False)  # not judged
    assert h.note_pack("G1", d2, 100.0, None, False)  # only full
    days = h.last_days("G1", d2, 3)
    assert [d["day"] for d in days] == ["2026-11-24", "2026-11-25", "2026-11-26"]
    assert days[0] == {"day": "2026-11-24", "max_mv": None, "status": None, "full": False}
    assert days[1] == {"day": "2026-11-25", "max_mv": 120, "status": "imbalance", "full": True}
    assert days[2]["max_mv"] is None and days[2]["full"] is True


def test_history_prunes_round_trips_and_drops_the_old_rule() -> None:
    h = PackHistory()
    h.note_pack("G1", date(2026, 11, 1), 100.0, 20, True)
    h.note_pack("G1", date(2026, 11, 20), 100.0, 20, True)
    h.note_pack("J1", date(2026, 11, 2), 100.0, 20, True)
    assert h.note_set_full("SET", "2026-11-26T09:15:00+00:00", 100.0)
    assert not h.note_set_full("SET", "2026-11-26T10:00:00+00:00", 80.0)
    h.prune(date(2026, 11, 26))
    assert list(h.packs) == ["G1"] and list(h.packs["G1"]) == ["2026-11-20"]
    again = PackHistory.from_dict(h.as_dict())
    assert again.packs == h.packs and again.sets_full == {"SET": "2026-11-26T09:15:00+00:00"}
    old = PackHistory.from_dict({"packs": {"G1": {"2026-11-25": {"max_mv": 20, "full": False}}}, "sets_full": {"SET": "x"}})
    assert old.packs == {} and old.sets_full == {"SET": "x"}  # 0.8.4 measured mid-curve: dropped
    assert PackHistory.from_dict(None).packs == {}
