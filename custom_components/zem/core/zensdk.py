"""Interpret and build messages of the Zendure zenSDK local API.

Field meanings and scales come from the public zenSDK documentation and
from our own measurements (MEET-zensdk). Nothing here talks to the network;
see ``client.py`` for that.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Final

from .models import (
    AcMode,
    GridReverse,
    PackReport,
    PackState,
    SetReport,
    SetStatus,
)

# --- Scales -----------------------------------------------------------------

KELVIN_TENTHS_OFFSET: Final = 2731
"""Temperatures are reported in 0.1 K: (raw − 2731) / 10 = °C."""

UNKNOWN_REMAINING_MINUTES: Final = 59940
"""`remainOutTime` value the set reports when the time is unknown."""

MAX_REQUEST_BYTES: Final = 512
"""Largest request body the local API accepts (zenSDK documentation)."""

ACTIVE_POWER_THRESHOLD: Final = 20.0
"""Below this many W (absolute) the set counts as idle."""

# --- Write rules ------------------------------------------------------------

WRITABLE_PROPERTIES: Final = frozenset({"acMode", "inputLimit", "outputLimit", "smartMode", "socSet", "minSoc", "gridReverse"})
"""The only properties ZEM ever writes (SPEC-basis §3.2)."""

NEVER_WRITE: Final = frozenset({"gridStandard", "gridOffMode", "batCalTime", "inverseMaxPower", "Fanmode", "Fanspeed", "lampSwitch"})
"""Installation or manufacturer settings; ZEM must never write these."""

MIN_SOC_RANGE: Final = (5.0, 50.0)
"""Allowed minimum SOC in % (the app does not go below 5 %)."""
MAX_SOC_RANGE: Final = (70.0, 100.0)
"""Allowed maximum SOC in %."""


class ZenSdkError(ValueError):
    """A report could not be interpreted or a command is not allowed."""


# --- Small helpers ------------------------------------------------------------


def _num(props: Mapping[str, Any], key: str, default: float | None = None) -> float | None:
    value = props.get(key, default)
    if value is None:
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except ValueError:
        return default


def _int(props: Mapping[str, Any], key: str) -> int | None:
    value = _num(props, key)
    return None if value is None else int(value)


def _power(props: Mapping[str, Any], key: str) -> float:
    value = _num(props, key, 0.0)
    return max(0.0, value if value is not None else 0.0)


def temperature_c(raw: float | None) -> float | None:
    """Convert a temperature in 0.1 K to °C."""
    if raw is None or raw <= 0:
        return None
    return round((raw - KELVIN_TENTHS_OFFSET) / 10, 1)


def signed_int16(raw: int) -> int:
    """Interpret an unsigned 16-bit value as two's complement."""
    raw &= 0xFFFF
    return raw - 0x10000 if raw >= 0x8000 else raw


def per_mille_to_percent(raw: float | None) -> float | None:
    """SOC limits are stored in 0.1 %: 1000 = 100 %."""
    return None if raw is None else raw / 10


def _enum(enum_type: type[AcMode] | type[PackState] | type[GridReverse], raw: int | None) -> Any:
    if raw is None:
        return None
    try:
        return enum_type(raw)
    except ValueError:
        return None


# --- Parsing ------------------------------------------------------------------


def parse_pack(raw: Mapping[str, Any]) -> PackReport:
    """Interpret one entry of ``packData``."""
    state = _enum(PackState, _int(raw, "state"))
    power = _power(raw, "power")
    if state is PackState.DELIVERING:
        power = -power
    elif state is not PackState.CHARGING:
        power = 0.0

    voltage_raw = _num(raw, "totalVol")
    current_raw = _int(raw, "batcur")
    vmax = _num(raw, "maxVol")
    vmin = _num(raw, "minVol")
    return PackReport(
        serial=str(raw.get("sn", "")),
        pack_type=int(_num(raw, "packType", 0) or 0),
        soc=float(_num(raw, "socLevel", 0.0) or 0.0),
        state=state,
        power=power,
        max_temperature=temperature_c(_num(raw, "maxTemp")),
        voltage=None if voltage_raw is None else voltage_raw / 100,
        current=None if current_raw is None else signed_int16(current_raw) / 10,
        cell_voltage_max=None if vmax is None else vmax / 100,
        cell_voltage_min=None if vmin is None else vmin / 100,
        firmware=_int(raw, "softVersion"),
    )


