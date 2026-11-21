"""Reading one set: a DataUpdateCoordinator per set."""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any, cast

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CAPACITY_OVERRIDE,
    CONF_HOST,
    CONF_NUMBER,
    CONF_PRODUCT,
    CONF_SERIAL,
    DOMAIN,
    LOGGER,
    SCAN_INTERVAL_IDLE,
)
from .core.client import ZendureClient, ZendureError
from .core.device_table import CapacityResult, model_info, set_capacity
from .core.health import SetHealth
from .core.models import SetReport, SetStatus
from .core.totals import SetSnapshot
from .core.zensdk import ZenSdkError, derive_status, parse_report

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry, ConfigSubentry


@dataclass(frozen=True, slots=True)
class SetData:
    """Latest known state of one set."""

    report: SetReport | None
    raw: Mapping[str, Any] | None
    capacity: CapacityResult | None
    status: SetStatus
    online: bool
    serial_mismatch: bool


class SetCoordinator(DataUpdateCoordinator[SetData]):
    """Reads ``/properties/report`` of one set and keeps the last good report.

    Never raises from an update: a set that does not answer becomes
    offline after a few attempts (core.health) without blocking other sets.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry[Any], subentry: ConfigSubentry) -> None:
        self.subentry_id = subentry.subentry_id
        self.number: int = int(subentry.data[CONF_NUMBER])
        self.serial: str = str(subentry.data[CONF_SERIAL])
        self.product: str = str(subentry.data.get(CONF_PRODUCT, ""))
        self.host: str = str(subentry.data[CONF_HOST])
        override = subentry.data.get(CONF_CAPACITY_OVERRIDE)
        self.capacity_override: float | None = float(override) if override else None
        self.client = ZendureClient(self.host, async_get_clientsession(hass))
        self.health = SetHealth()
        self._last_report: SetReport | None = None
        self._last_raw: Mapping[str, Any] | None = None
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"ZEM set {self.number}",
            update_interval=timedelta(seconds=SCAN_INTERVAL_IDLE),
            always_update=True,
        )

    @property
    def model_name(self) -> str:
        info = model_info(self.product)
        return info.name if info else self.product or "Zendure"

    @property
    def mismatch_issue_id(self) -> str:
        return f"serial_mismatch_{self.subentry_id}"

    async def _async_update_data(self) -> SetData:
        now = time.monotonic()
        mismatch = False
        try:
            raw = await self.client.get_report_raw()
            report = parse_report(raw)
        except (ZendureError, ZenSdkError) as err:
            self.health.record_failure(now, str(err))
            LOGGER.debug("Set %s not readable: %s", self.number, err)
        else:
            if report.serial != self.serial:
                mismatch = True
                self.health.record_failure(now, "different serial number")
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    self.mismatch_issue_id,
                    is_fixable=False,
                    severity=ir.IssueSeverity.ERROR,
                    translation_key="serial_mismatch",
                    translation_placeholders={"number": str(self.number), "host": self.host},
                )
            else:
                ir.async_delete_issue(self.hass, DOMAIN, self.mismatch_issue_id)
                self.health.record_success(now)
                self._last_report = report
                self._last_raw = raw
                if not self.product:
                    self.product = report.product
        self.health.check_stale(now)
        return self._build(mismatch)

    def _build(self, mismatch: bool) -> SetData:
        report = self._last_report
        capacity = set_capacity(report, self.capacity_override) if report else None
        online = self.health.online and not mismatch
        if not online or report is None:
            status = SetStatus.OFFLINE
        else:
            # Read-only milestone: use the SOC limits stored on the set itself.
            status = derive_status(report, report.min_soc or 0.0, report.max_soc or 100.0)
        return SetData(
            report=report,
            raw=self._last_raw,
            capacity=capacity,
            status=status,
            online=online,
            serial_mismatch=mismatch,
        )

    def snapshot(self) -> SetSnapshot:
        data = cast("SetData | None", self.data)  # None before the first refresh
        if data is None:
            return SetSnapshot(report=None, capacity_kwh=0.0, online=False)
        return SetSnapshot(
            report=data.report,
            capacity_kwh=data.capacity.capacity_kwh if data.capacity else 0.0,
            online=data.online,
            offline_since=self.health.offline_since,
        )
