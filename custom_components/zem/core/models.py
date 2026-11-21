"""Data models for one Zendure set, as read from the local zenSDK API."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, StrEnum


class AcMode(IntEnum):
    """Direction of the AC side, as written to and reported by the set."""

    CHARGE = 1
    DELIVER = 2


class PackState(IntEnum):
    """State of the battery as a whole or of a single pack."""

    STANDBY = 0
    CHARGING = 1
    DELIVERING = 2


class GridReverse(IntEnum):
    """Export of surplus solar power to the grid (see TOETS-gridreverse)."""

    OFF = 0
    ALLOWED = 1
    BLOCKED = 2


class SetStatus(StrEnum):
    """Derived status of a set (SPEC-basis §3.3, SPEC-entiteiten §3)."""

    OFFLINE = "offline"
    FAULT = "fault"
    CALIBRATING = "calibrating"
    BYPASS = "bypass"
    STANDBY = "standby"
    CHARGING = "charging"
    DISCHARGING = "discharging"
    FULL = "full"
    EMPTY = "empty"


@dataclass(frozen=True, slots=True)
class PackReport:
    """One battery pack, values already scaled to SI units."""

    serial: str
    pack_type: int
    soc: float
    """State of charge in %."""
    state: PackState | None
    power: float
    """Battery-side power in W, signed: + charging, − delivering."""
    max_temperature: float | None
    """Highest cell temperature in °C."""
    voltage: float | None
    """Pack voltage in V."""
    current: float | None
    """Pack current in A, signed: + charging, − delivering."""
    cell_voltage_max: float | None
    cell_voltage_min: float | None
    firmware: int | None


@dataclass(frozen=True, slots=True)
class SetReport:
    """One report of a set, interpreted and scaled.

    All power values are in W. ``battery_power_ac`` and
    ``battery_power_dc`` follow the ZEM sign convention.
    """

    serial: str
    product: str
    timestamp: int | None

    soc: float
    """Average state of charge in %."""

    grid_input_power: float
    """AC power the set takes from the house wiring (charging), W ≥ 0."""
    output_home_power: float
    """AC power the set delivers to the house wiring, W ≥ 0."""
    charge_power_ac: float
    """`outputPackPower`: AC-side charging power, W ≥ 0."""
    deliver_power_ac: float
    """`packInputPower`: AC-side delivering power, W ≥ 0."""
    solar_power: float
    solar_power_inputs: tuple[float, ...]
    offgrid_power: float

    battery_power_ac: float
    """Net AC exchange of the set with the house: + charging, − delivering.

    Includes solar from the set's own PV inputs (SPEC-basis §3.1).
    """
    battery_power_dc: float | None
    """Sum of the packs' battery-side power: + charging, − delivering."""

    ac_mode: AcMode | None
    input_limit: int
    output_limit: int
    smart_mode: int | None
    pack_state: PackState | None

    min_soc: float | None
    """Minimum SOC stored on the set, in %."""
    max_soc: float | None
    """Maximum SOC stored on the set, in %."""

    charge_max_limit: int | None
    inverse_max_power: int | None
    grid_reverse: GridReverse | None
    reverse_state: int | None

    bypass: bool
    calibrating: bool
    soc_limit_charge_stopped: bool
    soc_limit_discharge_stopped: bool
    fault: bool
    fault_level: int
    heating: bool

    enclosure_temperature: float | None
    remaining_discharge_minutes: int | None
    """Minutes the set reports until empty; None when unknown."""
    battery_voltage: float | None
    rssi: int | None
    pack_count: int
    packs: tuple[PackReport, ...] = field(default_factory=tuple)

    @property
    def max_pack_temperature(self) -> float | None:
        """Highest temperature over all packs, in °C."""
        temps = [p.max_temperature for p in self.packs if p.max_temperature is not None]
        return max(temps) if temps else None
