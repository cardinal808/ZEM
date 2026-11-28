"""Config flow: one ZEPHYR installation with up to three sets as subentries."""

from __future__ import annotations

from typing import Any, Literal

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
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .const import (
    CONF_APPLIANCE_AFTER_WASH,
    CONF_APPLIANCE_ENERGY,
    CONF_APPLIANCE_FROM,
    CONF_APPLIANCE_KIND,
    CONF_APPLIANCE_NAME,
    CONF_APPLIANCE_POWER,
    CONF_APPLIANCE_UNTIL,
    CONF_CALIBRATION_DAYS,
    CONF_CAPACITY_OVERRIDE,
    CONF_COST_EXPORT_COUNTERS,
    CONF_COST_IMPORT_COUNTERS,
    CONF_CURTAIL_INVERTER_W,
    CONF_CURTAIL_MODE,
    CONF_CURTAIL_NUMBER,
    CONF_CURTAIL_SWITCH,
    CONF_EXCLUDED_CLIMATE,
    CONF_EXCLUDED_ENERGY,
    CONF_EXCLUDED_MODES,
    CONF_EXPENSIVE_HOURS,
    CONF_HOST,
    CONF_LIVE_OFF_AFTER_RESTART,
    CONF_MAX_SOC,
    CONF_MIN_PRICE,
    CONF_MIN_SOC,
    CONF_NUMBER,
    CONF_P1_ENTITY,
    CONF_P1_EXPORT,
    CONF_P1_IMPORT,
    CONF_P1_SOURCE,
    CONF_PLAN_ALLOW_EXPORT,
    CONF_PLAN_BUFFER,
    CONF_PLAN_GRID_CHARGE_COST,
    CONF_PLAN_LOAD_MARGIN,
    CONF_PLAN_WEAR_COST,
    CONF_PRICE_ENTITY,
    CONF_PRICE_FORECAST_DAYS,
    CONF_PRICE_FORECAST_ENTITY,
    CONF_PRICE_FORECAST_MODE,
    CONF_PRICE_FORECAST_VALUE,
    CONF_PRODUCT,
    CONF_RESERVE_SOC,
    CONF_SERIAL,
    CONF_SOLAR_ENERGY,
    CONF_SOLAR_FORECAST,
    CONF_SOLAR_POWER,
    CONF_TARIFF_ENERGY_TAX,
    CONF_TARIFF_FIXED_MONTH,
    CONF_TARIFF_MARKUP_EXPORT,
    CONF_TARIFF_MARKUP_IMPORT,
    CONF_TARIFF_SOLAR_BONUS,
    CONF_TARIFF_SUPPLIER,
    CONF_TARIFF_VAT,
    CONF_VACATION_AWAY,
    CONF_WORKDAY_ENTITY,
    CURTAIL_MODES,
    CURTAIL_OFF,
    DEFAULT_EXCLUDED_MODES,
    DEFAULT_EXPENSIVE_HOURS,
    DEFAULT_PLAN_GRID_CHARGE_COST,
    DEFAULT_PLAN_WEAR_COST,
    DEFAULT_RESERVE_SOC,
    DOMAIN,
    HVAC_MODE_CHOICES,
    MAX_SETS,
    P1_SOURCE_PAIR,
    P1_SOURCE_SINGLE,
    SUBENTRY_APPLIANCE,
    SUBENTRY_SET,
    TARIFF_OWN,
)
from .core.appliances import DISHWASHER, WASHER
from .core.appliances import KINDS as APPLIANCE_KINDS
from .core.appliances import OTHER as OTHER_APPLIANCE
from .core.client import ZendureClient, ZendureError
from .core.costs import Tariffs
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