def parse_report(data: Mapping[str, Any]) -> SetReport:
    """Interpret a full ``/properties/report`` response.

    Raises ``ZenSdkError`` when the response is unusable (no properties,
    SOC out of range); such a set counts as offline (SPEC-meerdere-sets §2.4).
    """
    props = data.get("properties")
    if not isinstance(props, Mapping):
        raise ZenSdkError("report has no properties")

    soc = _num(props, "electricLevel")
    if soc is None or not 0 <= soc <= 100:
        raise ZenSdkError(f"implausible state of charge: {soc!r}")

    packs_raw = data.get("packData") or []
    if not isinstance(packs_raw, list):
        raise ZenSdkError("packData is not a list")
    packs = tuple(parse_pack(p) for p in packs_raw if isinstance(p, Mapping))

    grid_in = _power(props, "gridInputPower")
    home_out = _power(props, "outputHomePower")
    solar_inputs = tuple(
        _power(props, key)
        for key in ("solarPower1", "solarPower2", "solarPower3", "solarPower4", "solarPower5", "solarPower6")
        if key in props
    )
    battery_dc = round(sum(p.power for p in packs), 1) if packs else None

    soc_limit = _int(props, "socLimit") or 0
    remaining = _int(props, "remainOutTime")
    if remaining is not None and remaining >= UNKNOWN_REMAINING_MINUTES:
        remaining = None
    bat_volt = _num(props, "BatVolt")

    return SetReport(
        serial=str(data.get("sn", "")),
        product=str(data.get("product", "")),
        timestamp=_int(data, "timestamp"),
        soc=soc,
        grid_input_power=grid_in,
        output_home_power=home_out,
        charge_power_ac=_power(props, "outputPackPower"),
        deliver_power_ac=_power(props, "packInputPower"),
        solar_power=_power(props, "solarInputPower"),
        solar_power_inputs=solar_inputs,
        offgrid_power=_power(props, "gridOffPower"),
        battery_power_ac=grid_in - home_out,
        battery_power_dc=battery_dc,
        ac_mode=_enum(AcMode, _int(props, "acMode")),
        input_limit=_int(props, "inputLimit") or 0,
        output_limit=_int(props, "outputLimit") or 0,
        smart_mode=_int(props, "smartMode"),
        pack_state=_enum(PackState, _int(props, "packState")),
        min_soc=per_mille_to_percent(_num(props, "minSoc")),
        max_soc=per_mille_to_percent(_num(props, "socSet")),
        charge_max_limit=_int(props, "chargeMaxLimit"),
        inverse_max_power=_int(props, "inverseMaxPower"),
        grid_reverse=_enum(GridReverse, _int(props, "gridReverse")),
        reverse_state=_int(props, "reverseState"),
        bypass=(_int(props, "pass") or 0) > 0,
        calibrating=(_int(props, "socStatus") or 0) == 1,
        soc_limit_charge_stopped=bool(soc_limit & 0x1),
        soc_limit_discharge_stopped=bool(soc_limit & 0x2),
        fault=bool(_int(props, "is_error")) or (_int(props, "faultLevel") or 0) > 0,
        fault_level=_int(props, "faultLevel") or 0,
        heating=bool(_int(props, "heatState")),
        enclosure_temperature=temperature_c(_num(props, "hyperTmp")),
        remaining_discharge_minutes=remaining,
        battery_voltage=None if bat_volt is None else bat_volt / 100,
        rssi=_int(props, "rssi"),
        pack_count=_int(props, "packNum") or len(packs),
        packs=packs,
    )


# --- Derived values -----------------------------------------------------------


def derive_status(
    report: SetReport,
    min_soc: float,
    max_soc: float,
    margin: float = 0.5,
) -> SetStatus:
    """Status of a set that answered (offline is decided by the caller).

    Order of precedence: fault, calibration, bypass, full/empty, direction,
    standby. ``min_soc`` and ``max_soc`` are ZEM's own limits in %.
    """
    if report.fault:
        return SetStatus.FAULT
    if report.calibrating:
        return SetStatus.CALIBRATING
    if report.bypass:
        return SetStatus.BYPASS
    power = report.battery_power_ac
    if power > ACTIVE_POWER_THRESHOLD or report.pack_state is PackState.CHARGING:
        if report.soc >= max_soc - margin or report.soc_limit_charge_stopped:
            return SetStatus.FULL
        return SetStatus.CHARGING
    if power < -ACTIVE_POWER_THRESHOLD or report.pack_state is PackState.DELIVERING:
        if report.soc <= min_soc + margin or report.soc_limit_discharge_stopped:
            return SetStatus.EMPTY
        return SetStatus.DISCHARGING
    if report.soc >= max_soc - margin or report.soc_limit_charge_stopped:
        return SetStatus.FULL
    if report.soc <= min_soc + margin or report.soc_limit_discharge_stopped:
        return SetStatus.EMPTY
    return SetStatus.STANDBY


