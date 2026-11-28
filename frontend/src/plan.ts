// Calculations for the chart "Prijzen en plan" (SPEC-ui §4.2). Pure functions, tested with vitest.
import { dateFormat } from "./format";
import type { PlanAction } from "./types";

export interface Quarter {
  start: string;
  past: boolean;
  market: number | null;
  buy: number | null;
  sell: number | null;
  action: PlanAction | null;
  soc: number | null;
  solar: number | null;
  load: number | null;
  /** kWh of the air conditioner outside the battery (B41); absent without the counter. */
  excluded?: number | null;
  /** kWh of planned appliance runs in this quarter (B36). */
  appliances?: number | null;
  /** Solar surplus the planner counts as curtailed at a negative export price (B45). */
  curtail_kwh?: number;
  /** Cost of exporting that surplus when nothing is curtailed (€, B45). */
  export_cost?: number;
  indicative: boolean;
}

export interface PlanBlock {
  action: PlanAction;
  start: string;
  end: string;
  kwh: number;
  price: number;
  indicative: boolean;
}

export interface PlanView {
  now: string;
  state: string | null;
  calculated_at: string | null;
  reason: { nl: string; en: string } | null;
  soc_now: number | null;
  tomorrow_known_at: string | null;
  quarters: Quarter[];
  blocks: PlanBlock[];
  /** curtail_off / curtail_external / curtail_zephyr (B45). */
  curtail_mode?: string | null;
}

export type Period = "today" | "tomorrow" | "both";

export const dayKey = (iso: string, timeZone: string): string =>
  dateFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone,
  }).format(new Date(iso));

/** Local calendar days present in the view, in order (normally today and tomorrow). */
export function days(quarters: Quarter[], timeZone: string): string[] {
  const out: string[] = [];
  for (const q of quarters) {
    const key = dayKey(q.start, timeZone);
    if (out[out.length - 1] !== key) out.push(key);
  }
  return out;
}

export function quartersOf(
  quarters: Quarter[],
  period: Period,
  timeZone: string,
): Quarter[] {
  if (period === "both") return quarters;
  const wanted = days(quarters, timeZone)[period === "today" ? 0 : 1];
  return wanted
    ? quarters.filter((q) => dayKey(q.start, timeZone) === wanted)
    : [];
}

export function dayOf(
  quarters: Quarter[],
  index: number,
  timeZone: string,
): Quarter[] {
  const wanted = days(quarters, timeZone)[index];
  return wanted
    ? quarters.filter((q) => dayKey(q.start, timeZone) === wanted)
    : [];
}

export interface PriceStats {
  min: Quarter;
  max: Quarter;
  avg: number;
}

/** Lowest, highest and mean all-in price of the known (not indicative) quarters; null when none. */
export function stats(quarters: Quarter[]): PriceStats | null {
  const known = quarters.filter((q) => q.buy !== null && !q.indicative);
  if (!known.length) return null;
  let min = known[0];
  let max = known[0];
  let sum = 0;
  for (const q of known) {
    const price = q.buy as number;
    if (price < (min.buy as number)) min = q;
    if (price > (max.buy as number)) max = q;
    sum += price;
  }
  return { min, max, avg: sum / known.length };
}

/** Index of the running quarter (the first one that is not past), or -1. */
export function currentIndex(
  quarters: Quarter[],
  nowMs: number = Date.now(),
): number {
  const i = quarters.findIndex((q) => !q.past);
  if (i !== 0) return i;
  // Without a past quarter in view (the view "tomorrow") the first quarter is only "now" when it is.
  const start = new Date(quarters[0].start).getTime();
  return nowMs >= start && nowMs < start + 15 * 60_000 ? 0 : -1;
}

export interface Band {
  action: PlanAction | null;
  past: boolean;
  from: number;
  count: number;
}

/** Consecutive quarters with the same action (and past/future) as one segment. */
export function bands(quarters: Quarter[]): Band[] {
  const out: Band[] = [];
  quarters.forEach((q, i) => {
    const last = out[out.length - 1];
    if (last && last.action === q.action && last.past === q.past)
      last.count += 1;
    else out.push({ action: q.action, past: q.past, from: i, count: 1 });
  });
  return out;
}

