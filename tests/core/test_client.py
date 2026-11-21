"""HTTP client against a local test server that behaves like a set."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from conftest import load_fixture
from zem_core.client import (
    ZendureClient,
    ZendureConnectionError,
    ZendureResponseError,
    ZendureTimeout,
)
from zem_core.zensdk import ZenSdkError, power_command

Handler = Callable[[web.Request], Awaitable[web.StreamResponse]]


def run_with_server(routes: list[tuple[str, str, Handler]], test: Callable[[ZendureClient], Awaitable[Any]], timeout: float = 1.0) -> Any:
    async def main() -> Any:
        app = web.Application()
        for method, path, handler in routes:
            app.router.add_route(method, path, handler)
        server = TestServer(app)
        await server.start_server()
        try:
            async with aiohttp.ClientSession() as session:
                client = ZendureClient(server.host, session, port=server.port, timeout=timeout)
                return await test(client)
        finally:
            await server.close()

    return asyncio.run(main())


def test_get_report() -> None:
    async def report(_: web.Request) -> web.Response:
        return web.json_response(load_fixture("deliver_760"))

    r = run_with_server([("GET", "/properties/report", report)], lambda c: c.get_report())
    assert r.battery_power_ac == -760


def test_write_sends_validated_body() -> None:
    received: list[dict[str, Any]] = []

    async def write(request: web.Request) -> web.Response:
        received.append(json.loads(await request.read()))
        return web.json_response({})

    async def test(c: ZendureClient) -> None:
        await c.write("EEB4AEXAMPLE001", power_command(1200, include_ac_mode=True))

    run_with_server([("POST", "/properties/write", write)], test)
    assert received == [{"sn": "EEB4AEXAMPLE001", "properties": {"acMode": 1, "inputLimit": 1200, "outputLimit": 0, "smartMode": 1}}]


def test_forbidden_write_never_reaches_the_set() -> None:
    calls = 0

    async def write(_: web.Request) -> web.Response:
        nonlocal calls
        calls += 1
        return web.json_response({})

    async def test(c: ZendureClient) -> None:
        await c.write("EEB4AEXAMPLE001", {"gridStandard": 4})

    with pytest.raises(ZenSdkError):
        run_with_server([("POST", "/properties/write", write)], test)
    assert calls == 0


def test_timeout() -> None:
    async def slow(_: web.Request) -> web.Response:
        await asyncio.sleep(0.5)
        return web.json_response(load_fixture("standby"))

    with pytest.raises(ZendureTimeout):
        run_with_server([("GET", "/properties/report", slow)], lambda c: c.get_report(), timeout=0.1)


def test_http_error() -> None:
    async def broken(_: web.Request) -> web.Response:
        return web.Response(status=500)

    with pytest.raises(ZendureResponseError):
        run_with_server([("GET", "/properties/report", broken)], lambda c: c.get_report())


def test_invalid_json() -> None:
    async def garbage(_: web.Request) -> web.Response:
        return web.Response(text="not json")

    with pytest.raises(ZendureResponseError):
        run_with_server([("GET", "/properties/report", garbage)], lambda c: c.get_report())


def test_unusable_report() -> None:
    async def empty(_: web.Request) -> web.Response:
        return web.json_response({"sn": "x"})

    with pytest.raises(ZendureResponseError):
        run_with_server([("GET", "/properties/report", empty)], lambda c: c.get_report())


def test_unreachable_set() -> None:
    async def main() -> None:
        async with aiohttp.ClientSession() as session:
            client = ZendureClient("127.0.0.1", session, port=9, timeout=1.0)
            await client.get_report()

    with pytest.raises(ZendureConnectionError):
        asyncio.run(main())
