import { describe, expect, it } from "vitest";

import { clock, euro, kwh, minutesUntil, percent, sameDay, signedWatts, watts } from "../src/format";
import { language, t } from "../src/i18n";

describe("format", () => {
  it("writes prices in the user's notation", () => {
    expect(euro(0.274, "nl")).toBe("€ 0,27");
    expect(euro(0.274, "en")).toBe("€0.27");
    expect(euro(-0.05, "nl")).toBe("−€ 0,05");
  });

  it("rounds power and uses a true minus", () => {
    expect(watts(-623, "nl")).toBe("620 W");
    expect(watts(2400, "nl")).toBe("2,40 kW");
    expect(signedWatts(-623, "en")).toBe("−620 W");
    expect(signedWatts(120, "en")).toBe("+120 W");
    expect(signedWatts(0, "en")).toBe("0 W");
  });

  it("formats energy and percent", () => {
    expect(kwh(8.36, "nl")).toBe("8,4 kWh");
    expect(percent(75.6, "nl")).toBe("76 %");
  });

  it("shows clock times in Home Assistant's time zone, also around DST", () => {
    expect(clock("2026-11-26T21:45:00Z", "nl", "Europe/Amsterdam")).toBe("22:45");
    expect(clock("2026-03-29T01:00:00Z", "nl", "Europe/Amsterdam")).toBe("03:00");
    expect(clock("2026-10-25T00:30:00Z", "nl", "Europe/Amsterdam")).toBe("02:30");
    expect(clock("2026-10-25T01:30:00Z", "nl", "Europe/Amsterdam")).toBe("02:30");
  });

  it("knows the calendar day in the time zone", () => {
    expect(sameDay("2026-11-26T23:30:00Z", "2026-11-26T21:00:00Z", "Europe/Amsterdam")).toBe(false);
    expect(sameDay("2026-11-26T23:30:00Z", "2026-11-26T21:00:00Z", "UTC")).toBe(true);
  });

  it("counts minutes until a moment, never negative", () => {
    const now = Date.parse("2026-11-26T21:45:00Z");
    expect(minutesUntil("2026-11-27T01:00:00Z", now)).toBe(195);
    expect(minutesUntil("2026-11-26T21:00:00Z", now)).toBe(0);
  });
});

describe("i18n", () => {
  it("picks Dutch for nl and nl-BE, English otherwise", () => {
    expect(language("nl")).toBe("nl");
    expect(language("nl-BE")).toBe("nl");
    expect(language("de")).toBe("en");
    expect(language(undefined)).toBe("en");
  });

  it("fills placeholders and falls back to the key", () => {
    expect(t("nl", "battery.limits", { min: 10, max: 95 })).toBe("Grenzen 10–95 %");
    expect(t("en", "next.in", { time: "5 min" })).toBe("in 5 min");
    expect(t("nl", "does.not.exist")).toBe("does.not.exist");
  });
});
