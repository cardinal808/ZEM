"""Batteries in a set: cell balance and a short history (SPEC-ui §3.3, UI-4).

The cell difference (highest − lowest cell voltage in a pack) only says
something in the middle of the charge curve. LiFePO4 cells spread out near
full and near empty (measured 26-11: 120 mV at 100 % on an AB3000L), so the
difference is only judged between 20 and 90 % SOC; outside that window it is
shown but not labelled, and it does not count for the daily history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Final

GOOD_MV: Final = 30
WATCH_MV: Final = 80
JUDGE_MIN_SOC: Final = 20.0
JUDGE_MAX_SOC: Final = 90.0
FULL_SOC: Final = 99.5
KEEP_DAYS: Final = 14


def cell_delta_mv(vmin: float | None, vmax: float | None) -> int | None:
    """Highest minus lowest cell voltage in mV (the set reports per 10 mV)."""
    if vmin is None or vmax is None or vmax < vmin:
        return None
    return round((vmax - vmin) * 1000)


def judged(soc: float) -> bool:
    return JUDGE_MIN_SOC <= soc <= JUDGE_MAX_SOC


def cell_status(delta_mv: int | None, soc: float) -> str | None:
    """good / watch / high in the middle of the charge curve; edge near full or empty; None without data."""
    if delta_mv is None:
        return None
    if not judged(soc):
        return "edge"
    if delta_mv <= GOOD_MV:
        return "good"
    if delta_mv <= WATCH_MV:
        return "watch"
    return "high"


def day_status(max_mv: int | None) -> str | None:
    if max_mv is None:
        return None
    return "good" if max_mv <= GOOD_MV else "watch" if max_mv <= WATCH_MV else "high"


@dataclass(slots=True)
class PackHistory:
    """Per pack and day: the largest judged cell difference and whether the pack reached 100 %.

    Keyed by the pack's serial number; this stays in Home Assistant's storage
    and is never sent to the panel (B18).
    """

    packs: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)
    sets_full: dict[str, str] = field(default_factory=dict)
    """Set serial → last moment (ISO) the set reported ≥ 99.5 %."""

    def note_pack(self, serial: str, day: date, soc: float, delta_mv: int | None) -> bool:
        """Record one reading; True when something changed (to save)."""
        if not serial:
            return False
        days = self.packs.setdefault(serial, {})
        entry = days.setdefault(day.isoformat(), {"max_mv": None, "full": False})
        changed = False
        if delta_mv is not None and judged(soc) and (entry["max_mv"] is None or delta_mv > entry["max_mv"]):
            entry["max_mv"] = delta_mv
            changed = True
        if soc >= FULL_SOC and not entry["full"]:
            entry["full"] = True
            changed = True
        return changed

    def note_set_full(self, serial: str, moment_iso: str, soc: float) -> bool:
        if not serial or soc < FULL_SOC:
            return False
        self.sets_full[serial] = moment_iso
        return True

    def prune(self, today: date) -> None:
        oldest = (today - timedelta(days=KEEP_DAYS - 1)).isoformat()
        for serial in list(self.packs):
            days = {d: v for d, v in self.packs[serial].items() if d >= oldest}
            if days:
                self.packs[serial] = days
            else:
                del self.packs[serial]

    def last_days(self, serial: str, today: date, count: int = 7) -> list[dict[str, Any]]:
        """``count`` days ending today, oldest first; days without data have ``max_mv`` None."""
        days = self.packs.get(serial, {})
        out = []
        for back in range(count - 1, -1, -1):
            day = (today - timedelta(days=back)).isoformat()
            entry = days.get(day, {})
            max_mv = entry.get("max_mv")
            out.append({"day": day, "max_mv": max_mv, "status": day_status(max_mv), "full": bool(entry.get("full"))})
        return out

    def as_dict(self) -> dict[str, Any]:
        return {"packs": self.packs, "sets_full": self.sets_full}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> PackHistory:
        data = data or {}
        return cls(packs=dict(data.get("packs") or {}), sets_full=dict(data.get("sets_full") or {}))
