"""Capacity per pack and temperature limits."""

from __future__ import annotations

import copy

import pytest

from conftest import load_fixture
from zem_core.device_table import (
    charging_allowed_by_temperature,
    delivering_allowed_by_temperature,
    pack_info,
    set_capacity,
)
from zem_core.zensdk import parse_report


def test_capacity_of_own_set() -> None:
    result = set_capacity(parse_report(load_fixture("standby")))
    assert result.capacity_kwh == pytest.approx(11.04)
    assert result.complete


def test_pack_type_alone_is_not_enough() -> None:
    assert pack_info("solarFlow2400Pro", 500, "JO2AEXAMPLE0001") is not None
    assert pack_info("solarFlow2400Pro", 500, "XO2AEXAMPLE0001") is None
    assert pack_info("otherModel", 500, "JO2AEXAMPLE0001") is None
    assert pack_info("otherModel", 350, "GO2AEXAMPLE0002") is not None  # AB3000L fits several models


def test_unknown_pack_is_reported() -> None:
    data = copy.deepcopy(load_fixture("standby"))
    data["packData"][1]["packType"] = 999
    result = set_capacity(parse_report(data))
    assert not result.complete
    assert result.unknown_packs == ("GO2AEXAMPLE0002",)
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
