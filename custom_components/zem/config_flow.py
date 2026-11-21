"""Config flow: one ZEM installation with up to three sets as subentries."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentry,
    ConfigSubentryData,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import (
    CONF_HOST,
    CONF_MAX_SOC,
    CONF_MIN_SOC,
    CONF_NUMBER,
    CONF_P1_ENTITY,
    CONF_PRODUCT,
    CONF_SERIAL,
    DOMAIN,
    MAX_SETS,
    SUBENTRY_SET,
)
from .core.client import ZendureClient, ZendureError
from .core.device_table import model_info, set_capacity
from .core.models import SetReport
from .core.settings import Settings

HOST_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


class CannotConnect(Exception):
    """The set could not be reached or did not give a usable report."""


async def _probe(hass: HomeAssistant, host: str) -> SetReport:
    client = ZendureClient(host, async_get_clientsession(hass))
    try:
        return await client.get_report()
    except ZendureError as err:
        raise CannotConnect from err


def _set_subentries(entry: ConfigEntry[Any]) -> list[ConfigSubentry]:
    return [s for s in entry.subentries.values() if s.subentry_type == SUBENTRY_SET]


def _free_number(entry: ConfigEntry[Any] | None) -> int | None:
    used = {int(s.data[CONF_NUMBER]) for s in _set_subentries(entry)} if entry else set()
    return next((n for n in range(1, MAX_SETS + 1) if n not in used), None)


def _set_data(number: int, host: str, report: SetReport) -> dict[str, Any]:
    return {CONF_NUMBER: number, CONF_HOST: host, CONF_SERIAL: report.serial, CONF_PRODUCT: report.product}


def _set_title(number: int, report: SetReport) -> str:
    info = model_info(report.product)
    return f"Set {number} · {info.name if info else report.product}"


def _placeholders(host: str, report: SetReport) -> dict[str, str]:
    info = model_info(report.product)
    capacity = set_capacity(report)
    return {
        "model": info.name if info else report.product,
        "serial": f"…{report.serial[-4:]}",
        "host": host,
        "capacity": f"{capacity.capacity_kwh:.2f}".replace(".", ","),
        "packs": str(len(report.packs)),
    }


class ZemConfigFlow(ConfigFlow, domain=DOMAIN):
    """Install ZEM by adding the first set (by hand or via discovery)."""

    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._report: SetReport | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry[Any]) -> ZemOptionsFlow:
        return ZemOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry: ConfigEntry[Any]) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_SET: SetSubentryFlow}

    def _existing_entry(self) -> ConfigEntry[Any] | None:
        entries = self._async_current_entries(include_ignore=False)
        return entries[0] if entries else None

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            try:
                report = await _probe(self.hass, host)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                return await self._async_finish(host, report)
        return self.async_show_form(step_id="user", data_schema=HOST_SCHEMA, errors=errors)

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        host = str(discovery_info.ip_address)
        try:
            report = await _probe(self.hass, host)
        except CannotConnect:
            return self.async_abort(reason="cannot_connect")

        entry = self._existing_entry()
        if entry is not None:
            for sub in _set_subentries(entry):
                if sub.data[CONF_SERIAL] == report.serial:
                    if sub.data[CONF_HOST] != host:
                        # Same set, new IP address (DHCP): follow it.
                        self.hass.config_entries.async_update_subentry(entry, sub, data={**sub.data, CONF_HOST: host})
                    return self.async_abort(reason="already_configured")
            if _free_number(entry) is None:
                return self.async_abort(reason="max_sets")

        await self.async_set_unique_id(f"set_{report.serial}")
        self._abort_if_unique_id_configured()
        self._host, self._report = host, report
        self.context["title_placeholders"] = {"model": _placeholders(host, report)["model"]}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        assert self._host is not None and self._report is not None
        if user_input is not None:
            return await self._async_finish(self._host, self._report)
        return self.async_show_form(step_id="discovery_confirm", description_placeholders=_placeholders(self._host, self._report))

    async def _async_finish(self, host: str, report: SetReport) -> ConfigFlowResult:
        entry = self._existing_entry()
        if entry is None:
            await self.async_set_unique_id(DOMAIN, raise_on_progress=False)
            return self.async_create_entry(
                title="ZEM",
                data={},
                subentries=[
                    ConfigSubentryData(
                        data=_set_data(1, host, report),
                        subentry_type=SUBENTRY_SET,
                        title=_set_title(1, report),
                        unique_id=report.serial,
                    )
                ],
            )
        if any(s.data[CONF_SERIAL] == report.serial for s in _set_subentries(entry)):
            return self.async_abort(reason="already_configured")
        number = _free_number(entry)
        if number is None:
            return self.async_abort(reason="max_sets")
        self.hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=_set_data(number, host, report),  # type: ignore[arg-type]
                subentry_type=SUBENTRY_SET,
                title=_set_title(number, report),
                unique_id=report.serial,
            ),
        )
        return self.async_abort(reason="set_added", description_placeholders={"number": str(number)})


class SetSubentryFlow(ConfigSubentryFlow):
    """Add another set to an existing installation."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        entry = self._get_entry()
        number = _free_number(entry)
        if number is None:
            return self.async_abort(reason="max_sets")
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            try:
                report = await _probe(self.hass, host)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                if any(s.data[CONF_SERIAL] == report.serial for s in _set_subentries(entry)):
                    return self.async_abort(reason="already_configured")
                return self.async_create_entry(
                    title=_set_title(number, report),
                    data=_set_data(number, host, report),
                    unique_id=report.serial,
                )
        return self.async_show_form(step_id="user", data_schema=HOST_SCHEMA, errors=errors)


P1_HINTS = ("p1", "power_consumption", "net_power", "grid_power", "electricity_meter", "homewizard")


def suggest_p1_entity(hass: HomeAssistant) -> str | None:
    """Best guess for the P1 power sensor: a power sensor whose id looks like a grid meter."""
    candidates: list[tuple[int, str]] = []
    for state in hass.states.async_all("sensor"):
        if state.attributes.get("device_class") != SensorDeviceClass.POWER or state.entity_id.startswith("sensor.zem_"):
            continue
        name = state.entity_id.lower()
        score = sum(10 - i for i, hint in enumerate(P1_HINTS) if hint in name)
        if score:
            candidates.append((score, state.entity_id))
    return max(candidates)[1] if candidates else None


class ZemOptionsFlow(OptionsFlow):
    """Sources and battery limits."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        # The ranges (min 5-50 %, max 70-100 %) keep the minimum below the maximum.
        if user_input is not None:
            return self.async_create_entry(data={**self.config_entry.options, **user_input})
        options = dict(self.config_entry.options)
        current = options.get(CONF_P1_ENTITY) or suggest_p1_entity(self.hass)
        defaults = Settings()
        schema = vol.Schema(
            {
                vol.Required(CONF_P1_ENTITY, default=current) if current else vol.Required(CONF_P1_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.POWER)
                ),
                vol.Required(CONF_MIN_SOC, default=options.get(CONF_MIN_SOC, defaults.min_soc)): _percent(5, 50),
                vol.Required(CONF_MAX_SOC, default=options.get(CONF_MAX_SOC, defaults.max_soc)): _percent(70, 100),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


def _percent(low: int, high: int) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(min=low, max=high, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.BOX)
    )
