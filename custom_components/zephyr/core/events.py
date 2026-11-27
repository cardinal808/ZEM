"""Events for the screen *Diagnose* from the decision log (SPEC-ui §4.5, SPEC-ui-airco §3.4).

The decision log has one line per change of setpoint or reason, plus event
lines (live, shadow, test, second controller). The panel wants what a person
would call an event: another reason, another mode, live on or off, a flash
write, the air conditioner leaving or joining the battery. Pure, no Home
Assistant.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Final

from .engine import REASON_TEXT, Reason, ReasonCode

MAX_EVENTS: Final = 100
FLASH_KINDS: Final = ("standby", "soc_limits", "grid_reverse")
MARKERS: Final = ("live", "shadow", "test", "test_end", "second_controller")


def _reason_text(code: str, params: Mapping[str, Any] | None) -> dict[str, str] | None:
    try:
        reason = Reason(ReasonCode(code), dict(params or {}))
    except ValueError:
        return None
    if reason.code not in REASON_TEXT:
        return None
    try:
        return {"nl": reason.text("nl"), "en": reason.text("en")}
    except (KeyError, IndexError, ValueError):
        # A log line without the parameters (older line): the bare code is enough.
        return None


def events_from_log(log: Iterable[Mapping[str, Any]], limit: int = MAX_EVENTS) -> list[dict[str, Any]]:
    """Newest first, at most ``limit``."""
    out: list[dict[str, Any]] = []
    mode: str | None = None
    reason: str | None = None
    excluded = False
    for line in log:
        time = line.get("time")
        if "event" in line:
            if line["event"] in MARKERS:
                extra = {"power": line["power"]} if "power" in line else {}
                out.append({"time": time, "kind": line["event"], **extra})
            continue
        if line.get("mode") is not None and line["mode"] != mode:
            if mode is not None:
                out.append({"time": time, "kind": "mode", "mode": line["mode"]})
            mode = line["mode"]
        code = line.get("reason")
        if code is not None and code != reason:
            out.append(
                {
                    "time": time,
                    "kind": "reason",
                    "code": code,
                    "text": _reason_text(code, line.get("reason_params")),
                    "setpoint": line.get("setpoint"),
                }
            )
            reason = code
        now_excluded = bool(line.get("excluded"))
        if now_excluded != excluded:
            out.append(
                {"time": time, "kind": "excluded_on" if now_excluded else "excluded_off"}
                | ({"power": line["excluded"]} if now_excluded else {})
            )
            excluded = now_excluded
        for command in line.get("commands") or ():
            if command.get("kind") in FLASH_KINDS:
                out.append({"time": time, "kind": "flash", "cause": command["kind"], "set": command.get("set")})
    return out[::-1][:limit]
