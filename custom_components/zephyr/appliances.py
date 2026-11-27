"""Planned appliances in Home Assistant (B36, SPEC-geplande-verbruikers).

Each appliance is a subentry (name, kind, optional smart-plug power sensor, standard window).
ZEPHYR learns its profile from the plug (recorder history at start, then live), keeps the
announced runs in a store, gives them to the planner, and shows the advised start.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    CONF_APPLIANCE_AFTER_WASH,
    CONF_APPLIANCE_FROM,
    CONF_APPLIANCE_KIND,
    CONF_APPLIANCE_NAME,
    CONF_APPLIANCE_POWER,
    CONF_APPLIANCE_UNTIL,
    DOMAIN,
    LOGGER,
    SUBENTRY_APPLIANCE,
)
from .core.appliances import (
    DRYERS,
    OTHER,
    RUNS_KEPT,
    WASHER,
    PlannedRun,
    Run,
    default_profile,
    detect_runs,
    learned_profile,
    standard_window,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry, ConfigSubentry

STORAGE_VERSION = 1
HISTORY_DAYS = 10
RUNNING_W = 5.0


class Appliance:
    """One configured appliance."""

    def __init__(self, subentry: ConfigSubentry) -> None:
        data = subentry.data
        self.id = subentry.subentry_id
        self.name: str = data.get(CONF_APPLIANCE_NAME) or subentry.title
        self.kind: str = data.get(CONF_APPLIANCE_KIND, OTHER)
        self.power_entity: str | None = data.get(CONF_APPLIANCE_POWER) or None
        self.window_from: str = data.get(CONF_APPLIANCE_FROM) or ""
        self.window_until: str = data.get(CONF_APPLIANCE_UNTIL) or "20:00"
        self.after_washer: bool = bool(data.get(CONF_APPLIANCE_AFTER_WASH, False))
        """Dryer: planned along, once after the last wash, whenever the washing machine is planned."""
        self.runs: list[Run] = []
        self.samples: list[tuple[datetime, float]] = []
        self.power_w: float | None = None

    @property
    def running(self) -> bool | None:
        return None if self.power_entity is None or self.power_w is None else self.power_w > RUNNING_W

    def profile(self) -> list[float]:
        return learned_profile(self.runs[-RUNS_KEPT:]) or default_profile(self.kind)

    @property
    def profile_source(self) -> str:
        return "learned" if learned_profile(self.runs[-RUNS_KEPT:]) else "default"


class ApplianceManager:
    """Appliances, their learned runs and the planned runs of one ZEPHYR entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry[Any]) -> None:
        self.hass = hass
        self.entry = entry
        self.appliances: dict[str, Appliance] = {
            s.subentry_id: Appliance(s) for s in entry.subentries.values() if s.subentry_type == SUBENTRY_APPLIANCE
        }
        self.planned: list[PlannedRun] = []
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}.appliances")
        self._listeners: list[Callable[[], None]] = []
        self._on_change: Callable[[], None] | None = None
        self.revision = 0
        """Goes up with every change, so the panel knows when to fetch again."""

    # --- start, store ------------------------------------------------------------------

    async def async_start(self, on_change: Callable[[], None]) -> Callable[[], None]:
        """Load the store, learn from the recorder, listen to the plugs."""
        self._on_change = on_change
        stored = await self._store.async_load() or {}
        self.planned = [PlannedRun.from_dict(p) for p in stored.get("planned") or [] if p.get("appliance") in self.appliances]
        for appliance_id, runs in (stored.get("runs") or {}).items():
            if appliance_id in self.appliances:
                self.appliances[appliance_id].runs = [Run.from_dict(r) for r in runs][-RUNS_KEPT:]
        unsubs: list[Callable[[], None]] = []
        plugs = [a.power_entity for a in self.appliances.values() if a.power_entity]
        if plugs:
            unsubs.append(async_track_state_change_event(self.hass, plugs, self._plug_changed))
            self.hass.async_create_background_task(self._learn_history(), "zephyr: appliance history")
        unsubs.append(async_track_time_interval(self.hass, self._tidy, timedelta(minutes=1)))

        def stop() -> None:
            for unsub in unsubs:
                unsub()

        return stop

    def _save(self) -> None:
        self._store.async_delay_save(self._data, 5)

    def _data(self) -> dict[str, Any]:
        return {
            "planned": [p.as_dict() for p in self.planned],
            "runs": {a.id: [r.as_dict() for r in a.runs[-RUNS_KEPT:]] for a in self.appliances.values()},
        }

    def _changed(self, replan: bool = True) -> None:
        self.revision += 1
        for listener in list(self._listeners):
            listener()
        if replan and self._on_change is not None:
            self._on_change()

    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(listener)

        def remove() -> None:
            self._listeners.remove(listener)

        return remove

    # --- learning ----------------------------------------------------------------------

    async def _learn_history(self) -> None:
        """Runs from the recorder (raw history of the last days), once at start."""
        try:
            from homeassistant.components.recorder.history import state_changes_during_period
            from homeassistant.helpers.recorder import get_instance
        except ImportError:  # pragma: no cover - recorder not available
            return
        start = dt_util.utcnow() - timedelta(days=HISTORY_DAYS)
        for appliance in self.appliances.values():
            if not appliance.power_entity:
                continue
            entity = appliance.power_entity
            try:
                states = await get_instance(self.hass).async_add_executor_job(state_changes_during_period, self.hass, start, None, entity)
            except Exception as err:
                LOGGER.debug("Appliance %s: no history (%s)", appliance.name, err)
                continue
            samples = [(s.last_changed, w) for s in states.get(entity, []) if (w := _watts(s.state)) is not None]
            if samples:
                samples.append((dt_util.utcnow(), samples[-1][1]))  # the last state holds until now
            known = {r.start for r in appliance.runs}
            new = [r for r in detect_runs(samples) if r.start not in known]
            if new:
                appliance.runs = sorted(appliance.runs + new, key=lambda r: r.start)[-RUNS_KEPT:]
                LOGGER.debug("Appliance %s: %d runs from the recorder", appliance.name, len(new))
        self._save()
        self._changed()

    @callback
    def _plug_changed(self, event: Event[EventStateChangedData]) -> None:
        state = event.data["new_state"]
        if state is None:
            return
        for appliance in self.appliances.values():
            if appliance.power_entity != state.entity_id:
                continue
            watts = _watts(state.state)
            if watts is None:
                return
            was = appliance.running
            appliance.power_w = watts
            appliance.samples.append((state.last_changed, watts))
            cutoff = dt_util.utcnow() - timedelta(hours=12)
            appliance.samples = [s for s in appliance.samples if s[0] >= cutoff]
            if was != appliance.running:
                self._changed(replan=False)

    @callback
    def _tidy(self, now: datetime) -> None:
        """Close finished runs seen on the plugs; drop planned runs that ran or expired."""
        changed = False
        for appliance in self.appliances.values():
            if not appliance.samples:
                continue
            finished = [
                r
                for r in detect_runs([*appliance.samples, (now, appliance.power_w or 0.0)])
                if r.start not in {x.start for x in appliance.runs}
            ]
            # Only runs that ended (the series continues after them).
            for run in finished:
                if run.start + timedelta(minutes=run.minutes) < now - timedelta(minutes=5):
                    appliance.runs = [*appliance.runs, run][-RUNS_KEPT:]
                    self._consume(appliance.id, run.start)
                    changed = True
        before = len(self.planned)
        self.planned = [p for p in self.planned if p.window_end > now]
        if changed or len(self.planned) != before:
            self._save()
            self._changed()

    def _consume(self, appliance_id: str, started: datetime) -> None:
        """A run seen on the plug fulfils the first planned run of that appliance whose window it started in."""
        for index, planned in enumerate(self.planned):
            if planned.appliance == appliance_id and planned.window_start - timedelta(minutes=30) <= started <= planned.window_end:
                del self.planned[index]
                return

    # --- planning ----------------------------------------------------------------------

    def plan(
        self,
        appliance_id: str,
        runs: int = 1,
        start_after: datetime | None = None,
        done_before: datetime | None = None,
        fixed_start: datetime | None = None,
    ) -> list[PlannedRun]:
        """Announce runs; the window is the appliance's standard one unless given."""
        appliance = self.appliances[appliance_id]
        now = dt_util.now()
        start, end = standard_window(now, appliance.window_from, appliance.window_until)
        start = start_after or start
        end = done_before or end
        if fixed_start is not None:
            end = max(end, fixed_start + timedelta(minutes=len(appliance.profile())))
        after = None
        if appliance.kind in DRYERS:
            washers = [a.id for a in self.appliances.values() if a.kind == WASHER]
            after = next((w for w in washers if any(p.appliance == w for p in self.planned)), None)
        added = [PlannedRun(appliance_id, start, end, fixed_start, after) for _ in range(max(runs, 1))]
        self.planned.extend(added)
        if appliance.kind == WASHER:
            added += self._dryers_along(appliance_id, now)
        self._save()
        self._changed()
        return added

    def _dryers_along(self, washer_id: str, now: datetime) -> list[PlannedRun]:
        """Dryers set to run after the washing: one run each, after the last wash (none if one is planned)."""
        added: list[PlannedRun] = []
        for dryer in self.appliances.values():
            if dryer.kind not in DRYERS or not dryer.after_washer or any(p.appliance == dryer.id for p in self.planned):
                continue
            start, end = standard_window(now, dryer.window_from, dryer.window_until)
            run = PlannedRun(dryer.id, start, end, None, washer_id)
            self.planned.append(run)
            added.append(run)
        return added

    def clear(self, appliance_id: str | None = None) -> int:
        before = len(self.planned)
        along = {
            a.id
            for a in self.appliances.values()
            if appliance_id is not None
            and self.appliances.get(appliance_id) is not None
            and self.appliances[appliance_id].kind == WASHER
            and a.after_washer
        }
        # Clearing the washing also clears the dryer runs that were planned along with it.
        self.planned = [
            p
            for p in self.planned
            if appliance_id is not None and p.appliance != appliance_id and not (p.appliance in along and p.after == appliance_id)
        ]
        self._save()
        self._changed()
        return before - len(self.planned)

    def remove(self, index: int) -> bool:
        """Remove one planned run (its place in ``planned``)."""
        if not 0 <= index < len(self.planned):
            return False
        del self.planned[index]
        self._save()
        self._changed()
        return True

    def profiles(self) -> dict[str, list[float]]:
        return {a.id: a.profile() for a in self.appliances.values()}

    def runs_of(self, appliance_id: str) -> list[PlannedRun]:
        return [p for p in self.planned if p.appliance == appliance_id]

    def published(self) -> None:
        """The planner placed the runs (best starts set): update the entities."""
        self._changed(replan=False)

    def by_name(self, name: str) -> Appliance | None:
        lowered = name.strip().lower()
        return next((a for a in self.appliances.values() if a.name.lower() == lowered or a.id == name), None)

    def view(self) -> dict[str, Any]:
        """Appliances and planned runs for the panel (SPEC-ui-planner §4.1)."""
        appliances = []
        for a in self.appliances.values():
            profile = a.profile()
            item: dict[str, Any] = {
                "id": a.id,
                "name": a.name,
                "kind": a.kind,
                "plug": a.power_entity is not None,
                "running": a.running,
                "profile": a.profile_source,
                "runs_seen": len(a.runs),
                "kwh": round(sum(profile) / 60000, 3),
                "minutes": len(profile),
                "window": {"from": a.window_from or None, "until": a.window_until},
                "after_washer": a.after_washer,
            }
            if a.profile_source == "learned":
                item["profile_w"] = [round(w) for w in profile]
            appliances.append(item)
        planned = []
        for index, p in enumerate(self.planned):
            after = self.appliances.get(p.after) if p.after else None
            planned.append(
                {
                    "index": index,
                    "appliance": p.appliance,
                    "window_start": p.window_start.isoformat(),
                    "window_end": p.window_end.isoformat(),
                    "fixed_start": None if p.fixed_start is None else p.fixed_start.isoformat(),
                    "after": None if after is None else after.name,
                    "best_start": None if p.best_start is None else p.best_start.isoformat(),
                    **p.details,
                }
            )
        return {"revision": self.revision, "appliances": appliances, "planned": planned}

    def diagnostics(self) -> dict[str, Any]:
        return {
            "appliances": [
                {
                    "name": a.name,
                    "kind": a.kind,
                    "plug": a.power_entity is not None,
                    "profile": a.profile_source,
                    "kwh": round(sum(a.profile()) / 60000, 3),
                    "minutes": len(a.profile()),
                    "runs_seen": len(a.runs),
                    "running": a.running,
                }
                for a in self.appliances.values()
            ],
            "planned": [
                {
                    **p.as_dict(),
                    "appliance": self.appliances[p.appliance].name if p.appliance in self.appliances else p.appliance,
                    "best_start": None if p.best_start is None else p.best_start.isoformat(),
                    **p.details,
                }
                for p in self.planned
            ],
        }


def _watts(value: str) -> float | None:
    if value in (STATE_UNAVAILABLE, STATE_UNKNOWN, ""):
        return None
    try:
        return float(value)
    except ValueError:
        return None
