<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/logo-dark.png">
    <img src="docs/logo.png" alt="ZEPHYR" width="280">
  </picture>
</p>

# ZEPHYR

*Zendure Energy Planning, Home Yield & Regulation*  
**Forecasting Tomorrow. Planning Today.**

**ZEPHYR** is a Home Assistant integration (HACS) for Zendure home batteries. It controls one to three Zendure sets locally through the zenSDK API, keeps the grid meter at zero, and plans charging and discharging per quarter hour from dynamic prices and solar forecasts.

> **Status: in development (0.5, live control in test).** By default ZEPHYR runs in shadow mode: it reads your Zendure sets and computes every second what it would do, without controlling the battery, so you can compare safely with your current system. With the switch **"ZEPHYR controls the battery"** (`switch.zephyr_control`) ZEPHYR really controls the battery in zero-meter mode. Switch off your current control first.

> **Upgrading from ZEM (0.3.x)?** The integration was renamed and its domain changed from `zem` to `zephyr`. Remove the ZEM integration and the old custom repository in HACS, add `https://github.com/cardinal808/ZEPHYR`, install ZEPHYR, restart Home Assistant and add it again. Entities are now `sensor.zephyr_…`.

## Installation (test version)
1. In HACS: *Custom repositories* → add `https://github.com/cardinal808/ZEPHYR` as type *Integration*, then install **ZEPHYR**. Or copy `custom_components/zephyr` into your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Your set is usually found automatically (*Settings → Devices & services*). Otherwise add **ZEPHYR** and enter the IP address of the set.
4. More sets (up to 3): open ZEPHYR and choose *Add set*.
5. Optionally choose a solar forecast (Solcast *forecast tomorrow*) and your solar production counter: ZEPHYR then keeps a daily record of forecast against production for the planner.
6. Open ZEPHYR → *Configure* and choose your P1 meter (suggested automatically): one net sensor, or the import and export sensors of the DSMR integration (recommended: these report every telegram). Shadow mode starts in the mode *Zero meter*.

Requirements: HEMS turned off in the Zendure app; Home Assistant 2026.1 or newer.

## What you get in 0.3
- Shadow mode: `sensor.zephyr_setpoint` (what ZEPHYR would ask of the battery, + charging, − delivering), `sensor.zephyr_action`, `sensor.zephyr_reason` (in plain language), `select.zephyr_mode`, `binary_sensor.zephyr_p1_ok`, and per set `sensor.zephyr_set_1_setpoint`. Nothing is sent to the battery. ZEPHYR computes with a virtual set that carries out its own commands, in place of the real set that your current system drives; the diagnostics compare grid import and export of both (`control.twin`).
- The decision log is in the diagnostics download.
- Per set: state of charge, battery power (+ charging, − delivering), charge and delivery power, solar power, status, capacity (from the packs), temperature, online and fault.
- Totals over all sets: state of charge (weighted by capacity), energy stored, capacity, power, sets online.
- Diagnostics download with serial numbers and IP addresses hidden.

[Nederlands](README.nl.md)

## Live control (0.5, test phase)
- **Switch** `switch.zephyr_control`, off by default. It only switches on when the P1 reports and the set is online without a fault; ZEPHYR continues from what the set does now (no dip). Off: 0 W once, then your current system takes over again. After a restart the switch stays off (option *Live control off after a restart*, on by default during the test phase).
- **Deliver only in the most expensive hours** (optional): choose a Nord Pool price sensor in the options. ZEPHYR then delivers only in the N most expensive hours of the day (default 4) and otherwise only charges from solar. **Reserve** (default 20 %): below it ZEPHYR charges in the cheapest hours before the next expensive block; in the expensive hours the reserve may be used.
- **Safety:** if another system controls the set, ZEPHYR stops writing and says so. Too many flash writes: standby becomes 0 W in RAM. Home Assistant stops: all sets 0 W first.
- **Write test:** action `zephyr.test_command` (for example `power: -300` = deliver 300 W for 60 s, then standby), only in shadow mode with the mode Standby.
- **Test dashboard:** [`dashboards/zephyr-test.yaml`](dashboards/zephyr-test.yaml) with the switch, the mode, write-test buttons, a graph and the counters. Add it: *Settings → Dashboards → Add dashboard*, open it, ⋮ → *Edit dashboard* → ⋮ → *Raw configuration editor*, and paste the file. Counters missing? Enable `sensor.zephyr_set_1_write_count` and `…_switch_count` (off by default in installations from before 0.5.2).

## Cost log (0.6)
- Per quarter: import, export, battery charged/delivered, solar and the Nord Pool price, with the costs **actual**, **without battery** and **without battery and solar**. Also in shadow mode (then: the costs of your current setup).
- Enter your **own tariffs** in the options: energy tax (Netherlands 2026: €0.0916), supplier margins for import and export, VAT and optionally the fixed costs per month. A list of suppliers follows. Net metering (until the end of 2026) is included and settled per year.
- Optionally the meter's kWh counters (tariff 1 and 2) for import and export; without them ZEPHYR integrates the P1 power. With a solar counter also the savings from solar.
- Entities: `sensor.zephyr_costs_today|month|year` and `sensor.zephyr_savings_today|month|year` (€), with the breakdown as attributes. Action `zephyr.export_costs` writes the quarters as CSV to `config/zephyr/`.

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
