"""Solar power now from inverters the sets do not see (screen Nu)."""

from __future__ import annotations

import pytest

from zephyr_core.solar_now import CounterPower, total, watts


def test_power_sensors_in_w_and_kw_are_added_up() -> None:
    assert watts("1500", "W") == 1500
    assert watts("1.2", "kW") == 1200
    assert watts("-3", "W") == 0  # an inverter at night
    assert watts("unavailable", "W") is None
    assert total([watts("1500", "W"), watts("1.2", "kW"), None]) == 2700
    assert total([None, None]) is None


def test_counter_estimate_from_steps_and_fading_out() -> None:
    c = CounterPower()
    assert c.power(0) is None
    c.observe(100.0, 0)  # reference only
    assert c.power(10) is None
    c.observe(100.1, 300)  # 0.1 kWh in 5 min = 1200 W
    assert c.power(300) == pytest.approx(1200)
    assert c.power(900) == pytest.approx(600)  # no new step: at most 0.1 kWh over 10 min
    c.observe(100.1001, 310)  # a step within 20 s is noise, no new measurement
    assert c.power(310) == pytest.approx(1200)
