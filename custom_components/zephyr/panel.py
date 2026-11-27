"""ZEPHYR's own panel in the sidebar (M6, SPEC-ui §2).

The built panel lives in ``frontend/`` (one ES module plus fonts) and is served
under ``/zephyr_static``. The version is part of the module URL so a browser
loads the new panel after an update.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from aiohttp import web
from homeassistant.core import HomeAssistant
from homeassistant.helpers.http import KEY_HASS, HomeAssistantView
from homeassistant.loader import async_get_integration

from .const import DOMAIN

PANEL_URL: Final = "zephyr"
STATIC_URL: Final = "/zephyr_static"
WEBCOMPONENT: Final = "zephyr-panel"
SIDEBAR_ICON: Final = "mdi:home-lightning-bolt"
FRONTEND_DIR: Final = Path(__file__).parent / "frontend"
_DATA: Final = f"{DOMAIN}_panel"


async def async_register_panel(hass: HomeAssistant, entry_id: str) -> bool:
    """Show the panel while at least one installation is loaded. False without the HA frontend."""
    if "frontend" not in hass.config.components or hass.http is None:
        return False
    data: dict[str, object] = hass.data.setdefault(_DATA, {"static": False, "registered": False, "entries": set()})
    entries = data["entries"]
    assert isinstance(entries, set)
    if not data["static"]:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths([StaticPathConfig(STATIC_URL, str(FRONTEND_DIR), cache_headers=False)])
        hass.http.register_view(HousePictureView())
        data["static"] = True
    if not data["registered"]:
        from homeassistant.components import panel_custom

        version = (await async_get_integration(hass, DOMAIN)).version
        await panel_custom.async_register_panel(
            hass,
            frontend_url_path=PANEL_URL,
            webcomponent_name=WEBCOMPONENT,
            sidebar_title="ZEPHYR",
            sidebar_icon=SIDEBAR_ICON,
            module_url=f"{STATIC_URL}/{WEBCOMPONENT}.js?v={version}",
            require_admin=False,
            config={"static": STATIC_URL},
        )
        data["registered"] = True
    entries.add(entry_id)
    return True


def async_remove_panel(hass: HomeAssistant, entry_id: str, *, final: bool) -> None:
    """Forget an installation; remove the panel when the last one is removed or disabled.

    A reload (``final`` False) keeps the panel, so an open panel does not jump
    away; it shows "reloading" and subscribes again. The static path stays: HA
    cannot remove it.
    """
    data = hass.data.get(_DATA)
    if not data:
        return
    entries = data["entries"]
    assert isinstance(entries, set)
    entries.discard(entry_id)
    if final and not entries and data["registered"]:
        from homeassistant.components import frontend

        frontend.async_remove_panel(hass, PANEL_URL, warn_if_unknown=False)
        data["registered"] = False


class HousePictureView(HomeAssistantView):
    """The own house picture (Stroom), for logged-in users only; the panel asks HA for a signed URL."""

    url = "/api/zephyr/house_picture"
    name = "api:zephyr:house_picture"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        from .websocket_api import _entry

        hass = request.app[KEY_HASS]
        entry = _entry(hass)
        found = await entry.runtime_data.house.async_read_picture() if entry and entry.runtime_data.house else None
        if found is None:
            return web.Response(status=404)
        data, mime = found
        return web.Response(body=data, content_type=mime, headers={"Cache-Control": "private, max-age=86400"})
