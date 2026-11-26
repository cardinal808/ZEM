import { describe, expect, it } from "vitest";

import { formatNumber } from "../src/settings";
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
