import { describe, expect, it } from "vitest";

import {
  bands,
  blocksFor,
  bar,
  currentIndex,
  dayOf,
  days,
  pastSocLines,
  quartersOf,
  scale,
  socPoints,
  spreadPct,
  stats,
  sunLane,
  ticks,
  upcomingBlocks,
  type PlanBlock,
  type Period,
  type Quarter,
} from "../src/plan";

const TZ = "Europe/Amsterdam";

function makeDay(startUtc: string, prices: number[], pastUntil = 0, actions: (Quarter["action"])[] = []): Quarter[] {
  const t0 = Date.parse(startUtc);
  return prices.map((p, i) => ({
    start: new Date(t0 + i * 900_000).toISOString(),
    past: i < pastUntil,
    market: p - 0.12,
    buy: p,
    sell: p - 0.12,
    action: actions[i] ?? (i < pastUntil ? null : "hold"),
    soc: i < pastUntil ? null : 50,
    solar: 0,
    load: 0.1,
    indicative: false,
  }));
}

// 26 Nov 2026, local midnight = 23:00 UTC the day before.
const today = makeDay(
  "2026-11-25T23:00:00Z",
  Array.from({ length: 96 }, (_, i) => 0.2 + (i === 12 ? -0.05 : 0) + (i === 72 ? 0.2 : 0)),
  80,
);
const tomorrow = makeDay("2026-11-26T23:00:00Z", Array.from({ length: 96 }, () => 0.3)).map((q) => ({ ...q, indicative: true }));
const all = [...today, ...tomorrow];