class ZephyrConfigFlow(ConfigFlow, domain=DOMAIN):
    """Install ZEPHYR by adding the first set (by hand or via discovery)."""

    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        self._host: str | None = None
        self._report: SetReport | None = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry[Any]) -> ZephyrOptionsFlow:
        return ZephyrOptionsFlow()

    @classmethod
    @callback
    def async_get_supported_subentry_types(cls, config_entry: ConfigEntry[Any]) -> dict[str, type[ConfigSubentryFlow]]:
        return {SUBENTRY_SET: SetSubentryFlow, SUBENTRY_APPLIANCE: ApplianceSubentryFlow}

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
                title="ZEPHYR",
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

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        """Capacity by hand, for packs ZEPHYR does not recognise (0 = automatic)."""
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            value = float(user_input.get(CONF_CAPACITY_OVERRIDE) or 0)
            result = self.async_update_and_abort(entry, subentry, data_updates={CONF_CAPACITY_OVERRIDE: value or None})
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
            return result
        current = subentry.data.get(CONF_CAPACITY_OVERRIDE) or 0
        schema = vol.Schema(
            {
                vol.Optional(CONF_CAPACITY_OVERRIDE, default=current): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=0, max=60, step=0.01, unit_of_measurement="kWh", mode=selector.NumberSelectorMode.BOX)
                ),
            }
        )
        return self.async_show_form(step_id="reconfigure", data_schema=schema)


def _appliance_details_schema(kind: str, data: dict[str, Any]) -> vol.Schema:
    dishwasher = kind == DISHWASHER
    default_from = data.get(CONF_APPLIANCE_FROM, "" if dishwasher else "08:00:00")
    default_until = data.get(CONF_APPLIANCE_UNTIL, "07:00:00" if dishwasher else "20:00:00")
    dryer = kind.startswith("dryer")
    extra: dict[Any, Any] = (
        {vol.Optional(CONF_APPLIANCE_AFTER_WASH, default=bool(data.get(CONF_APPLIANCE_AFTER_WASH, False))): selector.BooleanSelector()}
        if dryer
        else {}
    )
    return vol.Schema(
        {
            vol.Optional(CONF_APPLIANCE_POWER, description={"suggested_value": data.get(CONF_APPLIANCE_POWER)}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="power")
            ),
            vol.Optional(CONF_APPLIANCE_ENERGY, description={"suggested_value": data.get(CONF_APPLIANCE_ENERGY)}): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="energy")
            ),
            vol.Optional(CONF_APPLIANCE_FROM, description={"suggested_value": default_from or None}): selector.TimeSelector(),
            vol.Required(CONF_APPLIANCE_UNTIL, default=default_until): selector.TimeSelector(),
            **extra,
        }
    )


