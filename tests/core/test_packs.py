"""Cell balance per pack and its short history (UI-4)."""

from __future__ import annotations

from datetime import date

import pytest

from zephyr_core.packs import PackHistory, cell_delta_mv, cell_status, day_status


def test_delta_in_mv() -> None:
    assert cell_delta_mv(3.36, 3.48) == 120
    assert cell_delta_mv(3.35, 3.40) == 50
    assert cell_delta_mv(None, 3.4) is None
    assert cell_delta_mv(3.5, 3.4) is None


@pytest.mark.parametrize(
    ("delta", "soc", "status"),
    [
        (20, 50.0, "good"),
        (30, 50.0, "good"),
        (50, 50.0, "watch"),
        (80, 89.0, "watch"),
        (90, 50.0, "high"),
        (120, 100.0, "edge"),  # measured 26-11 on a full AB3000L: normal at the top
        (40, 15.0, "edge"),
        (None, 50.0, None),
    ],
)
def test_status_only_in_the_middle_of_the_curve(delta: int | None, soc: float, status: str | None) -> None:
    assert cell_status(delta, soc) == status


def test_history_keeps_the_largest_judged_difference_and_full_days() -> None:
    h = PackHistory()
    d1, d2 = date(2026, 11, 25), date(2026, 11, 26)
    assert h.note_pack("G1", d1, 50.0, 20)
    assert h.note_pack("G1", d1, 60.0, 40)
    assert not h.note_pack("G1", d1, 60.0, 30)  # smaller: no change
    assert h.note_pack("G1", d1, 100.0, 120)  # not judged at the top, but the day counts as full
    assert h.note_pack("G1", d1, 100.0, 120) is False
    assert h.note_pack("G1", d2, 100.0, 120)
    days = h.last_days("G1", d2, 3)
    assert [d["day"] for d in days] == ["2026-11-24", "2026-11-25", "2026-11-26"]
    assert days[0] == {"day": "2026-11-24", "max_mv": None, "status": None, "full": False}
    assert days[1]["max_mv"] == 40 and days[1]["status"] == "watch" and days[1]["full"]
    assert days[2]["max_mv"] is None and days[2]["full"] is True


def test_history_prunes_and_round_trips() -> None:
    h = PackHistory()
    h.note_pack("G1", date(2026, 11, 1), 50.0, 20)
    h.note_pack("G1", date(2026, 11, 20), 50.0, 20)
    h.note_pack("J1", date(2026, 11, 2), 50.0, 20)
    assert h.note_set_full("SET", "2026-11-26T09:15:00+00:00", 100.0)
    assert not h.note_set_full("SET", "2026-11-26T10:00:00+00:00", 80.0)
    h.prune(date(2026, 11, 26))
    assert list(h.packs) == ["G1"] and list(h.packs["G1"]) == ["2026-11-20"]
    again = PackHistory.from_dict(h.as_dict())
    assert again.packs == h.packs and again.sets_full == {"SET": "2026-11-26T09:15:00+00:00"}
    assert PackHistory.from_dict(None).packs == {}


def test_day_status() -> None:
    assert (day_status(None), day_status(30), day_status(60), day_status(81)) == (None, "good", "watch", "high")
