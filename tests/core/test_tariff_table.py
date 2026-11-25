"""Tariff table (B28): the shipped file is valid (format check in CI), lookups and validation."""

from __future__ import annotations

import copy
import json
from datetime import date
from typing import Any

import pytest

from conftest import ROOT
from zephyr_core.tariff_table import TableError, newest, parse_table

SHIPPED = ROOT / "custom_components" / "zephyr" / "data" / "tariffs.json"


def _shipped() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(SHIPPED.read_text(encoding="utf-8"))
    return data


def test_shipped_table_is_valid() -> None:
    table = parse_table(_shipped())
    assert "NL" in table.countries
    assert table.suppliers
    for supplier in table.suppliers.values():
        assert supplier.periods[0].source.startswith("https://")


def _period(start: str, verified: bool, **values: Any) -> dict[str, Any]:
    return {"from": start, "source": "https://example.org", "checked": "2026-11-01", "verified": verified, **values}


def _table(verified: bool = True) -> dict[str, Any]:
    data = copy.deepcopy(_shipped())
    data["suppliers"] = {
        "test": {
            "name": "Test Energie",
            "country": "NL",
            "periods": [
                {
                    "from": "2026-01-01",
                    "markup_import": 0.02,
                    "markup_export": -0.01,
                    "source": "https://example.org",
                    "checked": "2026-11-01",
                    "verified": verified,
                },
                {
                    "from": "2026-07-01",
                    "markup_import": 0.03,
                    "markup_export": 0.0,
                    "solar_bonus": 5,
                    "source": "https://example.org",
                    "checked": "2026-11-01",
                    "verified": verified,
                },
            ],
        }
    }
    return data


def test_lookup_by_date() -> None:
    table = parse_table(_table())
    spring = table.tariffs("test", date(2026, 3, 1), fixed_month=12.0)
    summer = table.tariffs("test", date(2026, 8, 1))
    assert spring is not None and summer is not None
    assert (spring.markup_import, spring.markup_export, spring.fixed_month) == (0.02, -0.01, 12.0)
    assert (summer.markup_import, summer.solar_bonus) == (0.03, 5.0)
    assert spring.energy_tax == 0.09161 and spring.vat == 21.0
    assert "Test Energie" in spring.source
    assert table.tariffs("test", date(2025, 12, 31)) is None
    assert table.tariffs("unknown", date(2026, 3, 1)) is None


def test_unverified_suppliers_are_not_offered() -> None:
    table = parse_table(_table(verified=False))
    assert table.choices() == []
    assert table.tariffs("test", date(2026, 3, 1)) is None
    assert table.choices(include_unverified=True) == [("test", "Test Energie")]
    assert table.tariffs("test", date(2026, 3, 1), include_unverified=True) is not None


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda d: d.update(format=2), "format"),
        (lambda d: d["countries"]["NL"]["vat"][0].update(value=121), "outside"),
        (lambda d: d["suppliers"]["test"]["periods"][1].update({"from": "2025-01-01"}), "ascending"),
        (lambda d: d["suppliers"]["test"]["periods"][0].update(source="zonneplan.nl"), "link"),
        (lambda d: d["suppliers"]["test"].update(country="BE"), "country"),
        (lambda d: d["suppliers"]["test"]["periods"][0].update(markup_import="0,02"), "number"),
        (lambda d: d["suppliers"]["test"]["periods"][0].update(verified="yes"), "true or false"),
    ],
)
def test_invalid_tables_are_rejected(change: Any, message: str) -> None:
    data = _table()
    change(data)
    with pytest.raises(TableError, match=message):
        parse_table(data)


def test_newest_wins() -> None:
    old = parse_table(_table())
    data = _table()
    data["updated"] = "2027-01-15"
    new = parse_table(data)
    assert newest(old, new, None) is new
    assert newest(None) is None
