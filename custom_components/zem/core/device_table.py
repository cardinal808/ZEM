"""Known Zendure models and battery packs.

Sources: product specifications of Zendure and our own measurements
(MEET-zensdk). `packType` alone is not unique across models, so packs are
matched on model + packType + the first letter of the pack's serial number
(SPEC-basis §3.4). Unknown packs need a capacity from the user.
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


@dataclass(frozen=True, slots=True)
class PackKey:
    """Lookup key: model ('*' for any), packType and serial prefix."""

    product: str
    pack_type: int
    serial_prefix: str


MODELS: Final[dict[str, ModelInfo]] = {
    "solarFlow2400Pro": ModelInfo(
        product="solarFlow2400Pro",
        name="SolarFlow 2400 Pro",
        max_charge_power=2400,
        max_deliver_power=2400,
        charge_temperature=(0.0, 55.0),
        deliver_temperature=(-20.0, 55.0),
    ),
    # AC-coupled version without solar inputs (seen in a user's report, product
    # "solarFlow2400AC+"). Power from the product specifications; temperature
    # limits assumed equal to the 2400 Pro (same housing and battery).
    "solarFlow2400AC+": ModelInfo(
        product="solarFlow2400AC+",
        name="SolarFlow 2400 AC+",
        max_charge_power=2400,
        max_deliver_power=2400,
        charge_temperature=(0.0, 55.0),
        deliver_temperature=(-20.0, 55.0),
    ),
}

PACKS: Final[dict[PackKey, PackInfo]] = {
    # Built-in battery of the SolarFlow 2400 Pro (measured: packType 500).
    PackKey("solarFlow2400Pro", 500, "J"): PackInfo("Built-in battery (SolarFlow 2400 Pro)", 2.40),
    # Built-in battery of the SolarFlow 2400 AC+ (2.4 kWh base capacity, also packType 500).
    PackKey("solarFlow2400AC+", 500, "J"): PackInfo("Built-in battery (SolarFlow 2400 AC+)", 2.40),
    # AB3000L add-on battery (measured: packType 350).
    PackKey("*", 350, "G"): PackInfo("AB3000L", 2.88),
}

TEMPERATURE_MARGIN: Final = 2.0
"""ZEM stays this many °C inside the model's limits (SPEC-basis §10)."""


def model_info(product: str) -> ModelInfo | None:
    """Limits of a known model, or None."""
    return MODELS.get(product)


def pack_info(product: str, pack_type: int, serial: str) -> PackInfo | None:
    """Look up a pack; model-specific entries win over generic ones."""
    prefix = serial[:1].upper()
    for key in (PackKey(product, pack_type, prefix), PackKey("*", pack_type, prefix)):
        info = PACKS.get(key)
        if info is not None:
            return info
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