def conversion_efficiency(report: SetReport, min_power: float = 100.0) -> tuple[AcMode, float] | None:
    """Instantaneous AC↔battery efficiency from one report.

    Charging: battery side / AC side. Delivering: AC side / battery side.
    Returns None when the set is idle or the values are implausible. The
    learning module only uses stable samples (SPEC-planner §6).
    """
    dc = report.battery_power_dc
    if dc is None:
        return None
    if report.charge_power_ac >= min_power and dc > 0:
        eta = dc / report.charge_power_ac
        mode = AcMode.CHARGE
    elif report.deliver_power_ac >= min_power and dc < 0:
        eta = report.deliver_power_ac / -dc
        mode = AcMode.DELIVER
    else:
        return None
    if not 0.5 <= eta <= 1.0:
        return None
    return mode, round(eta, 4)


# --- Commands -------------------------------------------------------------------


def power_command(
    watts: int,
    *,
    include_ac_mode: bool,
    charge_max: int | None = None,
    deliver_max: int | None = None,
) -> dict[str, int]:
    """Power command in RAM (``smartMode`` 1). + charge, − deliver, 0 stop.

    ``include_ac_mode`` should only be true on a real change of direction
    (SPEC-basis §3.2). Limits are clamped to the device limits when given.
    """
    if watts > 0:
        value = min(watts, charge_max) if charge_max is not None else watts
        props = {"inputLimit": int(value), "outputLimit": 0, "smartMode": 1}
        if include_ac_mode:
            props = {"acMode": int(AcMode.CHARGE), **props}
    elif watts < 0:
        value = min(-watts, deliver_max) if deliver_max is not None else -watts
        props = {"outputLimit": int(value), "inputLimit": 0, "smartMode": 1}
        if include_ac_mode:
            props = {"acMode": int(AcMode.DELIVER), **props}
    else:
        props = {"inputLimit": 0, "outputLimit": 0, "smartMode": 1}
    return props


def standby_command() -> dict[str, int]:
    """Standby in flash: the set stays idle after a restart."""
    return {"inputLimit": 0, "outputLimit": 0, "smartMode": 0}


def soc_limits_command(min_soc: float, max_soc: float) -> dict[str, int]:
    """SOC limits in flash (they must survive a restart of the set)."""
    lo, hi = MIN_SOC_RANGE
    if not lo <= min_soc <= hi:
        raise ZenSdkError(f"minimum SOC {min_soc} outside {lo}–{hi} %")
    lo, hi = MAX_SOC_RANGE
    if not lo <= max_soc <= hi:
        raise ZenSdkError(f"maximum SOC {max_soc} outside {lo}–{hi} %")
    return {"minSoc": round(min_soc * 10), "socSet": round(max_soc * 10), "smartMode": 0}


def grid_reverse_command(allow_export: bool) -> dict[str, int]:
    """Allow or block export of surplus solar (does not stop battery export)."""
    value = GridReverse.ALLOWED if allow_export else GridReverse.BLOCKED
    return {"gridReverse": int(value)}


def validate_command(props: Mapping[str, int]) -> None:
    """Refuse anything ZEM is not allowed to write, or values out of range."""
    if not props:
        raise ZenSdkError("empty command")
    for key, value in props.items():
        if key in NEVER_WRITE or key not in WRITABLE_PROPERTIES:
            raise ZenSdkError(f"property {key!r} may not be written")
        if not isinstance(value, int) or isinstance(value, bool):
            raise ZenSdkError(f"property {key!r} must be an integer")
    checks = {
        "acMode": (1, 2),
        "smartMode": (0, 1),
        "inputLimit": (0, 10000),
        "outputLimit": (0, 10000),
        "socSet": (700, 1000),
        "minSoc": (0, 500),
        "gridReverse": (0, 2),
    }
    for key, value in props.items():
        lo, hi = checks[key]
        if not lo <= value <= hi:
            raise ZenSdkError(f"property {key!r}={value} outside {lo}–{hi}")


def encode_write_request(serial: str, props: Mapping[str, int]) -> bytes:
    """Body for ``POST /properties/write``; validated and below 512 bytes."""
    if not serial:
        raise ZenSdkError("serial number missing")
    validate_command(props)
    body = json.dumps({"sn": serial, "properties": dict(props)}, separators=(",", ":")).encode()
    if len(body) > MAX_REQUEST_BYTES:
        raise ZenSdkError(f"request of {len(body)} bytes exceeds {MAX_REQUEST_BYTES}")
    return body
