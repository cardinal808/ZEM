import { describe, expect, it } from "vitest";

import { byFloor } from "../src/house";
import type { HouseDevice } from "../src/stroom";

const dev = (id: string, floor: string, shown = true): HouseDevice =>
  ({ id, name: id, kind: "plug", floor, shown, power_w: 0, today_kwh: 0 }) as HouseDevice;

describe("byFloor", () => {
  it("groups shown consumers per floor in order", () => {
    const out = byFloor([dev("was", "attic"), dev("droger", "attic"), dev("vaat", "ground")]);
    expect(out.attic.map((d) => d.id)).toEqual(["was", "droger"]);
    expect(out.ground.map((d) => d.id)).toEqual(["vaat"]);
    expect(out.first).toBeUndefined();
  });

  it("leaves hidden consumers out", () => {
    expect(byFloor([dev("tv", "first", false)])).toEqual({});
  });
});
