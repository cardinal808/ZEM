"""Filling the unmeasured part of a cost quarter (OPDRACHT-onvolledige-kwartieren, SPEC-kosten §7).

Bjorn: leave nothing out, always fill. What was not measured is worked out from the quarter
before and after (linear interpolation), and guessed if need be; a counter difference over the
gap sets the total, the interpolation only the spread.

Rule per flow (import, export, charge, discharge, external solar):

1. **neighbours**: the last measured quarter before and the first after (kWh per quarter);
2. **interpolate**: linear between them; for a part of a quarter only the missing part
   (measured part + interpolated rate × missing share);
3. **scale on counters**: a counter difference over the gap sets the total (``scale_to``);
4. **limits**: solar only in daylight, never negative;
5. **guess**: no neighbours → the mean of the same quarter over the last 7 days; else the
   measured part itself (its own rate); only then 0 (``missing``).

Pure Python; ``cost_recorder`` supplies the quarters and the counters.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Final

FLOWS: Final = ("import_kwh", "export_kwh", "charge_kwh", "discharge_kwh", "solar_ext_kwh")
"""Flows that can be filled. ``solar_ext_kwh``: solar from the external counter (the sets' own PV
comes with the battery flows)."""

INTERPOLATED: Final = "interpolated"
SCALED: Final = "scaled"
COUNTER: Final = "counter"
HISTORY: Final = "history"
OWN_RATE: Final = "own_rate"
NONE: Final = "none"

STATUS_MEASURED: Final = "measured"
STATUS_ESTIMATED: Final = "estimated"
STATUS_MISSING: Final = "missing"

FULL_SHARE: Final = 0.95
"""A flow measured over at least this share of the quarter is taken as measured (as before)."""


def neighbour_value(record: Mapping[str, Any] | None, flow: str) -> float | None:
    """A flow's kWh in a stored quarter, if that quarter can serve as a neighbour."""
    if record is None:
        return None
    if record.get("status") == STATUS_MISSING:
        return None
    if flow == "solar_ext_kwh" and flow not in record:
        return None  # quarters before 0.8.79 have no external solar apart
    value = record.get(flow)
    return None if value is None else float(value)


def interpolate(before: float | None, after: float | None, count: int) -> list[float] | None:
    """``count`` values linearly between ``before`` and ``after`` (both outside the gap).

    One side missing: that side's value for all. Both missing: None.
    """
    if count <= 0:
        return []
    if before is None and after is None:
        return None
    if before is None:
        before = after
    if after is None:
        after = before
    assert before is not None and after is not None
    return [before + (after - before) * (i + 1) / (count + 1) for i in range(count)]


def scale_to(values: Sequence[float], total: float) -> list[float]:
    """Scale ``values`` so they add up to ``total``; spread evenly when they add up to 0."""
    if not values:
        return []
    total = max(total, 0.0)
    current = sum(max(v, 0.0) for v in values)
    if current <= 0:
        return [total / len(values)] * len(values)
    return [max(v, 0.0) * total / current for v in values]


def history_mean(records: Iterable[Mapping[str, Any]], flow: str) -> float | None:
    """Mean of a flow over earlier quarters at the same time of day (the caller selects them)."""
    values = [v for v in (neighbour_value(r, flow) for r in records) if v is not None]
    return sum(values) / len(values) if values else None


@dataclass(slots=True)
class Part:
    """What was measured of one flow in one quarter."""

    kwh: float
    share: float
    """Share of the quarter it was measured (0–1)."""


@dataclass(slots=True)
class Filled:
    kwh: float
    method: str
    """``measured`` flows have no method (not in the result's ``methods``)."""
    added: float = 0.0


def fill_part(
    part: Part,
    before: float | None,
    after: float | None,
    history: float | None = None,
    allowed: bool = True,
) -> Filled | None:
    """The flow over the whole quarter: the measured part plus the missing part.

    ``before``/``after``: the neighbour quarters (kWh per quarter). ``after`` is often unknown
    at closing time; then the measured part's own rate stands in for it (refined once the next
    quarter closed). ``allowed`` False (solar at night): the missing part is 0. Returns None when
    the flow was measured (share ≥ ``FULL_SHARE``).
    """
    if part.share >= FULL_SHARE:
        return None
    missing = max(1.0 - part.share, 0.0)
    if not allowed:
        return Filled(part.kwh, INTERPOLATED, 0.0)
    own_rate = part.kwh / part.share if part.share > 0.05 else None
    rate: float | None
    method = INTERPOLATED
    if before is not None or after is not None:
        side_after = after if after is not None else own_rate
        values = interpolate(before, side_after, 1)
        rate = values[0] if values else None
    elif own_rate is not None:
        rate, method = own_rate, OWN_RATE
    elif history is not None:
        rate, method = history, HISTORY
    else:
        return Filled(part.kwh, NONE, 0.0)
    assert rate is not None
    added = max(rate, 0.0) * missing
    return Filled(part.kwh + added, method, added)


@dataclass(slots=True)
class QuarterFill:
    """Result of filling one quarter: the flows, how, and its status."""

    values: dict[str, float] = field(default_factory=dict)
    methods: dict[str, str] = field(default_factory=dict)
    added: dict[str, float] = field(default_factory=dict)
    causes: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if any(m == NONE for m in self.methods.values()):
            return STATUS_MISSING
        return STATUS_ESTIMATED if self.methods else STATUS_MEASURED

    def as_record(self) -> dict[str, Any]:
        out: dict[str, Any] = {"status": self.status}
        if self.methods:
            out["fill"] = dict(sorted(self.methods.items()))
            out["fill_kwh"] = {k: round(v, 4) for k, v in sorted(self.added.items()) if v}
        if self.causes:
            out["fill_causes"] = sorted(set(self.causes))
        return out
