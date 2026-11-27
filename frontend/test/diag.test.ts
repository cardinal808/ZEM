import { describe, expect, it } from "vitest";

import {
  blockerText,
  eventKind,
  eventText,
  fastButtons,
  profileStats,
  relDiff,
  type DiagEvent,
} from "../src/diag";
import en from "../src/locales/en.json";
import nl from "../src/locales/nl.json";

const at = "2026-11-26T12:00:00+00:00";

describe("diagnose", () => {
  it("writes one sentence per event", () => {
    const reason: DiagEvent = {
      time: at,
      kind: "reason",
      code: "delivering",
      text: { nl: "Levert 600 W", en: "Delivering 600 W" },
    };
    expect(eventText(reason, "nl", "nl")).toBe("Levert 600 W");
    expect(
      eventText(
        { time: at, kind: "reason", code: "full", text: null },
        "nl",
        "nl",
      ),
    ).toBe("Reden: full");
    expect(
      eventText({ time: at, kind: "mode", mode: "fast_charge" }, "nl", "nl"),
    ).toBe("Modus: Snel opladen");
    expect(
      eventText({ time: at, kind: "excluded_on", power: 1800 }, "nl", "nl"),
    ).toBe("Airco buiten de accu: 1,8 kW");
    expect(eventText({ time: at, kind: "excluded_off" }, "en", "en")).toBe(
      "Air conditioner no longer outside the battery",
    );
    expect(
      eventText(
        { time: at, kind: "flash", cause: "soc_limits", set: 1 },
        "nl",
        "nl",
      ),
    ).toBe("Set 1: laadgrenzen in flash geschreven");
    expect(eventText({ time: at, kind: "test", power: 300 }, "en", "en")).toBe(
      "Write test 300 W",
    );
    expect(eventKind({ time: at, kind: "second_controller" })).toBe("warning");
    expect(eventKind({ time: at, kind: "excluded_on" })).toBe("airco");
  });

  it("has every event, kind and control text in both languages", () => {
    for (const texts of [nl, en]) {
      for (const k of [
        "reason_code",
        "mode",
        "live",
        "shadow",
        "test",
        "test_end",
        "second_controller",
        "excluded_on",
        "excluded_off",
        "flash",
      ])
        expect(texts.diag.event).toHaveProperty(k);
      for (const k of ["control", "mode", "live", "airco", "write", "warning"])
        expect(texts.diag.kind).toHaveProperty(k);
    }
    expect(Object.keys(nl.control).sort()).toEqual(
      Object.keys(en.control).sort(),
    );
    expect(Object.keys(nl.diag).sort()).toEqual(Object.keys(en.diag).sort());
  });

  it("keeps the fast buttons in place and stops the running one", () => {
    const modes = [
      "standby",
      "zero_meter",
      "fast_charge",
      "fast_discharge",
      "dynamic_forecasting",
    ];
    expect(fastButtons("dynamic_forecasting", modes, "zero_meter")).toEqual([
      { mode: "fast_charge", active: false, target: "fast_charge" },
      { mode: "fast_discharge", active: false, target: "fast_discharge" },
    ]);
    // Bjorn's test 26-11: from fast charge to fast discharge the buttons used to swap places.
    expect(
      fastButtons("fast_charge", modes, "dynamic_forecasting").map((b) => [
        b.mode,
        b.target,
      ]),
    ).toEqual([
      ["fast_charge", "dynamic_forecasting"],
      ["fast_discharge", "fast_discharge"],
    ]);
    expect(
      fastButtons("fast_discharge", modes, "fast_discharge")[1].target,
    ).toBe("zero_meter");
    expect(
      fastButtons("zero_meter", ["standby", "zero_meter"], "zero_meter"),
    ).toEqual([]);
  });

  it("translates the reasons live control cannot start", () => {
    expect(blockerText("set 2 is offline", "nl")).toBe("Set 2 is offline.");
    expect(blockerText("P1 is not reporting", "nl")).toBe(
      "De P1-sensor meldt niets.",
    );
    expect(blockerText("something new", "nl")).toBe("something new");
  });

  it("sums the profile and counts the learned hours", () => {
    const house = Array(24).fill(0.5);
    const airco = Array(24).fill(0);
    airco[12] = 1.2;
    const counts = Array(24).fill(3);
    counts[13] = 2;
    const st = profileStats({ house, airco, counts, min_count: 3 });
    expect(st.total).toBeCloseTo(12);
    expect(st.aircoTotal).toBeCloseTo(1.2);
    expect(st.top).toBe(2); // 1,7 rounded up to 0,5
    expect(st.learned).toBe(23);
    expect(
      profileStats({
        house: Array(24).fill(0),
        airco: [],
        counts: Array(24).fill(0),
        min_count: 2,
      }).learned,
    ).toBe(0);
  });
});

