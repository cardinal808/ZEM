"""Online/offline detection for one set (SPEC-meerdere-sets §2.4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

OFFLINE_AFTER_FAILURES: Final = 3
"""Consecutive failed reads before a set counts as offline."""
ONLINE_AFTER_SUCCESSES: Final = 2
"""Consecutive successful reads before an offline set counts as online again."""
STALE_AFTER_SECONDS: Final = 20.0
"""A set whose last good read is older than this counts as offline."""


@dataclass(slots=True)
class SetHealth:
    """Tracks reads of one set; ``online`` follows the rules with hysteresis."""

    online: bool = False
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_success: float | None = None
    offline_since: float | None = None
    episodes_offline: int = 0
    last_error: str | None = None
    _ever_online: bool = field(default=False, repr=False)

    def record_success(self, now: float) -> None:
        self.consecutive_failures = 0
        self.consecutive_successes += 1
        self.last_success = now
        self.last_error = None
        if not self.online and (not self._ever_online or self.consecutive_successes >= ONLINE_AFTER_SUCCESSES):
            self.online = True
            self._ever_online = True
            self.offline_since = None

    def record_failure(self, now: float, error: str) -> None:
        self.consecutive_successes = 0
        self.consecutive_failures += 1
        self.last_error = error
        if self.online and (self.consecutive_failures >= OFFLINE_AFTER_FAILURES or self._stale(now)):
            self._go_offline(now)
        elif not self.online and self.offline_since is None:
            self.offline_since = now

    def check_stale(self, now: float) -> None:
        """Call regularly; a set without a good read for too long goes offline."""
        if self.online and self._stale(now):
            self._go_offline(now)

    def _stale(self, now: float) -> bool:
        return self.last_success is None or now - self.last_success > STALE_AFTER_SECONDS

    def _go_offline(self, now: float) -> None:
        self.online = False
        self.offline_since = now
        self.episodes_offline += 1
