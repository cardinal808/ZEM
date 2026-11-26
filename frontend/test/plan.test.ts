import { describe, expect, it } from "vitest";

import {
  bands,
  bar,
  currentIndex,
  dayOf,
  days,
  pastSocLines,
  quartersOf,
  scale,
  socPoints,
  stats,
  ticks,
  upcomingBlocks,
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
});
