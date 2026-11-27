"""Screen *Stroom* (M6): energy per route today and how well the meter stayed at zero.

**Routes** come from the closed quarters of the cost log. Per quarter the energy is split
in a fixed order, so the numbers add up to what the log measured:

1. sun to the house, then sun to the battery, the rest of the sun to the grid;
2. battery to the house, the rest of the battery to the grid;
3. the grid covers the rest of the house and the rest of the charging.

Within a quarter import and export can both happen; the split works on the quarter's totals,
so it is an estimate per quarter, not per second.

**Airco** (B41): the battery does not feed it. Its share of the sun is the sun-to-house share in
proportion to the airco's share of the house; the grid gives the rest.

**Zero score:** every step of the controller adds the seconds since the previous step to a
5-minute bucket of the local day: *steering* when the controller regulates the meter
(delivering, charging from sun, idle because the demand is small, switching), and *in band*
when the meter is within ``band`` W of its target (0 W, or the airco's power when the airco is
kept out of the battery). Import and export beyond the target while steering are counted too.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Final

ZERO_REASONS: Final = frozenset({"delivering", "charging_solar", "idle_small", "switching"})
"""Reasons of the engine in which it steers the meter to its target."""

BUCKET_SECONDS: Final = 300
BUCKETS: Final = 24 * 3600 // BUCKET_SECONDS
MAX_GAP_SECONDS: Final = 30.0
"""A longer gap between two steps is not counted (HA hung, restart)."""


def _num(record: dict[str, Any], key: str) -> float:
    value = record.get(key)
    return float(value) if isinstance(value, int | float) else 0.0


ROUTES: Final = (
    "solar_house",
    "solar_battery",
    "solar_grid",
    "grid_house",
    "grid_battery",
    "battery_house",
    "battery_grid",
)


def split_quarter(record: dict[str, Any]) -> dict[str, float]:
    """kWh per route of one quarter (see the module text)."""
    solar = max(_num(record, "solar_kwh"), 0.0)
    charge = max(_num(record, "charge_kwh"), 0.0)
    discharge = max(_num(record, "discharge_kwh"), 0.0)
    house = max(_num(record, "house_kwh"), 0.0)
    solar_house = min(solar, house)
    solar_battery = min(solar - solar_house, charge)
    solar_grid = solar - solar_house - solar_battery
    battery_house = min(discharge, house - solar_house)
    battery_grid = discharge - battery_house
    grid_house = max(house - solar_house - battery_house, 0.0)
    grid_battery = max(charge - solar_battery, 0.0)
    return {
        "solar_house": solar_house,
        "solar_battery": solar_battery,
        "solar_grid": solar_grid,
        "grid_house": grid_house,
        "grid_battery": grid_battery,
        "battery_house": battery_house,
        "battery_grid": battery_grid,
    }


def routes(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Routes, airco and shares over the given quarters (the panel's *Energie per route* and *Airco*)."""
    total = dict.fromkeys(ROUTES, 0.0)
    house = solar = 0.0
    grid_battery_cost = 0.0
    grid_battery_priced = 0.0
    airco = airco_solar = airco_grid = airco_cost = airco_priced = 0.0
    airco_seen = False
    last: str | None = None
    for record in records:
        if record.get("source") == "hourly":
            continue  # worked out later from hourly statistics: no quarters to split
        split = split_quarter(record)
        for key, value in split.items():
            total[key] += value
        h = max(_num(record, "house_kwh"), 0.0)
        house += h
        solar += max(_num(record, "solar_kwh"), 0.0)
        buy = record.get("buy")
        if isinstance(buy, int | float):
            grid_battery_cost += split["grid_battery"] * buy
            grid_battery_priced += split["grid_battery"]
        if record.get("excluded_kwh") is not None:
            airco_seen = True
            x = min(max(_num(record, "excluded_kwh"), 0.0), h) if h > 0 else 0.0
            from_solar = split["solar_house"] * x / h if h > 0 else 0.0
            from_grid = x - from_solar
            airco += x
            airco_solar += from_solar
            airco_grid += from_grid
            if isinstance(buy, int | float):
                airco_cost += from_grid * buy
                airco_priced += from_grid
        last = record.get("start", last)

    def r(value: float) -> float:
        return round(value, 3)

    return {
        "routes": {key: r(value) for key, value in total.items()},
        "house_kwh": r(house),
        "solar_kwh": r(solar),
        "self_use": None if solar < 0.01 else round((solar - total["solar_grid"]) / solar, 3),
        "own_source": None if house < 0.01 else round((total["solar_house"] + total["battery_house"]) / house, 3),
        "grid_battery_price": None if grid_battery_priced < 0.01 else round(grid_battery_cost / grid_battery_priced, 4),
        "airco": None
        if not airco_seen
        else {
            "kwh": r(airco),
            "share": None if house < 0.01 else round(airco / house, 3),
            "solar_kwh": r(airco_solar),
            "grid_kwh": r(airco_grid),
            "grid_cost": None if airco_priced < 0.01 and airco_grid >= 0.01 else round(airco_cost, 2),
            "grid_price": None if airco_priced < 0.01 else round(airco_cost / airco_priced, 4),
        },
        "last_quarter": last,
        "quarters": len([r_ for r_ in records if r_.get("source") != "hourly"]),
    }


@dataclass(slots=True)
class ZeroBucket:
    steering: float = 0.0
    in_band: float = 0.0
    import_wh: float = 0.0
    export_wh: float = 0.0
    abs_ws: float = 0.0
    """∫|deviation| dt while steering (W·s), for the mean deviation."""


