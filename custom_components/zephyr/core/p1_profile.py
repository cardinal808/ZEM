"""P1 profile: fast, medium, slow or too slow, from the measured meter interval (OPDRACHT-p1-profiel).

The interval itself is measured in the engine (B26). The profile only switches parts that do not
scale with the interval on their own: the step filter (B20) is meant for a meter that reports
every second and is off for a slow meter (DSMR 4, one sample per 10 s), where it would hold a
real rise for a whole sample.

A profile changes only after the interval stayed in the new range for ``HOLD`` seconds, with a
20 % margin on the bounds (from slow to medium only below 5.6 s), so it does not flap.
"""

from __future__ import annotations

from typing import Final

FAST: Final = "fast"
MEDIUM: Final = "medium"
SLOW: Final = "slow"
TOO_SLOW: Final = "too_slow"
ORDER: Final = (FAST, MEDIUM, SLOW, TOO_SLOW)
BOUNDS: Final = (2.0, 7.0, 25.0)
"""Upper bound of the interval (s) for fast, medium and slow."""
MARGIN: Final = 0.2
HOLD: Final = 600.0
MIN_SAMPLES: Final = 10


def classify(interval: float) -> str:
    for name, bound in zip(ORDER, BOUNDS, strict=False):
        if interval <= bound:
            return name
    return TOO_SLOW


def _beyond_margin(current: str, candidate: str, interval: float) -> bool:
    """The interval is past the bound between the two profiles by the margin."""
    i, j = ORDER.index(current), ORDER.index(candidate)
    if j < i:  # faster: below the bound of the faster profile, minus the margin
        return interval < BOUNDS[j] * (1 - MARGIN)
    return interval > BOUNDS[j - 1] * (1 + MARGIN)


class P1Profile:
    def __init__(self) -> None:
        self.profile = MEDIUM
        """Until there are ``MIN_SAMPLES`` intervals: medium."""
        self.decided = False
        self.changed_at: float | None = None
        self._candidate: str | None = None
        self._since: float | None = None

    def update(self, now: float, interval: float | None, samples: int) -> str:
        if interval is None or samples < MIN_SAMPLES:
            return self.profile
        wanted = classify(interval)
        if not self.decided:
            self.profile, self.decided, self.changed_at = wanted, True, now
            return self.profile
        if wanted == self.profile or not _beyond_margin(self.profile, wanted, interval):
            self._candidate = self._since = None
            return self.profile
        if wanted != self._candidate:
            self._candidate, self._since = wanted, now
        elif self._since is not None and now - self._since >= HOLD:
            self.profile, self.changed_at = wanted, now
            self._candidate = self._since = None
        return self.profile

    @property
    def step_filter(self) -> bool:
        """The step filter (B20) only for meters that report within a few seconds."""
        return self.profile in (FAST, MEDIUM)
