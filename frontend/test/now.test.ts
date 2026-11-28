import { describe, expect, it } from "vitest";

import { nowNote, nowRows, p1Display, versionState, zephyrUpdate, type UpdateState } from "../src/now";
import { flows } from "../src/flow";

const upd = (attrs: Record<string, unknown>, state = "on"): UpdateState => ({
  entity_id: "update.zephyr_update",
  state,
  attributes: { release_url: "https://github.com/cardinal808/ZEPHYR/releases/v0.8.67", ...attrs },
});

describe("card Nu", () => {
  it("hides reasons that repeat the action and warns for problems", () => {
    expect(nowNote("delivering")).toBe("hide");
    expect(nowNote("charging_solar")).toBe("hide");
    expect(nowNote("plan_hold")).toBe("hide");
    expect(nowNote(null)).toBe("hide");
    expect(nowNote("full")).toBe("note");
    expect(nowNote("not_expensive")).toBe("note");
    expect(nowNote("p1_stale")).toBe("warn");
    expect(nowNote("blocked")).toBe("warn");
  });
});

describe("version in the header", () => {
  it("finds the HACS update entity of ZEPHYR by its release URL", () => {
    const other = { entity_id: "update.other", state: "on", attributes: { release_url: "https://github.com/x/y/releases" } };
    expect(zephyrUpdate({ "update.other": other })).toBeNull();
    expect(zephyrUpdate({ "update.other": other, "update.zephyr_update": upd({}) })?.entity_id).toBe(
      "update.zephyr_update",
    );
    expect(zephyrUpdate({ "sensor.x": { ...upd({}), entity_id: "sensor.x" } })).toBeNull();
    expect(zephyrUpdate(undefined)).toBeNull();
  });

  it("shows the running version without an update", () => {
    expect(versionState("0.8.66", null)).toEqual({ kind: "version", running: "0.8.66" });
    expect(versionState("0.8.66", upd({ installed_version: "v0.8.66", latest_version: "v0.8.66" }, "off")).kind).toBe(
      "version",
    );
  });

  it("offers the update when HACS has a newer version", () => {
    const v = versionState("0.8.66", upd({ installed_version: "v0.8.66", latest_version: "v0.8.67", in_progress: false }));
    expect(v).toMatchObject({ kind: "update", running: "0.8.66", latest: "0.8.67", entity: "update.zephyr_update", busy: false });
    expect(versionState("0.8.66", upd({ installed_version: "0.8.66", latest_version: "0.8.67", in_progress: 40 }))).toMatchObject({
      busy: true,
    });
  });

  it("asks for a restart when the installed version does not run yet", () => {
    expect(versionState("0.8.66", upd({ installed_version: "v0.8.67", latest_version: "v0.8.67" }, "off"))).toEqual({
      kind: "restart",
      running: "0.8.66",
      installed: "0.8.67",
    });
  });
});

describe("P1 on the card Nu", () => {
  it("is always in W with a sign, coloured by direction", () => {
    expect(p1Display(1100, "nl")).toEqual({ text: "+1.100 W", kind: "import" });
    expect(p1Display(-350.4, "nl")).toEqual({ text: "\u2212350 W", kind: "export" });
    expect(p1Display(6, "nl")).toEqual({ text: "+6 W", kind: "zero" });
    expect(p1Display(0, "en")).toEqual({ text: "0 W", kind: "zero" });
    expect(p1Display(-50, "en").kind).toBe("zero");
  });
});

describe("fixed rows on the card Nu", () => {
  const rows = (solar: number, grid: number, battery: number) =>
    nowRows(flows(solar, grid, battery).paths).map((r) => `${r.from}>${r.to} ${r.w}`);

  it("always has the same five rows, at least 0 W", () => {
    expect(rows(0, 6, -440)).toEqual(["sun>house 0", "batt>house 440", "grid>house 6", "sun>battery 0", "sun>grid 0"]);
  });

  it("names the source of what goes into the battery and the grid", () => {
    // Noon: sun 2100 W, house 550 W, battery charges 1200 W, 350 W export.
    expect(rows(2100, -350, 1200)).toEqual([
      "sun>house 550",
      "batt>house 0",
      "grid>house 0",
      "sun>battery 1200",
      "sun>grid 350",
    ]);
    // Night: charging 2400 W from the grid, house 150 W.
    expect(rows(0, 2550, 2400).slice(3)).toEqual(["grid>battery 2400", "sun>grid 0"]);
    // Sun 400 W and grid together charge 1200 W.
    expect(rows(400, 800, 1200)[3]).toBe("sun_grid>battery 1200");
    // The battery exports: house 300 W, battery 1000 W.
    expect(rows(0, -700, -1000).slice(3)).toEqual(["sun>battery 0", "batt>grid 700"]);
  });
});
