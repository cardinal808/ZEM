"""Tariff table: energy tax and VAT per country, margins per supplier (B28).

The table lives in the repository (``custom_components/zephyr/data/tariffs.json``)
and is kept up to date with pull requests; a format check runs in CI
(``tests/core/test_tariff_table.py``). ZEPHYR ships the table with each version
and fetches the newest one from GitHub once a month.

A supplier period is only offered once it is ``verified`` (amounts checked by a
user of that supplier against an invoice), as B28 requires.

Pure Python: parsing, validation and lookup. Fetching happens in the HA layer.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from .costs import Tariffs

FORMAT = 1


class TableError(ValueError):
    """The tariff table does not have the expected format."""


@dataclass(frozen=True, slots=True)
class Dated:
    start: date
    value: float
    source: str = ""


@dataclass(frozen=True, slots=True)
class Country:
    vat: tuple[Dated, ...]
    energy_tax: tuple[Dated, ...]
    saldering_until: date


@dataclass(frozen=True, slots=True)
class SupplierPeriod:
    start: date
    markup_import: float
    markup_export: float
    solar_bonus: float
    export_vat_after_saldering: bool
    source: str
    checked: date
    verified: bool
    note: str = ""


@dataclass(frozen=True, slots=True)
class Supplier:
    key: str
    name: str
    country: str
    periods: tuple[SupplierPeriod, ...]


@dataclass(frozen=True, slots=True)
class TariffTable:
    updated: date
    countries: dict[str, Country] = field(default_factory=dict)
    suppliers: dict[str, Supplier] = field(default_factory=dict)

    def choices(self, *, include_unverified: bool = False) -> list[tuple[str, str]]:
        """(key, name) of the suppliers that can be chosen, sorted by name."""
        out = [(s.key, s.name) for s in self.suppliers.values() if include_unverified or any(p.verified for p in s.periods)]
        return sorted(out, key=lambda item: item[1].lower())

    def tariffs(self, key: str, day: date, *, fixed_month: float = 0.0, include_unverified: bool = False) -> Tariffs | None:
        """Tariffs of supplier ``key`` on ``day``; None when unknown, unverified or not yet valid."""
        supplier = self.suppliers.get(key)
        if supplier is None:
            return None
        country = self.countries[supplier.country]
        period = _latest([p for p in supplier.periods if include_unverified or p.verified], day)
        vat = _latest(list(country.vat), day)
        tax = _latest(list(country.energy_tax), day)
        if period is None or vat is None or tax is None:
            return None
        return Tariffs(
            energy_tax=tax.value,
            vat=vat.value,
            markup_import=period.markup_import,
            markup_export=period.markup_export,
            solar_bonus=period.solar_bonus,
            export_vat_after_saldering=period.export_vat_after_saldering,
            fixed_month=fixed_month,
            saldering_until=country.saldering_until,
            source=f"{supplier.name} ({period.start.isoformat()}, checked {period.checked.isoformat()}; table {self.updated.isoformat()})",
        )


def _latest[T: (Dated, SupplierPeriod)](items: list[T], day: date) -> T | None:
    valid = [i for i in items if i.start <= day]
    return max(valid, key=lambda i: i.start) if valid else None


# --- parsing --------------------------------------------------------------------------


def _date(value: Any, where: str) -> date:
    if not isinstance(value, str):
        raise TableError(f"{where}: date expected (YYYY-MM-DD)")
    try:
        return date.fromisoformat(value)
    except ValueError as err:
        raise TableError(f"{where}: invalid date {value!r}") from err


def _number(value: Any, where: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TableError(f"{where}: number expected")
    if not low <= value <= high:
        raise TableError(f"{where}: {value} outside {low}–{high}")
    return float(value)


def _mapping(value: Any, where: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TableError(f"{where}: object expected")
    return value


def _sorted_unique(items: list[Any], where: str) -> None:
    starts = [i.start for i in items]
    if not starts:
        raise TableError(f"{where}: at least one entry needed")
    if starts != sorted(starts) or len(set(starts)) != len(starts):
        raise TableError(f"{where}: 'from' dates must be ascending and unique")


def _dated(items: Any, where: str, low: float, high: float) -> tuple[Dated, ...]:
    if not isinstance(items, list):
        raise TableError(f"{where}: list expected")
    out = []
    for n, raw in enumerate(items):
        entry = _mapping(raw, f"{where}[{n}]")
        out.append(
            Dated(
                _date(entry.get("from"), f"{where}[{n}].from"),
                _number(entry.get("value"), f"{where}[{n}].value", low, high),
                str(entry.get("source", "")),
            )
        )
    _sorted_unique(out, where)
    return tuple(out)


def parse_table(data: Any) -> TariffTable:
    """Validate and read a tariff table; raises TableError with the place of the problem."""
    root = _mapping(data, "table")
    if root.get("format") != FORMAT:
        raise TableError(f"table: format {root.get('format')!r} not supported (expected {FORMAT})")
    updated = _date(root.get("updated"), "updated")
    countries: dict[str, Country] = {}
    for code, raw in _mapping(root.get("countries"), "countries").items():
        where = f"countries.{code}"
        entry = _mapping(raw, where)
        countries[code] = Country(
            vat=_dated(entry.get("vat"), f"{where}.vat", 0, 30),
            energy_tax=_dated(entry.get("energy_tax"), f"{where}.energy_tax", 0, 1),
            saldering_until=_date(entry.get("saldering_until", "1970-01-01"), f"{where}.saldering_until"),
        )
    suppliers: dict[str, Supplier] = {}
    for key, raw in _mapping(root.get("suppliers"), "suppliers").items():
        where = f"suppliers.{key}"
        if not key.isidentifier() or key != key.lower():
            raise TableError(f"{where}: key must be lower case letters, digits and _")
        entry = _mapping(raw, where)
        name = entry.get("name")
        country = entry.get("country")
        if not isinstance(name, str) or not name:
            raise TableError(f"{where}.name: text expected")
        if country not in countries:
            raise TableError(f"{where}.country: {country!r} not in countries")
        periods_raw = entry.get("periods")
        if not isinstance(periods_raw, list):
            raise TableError(f"{where}.periods: list expected")
        periods = []
        for n, praw in enumerate(periods_raw):
            pw = f"{where}.periods[{n}]"
            p = _mapping(praw, pw)
            source = p.get("source")
            if not isinstance(source, str) or not source.startswith("http"):
                raise TableError(f"{pw}.source: link to the supplier's tariff page expected")
            for flag in ("verified", "export_vat_after_saldering"):
                if not isinstance(p.get(flag, False), bool):
                    raise TableError(f"{pw}.{flag}: true or false expected")
            periods.append(
                SupplierPeriod(
                    start=_date(p.get("from"), f"{pw}.from"),
                    markup_import=_number(p.get("markup_import"), f"{pw}.markup_import", -0.2, 0.2),
                    markup_export=_number(p.get("markup_export"), f"{pw}.markup_export", -0.2, 0.2),
                    solar_bonus=_number(p.get("solar_bonus", 0.0), f"{pw}.solar_bonus", 0, 50),
                    export_vat_after_saldering=bool(p.get("export_vat_after_saldering", False)),
                    source=source,
                    checked=_date(p.get("checked"), f"{pw}.checked"),
                    verified=bool(p.get("verified", False)),
                    note=str(p.get("note", "")),
                )
            )
        _sorted_unique(periods, f"{where}.periods")
        suppliers[key] = Supplier(key, name, str(country), tuple(periods))
    return TariffTable(updated, countries, suppliers)


def newest(*tables: TariffTable | None) -> TariffTable | None:
    """The table with the latest ``updated`` date (the first one on a tie)."""
    present = [t for t in tables if t is not None]
    return max(present, key=lambda t: t.updated) if present else None
