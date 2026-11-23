"""Known Zendure models and battery packs.

Sources: product specifications of Zendure, the official Zendure integration
(Zendure/Zendure-HA, MIT licence; facts only) and our own measurements
(MEET-zensdk). Packs are recognised by their serial number; `packType` is
only needed to tell the 8 kWh pack of a SolarFlow 4000 from an AB1000S.
Unknown packs need a capacity from the user.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from .models import SetReport


@dataclass(frozen=True, slots=True)
class ModelInfo:
    """Limits of one model of set."""

    product: str
    name: str
    max_charge_power: int
    max_deliver_power: int
    charge_temperature: tuple[float, float]
    """Allowed charging temperature range in °C."""
    deliver_temperature: tuple[float, float]
    """Allowed discharging temperature range in °C."""


@dataclass(frozen=True, slots=True)
class PackInfo:
    """Capacity of one kind of pack."""

    name: str
    capacity_kwh: float


# Temperature limits: the LiFePO4 ranges of the SolarFlow 2400 Pro, assumed for
# the other models too until their own values are known.
_CHARGE_T: Final = (0.0, 55.0)
_DELIVER_T: Final = (-20.0, 55.0)


def _key(product: str) -> str:
    """Product name as a lookup key: lower case, without spaces, dashes and underscores.

    Firmware and apps spell names differently ("solarFlow800Plus", "SolarFlow800 Plus",
    "SolarFlow-800-Plus"); they are the same model.
    """
    return "".join(ch for ch in product.lower() if ch not in " -_")


def _model(product: str, name: str, charge: int, deliver: int) -> ModelInfo:
    return ModelInfo(product, name, charge, deliver, _CHARGE_T, _DELIVER_T)


# Models with the local zenSDK API. Keys are the `product` of the report in
# lower case. Power: product specifications and the official Zendure
# integration (Zendure/Zendure-HA, MIT); the set's own chargeMaxLimit and
# inverseMaxPower in the report always win when ZEPHYR controls it.
MODELS: Final[dict[str, ModelInfo]] = {
    _key(m.product): m
    for m in (
        _model("solarFlow800", "SolarFlow 800", 1000, 800),
        _model("solarFlow800Plus", "SolarFlow 800 Plus", 1000, 800),
        _model("solarFlow800Pro", "SolarFlow 800 Pro", 1000, 800),
        _model("solarFlow1600AC+", "SolarFlow 1600 AC+", 1600, 1600),
        _model("solarFlow2400AC", "SolarFlow 2400 AC", 2400, 2400),
        _model("solarFlow2400AC+", "SolarFlow 2400 AC+", 2400, 2400),
        _model("solarFlow2400Pro", "SolarFlow 2400 Pro", 2400, 2400),  # measured
        _model("solarFlow4000AC+", "SolarFlow 4000 AC+", 2400, 2400),
    )
}

# Packs are recognised by their serial number (packType is not unique and
# is "reserved" in the zenSDK documentation). Facts taken from the official
# Zendure integration (Zendure/Zendure-HA, MIT) and our own measurements.
_AB1000 = PackInfo("AB1000", 0.96)
_AB1000S = PackInfo("AB1000S", 0.96)
_AIO2400 = PackInfo("Built-in battery (AIO 2400)", 2.40)
_AB3000 = PackInfo("AB3000X", 2.88)
_AB3000L = PackInfo("AB3000L", 2.88)
_BUILT_IN_2400 = PackInfo("Built-in battery (2.4 kWh)", 2.40)  # 2400 Pro (JO2A…), 2400 AC+ (JO4A…)
_BUILT_IN_8000 = PackInfo("Built-in battery (SolarFlow 4000 AC+)", 8.00)

TEMPERATURE_MARGIN: Final = 2.0
"""ZEPHYR stays this many °C inside the model's limits (SPEC-basis §10)."""


def model_info(product: str) -> ModelInfo | None:
    """Limits of a known model, or None."""
    return MODELS.get(_key(product))


def pack_info(product: str, pack_type: int, serial: str) -> PackInfo | None:
    """Recognise a pack by its serial number; None when unknown."""
    sn = serial.upper()
    if len(sn) < 4:
        return None
    first, fourth = sn[0], sn[3]
    match first:
        case "A":
            return _AIO2400 if fourth == "3" else _AB1000
        case "B":
            # packType 70 is the 8 kWh built-in battery only on a SolarFlow 4000;
            # other sets report 70 for an AB1000S as well.
            if pack_type == 70 and _key(product).startswith("solarflow4000"):
                return _BUILT_IN_8000
            return _AB1000S
        case "C":
            suffix = {"F": "S", "E": "X"}.get(fourth, "")
            return PackInfo(f"AB2000{suffix}", 1.92)  # also built into the 800 Plus/Pro and 1600 AC+
        case "F":
            return _AB3000
        case "G":
            return _AB3000L
        case "J":
            return _BUILT_IN_2400
    return None


@dataclass(frozen=True, slots=True)
class CapacityResult:
    """Capacity of a set and the packs that could not be identified."""

    capacity_kwh: float
    unknown_packs: tuple[str, ...]
    """Serial numbers of packs not in the table."""

    @property
    def complete(self) -> bool:
        return not self.unknown_packs


def set_capacity(report: SetReport, override_kwh: float | None = None) -> CapacityResult:
    """Usable nominal capacity of a set in kWh.

    A user override wins. Otherwise the sum of the known packs; unknown
    packs are listed so the UI can ask for the capacity.
    """
    if override_kwh is not None and override_kwh > 0:
        return CapacityResult(round(override_kwh, 3), ())
    total = 0.0
    unknown: list[str] = []
    for pack in report.packs:
        info = pack_info(report.product, pack.pack_type, pack.serial)
        if info is None:
            unknown.append(pack.serial)
        else:
            total += info.capacity_kwh
    return CapacityResult(round(total, 3), tuple(unknown))


def charging_allowed_by_temperature(product: str, temperature: float | None) -> bool:
    """False when the highest pack temperature is outside the safe range."""
    info = model_info(product)
    if info is None or temperature is None:
        return True
    lo, hi = info.charge_temperature
    return lo + TEMPERATURE_MARGIN <= temperature <= hi - TEMPERATURE_MARGIN


def delivering_allowed_by_temperature(product: str, temperature: float | None) -> bool:
    """False when the highest pack temperature is too high (or too low) to deliver."""
    info = model_info(product)
    if info is None or temperature is None:
        return True
    lo, hi = info.deliver_temperature
    return lo + TEMPERATURE_MARGIN <= temperature <= hi - TEMPERATURE_MARGIN
