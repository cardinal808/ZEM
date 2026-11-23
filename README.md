# ZEPHYR

*Zendure Energy Planning, Home Yield & Regulation*  
**Forecasting Tomorrow. Planning Today.**

**ZEPHYR** is a Home Assistant integration (HACS) for Zendure home batteries. It controls one to three Zendure sets locally through the zenSDK API, keeps the grid meter at zero, and plans charging and discharging per quarter hour from dynamic prices and solar forecasts.

> **Status: in development (0.4, shadow mode).** ZEPHYR reads your Zendure sets and calculates, second by second, what it would do to keep your grid meter at zero, but it does **not** control the battery yet. It can safely run next to an existing setup, so you can compare.

> **Upgrading from ZEM (0.3.x)?** The integration was renamed and its domain changed from `zem` to `zephyr`. Remove the ZEM integration and the old custom repository in HACS, add `https://github.com/cardinal808/ZEPHYR`, install ZEPHYR, restart Home Assistant and add it again. Entities are now `sensor.zephyr_…`.

## Installation (test version)
1. In HACS: *Custom repositories* → add `https://github.com/cardinal808/ZEPHYR` as type *Integration*, then install **ZEPHYR**. Or copy `custom_components/zephyr` into your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Your set is usually found automatically (*Settings → Devices & services*). Otherwise add **ZEPHYR** and enter the IP address of the set.
4. More sets (up to 3): open ZEPHYR and choose *Add set*.
5. Open ZEPHYR → *Configure* and choose your P1 meter (suggested automatically): one net sensor, or the import and export sensors of the DSMR integration (recommended: these report every telegram). Shadow mode starts in the mode *Zero meter*.

Requirements: HEMS turned off in the Zendure app; Home Assistant 2026.1 or newer.

## What you get in 0.3
- Shadow mode: `sensor.zephyr_setpoint` (what ZEPHYR would ask of the battery, + charging, − delivering), `sensor.zephyr_action`, `sensor.zephyr_reason` (in plain language), `select.zephyr_mode`, `binary_sensor.zephyr_p1_ok`, and per set `sensor.zephyr_set_1_setpoint`. Nothing is sent to the battery.
- The decision log is in the diagnostics download.
- Per set: state of charge, battery power (+ charging, − delivering), charge and delivery power, solar power, status, capacity (from the packs), temperature, online and fault.
- Totals over all sets: state of charge (weighted by capacity), energy stored, capacity, power, sets online.
- Diagnostics download with serial numbers and IP addresses hidden.

[Nederlands](README.nl.md)

## Supported sets and batteries
- Sets with the local zenSDK API: SolarFlow 800, 800 Plus, 800 Pro, 1600 AC+, 2400 AC, 2400 AC+, 2400 Pro and 4000 AC+. Tested so far: 2400 Pro and 2400 AC+. Turn HEMS off in the Zendure app.
- Batteries are recognised by their serial number: AB1000, AB1000S, AB2000(S/X), AB3000X, AB3000L and the built-in batteries of the 2400 Pro, 2400 AC+, 4000 AC+ and AIO 2400.
- Newer models (800 AC+, 800 Pro 2, 3000/4000 Mix) and batteries (AB2000L, AB3000S, B6400) probably work for reading, but are not in the tables yet; a diagnostics download lets us add them.
- **Not supported** (no local zenSDK API): SolarFlow Hub 1200/2000, Hyper 2000, Ace 1500, AIO 2400 and SuperBase. Only the built-in battery of an AIO 2400 connected to a SolarFlow as an extra pack is recognised.
- Battery not recognised? Home Assistant shows a repair notice. Enter the capacity via ZEPHYR → the set → *Reconfigure*, and please open an issue with the line from the notice so we can add it.

## Planned features
- Modes: Standby, Zero meter, Dynamic Forecasting, Fast charge, Fast discharge.
- One to three sets, with the grid demand distributed over the sets.
- Planner for today and tomorrow (dynamic prices, solar forecast, learned consumption).
- Efficiency measured per set, no manual input.
- Own panel in the Home Assistant sidebar.
- Shadow mode: ZEPHYR calculates alongside an existing setup without controlling the battery.

## Origin
ZEPHYR is a new implementation. It contains no code or text from other Zendure integrations or packages. Where other projects were consulted, only their behaviour was compared, after our own specification was written.

## License
MIT, see [LICENSE](LICENSE).
