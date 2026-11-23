"""Capacity per pack and temperature limits."""

from __future__ import annotations

import copy

import pytest

from conftest import load_fixture
from zephyr_core.device_table import (
    charging_allowed_by_temperature,
    delivering_allowed_by_temperature,
    model_info,
    pack_info,
    set_capacity,
)
from zephyr_core.zensdk import parse_report


def test_capacity_of_own_set() -> None:
    result = set_capacity(parse_report(load_fixture("standby")))
    assert result.capacity_kwh == pytest.approx(11.04)
    assert result.complete


def test_solarflow_2400_ac_plus() -> None:
    report = parse_report(load_fixture("ac_plus_grid_charge"))
    assert report.product == "solarFlow2400AC+"
    result = set_capacity(report)
    assert result.capacity_kwh == pytest.approx(2.40 + 2 * 2.88)
    assert result.complete
    assert report.battery_power_ac == 2386  # charging from the grid


@pytest.mark.parametrize(
    ("product", "pack_type", "serial", "name", "kwh"),
    [
        ("solarFlow2400Pro", 500, "JO2AEXAMPLE0001", "Built-in battery (2.4 kWh)", 2.40),
        ("solarFlow2400AC+", 500, "JO4AEXAMPLE0001", "Built-in battery (2.4 kWh)", 2.40),
        ("solarFlow2400Pro", 350, "GO2AEXAMPLE0002", "AB3000L", 2.88),
        ("solarFlow2400AC", 300, "FO2AEXAMPLE0003", "AB3000X", 2.88),
        ("solarFlow800Pro", 0, "CO4FEXAMPLE0004", "AB2000S", 1.92),
        ("solarFlow1600AC+", 0, "CO4EEXAMPLE0005", "AB2000X", 1.92),
        ("solarFlow800", 0, "CO4AEXAMPLE0006", "AB2000", 1.92),
        ("solarFlow800", 70, "BO1AEXAMPLE0007", "AB1000S", 0.96),
        ("solarFlow4000AC+", 70, "BO1AEXAMPLE0008", "Built-in battery (SolarFlow 4000 AC+)", 8.00),
        ("solarFlow800", 0, "AO1AEXAMPLE0009", "AB1000", 0.96),
        ("solarFlow800", 0, "AO13EXAMPLE0010", "Built-in battery (AIO 2400)", 2.40),
    ],
)
def test_packs_by_serial(product: str, pack_type: int, serial: str, name: str, kwh: float) -> None:
    info = pack_info(product, pack_type, serial)
    assert info is not None
    assert (info.name, info.capacity_kwh) == (name, kwh)


def test_unknown_serial_prefix() -> None:
    assert pack_info("solarFlow2400Pro", 500, "XO2AEXAMPLE0001") is None
    assert pack_info("solarFlow2400Pro", 500, "J") is None


def test_models_case_insensitive() -> None:
    assert model_info("solarflow2400ac+") is not None
    assert model_info("solarFlow800Pro") is not None


def test_unknown_pack_is_reported() -> None:
    data = copy.deepcopy(load_fixture("standby"))
    data["packData"][1]["sn"] = "XO2AEXAMPLE0002"
    result = set_capacity(parse_report(data))
    assert not result.complete
    assert result.unknown_packs == ("XO2AEXAMPLE0002",)
    assert result.capacity_kwh == pytest.approx(11.04 - 2.88)


def test_user_override_wins() -> None:
    assert set_capacity(parse_report(load_fixture("standby")), override_kwh=10.0).capacity_kwh == 10.0


@pytest.mark.parametrize(
    ("temp", "charge", "deliver"),
    [(18.0, True, True), (1.5, False, True), (-19.0, False, False), (52.0, True, True), (54.0, False, False), (None, True, True)],
)
def test_temperature_limits(temp: float | None, charge: bool, deliver: bool) -> None:
    assert charging_allowed_by_temperature("solarFlow2400Pro", temp) is charge
    assert delivering_allowed_by_temperature("solarFlow2400Pro", temp) is deliver


def test_unknown_model_does_not_block() -> None:
    assert charging_allowed_by_temperature("unknownModel", 80.0)
