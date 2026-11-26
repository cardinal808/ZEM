import { describe, expect, it } from "vitest";

import { aircoLine, type Excluded } from "../src/airco";

const ex = (extra: Partial<Excluded> = {}): Excluded => ({
  active: true,
  power_w: 1800,
  excluded_w: 1800,
  mode: "heat",
  action: "heating",
  blocked_modes: ["heat"],
  has_climate: true,
  seconds_since_step: 100,
  mean_step_interval_s: 500,
  last_step_kwh: 0.25,
  quality: "ok",
  ...extra,
});

describe("airco line (SPEC-ui-airco §4)", () => {
  it("is empty when not set up or off", () => {
    expect(aircoLine(null, "nl", "nl")).toBeNull();
    expect(aircoLine(ex({ active: false, power_w: 0, action: "idle" }), "nl", "nl")).toBeNull();
    expect(aircoLine(ex({ active: false, power_w: 0, mode: "off", action: "off" }), "nl", "nl")).toBeNull();
  });

  it("shows the power while heating", () => {
    const line = aircoLine(ex(), "nl", "nl")!;
    expect(line.text).toBe("Airco 1,8 kW · niet uit de accu");
    expect(line.allowed).toBe(false);
    expect(line.icon).toBe("heat");
    expect(line.estimate).toBeNull();
    expect(aircoLine(ex(), "en", "en")!.text).toBe("Air conditioner 1.8 kW · not from the battery");
  });

  it("adds what is kept off the battery when that is less", () => {
    expect(aircoLine(ex({ excluded_w: 1100 }), "nl", "nl")!.text).toBe("Airco 1,8 kW · niet uit de accu (1,1 kW nu buiten de accu)");
    expect(aircoLine(ex({ excluded_w: 0 }), "nl", "nl")!.text).toBe("Airco 1,8 kW · niet uit de accu"); // charging from solar
  });

  it("marks an estimate when starting or fading", () => {
    expect(aircoLine(ex({ quality: "starting" }), "nl", "nl")!.estimate).toContain("0,25 kWh");
    expect(aircoLine(ex({ quality: "fading", power_w: 900 }), "nl", "nl")!.estimate).not.toBeNull();
  });

  it("says cooling may use the battery", () => {
    const line = aircoLine(ex({ active: false, power_w: 0, mode: "cool", action: "cooling" }), "nl", "nl")!;
    expect(line.text).toBe("Airco koelen · mag uit de accu");
    expect(line.allowed).toBe(true);
    expect(line.icon).toBe("cool");
  });
});
