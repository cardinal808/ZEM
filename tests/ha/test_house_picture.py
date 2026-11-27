"""Own house picture on the screen Stroom: upload, place, serve, remove."""

from __future__ import annotations

import base64
import os
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.zephyr.stroom_devices import picture_mime

from .conftest import FakeSets
from .test_planner import PRICE, _set_prices, _setup, _test_day  # noqa: F401 (_test_day: autouse)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_picture_mime_by_first_bytes() -> None:
    assert picture_mime(PNG) == "image/png"
    assert picture_mime(b"\xff\xd8\xff\xe0rest") == "image/jpeg"
    assert picture_mime(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
    assert picture_mime(b"<svg></svg>") is None


async def test_upload_place_serve_and_remove(
    hass: HomeAssistant,
    fake_sets: FakeSets,
    freezer: FrozenDateTimeFactory,
    hass_ws_client: Any,
    hass_client_no_auth: Any,
    hass_admin_user: Any,
) -> None:
    """Upload → own picture on; placements are kept as fractions; the view serves it to logged-in users."""
    from custom_components.zephyr.panel import HousePictureView
    from custom_components.zephyr.websocket_api import settings_view, stroom_view

    assert await async_setup_component(hass, "http", {})
    hass.http.register_view(HousePictureView())
    client = await hass_ws_client(hass)
    _set_prices(hass)
    entry = await _setup(hass, fake_sets, freezer, (9, 0), price_entity=PRICE)
    assert stroom_view(entry)["picture"] is None
    # A fresh token: the fixture's would have expired while the clock moved to 09:00.
    refresh = await hass.auth.async_create_refresh_token(hass_admin_user, "https://example.com/app")
    auth = {"Authorization": f"Bearer {hass.auth.async_create_access_token(refresh)}"}
    http = await hass_client_no_auth()
    assert (await http.get("/api/zephyr/house_picture")).status == 401  # not without logging in

    await client.send_json_auto_id(
        {"type": "zephyr/house/picture/upload", "data": base64.b64encode(b"<svg/>").decode(), "width": 10, "height": 10}
    )
    assert (await client.receive_json())["error"]["code"] == "invalid_picture"

    await client.send_json_auto_id(
        {"type": "zephyr/house/picture/upload", "data": base64.b64encode(PNG).decode(), "width": 1600, "height": 1200}
    )
    result = (await client.receive_json())["result"]
    assert result["custom"] and result["has_image"] and result["version"] == 1

    items = {"battery": {"box": [0.1, 0.2], "point": [0.5, 1.7]}, "nonsense": {"box": [0, 0]}}
    await client.send_json_auto_id({"type": "zephyr/house/picture", "custom": True, "items": items, "hidden": ["ev", "x"]})
    assert (await client.receive_json())["success"]
    picture = stroom_view(entry)["picture"]
    assert picture["items"] == {"battery": {"box": [0.1, 0.2], "point": [0.5, 1.0]}}  # clamped, unknown dropped
    assert picture["hidden"] == ["ev"] and picture["width"] == 1600
    assert settings_view(hass, entry)["house_picture"]["custom"] is True

    response = await http.get("/api/zephyr/house_picture", headers=auth)
    assert response.status == 200 and response.content_type == "image/png"
    assert await response.read() == PNG

    await client.send_json_auto_id({"type": "zephyr/house/picture", "custom": False, "items": items})
    assert (await client.receive_json())["success"]
    assert stroom_view(entry)["picture"] is None  # default house again, the upload stays
    assert settings_view(hass, entry)["house_picture"]["has_image"] is True

    path = entry.runtime_data.house.picture_path
    await client.send_json_auto_id({"type": "zephyr/house/picture/delete"})
    assert (await client.receive_json())["result"]["has_image"] is False
    assert not os.path.exists(path)
    assert (await http.get("/api/zephyr/house_picture", headers=auth)).status == 404
