import { describe, expect, it } from "vitest";

import en from "../src/locales/en.json";
import nl from "../src/locales/nl.json";
import { dayScale, type SavingsDay } from "../src/savings";

const day = (v: number | null): SavingsDay => ({ day: "2026-11-01", savings_battery: v, incomplete: false });

describe("savings", () => {
  it("scales the day bars and cuts a single outlier", () => {
    expect(dayScale([day(0.4), day(0.6), day(0.3)])).toEqual({ top: 1, bottom: -0 });
    // A test day of −1,90 between days of about 0,5: cut at −1,50 (2 × typical 0,62, rounded up to 0,50).
    const s = dayScale([day(0.42), day(0.55), day(0.31), day(0.62), day(0.48), day(-1.9)]);
    expect(s.top).toBe(1);
    expect(s.bottom).toBe(-1.5);
    const flat = dayScale([day(0.1), day(0.12), day(0.08), day(0.11), day(-1.9)]);
    expect(flat.bottom).toBe(-0.5);
    expect(dayScale([day(null)])).toEqual({ top: 0.5, bottom: -0 });
  });

  it("has the same texts in both languages", () => {
    expect(Object.keys(nl.savings).sort()).toEqual(Object.keys(en.savings).sort());
    expect(nl.menu).toHaveProperty("savings");
    // Every error of zephyr/savings/backfill has a sentence.
    for (const code of ["no_counters", "no_battery_counters", "entity_missing", "bad_date", "no_connection"])
      expect(nl.savings).toHaveProperty(`bf_err_${code}`);
  });
});
