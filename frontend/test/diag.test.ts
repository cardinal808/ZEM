import { describe, expect, it } from "vitest";

import { blockerText, eventKind, eventText, fastButtons, type DiagEvent } from "../src/diag";
import en from "../src/locales/en.json";
import nl from "../src/locales/nl.json";

const at = "2026-11-26T12:00:00+00:00";

describe("diagnose", () => {
  it("writes one sentence per event", () => {
    const reason: DiagEvent = { time: at, kind: "reason", code: "delivering", text: { nl: "Levert 600 W", en: "Delivering 600 W" } };
    expect(eventText(reason, "nl", "nl")).toBe("Levert 600 W");
    expect(eventText({ time: at, kind: "reason", code: "full", text: null }, "nl", "nl")).toBe("Reden: full");
    expect(eventText({ time: at, kind: "mode", mode: "fast_charge" }, "nl", "nl")).toBe("Modus: Snel opladen");
    expect(eventText({ time: at, kind: "excluded_on", power: 1800 }, "nl", "nl")).toBe("Airco buiten de accu: 1,8 kW");
    expect(eventText({ time: at, kind: "excluded_off" }, "en", "en")).toBe("Air conditioner no longer outside the battery");
    expect(eventText({ time: at, kind: "flash", cause: "soc_limits", set: 1 }, "nl", "nl")).toBe("Set 1: laadgrenzen in flash geschreven");
    expect(eventText({ time: at, kind: "test", power: 300 }, "en", "en")).toBe("Write test 300 W");
    expect(eventKind({ time: at, kind: "second_controller" })).toBe("warning");
    expect(eventKind({ time: at, kind: "excluded_on" })).toBe("airco");
  });

  it("has every event, kind and control text in both languages", () => {
    for (const texts of [nl, en]) {
      for (const k of ["reason_code", "mode", "live", "shadow", "test", "test_end", "second_controller", "excluded_on", "excluded_off", "flash"])
        expect(texts.diag.event).toHaveProperty(k);
      for (const k of ["control", "mode", "live", "airco", "write", "warning"]) expect(texts.diag.kind).toHaveProperty(k);
    }
    expect(Object.keys(nl.control).sort()).toEqual(Object.keys(en.control).sort());
    expect(Object.keys(nl.diag).sort()).toEqual(Object.keys(en.diag).sort());
  });

  it("shows fast buttons and a way back", () => {
    const modes = ["standby", "zero_meter", "fast_charge", "fast_discharge", "dynamic_forecasting"];
    expect(fastButtons("dynamic_forecasting", modes, "zero_meter")).toEqual({ charge: true, discharge: true, stop: null });
    expect(fastButtons("fast_charge", modes, "dynamic_forecasting")).toEqual({ charge: false, discharge: true, stop: "dynamic_forecasting" });
    expect(fastButtons("fast_discharge", modes, "fast_discharge").stop).toBe("zero_meter");
  });

  it("translates the reasons live control cannot start", () => {
    expect(blockerText("set 2 is offline", "nl")).toBe("Set 2 is offline.");
    expect(blockerText("P1 is not reporting", "nl")).toBe("De P1-sensor meldt niets.");
    expect(blockerText("something new", "nl")).toBe("something new");
  });
});
