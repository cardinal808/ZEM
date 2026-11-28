"""ZephyrEngine: one step = modes → safety → controller → per-set targets → write rules.

Pure and deterministic: time and measurements come in, commands and state
go out. The Home Assistant layer decides whether the commands are sent
(shadow mode: never).

Modes Standby, Zero meter, Fast charge, Fast discharge and Dynamic Forecasting
(the planner's action per quarter, SPEC-planner §7). With
more than one set, the whole setpoint goes to the first available set; the
distributor of SPEC-meerdere-sets follows in M7.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from typing import Any

from .controller import ControllerInput, ZeroMeterController
from .counters import SetCounters
from .device_table import charging_allowed_by_temperature, delivering_allowed_by_temperature
from .excluded_load import exclusion_for_controller
from .grid_filter import GridFilter
from .models import AcMode, GridReverse, SetReport
from .p1_profile import P1Profile
from .planner import Action as PlanAction
from .settings import Settings
from .twin import GridTally, TwinSet
from .zensdk import grid_reverse_command, power_command, soc_limits_command, standby_command


class Mode(StrEnum):
    STANDBY = "standby"
    ZERO_METER = "zero_meter"
    FAST_CHARGE = "fast_charge"
    FAST_DISCHARGE = "fast_discharge"
    FORECAST = "dynamic_forecasting"


ZERO_METER_MODES = (Mode.ZERO_METER, Mode.FORECAST)
"""Modes that follow the P1 meter."""
PLAN_RESTART_PAUSE = 120.0
BATTERY_HISTORY_FOR = 60.0
"""s of real battery power kept for the virtual P1 at the moment of a measurement (§7.2)."""
"""s: grid charging (L) and export (X) start only after grid charging was off this long (§7)."""
PLAN_CHARGE_GRACE = 10.0
"""s: grid charging stops when the plan has not said L for this long (§7)."""


class Action(StrEnum):
    STANDBY = "standby"
    CHARGE = "charge"
    DELIVER = "deliver"
    HOLD = "hold"
    BLOCKED = "blocked"
    CALIBRATION = "calibration"


class ReasonCode(StrEnum):
    STANDBY_MODE = "standby_mode"
    P1_MISSING = "p1_missing"
    P1_LOST = "p1_lost"
    P1_STALE = "p1_stale"
    P1_TOO_SLOW = "p1_too_slow"
    NO_SET = "no_set"
    DELIVERING = "delivering"
    CHARGING_SOLAR = "charging_solar"
    IDLE_SMALL = "idle_small"
    FULL = "full"
    EMPTY = "empty"
    BLOCKED = "blocked"
    SWITCHING = "switching"
    FAST_CHARGE = "fast_charge"
    FAST_DISCHARGE = "fast_discharge"
    RECHARGE_MIN = "recharge_min"
    TEMPERATURE = "temperature"
    CALIBRATING = "calibrating"
    NOT_EXPENSIVE = "not_expensive"
    NO_PRICES = "no_prices"
    RESERVE_CHARGE = "reserve_charge"
    PLAN_CHARGE = "plan_charge"
    PLAN_CHARGE_WAIT = "plan_charge_wait"
    PLAN_HOLD = "plan_hold"
    PLAN_EXPORT = "plan_export"


REASON_TEXT: dict[ReasonCode, tuple[str, str]] = {
    ReasonCode.STANDBY_MODE: ("Standby mode.", "Modus Standby."),
    ReasonCode.P1_MISSING: (
        "No P1 reading yet: choose the P1 meter in the ZEPHYR options.",
        "Nog geen P1-meting: kies de P1-meter bij de opties van ZEPHYR.",
    ),
    ReasonCode.P1_LOST: ("No P1 reading for {age} s: sets in standby.", "Geen P1-meting sinds {age} s: sets in standby."),
    ReasonCode.P1_STALE: ("No fresh P1 reading ({age} s): battery at 0 W.", "Geen verse P1-meting ({age} s): accu op 0 W."),
    ReasonCode.P1_TOO_SLOW: (
        "The P1 meter reports too slowly ({interval} s); zero-meter control is paused.",
        "De P1-meter meldt te traag ({interval} s); Nul op de meter staat stil.",
    ),
    ReasonCode.NO_SET: ("No set available.", "Geen set beschikbaar."),
    ReasonCode.DELIVERING: ("Delivering {power} W to the house (grid {grid} W).", "Levert {power} W aan het huis (net {grid} W)."),
    ReasonCode.CHARGING_SOLAR: ("Charging {power} W from solar surplus.", "Laadt {power} W uit zonne-overschot."),
    ReasonCode.IDLE_SMALL: ("Demand too small ({power} W): battery idle.", "Vraag te klein ({power} W): accu staat stil."),
    ReasonCode.FULL: ("Battery full ({soc} %): charging stopped.", "Accu vol ({soc} %): laden gestopt."),
    ReasonCode.EMPTY: ("Battery empty ({soc} %): delivering stopped.", "Accu leeg ({soc} %): leveren gestopt."),
    ReasonCode.BLOCKED: ("Delivering is blocked.", "Leveren is geblokkeerd."),
    ReasonCode.SWITCHING: (
        "Waiting before switching between charging and delivering.",
        "Wacht even voor de wissel tussen laden en leveren.",
    ),
    ReasonCode.FAST_CHARGE: ("Fast charging to {soc} %.", "Snel opladen tot {soc} %."),
    ReasonCode.FAST_DISCHARGE: ("Fast discharging to {soc} %.", "Snel ontladen tot {soc} %."),
    ReasonCode.RECHARGE_MIN: ("Below the minimum SOC: recharging with {power} W.", "Onder het minimum: bijladen met {power} W."),
    ReasonCode.TEMPERATURE: ("Temperature outside the safe range ({temp} °C).", "Temperatuur buiten het veilige bereik ({temp} °C)."),
    ReasonCode.CALIBRATING: ("The set is calibrating itself.", "De set kalibreert zichzelf."),
    ReasonCode.NOT_EXPENSIVE: (
        "Delivering only in the most expensive hours (next from {next}).",
        "Levert alleen in de duurste uren (volgende vanaf {next}).",
    ),
    ReasonCode.NO_PRICES: ("No prices: delivering paused.", "Geen prijzen: leveren staat stil."),
    ReasonCode.RESERVE_CHARGE: (
        "Charging {power} W from the grid to the reserve of {reserve} % (cheap hour).",
        "Laadt {power} W uit het net tot de reserve van {reserve} % (goedkoop uur).",
    ),
    ReasonCode.PLAN_CHARGE: ("Plan: charging {power} W from the grid.", "Plan: laadt {power} W uit het net."),
    ReasonCode.PLAN_CHARGE_WAIT: (
        "Plan: grid charging starts after a pause of 2 minutes.",
        "Plan: laden uit het net start na een pauze van 2 minuten.",
    ),
    ReasonCode.PLAN_HOLD: ("Plan: holding, the battery does not deliver now.", "Plan: vasthouden, de accu levert nu niet."),
    ReasonCode.PLAN_EXPORT: ("Plan: exporting {power} W from the battery.", "Plan: levert {power} W terug uit de accu."),
}


@dataclass(frozen=True, slots=True)
class Reason:
    code: ReasonCode
    params: dict[str, Any] = field(default_factory=dict)

    def text(self, language: str = "en") -> str:
        en, nl = REASON_TEXT[self.code]
        template = nl if language.startswith("nl") else en
        return template.format(**self.params)


@dataclass(frozen=True, slots=True)
class SetView:
    """What the engine needs from one set."""

    key: str
    number: int
    report: SetReport | None
    online: bool
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class Command:
    key: str
    props: dict[str, int]
    kind: str
    """"power", "standby", "soc_limits" or "grid_reverse" (``gridReverse`` may also ride along
    with another command for the same set)."""
    cause: str | None = None
    """For the counters, when it differs from ``kind``: "startup" for SOC limits when the set is first seen."""

    @property
    def kinds(self) -> list[str]:
        """What to count for this command: its cause, and ``grid_reverse`` when it rides along."""
        first = self.cause or self.kind
        if self.kind != "grid_reverse" and "gridReverse" in self.props:
            return [first, "grid_reverse"]
        return [first]


@dataclass(frozen=True, slots=True)
class StepResult:
    mode: Mode
    action: Action
    reason: Reason
    setpoint: int
    """Total setpoint in W (+ charging)."""
    targets: dict[str, int]
    commands: tuple[Command, ...]
    grid_power: float | None
    p1_ok: bool
    p1_interval: float | None
    mode_finished: bool
    """Fast charge/discharge reached its goal; the caller returns to the previous mode."""
    battery_power: float | None = None
    """Battery power the engine worked with (the twin's in shadow mode)."""
    measured_grid_power: float | None = None
    """P1 as measured; differs from ``grid_power`` only in shadow mode with the twin."""


@dataclass(slots=True)
class _SetState:
    last_power: int | None = None
    last_sent_at: float = -1e9
    last_ac_mode: AcMode | None = None
    standby: bool = False
    zero_since: float | None = None
    full: bool = False
    empty: bool = False
    limits_checked: bool = False
    seen: bool = False
    """SOC limits checked once since the start: a later check is a settings change, not ``startup``."""
    flash_paused: bool = False
    grid_reverse_sent: tuple[GridReverse, float] | None = None
    counters: SetCounters = field(default_factory=SetCounters)


class ZephyrEngine:
    """Decides what every set should do. Keep one instance per installation."""

    def __init__(self, settings: Settings | None = None, mode: Mode = Mode.ZERO_METER) -> None:
        self.settings = (settings or Settings()).validated()
        self.mode = mode
        self.controller = ZeroMeterController(self.settings)
        self.grid_filter = GridFilter(self.settings)
        self._sets: dict[str, _SetState] = {}
        self._p1_value: float | None = None
        self._p1_at: float | None = None
        self._p1_interval: float | None = None
        self._block_since: float | None = None
        self._export_blocked: bool | None = None
        self.peak_kwh = 0.0
        """Energy of short peaks the step filter (B20) left to the grid, since the start (PLANNING 1.3)."""
        self._peak_at: tuple[float, float] | None = None
        self.p1_profile = P1Profile()
        self._stale = False
        self._stale_events: deque[float] = deque(maxlen=10_000)
        self.limits_cause: str | None = None
        """Cause for the next SOC-limit writes when not the first sight (e.g. "calibration")."""
        self.count_commands = True
        """Count commands when they are decided (shadow mode, tests). Live, the writer counts
        them once the set accepted them (``counters_record``)."""
        self.day_of: Callable[[float], str | None] = lambda _now: None
        """Local calendar day for the day totals of the counters (set by the HA layer)."""
        self._price_block: Reason | None = None
        self._align_p1 = False
        self._grid_history: deque[tuple[float, float]] = deque(maxlen=100)
        self._reserve_charge: tuple[int, float] | None = None
        self._started: float | None = None
        self._p1_changed_at: float | None = None
        self._p1_gaps: deque[float] = deque(maxlen=30)
        self._p1_seq = 0
        self._p1_sample_at: float | None = None
        self._p1_measured: float | None = None
        self._twins: dict[str, TwinSet] | None = None
        self._real_battery: float | None = None
        self._battery_history: deque[tuple[float, float]] = deque()
        """(time, real battery power of the sets), the last BATTERY_HISTORY_FOR s (shadow mode)."""
        self._twin_p1_at: float | None = None
        self._twin_real_at_p1: float | None = None
        self._p1_history: deque[tuple[float, float]] = deque(maxlen=200)
        self.tally_measured = GridTally()
        self._plan: PlanAction | None = None
        self._excluded_load = 0.0
        self._excluded_now = 0.0
        """W of the excluded load taken out of the P1 in the last zero-meter step (B41)."""
        self._plan_l_seen = -1e9
        self._grid_charging = False
        self._grid_charge_stopped = -1e9
        self._exporting = False
        self.tally_virtual = GridTally()

    def enable_twin(self) -> None:
        """Shadow mode: work with a virtual set that follows ZEPHYR's commands (core/twin.py)."""
        self._twins = {}
        self.controller.trust_commands = True

    def set_live(self, live: bool, now: float, sets: Sequence[SetView]) -> None:
        """Switch between shadow mode (twin) and live control (PLAN-M4b §2.2).

        Going live: the controller continues from the measured power of the sets (B35) and the
        write bookkeeping starts over, so the first real command is not suppressed by what the
        twin was told. Back to shadow: a fresh twin. The counters stay (B33): they cover the
        last hour and 24 hours whatever the mode, and the flash safety net needs them.
        """
        measured = sum(v.report.battery_power_ac for v in sets if v.report is not None and v.online)
        self._sets = {key: _SetState(counters=state.counters) for key, state in self._sets.items()}
        self.tally_virtual = GridTally()
        if live:
            self._twins = None
            self._real_battery = None
            self._battery_history.clear()
            self._twin_p1_at = self._twin_real_at_p1 = None
            # Live: work from the measured power of the set and wait until it has reached each
            # command (controller ``wait_for_reach``). Trusting the last command instead doubled
            # every start: a set starting from 0 W needs ~9 s before power flows, so after the
            # settle time P1 still showed the full demand and ZEPHYR added it again (seen live
            # 25-11: 520 -> 1030 -> 1290 W, export, then 0 W). Shifting P1 by a fixed 1.5 s to
            # match the report (0.5.3) did not fit either: the report lag varies (0-3 s).
            self._align_p1 = False
            self._grid_history.clear()
            self.controller.extra_settle = 0.0
            self.controller.trust_commands = False
            self.controller.wait_for_reach = True
            self.controller.take_over(measured, now)
        else:
            self._align_p1 = False
            self.controller.wait_for_reach = False
            self.enable_twin()
            self.controller.reset(now)

    @property
    def twin_enabled(self) -> bool:
        return self._twins is not None

    def _virtual_p1(self, now: float, measured: float, new_sample: bool) -> float:
        """The grid with the twin instead of the real set, at the moment of the P1 measurement.

        The P1 is taken at ``now - twin_delay`` (the moment the real report shows). A slow
        meter (DSMR 4, every 10 s) has no measurement at that moment: the newest one before it
        can be up to an interval older. The real battery and the twin are taken at the moment
        of that measurement too, not now: otherwise a step of the current controller in between
        makes the virtual P1 jump (OPDRACHT-p1-profiel §7.2). A repeat of the same value is not
        a new measurement and keeps the moment of the one it repeats.
        """
        assert self._twins is not None
        if new_sample or not self._p1_history:
            self._p1_history.append((now, measured))
        if self._real_battery is None:
            return measured
        at = now - self.settings.twin_delay
        t_p1, p1 = self._p1_history[0]
        for t, value in self._p1_history:
            if t <= at:
                t_p1, p1 = t, value
            else:
                break
        # The real report that shows the moment of the measurement: received twin_delay later.
        real = self._battery_history[0][1] if self._battery_history else self._real_battery
        for t, value in self._battery_history:
            if t <= t_p1 + self.settings.twin_delay:
                real = value
            else:
                break
        self._twin_p1_at, self._twin_real_at_p1 = t_p1, real
        # The controller waits this much longer after a command: the effect shows that much later.
        self.controller.extra_settle = self.settings.twin_delay
        twin = sum(t.power_at(now, t_p1) for t in self._twins.values())
        return p1 - real + twin

    def twin_alignment(self, now: float) -> dict[str, float] | None:
        """For the decision: the real battery the virtual P1 used and the age of that P1 measurement."""
        if self._twins is None or self._twin_p1_at is None or self._twin_real_at_p1 is None:
            return None
        return {"battery_real_at_p1": round(self._twin_real_at_p1), "p1_age_s": round(now - self._twin_p1_at, 1)}

    def _twin_power(self, now: float) -> float:
        assert self._twins is not None
        return sum(t.advance(now) for t in self._twins.values())

    # --- inputs ---------------------------------------------------------

    def update_settings(self, settings: Settings) -> None:
        self.settings = settings.validated()
        self.controller.settings = self.settings
        self.grid_filter.settings = self.settings
        for state in self._sets.values():
            state.limits_checked = False

    def set_mode(self, mode: Mode, now: float) -> None:
        if mode is not self.mode:
            self.mode = mode
            self.controller.reset(now)

    def p1_reported(self, now: float, value: float) -> None:
        """Every report of the P1 entity, also when the value did not change.

        Any report shows the source is alive (staleness). The meter's real
        interval is measured between changes of the value: some integrations
        re-report the same value much more often than the meter sends a new
        one (seen: every 0.4 s for a meter with a new value every 10 s).
        """
        measured = value
        # The meter's interval comes from the measured value: the twin changes the virtual one.
        changed = self._p1_measured is None or measured != self._p1_measured
        if self._twins is not None:
            self.tally_measured.add(now, measured)
            new_sample = changed or self._p1_interval is None or self._p1_sample_at is None or now - self._p1_sample_at >= self._p1_interval
            value = self._virtual_p1(now, measured, new_sample)
            self.tally_virtual.add(now, value)
        if changed:
            if self._p1_changed_at is not None:
                gap = now - self._p1_changed_at
                if 0 < gap < 120:
                    self._p1_gaps.append(gap)
                    # A steady value skips changes (gaps of 2x, 3x the interval), so take a low
                    # quantile of the recent gaps rather than the mean.
                    ordered = sorted(self._p1_gaps)
                    self._p1_interval = ordered[len(ordered) // 4]
            self._p1_changed_at = now
            self.p1_profile.update(now, self._p1_interval, len(self._p1_gaps))
            self.grid_filter.step_enabled = self.p1_profile.step_filter
        # A new sample: a changed value, or the same value after a full meter interval
        # (the load can really be constant). Repeats in between add nothing.
        if changed or self._p1_interval is None or self._p1_sample_at is None or now - self._p1_sample_at >= self._p1_interval:
            self._p1_seq += 1
            self._p1_sample_at = now
            self.grid_filter.update(now, value)
        self._p1_value = value
        self._p1_measured = measured
        self._p1_at = now

    # --- the step ---------------------------------------------------------

    def step(
        self,
        now: float,
        sets: Sequence[SetView],
        *,
        discharge_blocked: bool = False,
        price_block: Reason | None = None,
        reserve_charge: tuple[int, float] | None = None,
        plan_action: PlanAction | None = None,
        excluded_load: float = 0.0,
        export_blocked: bool | None = None,
    ) -> StepResult:
        """One control step.

        ``price_block``: delivering is not allowed now because of the prices (PLAN-M4b §2.6), with
        the reason to show. ``reserve_charge``: (power W, reserve %) to charge from the grid now.
        Both only apply to zero-meter control. ``plan_action``: the planner's action for now
        (mode Dynamic Forecasting; None = no plan, zero on the meter). ``excluded_load``: power (W)
        of a load the battery may not feed (B41, the air conditioner while heating); zero-meter
        control does not deliver for it. ``export_blocked``: block (True) or allow (False) the
        export of the sets' surplus solar (``gridReverse``) at a negative export price; None =
        ZEPHYR does not manage it.
        """
        s = self.settings
        self._export_blocked = export_blocked
        self._price_block = price_block if self.mode is Mode.ZERO_METER else None
        self._reserve_charge = reserve_charge if self.mode is Mode.ZERO_METER else None
        self._plan = plan_action if self.mode is Mode.FORECAST else None
        self._excluded_load = max(0.0, excluded_load)
        self._excluded_now = 0.0
        if self._plan is PlanAction.HOLD:
            self._price_block = Reason(ReasonCode.PLAN_HOLD)
        if self._twins is not None:
            sets = self._twin_views(now, sets)
        for view in sets:
            state = self._sets.setdefault(view.key, _SetState())
            self._update_flags(state, view)
            if view.report is not None and view.online:
                day = self.day_of(now)
                state.counters.observe_ac_status(view.report.ac_status, now, day)
                pack_state = view.report.pack_state
                state.counters.observe_pack_state(None if pack_state is None else int(pack_state), now, day)
        usable = [v for v in sorted(sets, key=lambda v: v.number) if self._usable(v)]
        primary = usable[0] if usable else None

        blocked = self._blocked(now, discharge_blocked or self._price_block is not None)
        if self._started is None:
            self._started = now
        # Before the first P1 report, count from the start: no standby command right after a restart.
        waiting_for_p1 = self.mode in ZERO_METER_MODES and self._p1_at is None and now - self._started <= s.p1_lost_after
        p1_age = None if self._p1_at is None else now - self._p1_at
        meter = self._p1_interval or 0.0
        # Until the meter's interval is known, only a lost P1 counts (no 0 W after 10 s at start-up).
        stale_after = max(s.p1_stale_after, 3 * meter) if self._p1_interval is not None else s.p1_lost_after
        # Many P1 sensors only report a change. A grid that is exactly balanced (often 0 W
        # when import and export are both 0.000 kW) then stays silent. That is not a stale
        # meter: hold the setpoint a little longer (p1_balanced_silence).
        if self._p1_measured is not None and abs(self._p1_measured) <= s.deadband:
            stale_after = max(stale_after, s.p1_balanced_silence)
        lost_after = max(s.p1_lost_after, 6 * meter)
        p1_ok = p1_age is not None and p1_age <= stale_after
        total = 0
        finished = False
        all_standby = False
        reason: Reason

        if self.mode is Mode.STANDBY:
            all_standby = True
            reason = Reason(ReasonCode.STANDBY_MODE)
            self.controller.reset(now)
        elif primary is None or primary.report is None:
            reason = self._no_set_reason(sets)
            self.controller.reset(now)
        elif self.mode in (Mode.FAST_CHARGE, Mode.FAST_DISCHARGE):
            total, reason, finished = self._fast(primary, blocked)
            self.controller.reset(now)
        elif waiting_for_p1:
            reason = Reason(ReasonCode.P1_MISSING)
            self.controller.reset(now)
        elif p1_age is None:
            all_standby = True
            reason = Reason(ReasonCode.P1_MISSING)
            self.controller.reset(now)
        elif p1_age > lost_after:
            all_standby = True
            reason = Reason(ReasonCode.P1_LOST, {"age": round(p1_age)})
            self.controller.reset(now)
        elif not p1_ok:
            reason = Reason(ReasonCode.P1_STALE, {"age": round(p1_age)})
            self.controller.reset(now)
            if not self._stale:
                self._stale_events.append(now)
            self._stale = True
        elif self._p1_interval is not None and self._p1_interval > s.too_slow_p1_interval:
            reason = Reason(ReasonCode.P1_TOO_SLOW, {"interval": round(self._p1_interval)})
            self.controller.reset(now)
        elif self.mode is Mode.FORECAST:
            total, reason = self._forecast(now, primary, usable, blocked)
        else:
            total, reason = self._zero_meter(now, primary, usable, blocked)
        if reason.code is not ReasonCode.P1_STALE:
            self._stale = False
        if self.mode is not Mode.FORECAST or total <= 0 or reason.code is not ReasonCode.PLAN_CHARGE:
            self._stop_grid_charge(now)
        if self.mode is not Mode.FORECAST or reason.code is not ReasonCode.PLAN_EXPORT:
            self._exporting = False

        targets = {v.key: 0 for v in sets}
        if primary is not None and total:
            targets[primary.key] = total
        if self.controller.followed_battery and primary is not None:
            # Shadow mode: the set already runs at this power, so nothing would be written.
            self._sets.setdefault(primary.key, _SetState()).last_power = targets[primary.key]
            self.controller.followed_battery = False
        # While waiting for the first P1 report, leave the sets as they are.
        commands = [] if waiting_for_p1 else self._commands(now, sets, targets, all_standby)
        if self._twins is not None:
            for cmd in commands:
                if cmd.key in self._twins:
                    self._twins[cmd.key].apply(now, cmd.props)
        action = Action.HOLD if waiting_for_p1 else self._action(total, reason)
        return StepResult(
            mode=self.mode,
            action=action,
            reason=reason,
            setpoint=total,
            targets=targets,
            commands=tuple(commands),
            grid_power=self._p1_value,
            p1_ok=p1_ok,
            p1_interval=None if self._p1_interval is None else round(self._p1_interval, 1),
            mode_finished=finished,
            battery_power=sum(v.report.battery_power_ac for v in sets if v.report is not None and v.online),
            measured_grid_power=self._p1_measured,
        )

    def _twin_views(self, now: float, sets: Sequence[SetView]) -> list[SetView]:
        """The real sets with their battery swapped for the twin; remembers the real power."""
        assert self._twins is not None
        self._real_battery = sum(v.report.battery_power_ac for v in sets if v.report is not None and v.online)
        self._battery_history.append((now, self._real_battery))
        while self._battery_history and now - self._battery_history[0][0] > BATTERY_HISTORY_FOR:
            self._battery_history.popleft()
        out: list[SetView] = []
        for v in sets:
            if v.report is None or not v.online:
                out.append(v)
                continue
            twin = self._twins.setdefault(v.key, TwinSet(self.settings))
            twin.settings = self.settings
            out.append(replace(v, report=twin.view(v.report, now)))
        return out

    def twin_summary(self) -> dict[str, float] | None:
        """Grid import/export since the start: measured (current system) and virtual (ZEPHYR)."""
        if self._twins is None:
            return None
        return {
            "import_wh_measured": round(self.tally_measured.import_wh, 1),
            "export_wh_measured": round(self.tally_measured.export_wh, 1),
            "import_wh_zephyr": round(self.tally_virtual.import_wh, 1),
            "export_wh_zephyr": round(self.tally_virtual.export_wh, 1),
            "battery_w_real": round(self._real_battery or 0.0),
            "battery_w_twin": round(sum(t.power for t in self._twins.values())),
        }

    # --- parts --------------------------------------------------------------

    def _usable(self, v: SetView) -> bool:
        r = v.report
        return v.online and v.enabled and r is not None and not r.fault and not r.calibrating and not r.bypass

    def _no_set_reason(self, sets: Sequence[SetView]) -> Reason:
        if any(v.online and v.report is not None and v.report.calibrating for v in sets):
            return Reason(ReasonCode.CALIBRATING)
        return Reason(ReasonCode.NO_SET)

    def _update_flags(self, state: _SetState, view: SetView) -> None:
        r = view.report
        if r is None or not view.online:
            return
        s = self.settings
        if r.soc >= s.max_soc - 0.5 or r.soc_limit_charge_stopped:
            state.full = True
        elif r.soc <= s.max_soc - 2:
            state.full = False
        if r.soc <= s.min_soc + 0.5 or r.soc_limit_discharge_stopped:
            state.empty = True
        elif r.soc >= s.min_soc + 2:
            state.empty = False

    def _blocked(self, now: float, requested: bool) -> bool:
        if not requested:
            self._block_since = None
            return False
        if self._block_since is None:
            self._block_since = now
        return now - self._block_since >= self.settings.discharge_block_delay

    def _limits(self, view: SetView, blocked: bool) -> tuple[float, float, Reason | None]:
        """Max charge and deliver power for this set now, and why one is 0."""
        s = self.settings
        r = view.report
        assert r is not None
        state = self._sets[view.key]
        charge = float(min(x for x in (s.max_charge_power, r.charge_max_limit, 2400) if x is not None))
        deliver = float(min(x for x in (s.max_deliver_power, r.inverse_max_power, 2400) if x is not None))
        why: Reason | None = None
        temp = r.max_pack_temperature
        if not charging_allowed_by_temperature(r.product, temp):
            charge = 0.0
            why = Reason(ReasonCode.TEMPERATURE, {"temp": temp})
        if not delivering_allowed_by_temperature(r.product, temp):
            deliver = 0.0
            why = Reason(ReasonCode.TEMPERATURE, {"temp": temp})
        if state.full:
            charge = 0.0
        if state.empty:
            deliver = 0.0
        if blocked:
            deliver = 0.0
        return charge, deliver, why

    def _fast(self, view: SetView, blocked: bool) -> tuple[int, Reason, bool]:
        s = self.settings
        r = view.report
        assert r is not None
        charge, deliver, why = self._limits(view, blocked)
        if self.mode is Mode.FAST_CHARGE:
            if self._sets[view.key].full:
                return 0, Reason(ReasonCode.FULL, {"soc": round(r.soc)}), True
            if charge <= 0 and why is not None:
                return 0, why, False
            return int(charge) // 10 * 10, Reason(ReasonCode.FAST_CHARGE, {"soc": round(s.max_soc)}), False
        if self._sets[view.key].empty:
            return 0, Reason(ReasonCode.EMPTY, {"soc": round(r.soc)}), True
        if deliver <= 0:
            return 0, why or Reason(ReasonCode.BLOCKED), False
        return -(int(deliver) // 10 * 10), Reason(ReasonCode.FAST_DISCHARGE, {"soc": round(s.min_soc)}), False

    def _stop_grid_charge(self, now: float) -> None:
        if self._grid_charging:
            self._grid_charging = False
            self._grid_charge_stopped = now

    def _forecast(self, now: float, primary: SetView, usable: Sequence[SetView], blocked: bool) -> tuple[int, Reason]:
        """Carry out the planner's action for now (SPEC-planner §7).

        L: charge from the grid at full power; starts only after 2 minutes without grid charging,
        stops at max_SOC (then as H) or 10 s after the plan stopped saying L. H: zero on the meter
        without delivering (charging from solar surplus stays). N: zero on the meter. X: deliver at
        full power, only after 2 minutes without grid charging and above min_SOC.
        """
        r = primary.report
        assert r is not None
        plan = self._plan
        if plan is PlanAction.CHARGE:
            self._plan_l_seen = now
        elif self._grid_charging and now - self._plan_l_seen < PLAN_CHARGE_GRACE:
            plan = PlanAction.CHARGE
        else:
            self._stop_grid_charge(now)
        state = self._sets[primary.key]
        charge, deliver, _ = self._limits(primary, blocked)
        if plan is PlanAction.CHARGE:
            if state.full or charge <= 0:
                self._price_block = Reason(ReasonCode.PLAN_HOLD)  # full: as H
                return self._zero_meter(now, primary, usable, True)
            if not self._grid_charging and now - self._grid_charge_stopped < PLAN_RESTART_PAUSE:
                self._price_block = Reason(ReasonCode.PLAN_CHARGE_WAIT)
                return self._zero_meter(now, primary, usable, True)
            self._grid_charging = True
            self.controller.reset(now)
            power = int(charge) // 10 * 10
            return power, Reason(ReasonCode.PLAN_CHARGE, {"power": power})
        if plan is PlanAction.EXPORT:
            ready = self._exporting or now - self._grid_charge_stopped >= PLAN_RESTART_PAUSE
            if ready and deliver > 0 and not state.empty:
                self._exporting = True
                self.controller.reset(now)
                power = int(deliver) // 10 * 10
                return -power, Reason(ReasonCode.PLAN_EXPORT, {"power": power})
        if plan is PlanAction.HOLD:
            return self._zero_meter(now, primary, usable, True)
        return self._zero_meter(now, primary, usable, blocked)

    def _zero_meter(self, now: float, primary: SetView, usable: Sequence[SetView], blocked: bool) -> tuple[int, Reason]:
        s = self.settings
        r = primary.report
        assert r is not None and self._p1_value is not None
        charge, deliver, why = self._limits(primary, blocked)

        # Below the minimum (self-consumption in standby): recharge gently, up to the minimum.
        if r.soc < s.min_soc and charge > 0:
            power = min(s.recharge_below_min_power, int(charge)) // 10 * 10
            self.controller.reset(now)
            return power, Reason(ReasonCode.RECHARGE_MIN, {"power": power})

        # Reserve (soft): charge from the grid in a cheap hour, up to the reserve (PLAN-M4b §2.6).
        if self._reserve_charge is not None and charge > 0 and r.soc < self._reserve_charge[1]:
            power = min(self._reserve_charge[0], int(charge)) // 10 * 10
            self.controller.reset(now)
            return power, Reason(ReasonCode.RESERVE_CHARGE, {"power": power, "reserve": round(self._reserve_charge[1])})

        battery = sum(v.report.battery_power_ac for v in usable if v.report is not None)
        grid = self._controller_grid(now, battery)
        # B41: the part of the excluded load the battery would deliver for stays on the grid.
        excluded = exclusion_for_controller(self._excluded_load, grid, battery)
        self._excluded_now = excluded
        out = self.controller.step(
            ControllerInput(
                now=now,
                grid_power=grid - excluded,
                battery_power=battery,
                max_charge=charge,
                max_deliver=deliver,
                p1_interval=self._p1_interval or 1.0,
                sample=self._p1_seq,
            )
        )
        sp = out.setpoint
        if sp < 0:
            params: dict[str, Any] = {"power": -sp, "grid": round(self._p1_value)}
            if excluded > 0:
                params["excluded"] = round(excluded)
            return sp, Reason(ReasonCode.DELIVERING, params)
        if sp > 0:
            return sp, Reason(ReasonCode.CHARGING_SOLAR, {"power": sp})
        if out.waiting_for_direction:
            return 0, Reason(ReasonCode.SWITCHING)
        if out.demand < 0 and deliver <= 0:
            if blocked:
                return 0, self._price_block or Reason(ReasonCode.BLOCKED)
            if self._sets[primary.key].empty:
                return 0, Reason(ReasonCode.EMPTY, {"soc": round(r.soc)})
            return 0, why or Reason(ReasonCode.BLOCKED)
        if out.demand > 0 and charge <= 0:
            if self._sets[primary.key].full:
                return 0, Reason(ReasonCode.FULL, {"soc": round(r.soc)})
            if why is not None:
                return 0, why
        return 0, Reason(ReasonCode.IDLE_SMALL, {"power": round(abs(out.demand))})

    def _commands(self, now: float, sets: Sequence[SetView], targets: dict[str, int], all_standby: bool) -> list[Command]:
        s = self.settings
        commands: list[Command] = []
        for view in sets:
            state = self._sets.setdefault(view.key, _SetState())
            r = view.report
            if r is None or not view.online:
                continue
            if r.calibrating or r.bypass:
                # The set calibrates itself or passes solar straight to the house: write nothing,
                # no 0 W and no standby (SPEC-basis §8). The idle timer starts again afterwards.
                state.zero_since = None
                continue
            # First time we see the set (or settings changed): its SOC limits must match ours.
            flash_ok = (
                state.counters.flash_count(now, 3600) < s.flash_limit_hour and state.counters.flash_count(now, 86400) < s.flash_limit_day
            )
            state.flash_paused = not flash_ok
            if not state.limits_checked and flash_ok:
                state.limits_checked = True
                cause = (self.limits_cause or "soc_limits") if state.seen else "startup"
                state.seen = True
                if r.min_soc != s.min_soc or r.max_soc != s.max_soc:
                    commands.append(Command(view.key, soc_limits_command(s.min_soc, s.max_soc), "soc_limits", cause))
                    self._record(state, cause, now)
            target = targets.get(view.key, 0)
            offgrid = r.offgrid_power > 0
            if target == 0:
                state.zero_since = state.zero_since if state.zero_since is not None else now
            else:
                state.zero_since = None
            go_standby = (all_standby or (state.zero_since is not None and now - state.zero_since >= s.standby_after)) and not offgrid
            if go_standby and not flash_ok:
                # Flash safety net (PLAN-M4b §2.7): 0 W in RAM instead of standby in flash.
                go_standby = False
                target = 0
            if go_standby:
                if not state.standby:
                    commands.append(Command(view.key, standby_command(), "standby"))
                    self._record(state, "standby", now)
                    state.standby = True
                    state.last_power = 0
                    state.last_sent_at = now
                continue
            if not self._should_send(state, target, now):
                continue
            if target == state.last_power and _report_matches(r, target):
                # Refresh due, but the set already reports exactly this command: nothing to send.
                state.last_sent_at = now
                state.counters.record("skipped", now, self.day_of(now))
                continue
            direction = AcMode.CHARGE if target > 0 else AcMode.DELIVER if target < 0 else None
            include_ac = direction is not None and (direction is not state.last_ac_mode or state.standby or r.ac_mode is not direction)
            commands.append(
                Command(
                    view.key,
                    power_command(target, include_ac_mode=include_ac, charge_max=r.charge_max_limit, deliver_max=r.inverse_max_power),
                    "power",
                )
            )
            self._record(state, "power", now)
            if include_ac and direction is not None and r.ac_mode is not None and r.ac_mode is not direction:
                state.counters.record("relay_commanded", now, self.day_of(now))
            if direction is not None:
                state.last_ac_mode = direction
            state.last_power = target
            state.last_sent_at = now
            state.standby = False
        self._grid_reverse(now, sets, commands)
        return commands

    def _count_peak(self, now: float, held_w: float) -> None:
        """Integrate the part of the grid power the controller does not see (a held peak)."""
        if self._peak_at is not None:
            t, w = self._peak_at
            dt = now - t
            if 0 < dt <= self.settings.step_hold + 5 and w > 0:
                self.peak_kwh += w / 1000 * dt / 3600
        self._peak_at = (now, max(held_w, 0.0))

    def _grid_reverse(self, now: float, sets: Sequence[SetView], commands: list[Command]) -> None:
        """Keep ``gridReverse`` of every set as wanted; rides along with a command of this step."""
        if self._export_blocked is None:
            return
        wanted = GridReverse.BLOCKED if self._export_blocked else GridReverse.ALLOWED
        for view in sets:
            r = view.report
            state = self._sets.get(view.key)
            if r is None or not view.online or state is None or state.flash_paused or r.calibrating or r.bypass:
                continue
            if r.grid_reverse is None or r.grid_reverse is wanted:
                continue
            sent = state.grid_reverse_sent
            if sent is not None and sent[0] is wanted and now - sent[1] < 60:
                continue  # sent, the set has not reported it yet
            props = grid_reverse_command(wanted is GridReverse.ALLOWED)
            for index, command in enumerate(commands):
                if command.key == view.key:
                    commands[index] = replace(command, props={**command.props, **props})
                    break
            else:
                commands.append(Command(view.key, props, "grid_reverse"))
            state.grid_reverse_sent = (wanted, now)
            self._record(state, "grid_reverse", now)

    def _should_send(self, state: _SetState, target: int, now: float) -> bool:
        """Write rules (SPEC-meerdere-sets §2.3)."""
        last = state.last_power
        if last is None:
            return True
        since = now - state.last_sent_at
        if target == last:
            return since >= 60 and not state.standby  # refresh
        if target == 0 or last == 0 or (target > 0) != (last > 0):
            return target == 0 or since >= 2
        if since < 2:
            return False
        # A small change is meter noise more often than a real one (seen in shadow mode:
        # -180, -170, -180, -190 W within 10 s). It waits for the refresh.
        return abs(target - last) >= self.settings.min_command_step or since >= 60

    def _controller_grid(self, now: float, battery: float = 0.0) -> float:
        """P1 for the controller: filtered (short peaks held back, small noise smoothed).

        The step filter only applies while delivering or idle. While the battery charges,
        a rise (a load switching on, or a cloud over the panels) must lower the charging at
        once; holding it would charge the battery from the grid for up to ``step_hold``
        seconds (seen live: +2.2 kW import while the charge setpoint went up).

        The same holds just after the charging stopped: the rise then comes partly from ZEPHYR
        itself (the set no longer takes the surplus). Holding it made the controller see "idle"
        and restart ``switch_delay`` (simulation: delivering after 21 s instead of 10 s). A short
        peak is still not delivered for, because swapping direction waits ``switch_delay``.
        """
        filtered = self.grid_filter.value(now)
        assert self._p1_value is not None
        charging_side = battery > 0 or self.controller.charging_side
        value = self._p1_value if filtered is None or (charging_side and self.grid_filter.holding) else filtered
        self._count_peak(now, self._p1_value - value)
        if not self._align_p1:
            return value
        # Live: the grid as it was when the set's report was made (see ``set_live``).
        self._grid_history.append((now, value))
        at = now - self.settings.twin_delay
        aligned = self._grid_history[0][1]
        for t, v in self._grid_history:
            if t <= at:
                aligned = v
            else:
                break
        return aligned

    @property
    def p1_now(self) -> float | None:
        """Latest grid power as measured by the P1 (W, + import): unfiltered, without the twin."""
        return self._p1_measured

    @property
    def excluded_now(self) -> float:
        """W of the excluded load (B41) the battery did not deliver for in the last step."""
        return self._excluded_now

    def _record(self, state: _SetState, kind: str, now: float) -> None:
        if self.count_commands:
            state.counters.record(kind, now, self.day_of(now))

    def p1_profile_view(self, now: float) -> dict[str, Any]:
        """The P1 profile and the times that follow from the meter interval (diagnostics)."""
        s = self.settings
        meter = self._p1_interval or 0.0
        while self._stale_events and now - self._stale_events[0] > 86_400:
            self._stale_events.popleft()
        profile = self.p1_profile
        return {
            "interval_s": None if self._p1_interval is None else round(self._p1_interval, 2),
            "samples": len(self._p1_gaps),
            "profile": profile.profile if profile.decided else None,
            "since_s": None if profile.changed_at is None else round(now - profile.changed_at),
            "step_filter": profile.step_filter,
            "stale_after_s": round(max(s.p1_stale_after, 3 * meter), 1) if self._p1_interval is not None else s.p1_lost_after,
            "lost_after_s": round(max(s.p1_lost_after, 6 * meter), 1),
            "deviation_time_s": round(max(s.deviation_time, 2 * meter), 1),
            "slow_control": meter > s.slow_p1_interval,
            "stale_24h": len(self._stale_events),
        }

    def counters_record(self, key: str, kind: str, now: float) -> None:
        """Count a write made outside the engine (live writes, the write test)."""
        self._sets.setdefault(key, _SetState()).counters.record(kind, now, self.day_of(now))

    def counters_export(self, now: float, wall: float) -> dict[str, Any]:
        """The counters of every set, to keep over a restart (wall-clock seconds)."""
        return {key: state.counters.as_dict(now, wall) for key, state in self._sets.items()}

    def counters_restore(self, data: Mapping[str, Any] | None, now: float, wall: float) -> None:
        for key, stored in (data or {}).items():
            if isinstance(stored, Mapping):
                self._sets.setdefault(key, _SetState()).counters.restore(stored, now, wall)

    def counters(self, now: float) -> dict[str, dict[str, int]]:
        """Writes and relay switches per set over the last hour and 24 hours (B33)."""
        return {key: state.counters.snapshot(now) | {"flash_paused": int(state.flash_paused)} for key, state in self._sets.items()}

    @staticmethod
    def _action(total: int, reason: Reason) -> Action:
        if total > 0:
            return Action.CHARGE
        if total < 0:
            return Action.DELIVER
        if reason.code in (ReasonCode.STANDBY_MODE, ReasonCode.P1_LOST, ReasonCode.P1_MISSING):
            return Action.STANDBY
        if reason.code is ReasonCode.CALIBRATING:
            return Action.CALIBRATION
        if reason.code in (ReasonCode.BLOCKED, ReasonCode.TEMPERATURE, ReasonCode.NO_SET, ReasonCode.P1_STALE, ReasonCode.P1_TOO_SLOW):
            return Action.BLOCKED
        return Action.HOLD


REFRESH_TOLERANCE = 10
"""W: a reported limit this close to the command counts as the same. ZEPHYR rounds to 10 W;
another system (shadow mode) writes exact values such as 296 W, which otherwise caused a
refresh every minute (seen at a tester: ~60 of 68 writes per hour)."""


def _report_matches(report: SetReport, target: int) -> bool:
    """True when the set reports the power command ZEPHYR would refresh (within 10 W)."""
    if report.smart_mode != 1:
        return False
    if target > 0:
        sent = min(target, report.charge_max_limit) if report.charge_max_limit else target
        return report.ac_mode is AcMode.CHARGE and abs(report.input_limit - sent) < REFRESH_TOLERANCE and report.output_limit == 0
    if target < 0:
        sent = min(-target, report.inverse_max_power) if report.inverse_max_power else -target
        return report.ac_mode is AcMode.DELIVER and abs(report.output_limit - sent) < REFRESH_TOLERANCE and report.input_limit == 0
    return report.input_limit == 0 and report.output_limit == 0
