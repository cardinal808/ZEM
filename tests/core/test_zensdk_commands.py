"""Commands ZEPHYR writes, and what it refuses to write."""

from __future__ import annotations

import json

import pytest

from zephyr_core.zensdk import (
    MAX_REQUEST_BYTES,
    ZenSdkError,
    encode_write_request,
    grid_reverse_command,
    power_command,
    soc_limits_command,
    standby_command,
    validate_command,
)


def test_charge_command_with_direction_change() -> None:
    assert power_command(1000, include_ac_mode=True) == {"acMode": 1, "inputLimit": 1000, "outputLimit": 0, "smartMode": 1}


def test_deliver_command_without_direction_change() -> None:
    assert power_command(-500, include_ac_mode=False) == {"outputLimit": 500, "inputLimit": 0, "smartMode": 1}


def test_zero_command_stays_in_ram() -> None:
    assert power_command(0, include_ac_mode=True) == {"inputLimit": 0, "outputLimit": 0, "smartMode": 1}


def test_commands_are_clamped_to_device_limits() -> None:
    assert power_command(3000, include_ac_mode=False, charge_max=2400)["inputLimit"] == 2400
    assert power_command(-3000, include_ac_mode=False, deliver_max=2400)["outputLimit"] == 2400


def test_standby_goes_to_flash() -> None:
    assert standby_command() == {"inputLimit": 0, "outputLimit": 0, "smartMode": 0}


def test_soc_limits_in_tenths_of_percent() -> None:
    assert soc_limits_command(10, 95) == {"minSoc": 100, "socSet": 950, "smartMode": 0}


@pytest.mark.parametrize(("lo", "hi"), [(4, 95), (51, 95), (10, 69), (10, 101)])
def test_soc_limits_out_of_range(lo: float, hi: float) -> None:
    with pytest.raises(ZenSdkError):
        soc_limits_command(lo, hi)


def test_grid_reverse() -> None:
    assert grid_reverse_command(True) == {"gridReverse": 1}
    assert grid_reverse_command(False) == {"gridReverse": 2}


@pytest.mark.parametrize("key", ["gridStandard", "gridOffMode", "batCalTime", "inverseMaxPower", "unknownField"])
def test_forbidden_properties(key: str) -> None:
    with pytest.raises(ZenSdkError):
        validate_command({key: 1})


@pytest.mark.parametrize("props", [{"acMode": 3}, {"socSet": 600}, {"minSoc": 600}, {"smartMode": 2}, {"inputLimit": -1}])
def test_values_out_of_range(props: dict[str, int]) -> None:
    with pytest.raises(ZenSdkError):
        validate_command(props)


def test_only_integers() -> None:
    with pytest.raises(ZenSdkError):
        validate_command({"inputLimit": 10.5})  # type: ignore[dict-item]
    with pytest.raises(ZenSdkError):
        validate_command({"smartMode": True})


def test_encoded_request() -> None:
    body = encode_write_request("EEB4AEXAMPLE001", power_command(-760, include_ac_mode=True))
    data = json.loads(body)
    assert data == {"sn": "EEB4AEXAMPLE001", "properties": {"acMode": 2, "outputLimit": 760, "inputLimit": 0, "smartMode": 1}}
    assert len(body) <= MAX_REQUEST_BYTES


def test_request_size_limit() -> None:
    with pytest.raises(ZenSdkError):
        encode_write_request("X" * 600, {"smartMode": 1})


def test_serial_required() -> None:
    with pytest.raises(ZenSdkError):
        encode_write_request("", {"smartMode": 1})
