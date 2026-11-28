import { number } from "./format";

// Pure helpers for the header and the card *Nu* (testable without Lit).

/**
 * Whether the card *Nu* shows the control's reason, and how.
 * Reasons that only repeat the action and the flows are hidden; problems are a warning.
 */
const REPEATS = new Set([
  "delivering",
  "charging_solar",
  "plan_charge",
  "plan_hold",
  "plan_export",
]);
const WARNINGS = new Set([
  "p1_missing",
  "p1_lost",
  "p1_stale",
  "p1_too_slow",
  "no_set",
  "blocked",
  "temperature",
]);

export function nowNote(
  code: string | null | undefined,
): "hide" | "note" | "warn" {
  if (!code || REPEATS.has(code)) return "hide";
  return WARNINGS.has(code) ? "warn" : "note";
}

/** The parts of an HA state that the version button needs. */
export interface UpdateState {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
}

/** The HACS update entity of ZEPHYR, found by its release URL (the entity id may differ). */
export function zephyrUpdate(
  states: Record<string, UpdateState> | undefined,
): UpdateState | null {
  if (!states) return null;
  for (const [id, st] of Object.entries(states)) {
    if (!id.startsWith("update.")) continue;
    const url = String(st.attributes?.release_url ?? "").toLowerCase();
    if (url.includes("github.com/cardinal808/zephyr/")) return st;
  }
  return null;
}

export type VersionState =
  | { kind: "version"; running: string }
  | {
      kind: "update";
      running: string;
      latest: string;
      entity: string;
      url: string | null;
      busy: boolean;
    }
  | { kind: "restart"; running: string; installed: string };

const clean = (v: unknown): string => String(v ?? "").replace(/^v/i, "");

/**
 * What the version spot in the header shows: the running version, an update when HACS
 * has a newer one, or *Herstart nodig* when HACS installed a version that does not run yet.
 */
export function versionState(
  running: string,
  update: UpdateState | null,
): VersionState {
  const run = clean(running);
  if (!update) return { kind: "version", running: run };
  const installed = clean(update.attributes.installed_version);
  const latest = clean(update.attributes.latest_version);
  if (installed && run && installed !== run)
    return { kind: "restart", running: run, installed };
  if (update.state === "on" && latest && latest !== run)
    return {
      kind: "update",
      running: run,
      latest,
      entity: update.entity_id,
      url:
        typeof update.attributes.release_url === "string"
          ? update.attributes.release_url
          : null,
      busy:
        update.attributes.in_progress === true ||
        typeof update.attributes.in_progress === "number",
    };
  return { kind: "version", running: run };
}

/** Within this many watts of zero the meter counts as "at zero" (grey), as in *Nul op de meter*. */
export const P1_ZERO_W = 50;

/**
 * The P1 value on the card *Nu*: always in W (Bjorn 28-11), with sign (+ import, − export).
 */
export function p1Display(
  gridW: number,
  locale: string,
): { text: string; kind: "import" | "export" | "zero" } {
  const w = Math.round(gridW);
  const sign = w > 0 ? "+" : w < 0 ? "\u2212" : "";
  const kind = Math.abs(w) <= P1_ZERO_W ? "zero" : w > 0 ? "import" : "export";
  return { text: `${sign}${number(Math.abs(w), locale, 0)} W`, kind };
}

/** Below this the row counts as nothing flowing (grey). */
export const NOW_ROW_MIN_W = 1;

export type NowSource = "sun" | "batt" | "grid" | "sun_grid" | "sun_batt";

export interface NowRow {
  key: "solar_house" | "battery_house" | "grid_house" | "to_battery" | "to_grid";
  from: NowSource;
  to: "house" | "battery" | "grid";
  w: number;
}

/**
 * The five fixed rows of the card *Nu* (Bjorn 28-11): always the same rows in the same order, at least 0 W,
 * so the card does not jump. Rows 4 and 5 name their source: *Net → accu*, *Zon + net → accu*, *Accu → net*;
 * with nothing flowing the usual source (the sun).
 */
export function nowRows(paths: Record<string, number>): NowRow[] {
  const p = (k: string): number => Math.max(0, Math.round(paths[k] ?? 0));
  const solarBatt = p("solar_battery");
  const gridBatt = p("grid_battery");
  const solarGrid = p("solar_grid");
  const battGrid = p("battery_grid");
  const on = (w: number): boolean => w >= NOW_ROW_MIN_W;
  const toBattery: NowSource = on(solarBatt) && on(gridBatt) ? "sun_grid" : on(gridBatt) ? "grid" : "sun";
  const toGrid: NowSource = on(solarGrid) && on(battGrid) ? "sun_batt" : on(battGrid) ? "batt" : "sun";
  return [
    { key: "solar_house", from: "sun", to: "house", w: p("solar_house") },
    { key: "battery_house", from: "batt", to: "house", w: p("battery_house") },
    { key: "grid_house", from: "grid", to: "house", w: p("grid_house") },
    { key: "to_battery", from: toBattery, to: "battery", w: solarBatt + gridBatt },
    { key: "to_grid", from: toGrid, to: "grid", w: solarGrid + battGrid },
  ];
}