describe("plan helpers", () => {
  it("splits the view into local days", () => {
    expect(days(all, TZ)).toEqual(["2026-11-26", "2026-11-27"]);
    expect(quartersOf(all, "today", TZ)).toHaveLength(96);
    expect(quartersOf(all, "tomorrow", TZ)[0].start).toBe("2026-11-26T23:00:00.000Z");
    expect(quartersOf(all, "both", TZ)).toHaveLength(192);
    expect(dayOf(all, 1, TZ)).toHaveLength(96);
  });

  it("finds lowest, highest and mean of known prices only", () => {
    const s = stats(today)!;
    expect(s.min.buy).toBeCloseTo(0.15);
    expect(s.min.start).toBe(today[12].start);
    expect(s.max.buy).toBeCloseTo(0.4);
    expect(s.avg).toBeCloseTo(0.2 + 0.15 / 96);
    expect(stats(tomorrow)).toBeNull(); // indicative only
  });

  it("knows the running quarter", () => {
    expect(currentIndex(today)).toBe(80);
  });

  it("merges equal actions into bands, split at now", () => {
    const b = bands(today);
    expect(b).toEqual([
      { action: null, past: true, from: 0, count: 80 },
      { action: "hold", past: false, from: 80, count: 16 },
    ]);
  });

  it("scales the price axis and draws negative bars below zero", () => {
    expect(scale(today)).toEqual({ lo: 0, hi: 0.4 });
    const neg = scale([{ ...today[0], buy: -0.07 }, today[72]]);
    expect(neg).toEqual({ lo: -0.1, hi: 0.4 });
    expect(bar(-0.05, neg).bottom).toBeCloseTo(10);
    expect(bar(-0.05, neg).height).toBeCloseTo(10);
    expect(bar(0.4, neg).bottom).toBeCloseTo(20);
  });

  it("places ticks on local full hours", () => {
    expect(ticks(today, 3, TZ)).toEqual([0, 12, 24, 36, 48, 60, 72, 84]);
  });

  it("draws the SOC line from now", () => {
    const pts = socPoints(today, 46).split(" ");
    expect(pts[0]).toBe("80,54.0");
    expect(pts[1]).toBe("81,50.0");
    expect(pts).toHaveLength(17);
  });

  it("keeps blocks that have not ended", () => {
    const blocks = [
      { action: "deliver" as const, start: "2026-11-26T18:00:00Z", end: "2026-11-26T20:00:00Z", kwh: 2, price: 0.3, indicative: false },
      { action: "charge" as const, start: "2026-11-26T20:00:00Z", end: "2026-11-26T22:00:00Z", kwh: 4, price: 0.2, indicative: false },
    ];
    expect(upcomingBlocks(blocks, "2026-11-26T19:00:00Z")).toHaveLength(2);
    expect(upcomingBlocks(blocks, "2026-11-26T20:00:00Z")).toHaveLength(1);
  });

  it("draws the measured SOC before now in pieces, broken where HA was off", () => {
    const qs = today.slice(0, 84).map((q, i) => ({ ...q, soc: i < 80 && i !== 40 ? 60 - i * 0.1 : q.soc }));
    const lines = pastSocLines(qs, 52);
    expect(lines).toHaveLength(2);
    expect(lines[0].split(" ")).toHaveLength(40);
    const last = lines[1].split(" ");
    expect(last[last.length - 2]).toBe("80,47.9"); // SOC 52.1 % at the end of the last past quarter
    expect(last[last.length - 1]).toBe("80,48.0");
  });

  it("picks the blocks of the chosen period", () => {
    const tz = "Europe/Amsterdam";
    const b = (start: string, end: string, action: "charge" | "hold" | "deliver" = "hold") =>
      ({ start, end, action, kwh: 0, price: 0.3, indicative: false }) as PlanBlock;
    const blocks = [
      b("2026-11-26T10:00:00Z", "2026-11-26T12:45:00Z", "deliver"), // past
      b("2026-11-26T12:45:00Z", "2026-11-26T20:45:00Z", "deliver"), // now – 21:45
      b("2026-11-26T20:45:00Z", "2026-11-27T02:00:00Z"), // over midnight
      b("2026-11-27T02:00:00Z", "2026-11-27T04:15:00Z", "charge"),
      b("2026-11-27T04:15:00Z", "2026-11-27T23:00:00Z"), // until 00:00 the day after
    ];
    const now = "2026-11-26T13:00:00Z";
    const starts = (p: Period) => blocksFor(blocks, p, now, "2026-11-27", tz).map((x) => x.start.slice(11, 16));
    expect(starts("today")).toEqual(["12:45", "20:45"]);
    expect(starts("tomorrow")).toEqual(["20:45", "02:00", "04:15"]);
    expect(starts("both")).toEqual(["12:45", "20:45", "02:00", "04:15"]);
    expect(blocksFor(blocks, "tomorrow", now, null, tz)).toEqual([]);
  });

  it("draws the solar lane with solar to spare", () => {
    const q = (solar: number | null, load: number | null, excluded: number | null, past = false) =>
      ({ start: "2026-11-26T11:00:00Z", past, market: 0.2, buy: 0.3, sell: 0.2, action: "hold", soc: 50, solar, load, excluded, indicative: false }) as Quarter;
    expect(sunLane([q(null, null, null)])).toBeNull();
    const lane = sunLane([q(0, 0.1, 0, true), q(0.2, 0.1, 0), q(0.4, 0.15, 0.3), q(0.4, 0.1, 0.2)]);
    expect(lane?.map((x) => x.height)).toEqual([0, 50, 100, 100]);
    expect(lane?.map((x) => x.over)).toEqual([false, true, false, true]);
    expect(lane?.[0].past).toBe(true);
  });

  it("gives the spread as a percentage of the lowest price", () => {
    expect(spreadPct(0.21, 0.38)).toBe(81);
    expect(spreadPct(0.2, 0.2)).toBe(0);
    expect(spreadPct(0, 0.3)).toBeNull();
    expect(spreadPct(-0.05, 0.3)).toBeNull();
  });
});

describe("tomorrow on its own", () => {
  const q = (iso: string, soc: number) => ({ start: iso, past: false, market: null, buy: 0.3, sell: 0.2, action: null, soc, solar: null, load: null, indicative: false });
  const tomorrow = [q("2026-11-28T00:00:00Z", 40), q("2026-11-28T00:15:00Z", 39)];
  it("has no 'now' when now is not in view", () => {
    expect(currentIndex(tomorrow, Date.UTC(2026, 10, 27, 17, 0))).toBe(-1);
    expect(currentIndex(tomorrow, Date.UTC(2026, 10, 28, 0, 5))).toBe(0);
  });
  it("starts the SOC line at the first quarter's value, not at the SOC now", () => {
    const pts = socPoints(tomorrow, 43).split(" ");
    expect(pts[0]).toBe("0,60.0");
  });
});
