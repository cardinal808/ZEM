"""Batteries in a set: cell balance and a short history (SPEC-celbalans.md, 0.8.6).

The cell difference (highest − lowest cell voltage in a pack) of LiFePO4 says
little in the middle of the charge: the voltage curve is flat there, so cells
with a different charge show almost the same voltage. Near full the fullest
cell reaches the steep knee first and an imbalance becomes visible. A high
charge current adds a voltage drop over the internal resistance. So the
difference is only judged near full (SOC ≥ 95 % or highest cell ≥ 3.40 V) and
with a small current (≤ 0.1 C); otherwise it is shown without a label.

Written on the clean side: no code, texts or thresholds of other projects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Final

GOOD_MV: Final = 30
BALANCING_MV: Final = 100
TOP_SOC: Final = 95.0
TOP_CELL_V: Final = 3.40
C_RATE: Final = 0.1
UNKNOWN_PACK_MAX_W: Final = 200.0
FULL_SOC: Final = 99.5
KEEP_DAYS: Final = 14
RULE: Final = 2
"""Version of the measuring rule; history of another rule is dropped (0.8.4 judged between 20 and 90 %)."""


def cell_delta_mv(vmin: float | None, vmax: float | None) -> int | None:
    """Highest minus lowest cell voltage in mV (the set reports per 10 mV)."""
    if vmin is None or vmax is None or vmax < vmin:
        return None
    return round((vmax - vmin) * 1000)


def rest_power_w(capacity_kwh: float | None) -> float:
    """0.1 C in W: a battery of C kWh at 0.1 C carries about C × 100 W."""
    return capacity_kwh * 1000 * C_RATE if capacity_kwh else UNKNOWN_PACK_MAX_W


def judged(soc: float, vmax: float | None, power_w: float, capacity_kwh: float | None) -> bool:
    """A moment at which the cell difference says something: near full and with a small current."""
    top = soc >= TOP_SOC or (vmax is not None and vmax >= TOP_CELL_V)
    return top and abs(power_w) <= rest_power_w(capacity_kwh)


def label(delta_mv: int | None) -> str | None:
    """good (≤ 30 mV), balancing (≤ 100 mV) or imbalance; None without a value."""
    if delta_mv is None:
        return None
    if delta_mv <= GOOD_MV:
        return "good"
    return "balancing" if delta_mv <= BALANCING_MV else "imbalance"


def cell_status(delta_mv: int | None, is_judged: bool) -> str | None:
    """The label on a judged moment; None otherwise (the value is shown without a label)."""
    return label(delta_mv) if is_judged else None


@dataclass(slots=True)
class PackHistory:
    """Per pack and day: the largest cell difference on a judged moment and whether the pack reached 100 %.

    Keyed by the pack's serial number; this stays in Home Assistant's storage
    and is never sent to the panel (B18).
    """

    packs: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)
    sets_full: dict[str, str] = field(default_factory=dict)
    """Set serial → last moment (ISO) the set reported ≥ 99.5 %."""

    def note_pack(self, serial: str, day: date, soc: float, delta_mv: int | None, is_judged: bool) -> bool:
        """Record one reading; True when something changed (to save)."""
        if not serial:
            return False
        days = self.packs.setdefault(serial, {})
        entry = days.setdefault(day.isoformat(), {"max_mv": None, "full": False})
        changed = False
        if delta_mv is not None and is_judged and (entry["max_mv"] is None or delta_mv > entry["max_mv"]):
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
        """``count`` days ending today, oldest first; days without a judged moment have ``max_mv`` None."""
        days = self.packs.get(serial, {})
        out = []
        for back in range(count - 1, -1, -1):
            day = (today - timedelta(days=back)).isoformat()
            entry = days.get(day, {})
            max_mv = entry.get("max_mv")
            out.append({"day": day, "max_mv": max_mv, "status": label(max_mv), "full": bool(entry.get("full"))})
        return out

    def as_dict(self) -> dict[str, Any]:
        return {"rule": RULE, "packs": self.packs, "sets_full": self.sets_full}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> PackHistory:
        data = data or {}
        packs = dict(data.get("packs") or {}) if data.get("rule") == RULE else {}
        return cls(packs=packs, sets_full=dict(data.get("sets_full") or {}))
