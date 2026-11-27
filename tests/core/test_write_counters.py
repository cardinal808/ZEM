"""Write and relay counters over a restart, per day and per cause (OPDRACHT-tellers-relais-flash)."""

from __future__ import annotations

from conftest import load_fixture
from zephyr_core.counters import SetCounters
from zephyr_core.engine import Command, SetView, ZephyrEngine
from zephyr_core.settings import Settings
from zephyr_core.zensdk import parse_report

WALL = 1_800_000_000.0


def _view(raw: dict | None = None) -> SetView:
    return SetView("a", 1, parse_report(raw or load_fixture("deliver_760")), True)


def test_counters_continue_over_a_restart() -> None:
    before = SetCounters()
    for t in (100.0, 50_000.0, 90_000.0, 90_500.0):
        before.record("power", t, "2026-11-27")
    before.record("standby", 90_600.0, "2026-11-27")
    before.observe_ac_status(1, 90_600.0)
    stored = before.as_dict(now=91_000.0, wall=WALL)  # 100.0 is older than 24 h: dropped

    after = SetCounters()  # new process: the monotonic clock starts again
    after.record("power", 20.0, "2026-11-27")
    after.restore(stored, now=30.0, wall=WALL + 60)
    snap = after.snapshot(30.0)
    assert snap["ram_24h"] == 4 and snap["ram_1h"] == 3  # 90 000, 90 500 and the new one
    assert snap["flash_24h"] == 1 and snap["flash_by_cause"]["standby"] == 1
    assert snap["days"][0]["ram"] == 5 and snap["days"][0]["flash_by_cause"] == {"standby": 1}
    assert snap["flash_by_cause"] == {"standby": 1, "soc_limits": 0, "startup": 0, "grid_reverse": 0, "test": 0}

    # The first report after the restart: same acStatus, no switch; a change counts.
    after.observe_ac_status(1, 31.0)
    assert after.snapshot(31.0)["relay_24h"] == 0
    after.observe_ac_status(0, 32.0, "2026-11-27")
    assert after.snapshot(32.0)["relay_24h"] == 1


def test_an_event_of_25_hours_ago_no_longer_counts() -> None:
    c = SetCounters()
    c.record("power", 0.0)
    assert c.snapshot(3_600.0)["ram_24h"] == 1
    assert c.snapshot(25 * 3_600.0)["ram_24h"] == 0


def test_relay_reported_commanded_and_pack_state_per_day() -> None:
    c = SetCounters()
    c.observe_ac_status(1, 0.0, "d")
    c.observe_pack_state(2, 0.0, "d")
    c.observe_pack_state(1, 10.0, "d")  # the set turns by itself
    c.observe_ac_status(2, 10.0, "d")
    day = c.snapshot(20.0)["days"][0]
    assert (day["relay"], day["relay_commanded"], day["pack_state"]) == (1, 0, 1)
    assert "relay_mismatch" not in day
    for t in (30.0, 40.0, 50.0):
        c.observe_ac_status(1 if t != 40.0 else 2, t, "d")
    assert c.snapshot(60.0)["days"][0]["relay_mismatch"] is True
    for t in range(10):
        c.record("x", float(t), f"2026-11-{t + 10}")
    assert len(c.days) == 7


def test_a_command_with_the_reported_direction_is_no_relay_switch() -> None:
    e = ZephyrEngine()
    e.p1_reported(0, 300)
    e.step(0, [_view()])  # reports acMode 2 (deliver) and delivers 760 W
    counts = e.counters(1)["a"]
    assert counts["relay_commanded_24h"] == 0

    # The set reports charging; a large import turns the direction: one commanded switch.
    e2 = ZephyrEngine()
    charging = SetView("a", 1, parse_report(load_fixture("charge_2400")), True)
    turned = []
    for t in range(0, 60, 2):
        e2.p1_reported(t, 4000)
        turned += [c for c in e2.step(t, [charging]).commands if c.props.get("acMode") == 2]
    assert turned
    assert e2.counters(61)["a"]["relay_commanded_24h"] == len(turned)


def test_soc_limits_at_the_first_sight_count_as_startup() -> None:
    e = ZephyrEngine(Settings(min_soc=10, max_soc=95))
    e.p1_reported(0, 0)
    first = e.step(0, [_view()])
    limits = [c for c in first.commands if c.kind == "soc_limits"]
    assert limits and limits[0].kinds == ["startup"]
    assert e.counters(1)["a"]["flash_by_cause"]["startup"] == 1


def test_grid_reverse_riding_along_is_counted_too() -> None:
    command = Command("a", {"outputLimit": 300, "gridReverse": 2}, "power")
    assert command.kinds == ["power", "grid_reverse"]
    assert Command("a", {"gridReverse": 2}, "grid_reverse").kinds == ["grid_reverse"]


def test_live_counting_is_left_to_the_writer() -> None:
    e = ZephyrEngine()
    e.count_commands = False
    e.p1_reported(0, 300)
    r = e.step(0, [_view()])
    assert r.commands and e.counters(1)["a"]["ram_24h"] == 0
    e.counters_record("a", "power", 1)
    assert e.counters(1)["a"]["ram_24h"] == 1
