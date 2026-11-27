"""Inverter power limit at a negative export price."""

from zephyr_core.curtail_limit import should_write, wanted_percent


def test_wanted_percent_keeps_a_small_import() -> None:
    # 3 kW solar, 1 kW exported: the house and battery take 2 kW; 5 kW inverter.
    assert wanted_percent(3000, -1000, 5000) == 39  # (2000 − 50) / 5000
    assert wanted_percent(0, 400, 5000) == 7  # dark: the limit follows the use, nothing to curtail
    assert wanted_percent(5000, -6000, 5000) == 0
    assert wanted_percent(100, 9000, 5000) == 100
    assert wanted_percent(3000, -1000, 0) == 100


def test_write_only_on_a_real_change() -> None:
    assert should_write(None, 40)
    assert not should_write(40.0, 41)
    assert should_write(40.0, 42)
    assert should_write(1.0, 0) and not should_write(0.0, 0)
    assert should_write(99.0, 100) and not should_write(100.0, 100)
