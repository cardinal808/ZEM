"""P1 filters: short peaks held back, noise smoothed, drops never held."""

from __future__ import annotations

from zephyr_core.grid_filter import GridFilter
from zephyr_core.settings import Settings


def _feed(f: GridFilter, values: list[float], start: float = 0.0) -> list[float]:
    return [f.update(start + i, v) for i, v in enumerate(values)]


def test_short_peak_is_held() -> None:
    f = GridFilter(Settings(noise_band=0))
    out = _feed(f, [10, 10, 2200, 2210, 2190, 2200, 15, 10])
    assert out[2:6] == [10, 10, 10, 10]
    assert out[6] == 15 and f.holds == 1


def test_long_load_is_followed_after_hold() -> None:
    f = GridFilter(Settings(noise_band=0, step_hold=5))
    out = _feed(f, [0] + [2000] * 8)
    assert out[1:5] == [0, 0, 0, 0]
    assert out[6] == 2000


def test_hold_runs_out_without_new_sample() -> None:
    f = GridFilter(Settings(noise_band=0, step_hold=10))
    _feed(f, [0, 2000])
    assert f.value(5) == 0
    assert f.value(12) == 2000


def test_drop_and_rise_from_export_are_not_held() -> None:
    f = GridFilter(Settings(noise_band=0))
    assert _feed(f, [2000, 0]) == [2000, 0]
    # From export back towards zero is the battery catching up, not a new load.
    f = GridFilter(Settings(noise_band=0))
    assert _feed(f, [-900, 50]) == [-900, 50]


def test_noise_is_smoothed_and_jumps_pass() -> None:
    f = GridFilter(Settings(step_threshold=0, noise_band=75, noise_window=3))
    out = _feed(f, [0, 30, -30, 30, -30])
    assert all(abs(v) <= 15 for v in out[1:])
    assert _feed(f, [400], start=5)[0] == 400
