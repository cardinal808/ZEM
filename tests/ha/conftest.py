"""Fixtures for the Home Assistant tests: sets are simulated per IP address."""

from __future__ import annotations

import copy
from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest

from conftest import load_fixture
from custom_components.zephyr.core.client import ZendureTimeout


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow loading custom_components/zephyr."""


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