class ApplianceSubentryFlow(ConfigSubentryFlow):
    """A planned appliance (B36): dishwasher, washing machine, dryer, ..."""

    def __init__(self) -> None:
        self._base: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        if user_input is not None:
            self._base = {
                CONF_APPLIANCE_NAME: user_input[CONF_APPLIANCE_NAME].strip(),
                CONF_APPLIANCE_KIND: user_input[CONF_APPLIANCE_KIND],
            }
            return await self.async_step_details()
        schema = vol.Schema(
            {
                vol.Required(CONF_APPLIANCE_NAME): selector.TextSelector(),
                vol.Required(CONF_APPLIANCE_KIND, default=WASHER): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=list(APPLIANCE_KINDS), translation_key="appliance_kind")
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_details(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        kind = self._base[CONF_APPLIANCE_KIND]
        if user_input is not None:
            data = {**self._base, **{k: v for k, v in user_input.items() if v not in (None, "")}}
            entry = self._get_entry()
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
            return self.async_create_entry(title=self._base[CONF_APPLIANCE_NAME], data=data)
        return self.async_show_form(step_id="details", data_schema=_appliance_details_schema(kind, {}))

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        kind = subentry.data.get(CONF_APPLIANCE_KIND, OTHER_APPLIANCE)
        if user_input is not None:
            keep = {CONF_APPLIANCE_NAME: subentry.data.get(CONF_APPLIANCE_NAME), CONF_APPLIANCE_KIND: kind}
            data = {**keep, **{k: v for k, v in user_input.items() if v not in (None, "")}}
            result = self.async_update_and_abort(entry, subentry, data=data)
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
            return result
        return self.async_show_form(step_id="reconfigure", data_schema=_appliance_details_schema(kind, dict(subentry.data)))


P1_HINTS = ("p1", "power_consumption", "net_power", "grid_power", "electricity_meter", "homewizard")
P1_PLATFORMS = ("dsmr", "dsmr_reader", "p1_monitor", "homewizard", "slimmelezer")
"""Integrations of smart-meter readers; HomeWizard only for its P1 meter (not its plugs)."""
SOLAR_PLATFORMS = (
    "solaredge",
    "solaredge_modbus",
    "solaredge_modbus_multi",
    "enphase_envoy",
    "fronius",
    "sma",
    "growatt_server",
    "huawei_solar",
    "goodwe",
    "solax",
    "sungrow",
    "solarman",
    "foxess",
    "apsystems",
    "hoymiles",
    "opendtu",
)
"""Inverter integrations: their production counter is a good solar counter."""
_PHASE = ("phase", "_l1", "_l2", "_l3")


def _platform_and_model(hass: HomeAssistant, entity_id: str) -> tuple[str | None, str]:
    entry = er.async_get(hass).async_get(entity_id)
    if entry is None:
        return None, ""
    model = ""
    if entry.device_id:
        device = dr.async_get(hass).async_get(entry.device_id)
        model = f"{device.manufacturer or ''} {device.model or ''}" if device is not None else ""
    return entry.platform, model


def _is_meter_reader(hass: HomeAssistant, entity_id: str) -> bool:
    platform, model = _platform_and_model(hass, entity_id)
    if platform not in P1_PLATFORMS:
        return False
    return platform != "homewizard" or "p1" in model.lower()


def suggest_p1_entity(hass: HomeAssistant) -> str | None:
    """Best guess for the P1 power sensor: a meter reader's total power, else a name like a grid meter."""
    candidates: list[tuple[int, str]] = []
    for state in hass.states.async_all("sensor"):
        if state.attributes.get("device_class") != SensorDeviceClass.POWER or state.entity_id.startswith("sensor.zephyr_"):
            continue
        name = state.entity_id.lower()
        score = sum(10 - i for i, hint in enumerate(P1_HINTS) if hint in name)
        if _is_meter_reader(hass, state.entity_id) and not any(p in name for p in _PHASE):
            # By integration: also a meter whose sensor has another name. A net (signed) total first.
            score += 50 + (5 if "production" not in name and "produced" not in name and "export" not in name else 0)
        if score:
            candidates.append((score, state.entity_id))
    return max(candidates)[1] if candidates else None


def suggest_p1_pair(hass: HomeAssistant) -> tuple[str | None, str | None]:
    """Import and export power sensors of a smart meter (as the DSMR integration names them)."""
    imports: list[str] = []
    exports: list[str] = []
    for state in hass.states.async_all("sensor"):
        if state.attributes.get("device_class") != SensorDeviceClass.POWER or state.entity_id.startswith("sensor.zephyr_"):
            continue
        name = state.entity_id.lower()
        if name.endswith("power_consumption") and "phase" not in name:
            imports.append(state.entity_id)
        elif name.endswith("power_production") and "phase" not in name:
            exports.append(state.entity_id)
    for imp in sorted(imports):
        prefix = imp.removesuffix("power_consumption")
        if f"{prefix}power_production" in exports:
            return imp, f"{prefix}power_production"
    # A single-phase connection: the meter may only offer the per-phase sensors (…_phase_1),
    # which then equal the total. Not when there are other phases (the total would be wrong).
    power = [st.entity_id for st in hass.states.async_all("sensor") if st.attributes.get("device_class") == SensorDeviceClass.POWER]
    if not any(e.endswith(("phase_2", "phase_3", "_l2", "_l3")) for e in power):
        for imp in sorted(e for e in power if e.endswith("power_consumed_phase_1")):
            exp = imp.replace("power_consumed_phase_1", "power_produced_phase_1")
            if exp in power:
                return imp, exp
    return None, None


def suggest_price(hass: HomeAssistant) -> str | None:
    """A Nord Pool price sensor: the HACS one (``raw_today``), else the current price of HA's own Nord Pool."""
    hacs = next(
        (st.entity_id for st in sorted(hass.states.async_all("sensor"), key=lambda st: st.entity_id) if "raw_today" in st.attributes),
        None,
    )
    if hacs is not None:
        return hacs
    registry = er.async_get(hass)
    return next(
        (
            e.entity_id
            for e in sorted(registry.entities.values(), key=lambda e: e.entity_id)
            if e.platform == "nordpool" and e.domain == "sensor" and (e.unique_id or "").endswith("-current_price")
        ),
        None,
    )


def suggest_workday(hass: HomeAssistant) -> str | None:
    """The binary sensor of the Workday integration, if there is one."""
    registry = er.async_get(hass)
    return next(
        (
            e.entity_id
            for e in sorted(registry.entities.values(), key=lambda e: e.entity_id)
            if e.platform == "workday" and e.domain == "binary_sensor"
        ),
        None,
    )


def suggest_solar(hass: HomeAssistant) -> tuple[str | None, str | None]:
    """A day-ahead forecast sensor with half-hour detail (Solcast) and a solar production counter."""
    forecast = next(
        (
            st.entity_id
            for st in sorted(hass.states.async_all("sensor"), key=lambda st: st.entity_id)
            if st.entity_id.endswith("forecast_tomorrow") and "detailedForecast" in st.attributes
        ),
        None,
    )
    energy = None
    for st in sorted(hass.states.async_all("sensor"), key=lambda st: st.entity_id):
        name = st.entity_id.lower()
        if st.attributes.get("device_class") != SensorDeviceClass.ENERGY or st.entity_id.startswith("sensor.zephyr_"):
            continue
        if st.attributes.get("state_class") != "total_increasing":
            continue
        if "forecast" in name:
            continue
        platform, _model = _platform_and_model(hass, st.entity_id)
        if platform in SOLAR_PLATFORMS:
            return forecast, st.entity_id  # an inverter's counter wins over a name
        if energy is None and any(word in name for word in ("solaredge", "solar", "pv", "inverter", "omvormer")):
            energy = st.entity_id
    return forecast, energy


def suggest_meter_counters(hass: HomeAssistant) -> tuple[list[str], list[str]]:
    """The smart meter's energy counters per tariff (DSMR: ``…energy_consumed_tariff_1/2``, ``…energy_produced_tariff_1/2``)."""
    names = sorted(st.entity_id for st in hass.states.async_all("sensor") if st.attributes.get("device_class") == SensorDeviceClass.ENERGY)
    imports = [n for n in names if "energy_consumed_tariff_" in n or "energy_import_tariff_" in n]
    exports = [n for n in names if "energy_produced_tariff_" in n or "energy_export_tariff_" in n]
    if imports and exports:
        return imports, exports
    # A meter reader with one total counter per direction (no tariffs), by integration.
    readers = [n for n in names if _is_meter_reader(hass, n) and not any(p in n for p in _PHASE)]
    imports = [n for n in readers if any(w in n for w in ("import", "consum", "delivered_to_client"))]
    exports = [n for n in readers if any(w in n for w in ("export", "produc", "delivered_by_client"))]
    return (imports[:1], exports[:1]) if imports and exports else ([], [])


def _energy_sensors() -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.ENERGY, multiple=True))


