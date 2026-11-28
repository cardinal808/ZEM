import { describe, expect, it } from "vitest";

import { controlValue, formatNumber, type SettingField } from "../src/settings";
import { t } from "../src/i18n";
import en from "../src/locales/en.json";
import nl from "../src/locales/nl.json";

describe("settings", () => {
  it("formats numbers by step", () => {
    expect(formatNumber(10, 1, "nl")).toBe("10");
    expect(formatNumber(0.03, 0.001, "nl")).toBe("0,03");
    expect(formatNumber(0.09161, "any", "nl")).toBe("0,09161");
    expect(formatNumber(21, 0.1, "en")).toBe("21");
    expect(formatNumber(1.25, 0.01, "en")).toBe("1.25");
  });

  it("has a label, help and more text for every field in both languages", () => {
    const keys = Object.keys(en.settings.fields);
    expect(Object.keys(nl.settings.fields).sort()).toEqual(keys.sort());
    for (const key of keys) {
      for (const part of ["label", "help", "more"]) {
        expect(t("nl", `settings.fields.${key}.${part}`)).not.toBe(`settings.fields.${key}.${part}`);
        expect(t("en", `settings.fields.${key}.${part}`)).not.toBe(`settings.fields.${key}.${part}`);
      }
    }
  });
});

describe("tariff fields from the table", () => {
  const field = (over: Partial<SettingField>): SettingField =>
    ({ key: "tariff_markup_import", kind: "number", tariff: true, active: false, in_use: 0.01653, value: 0, ...over }) as SettingField;

  it("shows the amount in use while the supplier's table applies", () => {
    expect(controlValue(field({}), 0)).toBe(0.01653);
  });

  it("shows the own value with own tariffs or without an amount in use", () => {
    expect(controlValue(field({ active: true }), 0.02)).toBe(0.02);
    expect(controlValue(field({ in_use: null }), 0)).toBe(0);
    expect(controlValue(field({ tariff: false }), 5)).toBe(5);
  });

  it("puts the energy tax in use into the info text", () => {
    expect(t("nl", "settings.fields.tariff_energy_tax.more", { in_use: "0,09161 €/kWh" })).toContain("nu 0,09161 €/kWh");
    expect(t("en", "settings.fields.tariff_vat.more")).toContain("21 %");
  });
});
