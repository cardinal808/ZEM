import { describe, expect, it } from "vitest";

import { draftToSave, fieldVisible, type SettingField } from "../src/settings";

const field = (key: string, show_if: SettingField["show_if"] = null): SettingField =>
  ({ key, kind: "entity", show_if }) as SettingField;

const p1Entity = field("p1_entity", { key: "p1_source", values: ["single"] });
const p1Import = field("p1_import_entity", { key: "p1_source", values: ["import_export"] });
const climate = field("excluded_climate_entity", { key: "excluded_energy_entity", values: ["*"] });
const curtail = field("curtail_number", { key: "curtail_negative", values: ["curtail_zephyr"] });

describe("fieldVisible", () => {
  it("shows the P1 fields that fit the chosen source, also before saving", () => {
    let source = "single";
    const valueOf = (k: string) => (k === "p1_source" ? source : null);
    expect(fieldVisible(p1Entity, valueOf)).toBe(true);
    expect(fieldVisible(p1Import, valueOf)).toBe(false);
    source = "import_export"; // switched in the form, not saved yet
    expect(fieldVisible(p1Entity, valueOf)).toBe(false);
    expect(fieldVisible(p1Import, valueOf)).toBe(true);
  });

  it("shows the inverter fields only when ZEPHYR curtails", () => {
    expect(fieldVisible(curtail, () => "curtail_external")).toBe(false);
    expect(fieldVisible(curtail, () => "curtail_zephyr")).toBe(true);
  });

  it("treats * as filled in", () => {
    expect(fieldVisible(climate, () => null)).toBe(false);
    expect(fieldVisible(climate, () => "")).toBe(false);
    expect(fieldVisible(climate, () => "sensor.airco_kwh")).toBe(true);
    expect(fieldVisible(field("plain"), () => null)).toBe(true);
  });
});

describe("draftToSave", () => {
  it("leaves hidden fields out, so a wrong hidden entity does not block saving", () => {
    const draft = { p1_source: "single", p1_import_entity: "sensor.gone", p1_entity: "sensor.p1" };
    const visible = (k: string) => k !== "p1_import_entity";
    expect(draftToSave(draft, visible)).toEqual({ p1_source: "single", p1_entity: "sensor.p1" });
  });
});
