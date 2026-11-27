// Screen "Diagnose" and the controls (SPEC-ui §4.1, §4.2 point 4, §4.5; UI-8). Pure helpers.
import { t, type Lang } from "./i18n";
import type { Localized } from "./types";

export interface DiagEvent {
  time: string;
  kind:
    | "reason"
    | "mode"
    | "live"
    | "shadow"
    | "test"
    | "test_end"
    | "second_controller"
    | "excluded_on"
    | "excluded_off"
    | "flash";
  code?: string;
  text?: Localized | null;
  setpoint?: number | null;
  mode?: string;
  power?: number;
  cause?: string;
  set?: number;
}

export interface DiagSet {
  number: number;
  ram_24h: number;
  flash_24h: number;
  relay_24h: number | null;
  failed_24h: number;
  last_error: string | null;
}

export interface ProfileDay {
  /** kWh per hour of the day (0–23), house without the air conditioner. */
  house: number[];
  /** kWh per hour of the air conditioner outside the battery (B41); empty without the counter. */
  airco: number[];
  /** Hours measured per hour of the day. */
  counts: number[];
  /** Measurements before an hour counts (workday 3, weekend 2); until then the planner uses the mean. */
  min_count: number;
}

export interface ProfileView {
  source: string;
  hours: number;
  /** kWh per hour the planner uses for an hour that is not learned yet. */
  mean: number;
  workday: ProfileDay;
  weekend: ProfileDay;
}

export interface EnergyGap {
  start: string;
  end: string;
  seconds: number;
  method: "none" | "interpolate" | "soc" | string;
  restart: boolean;
  kwh: Record<string, number>;
  pack_delta_kwh: number | null;
}

export interface EnergySet {
  set?: number | null;
  kwh: Record<string, number>;
  estimated: Record<string, number>;
  failed_reads: number;
  open_gap: { start: string; restart: boolean; pack_kwh: number | null } | null;
  gaps: EnergyGap[];
}

/** ZEPHYR's own energy counters per set (SPEC-tellers). */
export interface EnergyView {
  totals: Record<string, number>;
  sets: EnergySet[];
}

/** The counters shown per set, in the table's order. */
export const ENERGY_KEYS = ["charged", "discharged", "solar"] as const;

/** Estimated (gap-filled) kWh of the shown counters, and its share of their total. */
export function estimatedShare(s: EnergySet): {
  kwh: number;
  share: number | null;
} {
  let est = 0;
  let all = 0;
  for (const k of ENERGY_KEYS) {
    est += s.estimated[k] ?? 0;
    all += s.kwh[k] ?? 0;
  }
  return { kwh: est, share: all > 0 ? est / all : null };
}

/** Gaps of all sets, newest first, with the set number. */
export function allGaps(
  view: EnergyView,
): (EnergyGap & { set: number | null })[] {
  return view.sets
    .flatMap((s, i) => s.gaps.map((g) => ({ ...g, set: s.set ?? i + 1 })))
    .sort((a, b) => b.end.localeCompare(a.end));
}

export interface EventsView {
  entry_id: string;
  energy?: EnergyView | null;
  profile?: ProfileView | null;
  shadow: boolean;
  events: DiagEvent[];
  sets: DiagSet[];
}

/** One sentence per event, in the panel's language. */
export function eventText(e: DiagEvent, lang: Lang, locale: string): string {
  const kw = (w: number) =>
    new Intl.NumberFormat(locale, {
      minimumFractionDigits: 1,
      maximumFractionDigits: 1,
    }).format(w / 1000);
  switch (e.kind) {
    case "reason":
      return (
        e.text?.[lang] ??
        t(lang, "diag.event.reason_code", { code: e.code ?? "?" })
      );
    case "mode":
      return t(lang, "diag.event.mode", {
        mode: t(lang, `mode.${e.mode ?? ""}`),
      });
    case "test":
      return t(lang, "diag.event.test", {
        power: new Intl.NumberFormat(locale).format(e.power ?? 0),
      });
    case "excluded_on":
      return t(lang, "diag.event.excluded_on", { kw: kw(e.power ?? 0) });
    case "flash":
      return t(lang, "diag.event.flash", {
        set: e.set ?? "?",
        cause: t(lang, `diag.cause.${e.cause ?? ""}`),
      });
    default:
      return t(lang, `diag.event.${e.kind}`);
  }
}