describe("relDiff", () => {
  it("is the reality's difference from the plan as a fraction", () => {
    expect(relDiff({ expected: 10, actual: 12, diff: 2 })).toBeCloseTo(0.2);
    expect(relDiff({ expected: 10, actual: 8, diff: -2 })).toBeCloseTo(-0.2);
  });
  it("has no answer for an empty plan", () => {
    expect(relDiff({ expected: 0, actual: 3, diff: 3 })).toBeNull();
  });
});

import { cellKind } from "../src/stroom";

describe("cellKind", () => {
  it("colours a 5-minute cell by how it went", () => {
    expect(cellKind(null)).toBe("none");
    expect(cellKind([10, 10, 0, 0])).toBe("idle");
    expect(cellKind([300, 280, 1, 0])).toBe("good");
    expect(cellKind([300, 100, 20, 3])).toBe("import");
    expect(cellKind([300, 100, 2, 9])).toBe("export");
  });
});

import { allGaps, estimatedShare } from "../src/diag";

describe("energy counters", () => {
  const gap = (end: string) => ({
    start: end,
    end,
    seconds: 60,
    method: "soc",
    restart: false,
    kwh: {},
    pack_delta_kwh: null,
  });
  it("gives the estimated part of charged, delivered and solar", () => {
    const s = {
      kwh: { charged: 8, discharged: 2, solar: 0, dc_charged: 9 },
      estimated: { charged: 0.5, dc_charged: 3 },
      failed_reads: 0,
      open_gap: null,
      gaps: [],
    };
    expect(estimatedShare(s)).toEqual({ kwh: 0.5, share: 0.05 });
    expect(estimatedShare({ ...s, kwh: {}, estimated: {} }).share).toBeNull();
  });
  it("lists the gaps of all sets, newest first", () => {
    const view = {
      totals: {},
      sets: [
        {
          set: 1,
          kwh: {},
          estimated: {},
          failed_reads: 0,
          open_gap: null,
          gaps: [gap("2026-11-27T08:00:00Z")],
        },
        {
          set: 2,
          kwh: {},
          estimated: {},
          failed_reads: 0,
          open_gap: null,
          gaps: [gap("2026-11-27T09:00:00Z")],
        },
      ],
    };
    expect(allGaps(view).map((g) => g.set)).toEqual([2, 1]);
  });
});

import { devLimit, linePath } from "../src/stroom";

describe("regulation chart", () => {
  it("breaks the line at gaps", () => {
    const id = (v: number): number => v;
    expect(
      linePath(
        [
          [0, 1],
          [1, null],
          [2, 3],
          [3, 4],
        ],
        id,
        id,
      ),
    ).toBe("M0.0,1.0M2.0,3.0L3.0,4.0");
  });
  it("scales the deviation axis to the largest miss, at least 200 W", () => {
    expect(devLimit([[0, 30, 0, 0, 0, true]])).toBe(200);
    expect(
      devLimit([
        [0, 900, 300, 0, 0, true],
        [1, null, 0, 0, null, false],
      ]),
    ).toBe(600);
  });
});

import { signedW } from "../src/stroom";

describe("signedW", () => {
  it("keeps the sign on axis labels", () => {
    expect(signedW(600, "en")).toBe("+600 W");
    expect(signedW(-1250, "en")).toBe("−1,250 W");
    expect(signedW(0, "en")).toBe("0 W");
  });
});
