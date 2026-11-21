# ZEM

**ZEM** is a Home Assistant integration (HACS) for Zendure home batteries. It controls one to three Zendure sets locally through the zenSDK API, keeps the grid meter at zero, and plans charging and discharging per quarter hour from dynamic prices and solar forecasts.

> **Status: in development (0.2, read-only).** ZEM reads your Zendure sets and shows their state in Home Assistant. It does **not** control the battery yet, so it can safely run next to an existing setup.

## Installation (test version)
1. In HACS: *Custom repositories* → add `https://github.com/cardinal808/ZEM` as type *Integration*, then install **ZEM**. Or copy `custom_components/zem` into your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Your set is usually found automatically (*Settings → Devices & services*). Otherwise add **ZEM** and enter the IP address of the set.
4. More sets (up to 3): open ZEM and choose *Add set*.

Requirements: HEMS turned off in the Zendure app; Home Assistant 2026.1 or newer.

## What you get in 0.2
- Per set: state of charge, battery power (+ charging, − delivering), charge and delivery power, solar power, status, capacity (from the packs), temperature, online and fault.
- Totals over all sets: state of charge (weighted by capacity), energy stored, capacity, power, sets online.
- Diagnostics download with serial numbers and IP addresses hidden.

[Nederlands](README.nl.md)

## Planned features
- Modes: Standby, Zero meter, Dynamic Forecasting, Fast charge, Fast discharge.
- One to three sets, with the grid demand distributed over the sets.
- Planner for today and tomorrow (dynamic prices, solar forecast, learned consumption).
- Efficiency measured per set, no manual input.
- Own panel in the Home Assistant sidebar.
- Shadow mode: ZEM calculates alongside an existing setup without controlling the battery.

## Origin
ZEM is a new implementation. It contains no code or text from other Zendure integrations or packages. Where other projects were consulted, only their behaviour was compared, after our own specification was written.

## License
MIT, see [LICENSE](LICENSE).
