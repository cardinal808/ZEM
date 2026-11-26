"""Events for the screen Diagnose from the decision log (core/events.py)."""

from __future__ import annotations

from zephyr_core.events import events_from_log


def _d(t: str, reason: str, mode: str = "zero_meter", **extra: object) -> dict[str, object]:
    return {"time": f"2026-11-26T{t}:00+00:00", "mode": mode, "reason": reason, "setpoint": 0, "commands": [], **extra}


def test_events_are_changes_not_every_decision() -> None:
    log = [
        _d("10:00", "delivering", reason_params={"power": 600, "grid": 10}, setpoint=-600),
        _d("10:01", "delivering", reason_params={"power": 610}, setpoint=-610),
        {"time": "2026-11-26T10:02:00+00:00", "event": "live"},
        _d("10:03", "delivering", excluded=1800),
        _d("10:04", "full", reason_params={"soc": 95}, commands=[{"set": 1, "kind": "soc_limits", "socSet": 950}]),
        _d("10:05", "fast_charge", mode="fast_charge", reason_params={"soc": 95}),
        {"time": "2026-11-26T10:06:00+00:00", "event": "test", "power": 300},
        {"time": "2026-11-26T10:06:30+00:00", "event": "unknown_marker"},
    ]
    events = events_from_log(log)
    kinds = [e["kind"] for e in events]
    assert kinds == ["test", "reason", "mode", "flash", "excluded_off", "reason", "excluded_on", "live", "reason"]
    assert events[0]["power"] == 300
    first = events[-1]
    assert first["code"] == "delivering" and first["setpoint"] == -600
    assert first["text"] is not None and "600" in first["text"]["nl"]
    assert events[2]["mode"] == "fast_charge"
    assert events[3] == {"time": "2026-11-26T10:04:00+00:00", "kind": "flash", "cause": "soc_limits", "set": 1}
    assert events[6]["power"] == 1800


def test_older_lines_without_parameters_and_the_limit() -> None:
    # A reason that needs parameters but the line has none: no text, the code stays.
    events = events_from_log([_d("10:00", "delivering"), _d("10:01", "no_such_reason")])
    assert events[1]["text"] is None and events[0]["text"] is None
    log = [_d(f"10:{i:02d}", "delivering" if i % 2 else "idle_small") for i in range(60)] * 3
    assert len(events_from_log(log)) == 100
    assert events_from_log(log)[0]["time"] == "2026-11-26T10:59:00+00:00"