def _power_sensor() -> selector.EntitySelector:
    return selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.POWER))


async def supplier_choices(hass: HomeAssistant, entry: ConfigEntry[Any]) -> list[selector.SelectOptionDict]:
    """Own tariffs plus the verified suppliers of the newest tariff table (B28)."""
    from .tariff_provider import load_shipped

    runtime = getattr(entry, "runtime_data", None)
    provider = getattr(runtime, "tariffs", None)
    table = provider.table if provider is not None else await hass.async_add_executor_job(load_shipped)
    own = "Eigen tarieven (hieronder)" if hass.config.language.startswith("nl") else "Own tariffs (below)"
    choices = [selector.SelectOptionDict(value=TARIFF_OWN, label=own)]
    if table is not None:
        choices += [selector.SelectOptionDict(value=key, label=name) for key, name in table.choices()]
    return choices


class ZephyrOptionsFlow(OptionsFlow):
    """Sources and battery limits."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        # The ranges (min 5-50 %, max 70-100 %) keep the minimum below the maximum.
        errors: dict[str, str] = {}
        if user_input is not None:
            pair_given = bool(user_input.get(CONF_P1_IMPORT) and user_input.get(CONF_P1_EXPORT))
            if user_input.get(CONF_P1_SOURCE) != P1_SOURCE_PAIR and not user_input.get(CONF_P1_ENTITY) and pair_given:
                # Only the pair was filled in: that is clearly the choice.
                user_input[CONF_P1_SOURCE] = P1_SOURCE_PAIR
            if user_input.get(CONF_P1_SOURCE) == P1_SOURCE_PAIR:
                if not pair_given:
                    errors["base"] = "p1_pair_incomplete"
                elif user_input[CONF_P1_IMPORT] == user_input[CONF_P1_EXPORT]:
                    errors["base"] = "p1_pair_same"
            elif not user_input.get(CONF_P1_ENTITY):
                errors["base"] = "p1_missing"
            if not errors and user_input.get(CONF_EXCLUDED_CLIMATE) and not user_input.get(CONF_EXCLUDED_ENERGY):
                errors["base"] = "excluded_needs_counter"
            if not errors:
                data = {**self.config_entry.options, **user_input}
                for key in (
                    CONF_P1_ENTITY,
                    CONF_P1_IMPORT,
                    CONF_P1_EXPORT,
                    CONF_SOLAR_FORECAST,
                    CONF_SOLAR_ENERGY,
                    CONF_SOLAR_POWER,
                    CONF_EXCLUDED_ENERGY,
                    CONF_EXCLUDED_CLIMATE,
                    CONF_WORKDAY_ENTITY,
                    CONF_CURTAIL_SWITCH,
                    CONF_CURTAIL_NUMBER,
                    CONF_PRICE_ENTITY,
                    CONF_COST_IMPORT_COUNTERS,
                    CONF_COST_EXPORT_COUNTERS,
                ):
                    if not user_input.get(key):
                        data.pop(key, None)
                for key in (CONF_MIN_PRICE, CONF_TARIFF_FIXED_MONTH):
                    if user_input.get(key) is None:
                        data.pop(key, None)
                return self.async_create_entry(data=data)
        options = dict(self.config_entry.options)
        if user_input is not None:
            options.update(user_input)
        single = options.get(CONF_P1_ENTITY) or suggest_p1_entity(self.hass)
        pair_import, pair_export = suggest_p1_pair(self.hass)
        solar_forecast, solar_energy = suggest_solar(self.hass)
        price = options.get(CONF_PRICE_ENTITY) or suggest_price(self.hass)
        # Without an earlier choice, prefer the DSMR pair when it exists: it reports every telegram.
        default_source = P1_SOURCE_PAIR if pair_import and pair_export and not options.get(CONF_P1_ENTITY) else P1_SOURCE_SINGLE
        source = options.get(CONF_P1_SOURCE, default_source)
        defaults = Settings()
        tariffs = Tariffs()
        counters_import, counters_export = suggest_meter_counters(self.hass)
        suppliers = await supplier_choices(self.hass, self.config_entry)
        supplier = options.get(CONF_TARIFF_SUPPLIER, TARIFF_OWN)
        if supplier not in {c["value"] for c in suppliers}:
            supplier = TARIFF_OWN
        schema = vol.Schema(
            {
                vol.Required(CONF_P1_SOURCE, default=source): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=[P1_SOURCE_SINGLE, P1_SOURCE_PAIR], translation_key="p1_source")
                ),
                vol.Optional(CONF_P1_ENTITY, description={"suggested_value": single}): _power_sensor(),
                vol.Optional(CONF_P1_IMPORT, description={"suggested_value": options.get(CONF_P1_IMPORT) or pair_import}): _power_sensor(),
                vol.Optional(CONF_P1_EXPORT, description={"suggested_value": options.get(CONF_P1_EXPORT) or pair_export}): _power_sensor(),
                vol.Optional(
                    CONF_SOLAR_FORECAST, description={"suggested_value": options.get(CONF_SOLAR_FORECAST) or solar_forecast}
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
                vol.Optional(
                    CONF_SOLAR_ENERGY, description={"suggested_value": options.get(CONF_SOLAR_ENERGY) or solar_energy}
                ): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.ENERGY)),
                vol.Optional(CONF_SOLAR_POWER, description={"suggested_value": options.get(CONF_SOLAR_POWER)}): (
                    selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.POWER, multiple=True)
                    )
                ),
                vol.Optional(CONF_EXCLUDED_ENERGY, description={"suggested_value": options.get(CONF_EXCLUDED_ENERGY)}): (
                    selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor", device_class=SensorDeviceClass.ENERGY))
                ),
                vol.Optional(CONF_EXCLUDED_CLIMATE, description={"suggested_value": options.get(CONF_EXCLUDED_CLIMATE)}): (
                    selector.EntitySelector(selector.EntitySelectorConfig(domain="climate"))
                ),
                vol.Required(
                    CONF_EXCLUDED_MODES, default=options.get(CONF_EXCLUDED_MODES, DEFAULT_EXCLUDED_MODES)
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=HVAC_MODE_CHOICES, multiple=True, translation_key="hvac_modes")
                ),
                vol.Required(CONF_MIN_SOC, default=options.get(CONF_MIN_SOC, defaults.min_soc)): _percent(5, 50),
                vol.Required(CONF_MAX_SOC, default=options.get(CONF_MAX_SOC, defaults.max_soc)): _percent(70, 100),
                vol.Optional(CONF_PRICE_ENTITY, description={"suggested_value": price}): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(
                    CONF_EXPENSIVE_HOURS, default=options.get(CONF_EXPENSIVE_HOURS, DEFAULT_EXPENSIVE_HOURS)
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(min=1, max=12, step=1, unit_of_measurement="h", mode=selector.NumberSelectorMode.BOX)
                ),
                vol.Required(CONF_RESERVE_SOC, default=options.get(CONF_RESERVE_SOC, DEFAULT_RESERVE_SOC)): _percent(0, 80),
                vol.Optional(CONF_MIN_PRICE, description={"suggested_value": options.get(CONF_MIN_PRICE)}): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=-1, max=2, step=0.01, unit_of_measurement="€/kWh", mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(CONF_TARIFF_SUPPLIER, default=supplier): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=suppliers, mode=selector.SelectSelectorMode.DROPDOWN)
                ),
                vol.Required(CONF_TARIFF_ENERGY_TAX, default=options.get(CONF_TARIFF_ENERGY_TAX, tariffs.energy_tax)): _box(
                    0, 1, "any", "€/kWh"
                ),
                vol.Required(CONF_TARIFF_MARKUP_IMPORT, default=options.get(CONF_TARIFF_MARKUP_IMPORT, tariffs.markup_import)): _box(
                    -1, 1, "any", "€/kWh"
                ),
                vol.Required(CONF_TARIFF_MARKUP_EXPORT, default=options.get(CONF_TARIFF_MARKUP_EXPORT, tariffs.markup_export)): _box(
                    -1, 1, "any", "€/kWh"
                ),
                vol.Required(CONF_TARIFF_VAT, default=options.get(CONF_TARIFF_VAT, tariffs.vat)): _box(0, 30, 0.1, "%"),
                vol.Required(CONF_TARIFF_SOLAR_BONUS, default=options.get(CONF_TARIFF_SOLAR_BONUS, tariffs.solar_bonus)): _box(
                    0, 50, 0.1, "%"
                ),
                vol.Optional(CONF_TARIFF_FIXED_MONTH, description={"suggested_value": options.get(CONF_TARIFF_FIXED_MONTH)}): _box(
                    -200, 500, 0.01, "€"
                ),
                vol.Optional(
                    CONF_COST_IMPORT_COUNTERS, description={"suggested_value": options.get(CONF_COST_IMPORT_COUNTERS) or counters_import}
                ): _energy_sensors(),
                vol.Optional(
                    CONF_COST_EXPORT_COUNTERS, description={"suggested_value": options.get(CONF_COST_EXPORT_COUNTERS) or counters_export}
                ): _energy_sensors(),
                vol.Required(CONF_PLAN_WEAR_COST, default=options.get(CONF_PLAN_WEAR_COST, DEFAULT_PLAN_WEAR_COST)): _box(
                    0, 0.5, 0.001, "€/kWh"
                ),
                vol.Required(
                    CONF_PLAN_GRID_CHARGE_COST, default=options.get(CONF_PLAN_GRID_CHARGE_COST, DEFAULT_PLAN_GRID_CHARGE_COST)
                ): _box(0, 0.5, 0.001, "€/kWh"),
                vol.Required(CONF_PLAN_ALLOW_EXPORT, default=options.get(CONF_PLAN_ALLOW_EXPORT, False)): bool,
                vol.Required(CONF_PLAN_LOAD_MARGIN, default=options.get(CONF_PLAN_LOAD_MARGIN, 0)): _percent(0, 50),
                vol.Required(CONF_PLAN_BUFFER, default=options.get(CONF_PLAN_BUFFER, 0)): _percent(0, 50),
                vol.Required(CONF_CALIBRATION_DAYS, default=options.get(CONF_CALIBRATION_DAYS, 21)): _box(0, 90, 1, "d"),
                vol.Optional(CONF_PRICE_FORECAST_ENTITY, description={"suggested_value": options.get(CONF_PRICE_FORECAST_ENTITY)}): (
                    selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor"))
                ),
                vol.Required(
                    CONF_PRICE_FORECAST_MODE, default=options.get(CONF_PRICE_FORECAST_MODE, "indicative")
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=["off", "indicative", "use"], translation_key="price_forecast_mode")
                ),
                vol.Required(CONF_PRICE_FORECAST_DAYS, default=options.get(CONF_PRICE_FORECAST_DAYS, 1)): _box(0, 2, 1, "d"),
                vol.Required(CONF_PRICE_FORECAST_VALUE, default=options.get(CONF_PRICE_FORECAST_VALUE, "low")): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=["low", "mid"], translation_key="price_forecast_value")
                ),
                vol.Optional(
                    CONF_WORKDAY_ENTITY, description={"suggested_value": options.get(CONF_WORKDAY_ENTITY) or suggest_workday(self.hass)}
                ): (selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor", integration="workday"))),
                vol.Required(CONF_CURTAIL_MODE, default=options.get(CONF_CURTAIL_MODE, CURTAIL_OFF)): selector.SelectSelector(
                    selector.SelectSelectorConfig(options=list(CURTAIL_MODES), translation_key="curtail_mode")
                ),
                vol.Optional(CONF_CURTAIL_SWITCH, description={"suggested_value": options.get(CONF_CURTAIL_SWITCH)}): (
                    selector.EntitySelector(selector.EntitySelectorConfig(domain="switch"))
                ),
                vol.Optional(CONF_CURTAIL_NUMBER, description={"suggested_value": options.get(CONF_CURTAIL_NUMBER)}): (
                    selector.EntitySelector(selector.EntitySelectorConfig(domain="number"))
                ),
                vol.Required(CONF_CURTAIL_INVERTER_W, default=options.get(CONF_CURTAIL_INVERTER_W, 0)): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0, max=100000, step=100, unit_of_measurement="W", mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(CONF_VACATION_AWAY, default=options.get(CONF_VACATION_AWAY, False)): bool,
                vol.Required(CONF_LIVE_OFF_AFTER_RESTART, default=options.get(CONF_LIVE_OFF_AFTER_RESTART, False)): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)


def _box(low: float, high: float, step: float | Literal["any"], unit: str) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(min=low, max=high, step=step, unit_of_measurement=unit, mode=selector.NumberSelectorMode.BOX)
    )


def _percent(low: int, high: int) -> selector.NumberSelector:
    return selector.NumberSelector(
        selector.NumberSelectorConfig(min=low, max=high, step=1, unit_of_measurement="%", mode=selector.NumberSelectorMode.BOX)
    )
