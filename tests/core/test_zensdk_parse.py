"""Parsing of real reports from our own set (serial numbers replaced)."""

from __future__ import annotations

import copy
import dataclasses

import pytest

from conftest import load_fixture
from zem_core.models import AcMode, GridReverse, PackState, SetStatus
from zem_core.zensdk import (
    ZenSdkError,
    conversion_efficiency,
    derive_status,
    parse_report,
    signed_int16,
    temperature_c,
)


def test_standby() -> None:
    r = parse_report(load_fixture("standby"))
    assert r.product == "solarFlow2400Pro"
    assert r.serial == "EEB4AEXAMPLE001"
    assert r.soc == 54
    assert r.battery_power_ac == 0
    assert r.battery_power_dc == 0
    assert r.ac_mode is AcMode.DELIVER  # last direction stays in the report
    assert r.smart_mode == 0
    assert r.pack_state is PackState.STANDBY
    assert r.min_soc == 10
    assert r.max_soc == 100
    assert r.remaining_discharge_minutes is None  # 59940 = unknown
    assert r.enclosure_temperature == 18.0
    assert r.grid_reverse is GridReverse.ALLOWED
    assert r.pack_count == 4 and len(r.packs) == 4
    assert r.battery_voltage == pytest.approx(49.35)
    assert derive_status(r, min_soc=10, max_soc=95) is SetStatus.STANDBY


def test_charging_2400() -> None:
    r = parse_report(load_fixture("charge_2400"))
    assert r.ac_mode is AcMode.CHARGE
    assert r.charge_power_ac == 2386  # outputPackPower = charging
    assert r.deliver_power_ac == 0
    assert r.battery_power_ac == 2386  # + = charging (B16)
    assert r.battery_power_dc == 2196
    assert r.input_limit == 2400 and r.output_limit == 0
    assert r.smart_mode == 1
    big = r.packs[0]
    assert big.pack_type == 500
    assert big.power == 883
    assert big.current == pytest.approx(17.6)
    assert big.voltage == pytest.approx(50.2)
    assert big.voltage is not None and big.current is not None
    assert big.voltage * big.current == pytest.approx(big.power, abs=2)
    assert derive_status(r, min_soc=10, max_soc=95) is SetStatus.CHARGING
    mode, eta = conversion_efficiency(r) or (None, 0.0)
    assert mode is AcMode.CHARGE
    assert eta == pytest.approx(2196 / 2386, abs=1e-4)


def test_delivering_760() -> None:
    r = parse_report(load_fixture("deliver_760"))
    assert r.ac_mode is AcMode.DELIVER
    assert r.deliver_power_ac == 760  # packInputPower = delivering
    assert r.battery_power_ac == -760
    assert r.battery_power_dc == -867
    assert r.packs[0].current == pytest.approx(-6.3)  # two's complement
    assert r.remaining_discharge_minutes == 427
    assert derive_status(r, min_soc=10, max_soc=95) is SetStatus.DISCHARGING
    mode, eta = conversion_efficiency(r) or (None, 0.0)
    assert mode is AcMode.DELIVER
    assert eta == pytest.approx(760 / 867, abs=1e-4)


def test_delivering_2400_with_export_blocked() -> None:
    r = parse_report(load_fixture("deliver_2400_export_blocked"))
    assert r.grid_reverse is GridReverse.BLOCKED
    assert r.reverse_state == 0  # not reliable without a Zendure meter
    assert r.battery_power_ac == -2401
    assert r.battery_power_dc == -2517
    _, eta = conversion_efficiency(r) or (None, 0.0)
    assert eta == pytest.approx(0.954, abs=1e-3)


def test_efficiency_rises_with_power() -> None:
    low = conversion_efficiency(parse_report(load_fixture("deliver_760")))
    high = conversion_efficiency(parse_report(load_fixture("deliver_2400_export_blocked")))
    assert low is not None and high is not None
    assert high[1] > low[1]


def test_idle_has_no_efficiency() -> None:
    assert conversion_efficiency(parse_report(load_fixture("standby"))) is None


@pytest.mark.parametrize(
    ("raw", "charge_stop", "discharge_stop"), [(0, False, False), (1, True, False), (2, False, True), (17, True, False), (18, False, True)]
)
def test_soc_limit_low_bits(raw: int, charge_stop: bool, discharge_stop: bool) -> None:
    data = copy.deepcopy(load_fixture("standby"))
    data["properties"]["socLimit"] = raw
    r = parse_report(data)
    assert r.soc_limit_charge_stopped is charge_stop
    assert r.soc_limit_discharge_stopped is discharge_stop


@pytest.mark.parametrize(("raw", "bypass"), [(0, False), (1, True), (2, True)])
def test_bypass_any_positive_value(raw: int, bypass: bool) -> None:
    data = copy.deepcopy(load_fixture("standby"))
    data["properties"]["pass"] = raw
    assert parse_report(data).bypass is bypass


def test_status_precedence() -> None:
    base = parse_report(load_fixture("deliver_760"))
    assert derive_status(dataclasses.replace(base, fault=True), 10, 95) is SetStatus.FAULT
    assert derive_status(dataclasses.replace(base, calibrating=True), 10, 95) is SetStatus.CALIBRATING
    assert derive_status(dataclasses.replace(base, bypass=True), 10, 95) is SetStatus.BYPASS
    assert derive_status(dataclasses.replace(base, soc=10.3), 10, 95) is SetStatus.EMPTY
    charging = parse_report(load_fixture("charge_2400"))
    assert derive_status(dataclasses.replace(charging, soc=94.6), 10, 95) is SetStatus.FULL


def test_fault_and_calibration_flags() -> None:
    data = copy.deepcopy(load_fixture("standby"))
    data["properties"]["faultLevel"] = 2
    data["properties"]["socStatus"] = 1
    r = parse_report(data)
    assert not r.fault and r.fault_level == 2  # faultLevel alone is informative
    assert r.calibrating
    data["properties"]["is_error"] = 1
    assert parse_report(data).fault


def test_unusable_reports() -> None:
    with pytest.raises(ZenSdkError):
        parse_report({"sn": "x"})
    data = copy.deepcopy(load_fixture("standby"))
    data["properties"]["electricLevel"] = 150
    with pytest.raises(ZenSdkError):
        parse_report(data)


def test_scale_helpers() -> None:
    assert temperature_c(2731) == 0.0
    assert temperature_c(2911) == 18.0
    assert temperature_c(None) is None
    assert signed_int16(65473) == -63
    assert signed_int16(176) == 176
