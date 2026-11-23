"""Filters on the P1 value before the controller sees it (B20, B22).

Two filters, both on time rather than on a number of samples, so a slow meter
is not filtered more than a fast one:

* **Step filter (B20):** a sudden rise of the grid power by more than
  ``step_threshold`` above max(previous value, 0) is held back for at most
  ``step_hold`` seconds. Short peaks (a boiling-water tap heating its tank,
  4–10 s at ~2 kW) are over before the battery could follow them anyway
  (it ramps at ~330 W/s); chasing them only costs writes and, afterwards,
  energy exported while the battery ramps back. A load that is still there
  after the hold time is followed normally. A drop is never held: that
  would cause export.
* **Noise filter (B22):** when the new value is within ``noise_band`` of the
  mean over the last ``noise_window`` seconds, the controller gets that mean.
  Small up-and-down noise (±30 W) then no longer crosses the dead band in
  both directions; real changes larger than the band pass at once.

The raw value stays what is shown and what decides about staleness.
"""

from __future__ import annotations

from collections import deque

from .settings import Settings


class GridFilter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._last_raw: float | None = None
        self._hold_value: float | None = None
        self._hold_since: float | None = None
        self._samples: deque[tuple[float, float]] = deque()
        self._out: float | None = None
        self.holds = 0
        """Number of steps held back (diagnostics)."""

    def reset(self) -> None:
        self._hold_value = None
        self._hold_since = None
        self._samples.clear()

    @property
    def holding(self) -> bool:
        return self._hold_value is not None

    def update(self, now: float, raw: float) -> float:
        """A new P1 sample. Returns the value for the controller."""
        s = self.settings
        previous = self._last_raw
        self._last_raw = raw

        # --- step filter ---
        if self._hold_value is not None:
            assert self._hold_since is not None
            if raw <= self._hold_value + s.step_threshold / 2 or now - self._hold_since >= s.step_hold:
                self._hold_value = None  # peak over, or it stays: follow again
                self._hold_since = None
                self._samples.clear()
        elif s.step_threshold > 0 and previous is not None and raw - max(previous, 0.0) > s.step_threshold:
            self._hold_value = previous
            self._hold_since = now
            self.holds += 1
        if self._hold_value is not None:
            self._out = self._hold_value
            return self._out

        # --- noise filter ---
        value = raw
        if s.noise_band > 0 and s.noise_window > 0:
            while self._samples and now - self._samples[0][0] > s.noise_window:
                self._samples.popleft()
            self._samples.append((now, raw))
            mean = sum(v for _, v in self._samples) / len(self._samples)
            if abs(raw - mean) <= s.noise_band:
                value = mean
            else:
                self._samples.clear()
                self._samples.append((now, raw))
        self._out = value
        return value

    def value(self, now: float) -> float | None:
        """Value for the controller now; a hold that ran out releases the raw value."""
        if self._hold_value is not None and self._hold_since is not None and now - self._hold_since >= self.settings.step_hold:
            self._hold_value = None
            self._hold_since = None
            self._samples.clear()
            self._out = self._last_raw
        return self._out
