import { describe, expect, it } from "vitest";

import en from "../src/locales/en.json";
import nl from "../src/locales/nl.json";
import { busSegments, houseLayout, shownFloor, type Tap } from "../src/house";

/** Connections of the default house (3 storeys), top to bottom. */
const taps = (o: {
  battery?: number;
  shed?: number;
  roof?: number;
  attic?: number;
  first?: number;
  rest?: number;
  ground?: number;
  ev?: number;
  grid?: number;
}): Tap[] => [
  { y: 52, w: o.battery ?? 0 },
  { y: 80, w: o.shed ?? 0 },
  { y: 354, w: o.roof ?? 0 },
  { y: 462, w: -(o.attic ?? 0) },
  { y: 640, w: -(o.first ?? 0) },
  { y: 750, w: -(o.rest ?? 0) },
  { y: 840, w: -(o.ground ?? 0) },
  { y: 968, w: -(o.ev ?? 0) },
  { y: 1030, w: o.grid ?? 0 },
];
const dirs = (t: Tap[]) => busSegments(t).map((s) => s.dir);

describe("busSegments (OPDRACHT-ui-huisplaatje-isometrisch §3)", () => {
  it("the mock: battery charging, grid the biggest source at the bottom", () => {
    // Sun 3.96 kW (shed 1.12, roof 2.84), battery charges 600 W, grid 1.00 kW, charge point 1.40 kW.
    const segs = busSegments(
      taps({
        battery: -600,
        shed: 1120,
        roof: 2840,
        attic: 420,
        first: 380,
        rest: 310,
        ground: 1850,
        ev: 1400,
        grid: 1000,
      }),
    );
    expect(segs[0]).toEqual({ y0: 52, y1: 80, w: 600, dir: -1 }); // up, to the battery
    expect(segs[1].dir).toBe(1); // middle part down
    expect(segs.at(-1)).toEqual({ y0: 968, y1: 1030, w: 1000, dir: -1 }); // grid up
  });

  it("only sun: everything flows down from the panels", () => {
    expect(dirs(taps({ roof: 1000, rest: 600, ground: 400 }))).toEqual([
      0, 0, 1, 1, 1, 1, 0, 0,
    ]);
  });

  it("battery delivering, grid as the biggest source: both ends feed the middle", () => {
    const d = dirs(taps({ battery: 300, rest: 1500, grid: 1200 }));
    expect(d.slice(0, 5)).toEqual([1, 1, 1, 1, 1]);
    expect(d.slice(5)).toEqual([-1, -1, -1]);
  });

  it("export: the bottom piece runs down to the grid", () => {
    const segs = busSegments(taps({ roof: 3000, rest: 500, grid: -2500 }));
    expect(segs.at(-1)).toEqual({ y0: 968, y1: 1030, w: 2500, dir: 1 });
  });

  it("no dots below 10 W", () => {
    expect(dirs(taps({ roof: 8, rest: 8 })).every((d) => d === 0)).toBe(true);
  });
});

describe("the new houses", () => {
  it("branches line up with the middle of the floor boxes", () => {
    for (const storeys of [2, 3] as const) {
      const L = houseLayout(storeys);
      for (const [k, y] of Object.entries(L.floors)) {
        const b = L.boxes[k as "first"];
        expect(b[1] + b[3] / 2).toBe(y);
      }
    }
    expect(houseLayout(2).floors.attic).toBeUndefined();
  });

  it("the alternative house shows the attic on the 1st floor", () => {
    expect(shownFloor("attic", 2)).toBe("first");
    expect(shownFloor("attic", 3)).toBe("attic");
    expect(shownFloor("ground", 2)).toBe("ground");
  });

  it("has the texts in both languages", () => {
    for (const key of [
      "default",
      "default_sub",
      "alt",
      "alt_sub",
      "old",
      "old_sub",
      "own_sub",
      "alt_note",
    ]) {
      expect((nl.picture as Record<string, string>)[key]).toBeTruthy();
      expect((en.picture as Record<string, string>)[key]).toBeTruthy();
    }
    for (const key of [
      "shed_short",
      "roof_short",
      "roof_box",
      "shed_box",
      "import_t",
      "export_t2",
      "grid_zero",
    ]) {
      expect((nl.house as Record<string, string>)[key]).toBeTruthy();
      expect((en.house as Record<string, string>)[key]).toBeTruthy();
    }
  });
});
