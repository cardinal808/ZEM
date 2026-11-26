import { describe, expect, it } from "vitest";

import en from "../src/locales/en.json";
import nl from "../src/locales/nl.json";
import { choiceLabel, entityChoices, parseNumber, resolveEntity, sameValue, stepInterval, toggleChoice } from "../src/settings-edit";

describe("settings edit", () => {
  it("reads numbers in both notations", () => {
    expect(parseNumber("0,021", "nl")).toBe(0.021);
    expect(parseNumber(" 15 ", "nl")).toBe(15);
    expect(parseNumber("-0,5", "nl")).toBe(-0.5);
    expect(parseNumber("1.250,5", "nl")).toBe(1250.5);
    expect(parseNumber("0.021", "en")).toBe(0.021);
    expect(parseNumber("1,250.5", "en")).toBe(1250.5);
    expect(parseNumber("", "nl")).toBeNull();
    expect(parseNumber("veel", "nl")).toBeNull();
    expect(parseNumber("1,2,3", "nl")).toBeNull();
  });

  it("lists matching entities and resolves what was typed", () => {
    const states = {
      "sensor.b": { attributes: { device_class: "power", friendly_name: "P1 vermogen" } },
      "sensor.a": { attributes: { device_class: "energy", friendly_name: "Airco teller" } },
      "climate.living": { attributes: { friendly_name: "Woonkamer" } },
      "sensor.c": { attributes: { device_class: "power" } },
    };
    const power = entityChoices(states, "sensor", "power");
    expect(power.map((c) => c.id)).toEqual(["sensor.b", "sensor.c"]);
    expect(entityChoices(states, "climate", null).map((c) => c.id)).toEqual(["climate.living"]);
    expect(choiceLabel(power[0])).toBe("P1 vermogen (sensor.b)");
    expect(choiceLabel(power[1])).toBe("sensor.c");
    expect(resolveEntity("sensor.c", power)).toBe("sensor.c");
    expect(resolveEntity("P1 vermogen (sensor.b)", power)).toBe("sensor.b");
    expect(resolveEntity("p1 vermogen", power)).toBe("sensor.b");
    expect(resolveEntity("sensor.a", power)).toBeNull();
    expect(resolveEntity("", power)).toBeNull();
  });

  it("compares and toggles", () => {
    expect(sameValue(["heat"], ["heat"])).toBe(true);
    expect(sameValue(["heat"], ["heat", "cool"])).toBe(false);
    expect(sameValue(undefined, null)).toBe(true);
    expect(sameValue(10, 10)).toBe(true);
    const options = ["heat", "cool", "dry"];
    expect(toggleChoice(["heat"], "dry", options)).toEqual(["heat", "dry"]);
    expect(toggleChoice(["dry", "heat"], "heat", options)).toEqual(["dry"]);
  });

  it("writes the counter rhythm", () => {
    expect(stepInterval(510, "nl")).toBe("8,5 min");
    expect(stepInterval(40, "nl")).toBe("40 s");
  });

  it("has a text for every error of zephyr/settings/set", () => {
    const codes = ["choose_one", "entity_missing", "excluded_needs_counter", "not_a_bool", "not_a_number", "not_an_entity", "off_step", "out_of_range", "p1_missing", "p1_pair_incomplete", "p1_pair_same", "required", "unknown_choice", "unknown_key"];
    for (const code of [...codes, "failed", "range"]) {
      expect(nl.settings.errors).toHaveProperty(code);
      expect(en.settings.errors).toHaveProperty(code);
    }
  });
});