export interface Scale {
  lo: number;
  hi: number;
}

/** Price axis: from 0 (or the lowest negative price) to the highest price, on 5-cent steps. */
export function scale(quarters: Quarter[]): Scale {
  // A negative export price is drawn below zero too (B45).
  const prices = quarters
    .flatMap((q) => [q.buy, q.sell !== null && q.sell < 0 ? q.sell : null])
    .filter((p): p is number => p !== null);
  if (!prices.length) return { lo: 0, hi: 0.4 };
  const lo = Math.min(0, Math.floor(Math.min(...prices) * 20) / 20);
  const hi = Math.max(lo + 0.05, Math.ceil(Math.max(...prices) * 20) / 20);
  return { lo, hi };
}

/** Bottom and height (0–100 %) of a bar from 0 to ``price``; works for negative prices. */
export function bar(
  price: number,
  s: Scale,
): { bottom: number; height: number } {
  const span = s.hi - s.lo;
  const y0 = Math.min(price, 0);
  const y1 = Math.max(price, 0);
  return {
    bottom: ((y0 - s.lo) / span) * 100,
    height: Math.max(((y1 - y0) / span) * 100, 0.8),
  };
}

/** Quarters that start on a full hour divisible by ``everyHours`` (local time): tick positions. */
export function ticks(
  quarters: Quarter[],
  everyHours: number,
  timeZone: string,
): number[] {
  const hour = dateFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone,
  });
  const out: number[] = [];
  quarters.forEach((q, i) => {
    const [h, m] = hour.format(new Date(q.start)).split(":").map(Number);
    if (m === 0 && h % everyHours === 0) out.push(i);
  });
  return out;
}

/** SOC line: points (x = quarter index at the end of the quarter, y = 100 − %) from the running quarter on. */
export function socPoints(quarters: Quarter[], socNow: number | null): string {
  const now = currentIndex(quarters);
  const pts: string[] = [];
  if (now >= 0 && socNow !== null)
    pts.push(`${now},${(100 - socNow).toFixed(1)}`);
  else if (now < 0) {
    // Now is not in view (tomorrow): start the line at the left edge with the first quarter's value.
    const first = quarters.find((q) => !q.past && q.soc !== null);
    if (first && first.soc !== null)
      pts.push(`0,${(100 - first.soc).toFixed(1)}`);
  }
  quarters.forEach((q, i) => {
    if (!q.past && q.soc !== null)
      pts.push(`${i + 1},${(100 - q.soc).toFixed(1)}`);
  });
  return pts.join(" ");
}

/**
 * Measured SOC before now (end of each past quarter), as separate line pieces:
 * a quarter without a value (HA was off) breaks the line. The last piece runs to now.
 */
export function pastSocLines(
  quarters: Quarter[],
  socNow: number | null,
): string[] {
  const now = currentIndex(quarters);
  const lines: string[][] = [];
  let piece: string[] = [];
  quarters.forEach((q, i) => {
    if (!q.past) return;
    if (q.soc === null) {
      if (piece.length) lines.push(piece);
      piece = [];
      return;
    }
    piece.push(`${i + 1},${(100 - q.soc).toFixed(1)}`);
  });
  if (piece.length) {
    if (
      now >= 0 &&
      socNow !== null &&
      piece[piece.length - 1].startsWith(`${now},`)
    )
      piece.push(`${now},${(100 - socNow).toFixed(1)}`);
    lines.push(piece);
  }
  return lines.filter((l) => l.length > 1).map((l) => l.join(" "));
}

/** Future blocks of the plan, the running one first (it may have started before now). */
export function upcomingBlocks(
  blocks: PlanBlock[],
  nowIso: string,
): PlanBlock[] {
  const now = new Date(nowIso).getTime();
  return blocks.filter((b) => new Date(b.end).getTime() > now);
}

/**
 * The blocks the cards *Blokken* and *Waarom dit plan* show for the chosen period:
 * today = still to come today (a block over midnight included), tomorrow = every block that touches tomorrow,
 * 48 uur = everything still to come.
 */
