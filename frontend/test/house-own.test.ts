import { describe, expect, it } from "vitest";

import { nextUnplaced } from "../src/house-editor";
import { OWN_BOX_W, ownLine } from "../src/house";

describe("ownLine", () => {
  it("leaves the box on the side of the spot and bends once", () => {
    const pts = ownLine([0.1, 0.2], [0.8, 0.6], 1000, 500);
    expect(pts[0][0]).toBeCloseTo((0.1 + OWN_BOX_W) * 1000); // right edge
    expect(pts).toHaveLength(3);
    expect(pts[1]).toEqual([800, pts[0][1]]);
    expect(pts[2]).toEqual([800, 300]);
  });

  it("goes straight down when the spot is under the box", () => {
    const pts = ownLine([0.1, 0.2], [0.2, 0.9], 1000, 500);
    expect(pts).toHaveLength(2);
    expect(pts[0][0]).toBe(200);
  });

  it("keeps a box at the right edge inside the picture", () => {
    const pts = ownLine([0.95, 0.1], [0.1, 0.5], 1000, 500);
    expect(pts[0][0]).toBeCloseTo((1 - OWN_BOX_W) * 1000);
  });
});

describe("nextUnplaced", () => {
  it("skips placed and hidden items and wraps around", () => {
    const items = { roof: { box: [0, 0] as [number, number], point: [0, 0] as [number, number] } };
    expect(nextUnplaced(items, ["shed_solar"], null)).toBe("battery");
    expect(nextUnplaced(items, [], "shed")).toBe("shed_solar");
  });
});
