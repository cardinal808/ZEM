"""The control log over the last 48 hours, kept over restarts and updates.

The log (decisions on a change of setpoint or reason, and events such as live, shadow,
calibration and a write test) lives in memory for the panel and the diagnostics. Once a
minute the new lines are appended to one file per UTC hour under
``.storage/zephyr_log/<entry>/``; files older than 48 hours are removed. Appending a few
lines a minute keeps the disk writes small, unlike a Store that rewrites its whole file.
"""

from __future__ import annotations

import asyncio
import json
from collections import deque
from collections.abc import Iterable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DOMAIN, LOGGER

KEEP = timedelta(hours=48)
MAX_LINES = 40_000
"""Upper bound in memory and in the diagnostics (about 6 MB at most)."""
FLUSH_EVERY = timedelta(minutes=1)

_LAST_FLUSH: dict[str, asyncio.Task[None]] = {}
"""The flush at an unload, per entry: a reload reads the files only after it."""


def log_dir(hass: HomeAssistant, entry_id: str) -> Path:
    return Path(hass.config.path(".storage", f"{DOMAIN}_log", entry_id))


def _cutoff(now: datetime) -> str:
    """ISO time 48 hours back, comparable as text with the log's ``time`` (UTC, seconds)."""
    return (now - KEEP).astimezone(dt_util.UTC).isoformat(timespec="seconds")


def _hour_file(time: str) -> str:
    return f"{time[:13]}.jsonl"  # 2026-11-28T08.jsonl


def append_lines(directory: Path, lines: Iterable[dict[str, Any]], cutoff: str) -> None:
    """Executor: append ``lines`` to their hour files and remove files older than ``cutoff``."""
    directory.mkdir(parents=True, exist_ok=True)
    by_file: dict[str, list[str]] = {}
    for line in lines:
        by_file.setdefault(_hour_file(str(line.get("time", ""))), []).append(json.dumps(line, separators=(",", ":")))
    for name, texts in by_file.items():
        with (directory / name).open("a", encoding="utf-8") as handle:
            handle.write("\n".join(texts) + "\n")
    oldest = _hour_file(cutoff)
    for path in directory.glob("*.jsonl"):
        if path.name < oldest:
            path.unlink(missing_ok=True)


def read_lines(directory: Path, cutoff: str) -> list[dict[str, Any]]:
    """Executor: all lines since ``cutoff``, oldest first; broken lines are skipped."""
    if not directory.is_dir():
        return []
    out: list[dict[str, Any]] = []
    oldest = _hour_file(cutoff)
    for path in sorted(directory.glob("*.jsonl")):
        if path.name < oldest:
            continue
        for text in path.read_text(encoding="utf-8").splitlines():
            try:
                line = json.loads(text)
            except ValueError:
                continue
            if isinstance(line, dict) and str(line.get("time", "")) >= cutoff:
                out.append(line)
    return out[-MAX_LINES:]


class LogFile:
    """Keeps ``log`` (the control log in memory) at 48 hours and writes it to disk."""

    def __init__(self, hass: HomeAssistant, entry_id: str, log: deque[dict[str, Any]]) -> None:
        self.hass = hass
        self.entry_id = entry_id
        self.directory = log_dir(hass, entry_id)
        self.log = log
        self._pending: list[dict[str, Any]] = []
        self.restored = 0

    def add(self, line: dict[str, Any]) -> None:
        self.log.append(line)
        self._pending.append(line)

    async def async_restore(self) -> None:
        """Put the lines from before the start in front of what came since."""
        last = _LAST_FLUSH.pop(self.entry_id, None)
        if last is not None:
            await asyncio.wait([last])
        try:
            old = await self.hass.async_add_executor_job(read_lines, self.directory, _cutoff(dt_util.utcnow()))
        except OSError as err:
            LOGGER.warning("Could not read the ZEPHYR log: %s", err)
            return
        new = list(self.log)
        self.log.clear()
        self.log.extend(old + new)
        self.restored = len(old)

    async def async_flush(self, _now: datetime | None = None) -> None:
        cutoff = _cutoff(dt_util.utcnow())
        while self.log and str(self.log[0].get("time", "")) < cutoff:
            self.log.popleft()
        if not self._pending:
            return
        lines, self._pending = self._pending, []
        try:
            await self.hass.async_add_executor_job(append_lines, self.directory, lines, cutoff)
        except OSError as err:
            LOGGER.warning("Could not write the ZEPHYR log: %s", err)

    def flush_at_unload(self) -> None:
        task = self.hass.async_create_task(self.async_flush(), "zephyr: write the log")
        _LAST_FLUSH[self.entry_id] = task
        task.add_done_callback(lambda done: _LAST_FLUSH.pop(self.entry_id, None) if _LAST_FLUSH.get(self.entry_id) is done else None)

    @property
    def since(self) -> str | None:
        return str(self.log[0].get("time")) if self.log else None
