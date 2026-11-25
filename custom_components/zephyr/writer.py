"""Sends commands to the sets in live mode (PLAN-M4b §2.1).

Per set a queue of length one: a new command replaces one that is still waiting
(the newest wins), while a write is in flight the next one waits for it. A
failed write is not retried; the next control step sends the current setpoint.
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from homeassistant.core import HomeAssistant

from .const import LOGGER
from .coordinator import SetCoordinator
from .core.client import ZendureError

HOUR = 3600.0


@dataclass(slots=True)
class WriteStats:
    ok: deque[float] = field(default_factory=deque)
    failed: deque[float] = field(default_factory=deque)
    last_error: str | None = None
    last_duration: float | None = None
    smartmode_reverted: deque[float] = field(default_factory=deque)
    """Reports with ``smartMode`` 0 while ZEPHYR's last command was in RAM (PLAN-M4b §2.7)."""

    def snapshot(self, now: float) -> dict[str, object]:
        for events in (self.ok, self.failed):
            while events and now - events[0] > 24 * HOUR:
                events.popleft()
        return {
            "ok_24h": len(self.ok),
            "failed_24h": len(self.failed),
            "failed_1h": sum(1 for t in self.failed if now - t <= HOUR),
            "last_error": self.last_error,
            "last_duration_s": None if self.last_duration is None else round(self.last_duration, 2),
            "smartmode_reverted_24h": sum(1 for t in self.smartmode_reverted if now - t <= 24 * HOUR),
        }


class SetWriter:
    """Writes to one set; at most one request at a time."""

    def __init__(self, hass: HomeAssistant, coordinator: SetCoordinator, on_done: Callable[[], None] | None = None) -> None:
        self.hass = hass
        self.coordinator = coordinator
        self.stats = WriteStats()
        self._pending: dict[str, int] | None = None
        self.last_props: dict[str, int] | None = None
        """The last command written successfully, and when (for checks against the reports)."""
        self.last_at: float | None = None
        self.limits_before: tuple[int, int] | None = None
        """The limits (in, out) the set reported when the last command was written: while the set
        still shows these, it has not applied the command yet (a start from 0 W takes 9-17 s)."""
        self._task: asyncio.Task[None] | None = None
        self._on_done = on_done

    def send(self, props: Mapping[str, int]) -> None:
        """Queue a command; replaces a waiting one."""
        self._pending = dict(props)
        if self._task is None or self._task.done():
            self._task = self.hass.async_create_background_task(self._run(), f"zephyr write set {self.coordinator.number}")

    async def send_now(self, props: Mapping[str, int]) -> bool:
        """Write and wait (shutdown, leaving live mode, test command). Returns success."""
        if self._task is not None and not self._task.done():
            self._pending = None
            await asyncio.wait([self._task])
        return await self._write(dict(props))

    async def _run(self) -> None:
        while self._pending is not None:
            props, self._pending = self._pending, None
            await self._write(props)

    async def _write(self, props: dict[str, int]) -> bool:
        started = time.monotonic()
        data = self.coordinator.data
        report = data.report if data is not None else None
        before = (report.input_limit, report.output_limit) if report is not None else None
        try:
            await self.coordinator.client.write(self.coordinator.serial, props)
        except (ZendureError, ValueError) as err:
            self.stats.failed.append(time.monotonic())
            self.stats.last_error = f"{type(err).__name__}: {err}"
            LOGGER.warning("Write to set %s failed: %s", self.coordinator.number, err)
            ok = False
        else:
            self.stats.ok.append(time.monotonic())
            self.stats.last_error = None
            if props != self.last_props:
                self.limits_before = before
            self.last_props = props
            self.last_at = time.monotonic()
            ok = True
        self.stats.last_duration = time.monotonic() - started
        if self._on_done is not None:
            self._on_done()
        return ok
