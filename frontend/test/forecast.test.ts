import { describe, expect, it } from "vitest";

import en from "../src/locales/en.json";
import nl from "../src/locales/nl.json";
import {
  forecastDays,
  forecastMode,
  forecastPaths,
  type ForecastSlot,
  type PriceForecast,
  type Quarter,
} from "../src/plan";
import { dayScale, type SavingsDay } from "../src/savings";

const q = (start: string): Quarter => ({
  start,
  past: false,
  market: 0.2,
  buy: 0.3,
  sell: 0.2,
  action: "hold",
  soc: 50,
  solar: 0,
  load: 0.1,
  indicative: true,
});
const f = (start: string, buy: number): ForecastSlot => ({
  start,
  market: buy - 0.1,
  low: buy - 0.15,
  high: buy,
  buy,
  buy_low: buy - 0.05,
  buy_high: buy + 0.05,
});

describe("price forecast (OPDRACHT-ui-prijsvoorspelling)", () => {
  it("draws a dashed line and a band over the shown quarters, broken where there is no forecast", () => {
    const quarters = [
      q("2026-11-30T07:00:00Z"),
      q("2026-11-30T07:15:00Z"),
      q("2026-11-30T07:30:00Z"),
    ];
    const forecast = [
      f("2026-11-30T07:00:00Z", 0.4),
      f("2026-11-30T07:30:00Z", 0.45),
    ];
    const paths = forecastPaths(quarters, forecast, { lo: 0, hi: 0.5 });
    expect(paths).toHaveLength(2);
    expect(paths[0].line).toBe("0.5,20.00");
    expect(paths[0].band.split(" ")).toHaveLength(2);
    expect(forecastPaths(quarters, undefined, { lo: 0, hi: 0.5 })).toEqual([]);
  });

  it("sums up the forecast days the chart does not show", () => {
    const shown = [q("2026-11-29T12:00:00Z")];
    const forecast = [
      f("2026-11-30T07:00:00Z", 0.47),
      f("2026-11-30T03:00:00Z", 0.3),
    ];
    const result = forecastDays(forecast, shown, "Europe/Amsterdam");
    expect(result).toHaveLength(1);
    expect(result[0].max.buy).toBe(0.47);
    expect(result[0].avg).toBeCloseTo(0.385);
  });

  it("says in one phrase what the forecast does for the plan", () => {
    const base: PriceForecast = {
      source: { name: "jeroen.nl", url: "" },
      mode: "use",
      value: "low",
      slots: [],
      compare: null,
    };
    expect(forecastMode(base)).toBe("fc_used");
    expect(forecastMode({ ...base, mode: "indicative" })).toBe("fc_info");
    const compare = {
      action_without: "H",
      action_with: "L",
      first_action_differs: true,
      expected_cost_without: 0,
      expected_cost_with: 0,
      grid_charge_kwh_without: 0,
      grid_charge_kwh_with: 0,
    };
    expect(forecastMode({ ...base, mode: "indicative", compare })).toBe(
      "fc_would",
    );
  });

  it("has every text in both languages", () => {
    for (const key of [
      "fc_label",
      "fc_stats",
      "fc_would",
      "fc_used",
      "fc_info",
      "fc_source",
      "fc_action_L",
    ]) {
      expect((nl.plan as Record<string, string>)[key]).toBeTruthy();
      expect((en.plan as Record<string, string>)[key]).toBeTruthy();
    }
  });
});

describe("savings with solar (OPDRACHT-besparing-zon)", () => {
  const day = (bat: number, sun: number): SavingsDay => ({
    day: "2026-11-26",
    savings_battery: bat,
    savings_solar: sun,
    incomplete: false,
  });

  it("scales the stacked bars on solar + battery", () => {
    expect(dayScale([day(0.9, 5.7)]).top).toBe(1);
    expect(dayScale([day(0.9, 5.7)], true).top).toBe(7);
  });

  it("has the new texts in both languages", () => {
    for (const key of [
      "estimated",
      "title_solar",
      "sun_direct",
      "sun_export",
      "battery_only",
      "bf_soc",
      "bf_warn_pv",
    ]) {
      expect((nl.savings as Record<string, string>)[key]).toBeTruthy();
      expect((en.savings as Record<string, string>)[key]).toBeTruthy();
    }
  });
});