export function blocksFor(
  blocks: PlanBlock[],
  period: Period,
  nowIso: string,
  tomorrowKey: string | null,
  timeZone: string,
): PlanBlock[] {
  const upcoming = upcomingBlocks(blocks, nowIso);
  if (period === "both") return upcoming;
  const wanted = period === "today" ? dayKey(nowIso, timeZone) : tomorrowKey;
  if (!wanted) return [];
  return upcoming.filter((b) => {
    const first = dayKey(b.start, timeZone);
    const last = dayKey(
      new Date(new Date(b.end).getTime() - 1).toISOString(),
      timeZone,
    );
    return first <= wanted && wanted <= last;
  });
}

export interface SunQuarter {
  /** Bar height, % of the lane (the sunniest quarter in view = 100). */
  height: number;
  past: boolean;
  /** More solar than the house and the air conditioner use: solar to spare for the battery. */
  over: boolean;
}

/** The solar lane under the action band; null when no quarter has solar data. */
export function sunLane(quarters: Quarter[]): SunQuarter[] | null {
  if (!quarters.some((q) => q.solar !== null)) return null;
  const top = Math.max(0.05, ...quarters.map((q) => q.solar ?? 0));
  return quarters.map((q) => {
    const solar = q.solar ?? 0;
    const use = (q.load ?? 0) + (q.excluded ?? 0) + (q.appliances ?? 0);
    return {
      height: solar > 0 ? Math.round((solar / top) * 1000) / 10 : 0,
      past: q.past,
      over: solar > 0 && q.load !== null && solar > use,
    };
  });
}

/** Spread: how much the highest price is above the day's mean, in %; null when the mean is not above zero (then % means nothing). */
export function spreadPct(avg: number, high: number): number | null {
  if (avg <= 0.005) return null;
  return Math.round(((high - avg) / avg) * 100);
}

export interface RunInput {
  name: string;
  start: string;
  minutes: number;
  fixed: boolean;
}

export interface RunBar {
  name: string;
  fixed: boolean;
  /** Position in quarters from the first quarter shown (may be fractional). */
  left: number;
  width: number;
  /** Row, so overlapping runs do not hide each other. */
  row: number;
}

/** Planned runs as bars on the chart's time axis; runs outside the shown quarters are left out. */
export function runBars(quarters: Quarter[], runs: RunInput[]): RunBar[] {
  if (!quarters.length) return [];
  const t0 = new Date(quarters[0].start).getTime();
  const n = quarters.length;
  const q = 15 * 60_000;
  const out: RunBar[] = [];
  const rowsEnd: number[] = [];
  for (const r of [...runs].sort((a, b) => a.start.localeCompare(b.start))) {
    const left = (new Date(r.start).getTime() - t0) / q;
    const width = Math.max(0.5, r.minutes / 15);
    if (left + width <= 0 || left >= n) continue;
    const from = Math.max(0, left);
    const to = Math.min(n, left + width);
    let row = rowsEnd.findIndex((end) => end <= from);
    if (row < 0) row = rowsEnd.length;
    rowsEnd[row] = to;
    out.push({
      name: r.name,
      fixed: r.fixed,
      left: from,
      width: to - from,
      row,
    });
  }
  return out;
}

export interface NegativeSummary {
  hours: number;
  cost: number;
  /** "today", "tomorrow" or "both": the days with a negative export price still to come. */
  when: "today" | "tomorrow" | "both";
}

/** Negative export prices still to come, and what exporting the surplus then costs (no curtailing); null when none. */
export function negativeAhead(
  quarters: Quarter[],
  timeZone: string,
): NegativeSummary | null {
  const ahead = quarters.filter(
    (q) => !q.past && q.sell !== null && q.sell < 0,
  );
  if (!ahead.length) return null;
  const first = days(quarters, timeZone)[0];
  const today = ahead.some((q) => dayKey(q.start, timeZone) === first);
  const later = ahead.some((q) => dayKey(q.start, timeZone) !== first);
  return {
    hours: ahead.length / 4,
    cost: ahead.reduce((sum, q) => sum + (q.export_cost ?? 0), 0),
    when: today && later ? "both" : today ? "today" : "tomorrow",
  };
}
