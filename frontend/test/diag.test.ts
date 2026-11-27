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

import { deviceName, deviceRows, type HouseDevice } from "../src/stroom";

describe("consumers today", () => {
  const d = (id: string, kwh: number | null, shown = true): HouseDevice => ({
    id,
    name: id === "airco" ? null : id,
    kind: id === "airco" ? "airco" : "washer",
    floor: "ground",
    shown,
    power_w: null,
    today_kwh: kwh,
  });
  it("lists shown consumers by kWh today, then the rest of the house", () => {
    const rows = deviceRows(
      [d("wash", 0.9), d("airco", 6.3), d("dry", 1.5, false)],
      3.9,
    );
    expect(rows.map((r) => r.id)).toEqual(["airco", "wash", "rest"]);
  });
  it("names the airco from the texts", () => {
    expect(deviceName(d("airco", 1), (k) => k)).toBe("stroom.kind_airco");
    expect(deviceName(d("wash", 1), (k) => k)).toBe("wash");
  });
});

import { estimateCost, tapAction, type ApplianceItem } from "../src/appliances";
import { runBars, type Quarter as PQ } from "../src/plan";

describe("appliance buttons", () => {
  it("washer goes 0 → 1 → 2 → off, the others 0 → 1 → off", () => {
    expect([0, 1, 2].map((n) => tapAction("washer", n))).toEqual([
      "plan",
      "plan",
      "clear",
    ]);
    expect([0, 1].map((n) => tapAction("dishwasher", n))).toEqual([
      "plan",
      "clear",
    ]);
  });

  const q = (iso: string, buy: number): PQ => ({
    start: iso,
    past: false,
    market: null,
    buy,
    sell: null,
    action: null,
    soc: null,
    solar: null,
    load: null,
    indicative: false,
  });
  const washer: ApplianceItem = {
    id: "w",
    name: "Was",
    kind: "washer",
    plug: true,
    running: false,
    profile: "default",
    runs_seen: 0,
    kwh: 1.0,
    minutes: 60,
    window: { from: "10:00:00", until: "15:00:00" },
  };
  it("estimates one run at the cheapest start within the window", () => {
    const quarters: PQ[] = [];
    for (let i = 0; i < 96; i++) {
      const h = Math.floor(i / 4);
      quarters.push(
        q(
          new Date(Date.UTC(2026, 10, 28, 0, i * 15)).toISOString(),
          h >= 12 && h < 14 ? 0.1 : 0.3,
        ),
      );
    }
    const est = estimateCost(
      quarters,
      washer,
      Date.UTC(2026, 10, 28, 6, 0),
      "UTC",
    );
    expect(est).toBeCloseTo(0.1); // 12:00–13:00 at € 0,10
    expect(
      estimateCost(
        quarters,
        { ...washer, window: { from: "16:00:00", until: "17:00:00" } },
        Date.UTC(2026, 10, 28, 6, 0),
        "UTC",
      ),
    ).toBeCloseTo(0.3);
  });
  it("draws runs as bars, overlapping ones on a new row", () => {
    const quarters = [0, 1, 2, 3, 4, 5, 6, 7].map((i) =>
      q(new Date(Date.UTC(2026, 10, 28, 10, i * 15)).toISOString(), 0.2),
    );
    const bars = runBars(quarters, [
      { name: "Was", start: "2026-11-28T10:15:00Z", minutes: 60, fixed: false },
      {
        name: "Droger",
        start: "2026-11-28T10:45:00Z",
        minutes: 30,
        fixed: true,
      },
    ]);
    expect(bars.map((b) => [b.left, b.width, b.row])).toEqual([
      [1, 4, 0],
      [3, 2, 1],
    ]);
  });
});

import { peakStats } from "../src/diag";

describe("short peaks", () => {
  it("gives today and the mean of the finished days", () => {
    const days = [
      { day: "2026-11-25", kwh: 0.04, holds: 10 },
      { day: "2026-11-26", kwh: 0.08, holds: 20 },
      { day: "2026-11-27", kwh: 0.02, holds: 5 },
    ];
    const st = peakStats(days, "2026-11-27");
    expect(st.today?.holds).toBe(5);
    expect(st.mean).toBeCloseTo(0.06);
    expect(peakStats([], "2026-11-27")).toEqual({ today: null, mean: null });
  });
});

import { negativeAhead } from "../src/plan";
import { searchChoices, wrongDomain } from "../src/settings-edit";

describe("curtailing and the entity picker", () => {
  const q = (iso: string, sell: number, cost = 0, past = false) => ({
    start: iso,
    past,
    market: null,
    buy: 0.02,
    sell,
    action: null,
    soc: null,
    solar: null,
    load: null,
    indicative: false,
    export_cost: cost,
  });
  it("sums the negative export prices still to come", () => {
    const quarters = [
      q("2026-11-27T12:00:00Z", -0.03, 0.05, true),
      q("2026-11-27T13:00:00Z", 0.05),
      q("2026-11-28T12:00:00Z", -0.04, 0.1),
      q("2026-11-28T12:15:00Z", -0.04, 0.1),
    ];
    expect(negativeAhead(quarters, "UTC")).toEqual({
      hours: 0.5,
      cost: 0.2,
      when: "tomorrow",
    });
    expect(negativeAhead([q("2026-11-27T13:00:00Z", 0.05)], "UTC")).toBeNull();
  });
  it("finds entities on any part of name and id", () => {
    const choices = [
      {
        id: "switch.solaredge_export_limit",
        name: "SolarEdge exportbegrenzer",
      },
      { id: "switch.inverter_solar_power", name: "Omvormer solar aan/uit" },
      { id: "switch.kitchen", name: "Keuken" },
    ];
    expect(searchChoices(choices, "export").map((c) => c.id)).toEqual([
      "switch.solaredge_export_limit",
    ]);
    expect(searchChoices(choices, "solar").length).toBe(2);
    expect(searchChoices(choices, "omv aan").map((c) => c.id)).toEqual([
      "switch.inverter_solar_power",
    ]);
  });
  it("names the wrong domain", () => {
    expect(wrongDomain("sensor.solaredge_ac_power", "number")).toBe("sensor");
    expect(wrongDomain("number.limit", "number")).toBeNull();
    expect(wrongDomain("SolarEdge", "number")).toBeNull();
  });
});
