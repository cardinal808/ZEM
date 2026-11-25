"""ZephyrEngine: one step = modes → safety → controller → per-set targets → write rules.

Pure and deterministic: time and measurements come in, commands and state
go out. The Home Assistant layer decides whether the commands are sent
(shadow mode: never).

M3 scope: modes Standby, Zero meter, Fast charge and Fast discharge. With
more than one set, the whole setpoint goes to the first available set; the
distributor of SPEC-meerdere-sets follows in M7.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .controller import ControllerInput, ZeroMeterController
from .counters import SetCounters
from .device_table import charging_allowed_by_temperature, delivering_allowed_by_temperature
from .grid_filter import GridFilter
from .models import AcMode, SetReport
from .settings import Settings
from .zensdk import power_command, soc_limits_command, standby_command


class Mode(StrEnum):
    STANDBY = "standby"
    ZERO_METER = "zero_meter"
    FAST_CHARGE = "fast_charge"
    FAST_DISCHARGE = "fast_discharge"


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
    """"power", "standby" or "soc_limits"."""


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
        self._started: float | None = None
        self._p1_changed_at: float | None = None
        self._p1_gaps: deque[float] = deque(maxlen=30)
        self._p1_seq = 0
        self._p1_sample_at: float | None = None

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
        changed = self._p1_value is None or value != self._p1_value
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
        # A new sample: a changed value, or the same value after a full meter interval
        # (the load can really be constant). Repeats in between add nothing.
        if changed or self._p1_interval is None or self._p1_sample_at is None or now - self._p1_sample_at >= self._p1_interval:
            self._p1_seq += 1
            self._p1_sample_at = now
            self.grid_filter.update(now, value)
        self._p1_value = value
        self._p1_at = now

    # --- the step ---------------------------------------------------------

    def step(self, now: float, sets: Sequence[SetView], *, discharge_blocked: bool = False) -> StepResult:
        s = self.settings
        for view in sets:
            state = self._sets.setdefault(view.key, _SetState())
            self._update_flags(state, view)
            if view.report is not None and view.online:
                state.counters.observe_ac_status(view.report.ac_status, now)
        usable = [v for v in sorted(sets, key=lambda v: v.number) if self._usable(v)]
        primary = usable[0] if usable else None

        blocked = self._blocked(now, discharge_blocked)
        if self._started is None:
            self._started = now
        # Before the first P1 report, count from the start: no standby command right after a restart.
        waiting_for_p1 = self.mode is Mode.ZERO_METER and self._p1_at is None and now - self._started <= s.p1_lost_after
        p1_age = None if self._p1_at is None else now - self._p1_at
        meter = self._p1_interval or 0.0
        # Until the meter's interval is known, only a lost P1 counts (no 0 W after 10 s at start-up).
        stale_after = max(s.p1_stale_after, 2.5 * meter) if self._p1_interval is not None else s.p1_lost_after
        # Many P1 sensors only report a change. A grid that is exactly balanced (often 0 W
        # when import and export are both 0.000 kW) then stays silent. That is not a stale
        # meter: hold the setpoint a little longer (p1_balanced_silence).
        if self._p1_value is not None and abs(self._p1_value) <= s.deadband:
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
        elif self._p1_interval is not None and self._p1_interval > s.too_slow_p1_interval:
            reason = Reason(ReasonCode.P1_TOO_SLOW, {"interval": round(self._p1_interval)})
            self.controller.reset(now)
        else:
            total, reason = self._zero_meter(now, primary, usable, blocked)

        targets = {v.key: 0 for v in sets}
        if primary is not None and total:
            targets[primary.key] = total
        if self.controller.followed_battery and primary is not None:
            # Shadow mode: the set already runs at this power, so nothing would be written.
            self._sets.setdefault(primary.key, _SetState()).last_power = targets[primary.key]
            self.controller.followed_battery = False
        # While waiting for the first P1 report, leave the sets as they are.
        commands = [] if waiting_for_p1 else self._commands(now, sets, targets, all_standby)
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
        )

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

    def _zero_meter(self, now: float, primary: SetView, usable: Sequence[SetView], blocked: bool) -> tuple[int, Reason]:
        s = self.settings
        r = primary.report
        assert r is not None and self._p1_value is not None
        charge, deliver, why = self._limits(primary, blocked)

        # Below the minimum (self-consumption in standby): recharge gently.
        if r.soc < s.min_soc - 1 and charge > 0:
            power = min(s.recharge_below_min_power, int(charge)) // 10 * 10
            self.controller.reset(now)
            return power, Reason(ReasonCode.RECHARGE_MIN, {"power": power})

        battery = sum(v.report.battery_power_ac for v in usable if v.report is not None)
        out = self.controller.step(
            ControllerInput(
                now=now,
                grid_power=self._controller_grid(now, battery),
                battery_power=battery,
                max_charge=charge,
                max_deliver=deliver,
                p1_interval=self._p1_interval or 1.0,
                sample=self._p1_seq,
            )
        )
        sp = out.setpoint
        if sp < 0:
            return sp, Reason(ReasonCode.DELIVERING, {"power": -sp, "grid": round(self._p1_value)})
        if sp > 0:
            return sp, Reason(ReasonCode.CHARGING_SOLAR, {"power": sp})
        if out.waiting_for_direction:
            return 0, Reason(ReasonCode.SWITCHING)
        if out.demand < 0 and deliver <= 0:
            if blocked:
                return 0, Reason(ReasonCode.BLOCKED)
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
            # First time we see the set (or settings changed): its SOC limits must match ours.
            if not state.limits_checked:
                state.limits_checked = True
                if r.min_soc != s.min_soc or r.max_soc != s.max_soc:
                    commands.append(Command(view.key, soc_limits_command(s.min_soc, s.max_soc), "soc_limits"))
                    state.counters.record("soc_limits", now)
            target = targets.get(view.key, 0)
            offgrid = r.offgrid_power > 0
            if target == 0:
                state.zero_since = state.zero_since if state.zero_since is not None else now
            else:
                state.zero_since = None
            go_standby = (all_standby or (state.zero_since is not None and now - state.zero_since >= s.standby_after)) and not offgrid
            if go_standby:
                if not state.standby:
                    commands.append(Command(view.key, standby_command(), "standby"))
                    state.counters.record("standby", now)
                    state.standby = True
                    state.last_power = 0
                    state.last_sent_at = now
                continue
            if not self._should_send(state, target, now):
                continue
            if target == state.last_power and _report_matches(r, target):
                # Refresh due, but the set already reports exactly this command: nothing to send.
                state.last_sent_at = now
                state.counters.record("skipped", now)
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
            state.counters.record("power", now)
            if direction is not None:
                state.last_ac_mode = direction
            state.last_power = target
            state.last_sent_at = now
            state.standby = False
        return commands

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
        if filtered is None or (charging_side and self.grid_filter.holding):
            return self._p1_value
        return filtered

    def counters(self, now: float) -> dict[str, dict[str, int]]:
        """Writes and relay switches per set over the last hour and 24 hours (B33)."""
        return {key: state.counters.snapshot(now) for key, state in self._sets.items()}

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