/** Kind label for the list (a word, not only a colour). */
export function eventKind(
  e: DiagEvent,
): "control" | "mode" | "live" | "airco" | "write" | "warning" {
  if (e.kind === "mode") return "mode";
  if (
    e.kind === "live" ||
    e.kind === "shadow" ||
    e.kind === "test" ||
    e.kind === "test_end"
  )
    return "live";
  if (e.kind === "excluded_on" || e.kind === "excluded_off") return "airco";
  if (e.kind === "flash") return "write";
  if (e.kind === "second_controller") return "warning";
  return "control";
}

export interface FastButton {
  mode: "fast_charge" | "fast_discharge";
  /** This fast mode runs now: the button stops it. */
  active: boolean;
  /** Mode to switch to on a tap. */
  target: string;
}

/**
 * Snel laden and Snel ontladen, always in the same place (a second tap must not hit another button):
 * the running one stops and goes back to the mode it came from.
 */
export function fastButtons(
  mode: string,
  modes: string[],
  previous: string,
): FastButton[] {
  const back =
    previous === "fast_charge" || previous === "fast_discharge"
      ? "zero_meter"
      : previous;
  return (["fast_charge", "fast_discharge"] as const)
    .filter((m) => modes.includes(m))
    .map((m) => ({
      mode: m,
      active: mode === m,
      target: mode === m ? back : m,
    }));
}

const BLOCKERS: [RegExp, string][] = [
  [/^no P1 sensor chosen$/, "no_p1"],
  [/^P1 is not reporting$/, "p1_silent"],
  [/^no sets$/, "no_sets"],
  [/^set (\d+) is offline$/, "offline"],
  [/^set (\d+) reports a different serial number$/, "serial"],
  [/^set (\d+) reports an error$/, "fault"],
  [/^a write test is running$/, "test"],
];

/** Why live control cannot start, in the panel's language (the backend gives English sentences). */
export function blockerText(blocker: string, lang: Lang): string {
  for (const [re, key] of BLOCKERS) {
    const m = re.exec(blocker);
    if (m) return t(lang, `control.blocker.${key}`, { set: m[1] ?? "" });
  }
  return blocker;
}

/** Day total and top of the hour scale (rounded up to 0,5 kWh) of a profile day. */
export function profileStats(d: ProfileDay): {
  total: number;
  aircoTotal: number;
  top: number;
  learned: number;
} {
  const total = d.house.reduce((a, b) => a + b, 0);
  const aircoTotal = d.airco.reduce((a, b) => a + b, 0);
  const peak = Math.max(0, ...d.house.map((h, i) => h + (d.airco[i] ?? 0)));
  return {
    total,
    aircoTotal,
    top: Math.max(0.5, Math.ceil(peak * 2) / 2),
    learned: d.counts.filter((c) => c >= d.min_count).length,
  };
}

export type CheckMetric = "load" | "solar" | "import" | "export" | "cost";

export interface CheckPair {
  expected: number;
  actual: number;
  diff: number;
  mean_abs_day?: number;
}

export interface CheckDay extends Partial<Record<CheckMetric, CheckPair>> {
  date: string;
  /** Quarters with an expectation, out of the day's quarters. */
  quarters: number;
  of: number;
  soc_end?: { expected: number; actual: number | null };
}

export interface PlanCheckView {
  days: CheckDay[];
  summary: Partial<Record<CheckMetric, CheckPair>> & { days: number };
}

/** Difference as a share of what was expected (null when nothing was expected). */
export function relDiff(p: CheckPair): number | null {
  return Math.abs(p.expected) < 0.05
    ? null
    : (p.actual - p.expected) / Math.abs(p.expected);
}
