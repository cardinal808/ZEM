"""Price forecast from jeroen.nl as an optional source (OPDRACHT-prijsvoorspelling-jeroen).

ZEPHYR never fetches anything from jeroen.nl. It only reads the sensor of the HACS integration
ha-jeroen-nl, which the user installs with an API key of their own account. That sensor's
attribute ``prices`` lists the fixed quarters from now on and then the forecast quarters
(``forecast: true``, with ``market``, ``low`` and ``high``: the 80 % band, p10–p90).

* Only forecast quarters are used; the sensor's all-in ``price`` is not: ZEPHYR prices the bare
  ``market`` / ``low`` / ``high`` with its own tariffs, like every other slot.
* Units (€/kWh, €/MWh, cents) are recognised from the sensor, not assumed. Slots are kept by
  their start in UTC, so days of 92 or 100 quarters work.
* Nord Pool always leads: a forecast quarter is used only from the end of the last known price
  on, without a gap, never for the running quarter, and only while the forecast is fresh
  (≤ 36 h). Forecast slots are always *indicative*: not in the totals.

Pure Python.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Any, Final

QUARTER: Final = timedelta(minutes=15)
STALE_AFTER: Final = timedelta(hours=36)

MODE_OFF: Final = "off"
MODE_INDICATIVE: Final = "indicative"
MODE_USE: Final = "use"
MODES: Final = (MODE_OFF, MODE_INDICATIVE, MODE_USE)
VALUE_LOW: Final = "low"
VALUE_MID: Final = "mid"
VALUES: Final = (VALUE_LOW, VALUE_MID)


@dataclass(frozen=True, slots=True)
class ForecastSlot:
    start: datetime
    end: datetime
    market: float
    low: float
    high: float
    band: bool
    """``low`` and ``high`` were given (else both equal ``market``)."""

    def value(self, which: str) -> float:
        return self.low if which == VALUE_LOW else self.market


@dataclass(slots=True)
class Forecast:
    slots: list[ForecastSlot] = field(default_factory=list)
    made: datetime | None = None
    issues: list[str] = field(default_factory=list)
    readable: bool = True
    """False when the sensor has a value but nothing could be read (a repair issue)."""


def _scale(unit: str) -> float:
    """Factor to €/kWh from the sensor's unit (attribute ``unit_of_measurement``)."""
    u = unit.replace(" ", "").lower()
    if "mwh" in u:
        return 0.001
    if u.startswith(("ct", "cent", "c/")):
        return 0.01
    return 1.0


def _time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        moment = value
    elif isinstance(value, str):
        try:
            moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    else:
        return None
    return moment.astimezone(UTC) if moment.tzinfo is not None else None


def _float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_forecast(state_value: str | None, attributes: Mapping[str, Any]) -> Forecast:
    """The forecast quarters from the sensor's attributes."""
    out = Forecast(made=_time(attributes.get("forecast_made")))
    rows = attributes.get("prices")
    has_value = state_value not in (None, "", "unknown", "unavailable")
    if not isinstance(rows, list):
        out.readable = not has_value
        if has_value:
            out.issues.append("no_prices_attribute")
        return out
    factor = _scale(str(attributes.get("unit_of_measurement") or attributes.get("unit") or "€/kWh"))
    without_band = 0
    for row in rows:
        if not isinstance(row, Mapping) or row.get("forecast") is not True:
            continue
        start, end, market = _time(row.get("start")), _time(row.get("end")), _float(row.get("market"))
        if start is None or market is None:
            continue
        low, high = _float(row.get("low")), _float(row.get("high"))
        band = low is not None and high is not None
        if not band:
            without_band += 1
        out.slots.append(
            ForecastSlot(
                start=start,
                end=end or start + QUARTER,
                market=market * factor,
                low=(low if low is not None else market) * factor,
                high=(high if high is not None else market) * factor,
                band=band,
            )
        )
    out.slots.sort(key=lambda s: s.start)
    if without_band:
        out.issues.append(f"{without_band} forecast quarters without low/high: market used")
    if has_value and not rows:
        out.readable = False
        out.issues.append("empty_prices")
    return out


def stale(forecast: Forecast, now: datetime) -> bool:
    """Not refreshed for more than 36 h: by the run time, else by the first forecast quarter."""
    if forecast.made is not None:
        return now - forecast.made > STALE_AFTER
    if forecast.slots:
        return now - forecast.slots[0].start > STALE_AFTER
    return False


@dataclass(slots=True)
class Extension:
    markets: list[tuple[datetime, float, bool]]
    used: list[ForecastSlot]
    reason: str | None
    """Why nothing was used (``no_slots``, ``stale``, ``gap``, ``no_known_prices``), else None."""


def extend_markets(
    markets: Sequence[tuple[datetime, float, bool]],
    forecast: Forecast,
    now: datetime,
    tz: tzinfo,
    days: int,
    which: str = VALUE_LOW,
) -> Extension:
    """The horizon with forecast quarters after the last known (Nord Pool) price.

    ``markets``: (start, market, indicative) from ``horizon_markets``; its indicative quarters
    (today's pattern standing in for tomorrow) are replaced. The forecast runs from the end of the
    last known price for ``days`` days (to local midnight), without a gap; the running quarter
    always keeps its known price.
    """
    known = [m for m in markets if not m[2]]
    if not known:
        return Extension(list(markets), [], "no_known_prices")
    if days <= 0 or not forecast.slots:
        return Extension(list(markets), [], "no_slots")
    if stale(forecast, now):
        return Extension(list(markets), [], "stale")
    known_end = known[-1][0] + QUARTER
    local_end = known_end.astimezone(tz)
    # Up to the local midnight after the known prices end, plus (days − 1) days. Local wall-clock
    # arithmetic, so a day of 23 or 25 hours ends at midnight too.
    end = local_end.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=days)
    end_utc = end.astimezone(UTC)
    by_start = {s.start: s for s in forecast.slots}
    used: list[ForecastSlot] = []
    t = known_end
    while t < end_utc:
        slot = by_start.get(t)
        if slot is None:
            break  # a gap: nothing after it
        used.append(slot)
        t += QUARTER
    if not used:
        return Extension(list(markets), [], "gap")
    out = [m for m in markets if not m[2] and m[0] < known_end]
    out.extend((s.start, s.value(which), True) for s in used)
    return Extension(out, used, None)
