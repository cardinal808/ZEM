import { describe, expect, it } from "vitest";

import { packName, summarize, type Pack, type SetInfo } from "../src/sets";

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
  cell_status: "good",
  history: [],
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

  it("finds the worst judged cell difference, ignoring full/empty packs", () => {
    const s = summarize([
      set([
        pack(0, "AB3000L", false, 1, { cell_delta_mv: 120, cell_status: "edge", soc: 100, temp: 21 }),
        pack(1, "AB3000L", false, 2, { cell_delta_mv: 50, cell_status: "watch", soc: 73 }),
        pack(2, "AB3000L", false, 3, { cell_delta_mv: 20, cell_status: "good", soc: 78 }),
      ]),
    ]);
    expect(s.worst?.mv).toBe(50);
    expect(s.worst?.status).toBe("watch");
    expect(s.largest).toBe(120);
    expect([s.socMin, s.socMax, s.warmest]).toEqual([73, 100, 21]);
  });

  it("has no judged worst when every pack is full", () => {
    const s = summarize([set([pack(0, "AB3000L", false, 1, { cell_delta_mv: 120, cell_status: "edge", soc: 100 })])]);
    expect(s.worst).toBeNull();
    expect(s.largest).toBe(120);
  });

  it("lists offline sets", () => {
    expect(summarize([set([], false)]).offline).toHaveLength(1);
  });
});