@dataclass(slots=True)
class ZeroScore:
    """How well the meter stayed at its target today (see the module text)."""

    band: float = 50.0
    day: date | None = None
    buckets: dict[int, ZeroBucket] = field(default_factory=dict)
    _last: tuple[float, bool, float | None] | None = None
    """(monotonic time, steering, deviation W) of the previous step."""

    def add(self, now: float, day: date, seconds_of_day: float, steering: bool, deviation: float | None) -> None:
        """One step of the controller. The previous step's state counts for the time since it."""
        if day != self.day:
            self.day, self.buckets = day, {}
        previous, self._last = self._last, (now, steering, deviation)
        if previous is None:
            return
        at, was_steering, was_deviation = previous
        dt = now - at
        if dt <= 0 or dt > MAX_GAP_SECONDS:
            return
        index = min(int(max(seconds_of_day - dt, 0.0)) // BUCKET_SECONDS, BUCKETS - 1)
        bucket = self.buckets.setdefault(index, ZeroBucket())
        if not was_steering or was_deviation is None:
            return
        bucket.steering += dt
        bucket.abs_ws += abs(was_deviation) * dt
        if abs(was_deviation) <= self.band:
            bucket.in_band += dt
        if was_deviation > 0:
            bucket.import_wh += was_deviation * dt / 3600
        else:
            bucket.export_wh += -was_deviation * dt / 3600

    def view(self) -> dict[str, Any]:
        steering = sum(b.steering for b in self.buckets.values())
        in_band = sum(b.in_band for b in self.buckets.values())
        cells: list[list[float] | None] = [None] * BUCKETS
        for index, b in self.buckets.items():
            cells[index] = [
                round(b.steering),
                round(b.in_band),
                round(b.import_wh, 1),
                round(b.export_wh, 1),
            ]
        return {
            "date": None if self.day is None else self.day.isoformat(),
            "band_w": self.band,
            "bucket_s": BUCKET_SECONDS,
            "score": None if steering < 60 else round(in_band / steering, 3),
            "steering_s": round(steering),
            "import_kwh": round(sum(b.import_wh for b in self.buckets.values()) / 1000, 3),
            "export_kwh": round(sum(b.export_wh for b in self.buckets.values()) / 1000, 3),
            "mean_dev_w": None if steering < 60 else round(sum(b.abs_ws for b in self.buckets.values()) / steering),
            "buckets": cells,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "day": None if self.day is None else self.day.isoformat(),
            "buckets": {str(i): [b.steering, b.in_band, b.import_wh, b.export_wh, b.abs_ws] for i, b in self.buckets.items()},
        }

    def restore(self, data: dict[str, Any] | None, today: date) -> None:
        """Today's buckets from storage (after a restart); another day is dropped."""
        if not data or data.get("day") != today.isoformat():
            return
        self.day = today
        for key, values in (data.get("buckets") or {}).items():
            try:
                self.buckets[int(key)] = ZeroBucket(*(float(v) for v in values[:5]))
            except (TypeError, ValueError):
                continue


REG_WINDOW_SECONDS: Final = 600
REG_JUMP_W: Final = 150.0
"""A deviation beyond this is a peak; leaving the band towards it starts a recovery."""


@dataclass(slots=True)
class RegulationLog:
    """The last 10 minutes of the controller, one sample per second (card *Regeling*).

    Per sample: seconds before *now*, P1, the meter's target (0 W or the airco), the setpoint
    asked of the sets and the battery power measured (both + charging), and whether it steered.
    """

    band: float = 50.0
    samples: list[tuple[float, float | None, float, int, float | None, bool]] = field(default_factory=list)

    def add(self, now: float, grid: float | None, target: float, setpoint: int, battery: float | None, steering: bool) -> None:
        if self.samples and now - self.samples[-1][0] < 1.0:
            self.samples[-1] = (self.samples[-1][0], grid, target, setpoint, battery, steering)
        else:
            self.samples.append((now, grid, target, setpoint, battery, steering))
        cut = now - REG_WINDOW_SECONDS
        while self.samples and self.samples[0][0] < cut:
            self.samples.pop(0)

    def view(self, now: float) -> dict[str, Any]:
        rows = [
            [round(at - now, 1), None if g is None else round(g), round(t), s, None if b is None else round(b), steer]
            for at, g, t, s, b, steer in self.samples
        ]
        follow = [abs(s - b) for _at, _g, _t, s, b, steer in self.samples if steer and b is not None]
        peaks = 0
        recoveries: list[float] = []
        out_since: float | None = None
        peaked = False
        for at, g, t, _s, _b, steer in self.samples:
            if not steer or g is None:
                out_since, peaked = None, False
                continue
            dev = abs(g - t)
            if dev > self.band:
                if out_since is None:
                    out_since = at
                if dev > REG_JUMP_W and not peaked:
                    peaks += 1
                    peaked = True
            elif out_since is not None:
                if peaked:
                    recoveries.append(at - out_since)
                out_since, peaked = None, False
        recoveries.sort()
        return {
            "window_s": REG_WINDOW_SECONDS,
            "band_w": self.band,
            "samples": rows,
            "follow_w": None if not follow else round(sum(follow) / len(follow)),
            "peaks": peaks,
            "recovery_s": None if not recoveries else round(recoveries[len(recoveries) // 2], 1),
        }
