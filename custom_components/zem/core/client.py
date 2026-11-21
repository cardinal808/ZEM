"""Async HTTP client for one Zendure set (zenSDK local API).

Uses aiohttp, which Home Assistant ships. The session is passed in, so the
integration can use Home Assistant's shared session and tests can use a
local test server.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import aiohttp

from .models import SetReport
from .zensdk import ZenSdkError, encode_write_request, parse_report

DEFAULT_TIMEOUT = 3.0
"""Seconds per request (SPEC-meerdere-sets §2.3)."""


class ZendureError(Exception):
    """Base error for communication with a set."""


class ZendureTimeout(ZendureError):
    """The set did not answer in time."""


class ZendureConnectionError(ZendureError):
    """The set could not be reached."""


class ZendureResponseError(ZendureError):
    """The set answered, but the answer is unusable."""


class ZendureClient:
    """Talks to one set at ``http://<host>``."""

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        port: int | None = None,
    ) -> None:
        if not host:
            raise ValueError("host is required")
        self._base = f"http://{host}" if port is None else f"http://{host}:{port}"
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    @property
    def base_url(self) -> str:
        return self._base

    async def get_report_raw(self) -> Mapping[str, Any]:
        """``GET /properties/report`` as a dictionary."""
        try:
            async with self._session.get(f"{self._base}/properties/report", timeout=self._timeout) as resp:
                if resp.status != 200:
                    raise ZendureResponseError(f"HTTP {resp.status}")
                data = await resp.json(content_type=None)
        except TimeoutError as err:
            raise ZendureTimeout("no answer within the time limit") from err
        except aiohttp.ClientConnectionError as err:
            raise ZendureConnectionError(str(err)) from err
        except (aiohttp.ContentTypeError, ValueError) as err:
            raise ZendureResponseError("answer is not valid JSON") from err
        if not isinstance(data, Mapping):
            raise ZendureResponseError("answer is not a JSON object")
        return data

    async def get_report(self) -> SetReport:
        """Read and interpret the current report."""
        raw = await self.get_report_raw()
        try:
            return parse_report(raw)
        except ZenSdkError as err:
            raise ZendureResponseError(str(err)) from err

    async def write(self, serial: str, props: Mapping[str, int]) -> None:
        """``POST /properties/write``; the command is validated first."""
        body = encode_write_request(serial, props)
        try:
            async with self._session.post(
                f"{self._base}/properties/write",
                data=body,
                headers={"Content-Type": "application/json"},
                timeout=self._timeout,
            ) as resp:
                if resp.status != 200:
                    raise ZendureResponseError(f"HTTP {resp.status}")
                await resp.read()
        except TimeoutError as err:
            raise ZendureTimeout("no answer within the time limit") from err
        except aiohttp.ClientConnectionError as err:
            raise ZendureConnectionError(str(err)) from err
