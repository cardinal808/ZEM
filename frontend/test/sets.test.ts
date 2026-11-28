import { describe, expect, it } from "vitest";

import { dayBars, packName, summarize, type BatteryDay, type Pack, type PackDay, type SetInfo } from "../src/sets";

const days = (mvs: (number | null)[]): PackDay[] =>
  mvs.map((mv, i) => ({
    day: `2026-11-${String(20 + i).padStart(2, "0")}`,
    max_mv: mv,
    status: mv === null ? null : mv <= 30 ? "good" : mv <= 100 ? "balancing" : "imbalance",
    full: mv !== null,
  }));

const pack = (index: number, model: string | null, builtIn: boolean, number: number, extra: Partial<Pack> = {}): Pack => ({
  index,
  model,
  built_in: builtIn,
  number,
  capacity_kwh: 2.88,
  soc: 50,
  energy_kwh: 1.44,
  power_w: 0,
  temp: 18,
  cell_min_v: 3.3,
  cell_max_v: 3.32,
  cell_delta_mv: 20,
  cell_judged: false,
  cell_status: null,
  history: days([null, null, null, null, null, null, null]),
  ...extra,
});

const set = (packs: Pack[], online = true): SetInfo => ({
  id: "a",
  number: 1,
  model: "SolarFlow 2400 Pro",
  online,
  status: "standby",
  soc: 50,
  capacity_kwh: 11.04,
  energy_kwh: 5.5,
  power_w: 0,
  solar_w: 0,
  enclosure_temp: 20,
  limits: { min: 10, max: 100 },
  last_full: null,
  relays_24h: 2,
  packs,
});

describe("sets", () => {
  const packs = [pack(0, "Built-in battery (2.4 kWh)", true, 1), pack(1, "AB3000L", false, 1), pack(2, "AB3000L", false, 2), pack(3, null, false, 1)];

  it("names packs", () => {
    expect(packs.map((p) => packName(p, packs, "nl"))).toEqual(["Ingebouwd", "AB3000L 1", "AB3000L 2", "Accu 4"]);
    const single = [pack(0, "AB3000L", false, 1)];
    expect(packName(single[0], single, "en")).toBe("AB3000L");
  });

  it("judges only what the backend judged: the diagnostics of 26-11", () => {
    const full = (mv: number, status: Pack["cell_status"], i: number): Pack =>
      pack(i, "AB3000L", false, i + 1, { soc: 100, cell_delta_mv: mv, cell_judged: true, cell_status: status });
    const s = summarize([set([full(50, "balancing", 0), full(120, "imbalance", 1), full(70, "balancing", 2), full(40, "balancing", 3)])]);
    expect(s.now?.mv).toBe(120);
    expect(s.now?.status).toBe("imbalance");
    expect(s.notFull).toBe(false);
  });

  it("ignores values that are not judged", () => {
    const s = summarize([set([pack(0, "AB3000L", false, 1, { cell_delta_mv: 200, cell_judged: false })])]);
    expect(s.now).toBeNull();
    expect(s.notFull).toBe(true);
  });

  it("falls back to the last judged day and counts imbalance days", () => {
    const s = summarize([
      set([
        pack(0, "AB3000L", false, 1, { history: days([110, null, 120, null, 130, null, null]) }),
        pack(1, "AB3000L", false, 2, { history: days([20, null, 30, null, 40, null, null]) }),
      ]),
    ]);
    expect(s.now).toBeNull();
    expect(s.lastDay).toEqual({ day: "2026-11-24", mv: 130, status: "imbalance" });
    expect(s.imbalance?.days).toBe(3);
    expect(s.imbalance?.lastDay).toBe("2026-11-24");
  });

  it("lists offline sets", () => {
    expect(summarize([set([], false)]).offline).toHaveLength(1);
  });

  it("shows the warmest inverter in the summary, not the warmest pack", () => {
    const a = set(packs);
    const b = { ...set(packs), id: "b", number: 2, enclosure_temp: 31 };
    expect(summarize([a]).inverter).toBe(20);
    expect(summarize([a, b]).inverter).toBe(31);
    expect(summarize([{ ...a, enclosure_temp: null }]).inverter).toBeNull();
  });
});

describe("battery per day", () => {
  const d = (solar: number, grid: number, house: number, exp: number): BatteryDay => ({
    date: "2026-11-27",
    solar_battery: solar,
    grid_battery: grid,
    battery_house: house,
    battery_grid: exp,
    soc_min: 10,
    soc_max: 100,
    cycles: 0.5,
    quarters: 96,
  });

  it("puts charged and delivered on one scale: the largest side fills half", () => {
    const bars = dayBars([d(1, 3, 2, 0), d(0, 0, 8, 0)], 80);
    expect(bars[1].house).toBe(80);
    expect(bars[0]).toEqual({ solar: 10, grid: 30, house: 20, export: 0 });
  });

  it("does not blow up an almost empty week", () => {
    const bars = dayBars([d(0, 0, 0.1, 0), d(0, 0, 0, 0)], 80);
    expect(bars[0].house).toBe(16);
    expect(bars[1]).toEqual({ solar: 0, grid: 0, house: 0, export: 0 });
  });
});
