"""Fixtures for the Home Assistant tests: sets are simulated per IP address."""

from __future__ import annotations

import asyncio
import copy
import threading
import traceback
from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest

from conftest import load_fixture
from custom_components.zephyr.core.client import ZendureTimeout


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow loading custom_components/zephyr."""


@pytest.fixture(autouse=True)
def log_dir_in_tmp(tmp_path: Any) -> Generator[Any]:
    """The 48-hour log goes to a temporary folder, not into the test config of the package."""
    with patch("custom_components.zephyr.log_file.log_dir", lambda _hass, entry_id: tmp_path / "zephyr_log" / entry_id):
        yield tmp_path / "zephyr_log"


@pytest.fixture(autouse=True)
def no_timers_from_other_threads() -> Generator[None]:
    """Fail when a timer is scheduled on the event loop from a worker thread.

    That happens when a plain function (no ``@callback``, no coroutine) is given to an HA
    helper such as ``async_track_time_interval``: HA runs it in the executor. The loop's timer
    heap is not thread-safe; it broke now and then as "list changed size during iteration".
    """
    original = asyncio.BaseEventLoop.call_at
    offenders: list[str] = []

    def call_at(self: asyncio.BaseEventLoop, when: float, callback: Any, *args: Any, **kwargs: Any) -> Any:
        if threading.current_thread() is not threading.main_thread():
            offenders.append("".join(traceback.format_stack(limit=8)))
        return original(self, when, callback, *args, **kwargs)

    with patch.object(asyncio.BaseEventLoop, "call_at", call_at):
        yield
    assert not offenders, offenders[0]


class FakeSets:
    """Answers of simulated sets by host: a report, or an exception."""

    def __init__(self) -> None:
        self.answers: dict[str, dict[str, Any] | Exception] = {}
        self.reads: dict[str, int] = {}
        self.writes: list[tuple[str, dict[str, int]]] = []

    def add(self, host: str, fixture: str, serial: str | None = None, **props: Any) -> dict[str, Any]:
        data = copy.deepcopy(load_fixture(fixture))
        if serial:
            data["sn"] = serial
        data["properties"].update(props)
        self.answers[host] = data
        return data

    def fail(self, host: str) -> None:
        self.answers[host] = ZendureTimeout("simulated timeout")


@pytest.fixture(autouse=True)
def no_tariff_fetch() -> Generator[list[int]]:
    """No network in tests: fetching the tariff table fails like an offline installation."""
    calls: list[int] = []

    async def fetch(self: Any) -> bool:
        calls.append(1)
        self.last_error = "offline (test)"
        return False

    with patch("custom_components.zephyr.tariff_provider.TariffProvider.async_fetch", fetch):
        yield calls


@pytest.fixture
def fake_sets() -> Generator[FakeSets]:
    fake = FakeSets()

    async def get_report_raw(client: Any) -> dict[str, Any]:
        host = client.base_url.removeprefix("http://").split(":")[0]
        fake.reads[host] = fake.reads.get(host, 0) + 1
        answer = fake.answers.get(host)
        if answer is None:
            raise ZendureTimeout("no such host")
        if isinstance(answer, Exception):
            raise answer
        return answer

    async def write(client: Any, serial: str, props: dict[str, int]) -> None:
        fake.writes.append((serial, dict(props)))

    with (
        patch("custom_components.zephyr.core.client.ZendureClient.get_report_raw", get_report_raw),
        patch("custom_components.zephyr.core.client.ZendureClient.write", write),
    ):
        yield fake
