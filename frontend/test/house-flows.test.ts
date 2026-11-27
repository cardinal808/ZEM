import { describe, expect, it } from "vitest";

import { flows } from "../src/flow";
import { dominant, flowParts } from "../src/house";

describe("dominant", () => {
  it("picks the source that supplies the most", () => {
    expect(dominant({ sun: 0, batt: 540, grid: 20 }, null)).toBe("batt");
    expect(dominant({ sun: 600, batt: 0, grid: 0 }, "batt")).toBe("sun");
  });

  it("keeps the current colour until another source is 50 W bigger", () => {
    expect(dominant({ sun: 320, batt: 300, grid: 0 }, "batt")).toBe("batt");
    expect(dominant({ sun: 360, batt: 300, grid: 0 }, "batt")).toBe("sun");
  });

  it("is null when nothing flows", () => {
    expect(dominant({ sun: 0, batt: 5, grid: 0 }, "grid")).toBeNull();
  });
});

describe("flowParts", () => {
  it("says where each source goes", () => {
    const evening = flowParts(flows(0, 20, -540).paths);
    expect(evening).toEqual([
      { from: "batt", total: 540, to: [["house", 540]] },
      { from: "grid", total: 20, to: [["house", 20]] },
    ]);
    const day = flowParts(flows(3200, -200, 2400).paths);
    expect(day).toEqual([
      { from: "sun", total: 3200, to: [["house", 600], ["battery", 2400], ["grid", 200]] },
    ]);
  });
});

describe("hubPath", () => {
  it("runs level to the Huis spot, then straight", async () => {
    const { hubPath } = await import("../src/house");
    expect(hubPath([100, 50], [400, 300])).toEqual([[100, 50], [400, 50], [400, 300]]);
    expect(hubPath([400, 50], [400, 300])).toEqual([[400, 50], [400, 300]]);
  });
});
