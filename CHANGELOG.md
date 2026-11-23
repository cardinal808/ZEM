# Changelog

## Unreleased

### 0.4.7
- Product names are recognised with spaces, dashes or underscores and in any case (for example "SolarFlow800 Plus" or "solarflow-800-plus"), B23.

### 0.4.6
- **Solar forecast next to the real production** (B31, B32). Two optional sensors in the options:
  - the forecast for tomorrow with half-hour detail (Solcast `…_forecast_tomorrow`);
  - the solar production counter in kWh.
- Every evening at 23:00 ZEPHYR stores tomorrow's forecast (mid, low and high estimate per half hour) and every hour the counter. Kept for 400 days in ZEPHYR's own storage.
- The diagnostics show the last 60 days (forecast against production) and the raw data of the last 3 days.
- This is the yardstick for the planner's forecast correction and uncertainty (M5). The data cannot be recovered later, so collection starts now.
- P1 options: on a single-phase connection whose meter only offers per-phase sensors (`…_power_consumed_phase_1` / `…_power_produced_phase_1`), that pair is suggested. Not when other phases exist.

### 0.4.5
- Step filter: a rise is measured from the lowest P1 value of the last 2.5 s (`step_window`), not only from the previous sample. A meter sample can fall halfway a rise (seen live: −21, 417, 2263 W); the filter then held at 417 W instead of at the level before the peak.

### 0.4.4
- **P1 filters before the controller** (B20, B22), both on time so a slow meter is not filtered more:
  - *Noise filter:* within 75 W of the mean of the last 3 s, the controller gets that mean. Replay of recorded days: 17–32 % fewer writes, same accuracy and grid energy.
  - *Step filter:* a sudden rise of more than 800 W (above max(previous value, 0)) is held back for at most 10 s; a drop is never held. Short peaks such as a boiling-water tap heating its tank (every ~34 min, ~2 kW for 4–10 s) are no longer chased. A longer load is followed after 10 s (scenario B2 now allows step hold + 8 s).
  - The number of held steps is in the diagnostics (`p1_filter`).
- Replay tool: `--battery` for one signed battery sensor and `--compare-filters` to compare filter settings on a recording.

### 0.4.3
- P1 options: when the DSMR import and export sensors are found and no P1 sensor was chosen before, *Import and export* is the default. When only the two sensors are filled in, they are used even if the choice was left on *One net sensor*.

### 0.4.2
- **P1 as two sensors** (B30): in the options choose either one net sensor or the import and export sensors as the DSMR integration provides them (kW or W). ZEPHYR then sees every meter telegram, also when the value stays the same, instead of relying on a combined template sensor that only reports changes. The DSMR pair is suggested automatically. Both sensors of one telegram are combined after 0.2 s, so ZEPHYR never sees half a telegram.
- **Repair notice when no P1 meter is chosen**, for example right after a fresh install. It disappears as soon as a P1 source is set.

### 0.4.1
- Counters per set for writes and relay switches, over the last hour and 24 hours: power commands (RAM), standby and SOC limits (flash), skipped refreshes, and relay switches seen in `acStatus`. In the diagnostics and as two diagnostic sensors per set (*Writes (24 h)*, *Relay switches (24 h)*, off by default). In shadow mode the writes are what ZEPHYR would send; relay switches are what the set really does.
- The refresh every 60 s is skipped when the set already reports exactly the same command (same direction and limit, `smartMode` 1). Shadow data showed ~35 of 108 would-be writes in an hour were such refreshes at a constant 2400 W.

### 0.4.0
- **New name: ZEPHYR** (Zendure Energy Planning, Home Yield & Regulation), was ZEM. The repository is now `cardinal808/ZEPHYR` (the old address redirects).
- **Breaking:** the integration domain is now `zephyr` (was `zem`). Entities are renamed from `sensor.zem_…` to `sensor.zephyr_…`. To upgrade: remove the ZEM integration and the old custom repository in HACS, add `https://github.com/cardinal808/ZEPHYR`, install ZEPHYR, restart Home Assistant and add ZEPHYR again. Shadow mode only, so nothing is lost apart from history.

### 0.3.9
- `faultLevel` alone no longer counts as a fault; only `is_error` does. A 2400 AC+ at 100 % reported faultLevel 2 without an error, and ZEM then took the set out of control ("No set available"). (Was meant for 0.3.8 but missed the merge.)
- A silent P1 sensor with a balanced grid is not stale right away. Many P1 sensors only report changes; at exactly 0 W they stay silent, and ZEM went to 0 W after 10 s (seen several times per minute in shadow mode). Within the dead zone ZEM now holds the setpoint for up to 30 s; with an unbalanced grid the 10 s limit stays.

### 0.3.8
- `faultLevel` alone no longer counts as a fault; only `is_error` does. A 2400 AC+ at 100 % reported faultLevel 2 without an error, and ZEM then took the set out of control ("No set available"), so it would not have delivered in the evening. The value stays visible in the diagnostics.
- Battery recognition below was built as 0.3.4 but merged late. Versions 0.3.5–0.3.7 were merged without raising the version number in `manifest.json` (it stayed 0.3.3); a test now checks that the manifest matches this changelog.
- Batteries recognised by serial number: AB1000, AB1000S, AB2000(S/X), AB3000X, AB3000L and the built-in batteries of the 2400 Pro, 2400 AC+, 4000 AC+ and AIO 2400 (facts from the official Zendure integration, MIT).
- All sets with the local zenSDK API in the model table (800, 800 Plus, 800 Pro, 1600 AC+, 2400 AC, 2400 AC+, 2400 Pro, 4000 AC+); model names are matched case-insensitively.
- Unknown battery: repair notice in Home Assistant, capacity by hand via *Reconfigure* on the set, and type and serial prefix (not the full serial) in the diagnostics.

### 0.3.7
- The reason stays steady between two decisions. With a full battery and solar surplus it alternated every second between "Battery full" and "Demand too small" (seen in shadow mode).

### 0.3.6
- Slow meters (DSMR 4, a new value about every 10 s) are supported: "P1 too slow" now only above 25 s, and the 0 W / standby safety times scale with the meter (at least 2.5 and 6 intervals). Before, a DSMR 4 meter would regularly have been seen as too slow or stale.
- Slow meters use full correction (gain 1.0): the controller already waits for a new P1 value after the set has settled. Simulation with a 10 s meter (±1.5 s): 95 % within ±50 W; 15 s: 94 %; 20 s: 87 %.
- At start-up, until the meter's interval is known, only a lost P1 (60 s) counts.
- Simulator: meter jitter and stepping every second like Home Assistant.

### 0.3.5
- P1 interval is measured between new values, not between reports. Some integrations re-report the same value much more often than the meter sends one (seen: every 0.4 s for a meter with a new value every 10 s); ZEM then treated a slow meter as fast.
- The controller decides once per new P1 value. Repeats of the same value in between no longer lead to new setpoints (in shadow mode this gave a write every 3 s).

### 0.3.3
- SolarFlow 2400 AC+ recognised: model name, limits and the 2.4 kWh built-in battery (before, its capacity was too low by 2.4 kWh). Thanks to a tester for the diagnostics.

### 0.3.2
- Minimum and maximum state of charge in the options (Configure). Defaults stay 10 % and 95 %.

### 0.3.1
- After a (re)start, Zero meter waits up to 60 s for the first P1 report and leaves the sets alone. Before, it would have sent standby immediately (seen in the shadow-mode diagnostics).

### M3 – Controller and shadow mode (0.3.0)
- `core/controller.py`: zero-meter controller in position form. It starts from its own last command (the report lags), waits until the set has settled (start-up 2.5 s, ramp 330 W/s, report lag), then corrects the whole grid error. Separate grid targets for delivering (+15 W) and charging from solar (−30 W), dead zone, minimum power with start/stop hysteresis, 10 s delay before switching between charging and delivering, slow P1 meters handled.
- `core/engine.py`: modes Standby, Zero meter, Fast charge, Fast discharge; P1 freshness (0 W after 10 s, standby after 60 s); full/empty with hysteresis, temperature limits, discharge block; recharge below the minimum; SOC limits aligned once; write rules (only on change, 2 s apart, acMode only on a change of direction, 60 s refresh, standby after 5 min); reasons in English and Dutch.
- `sim/`: closed-loop simulator (set model with start-up, ramp and report lag) and scenarios B1–B12 as tests.
- `tools/replay_opname.py`: replays a recorded day (Home Assistant history CSV) through the simulator and compares with the recorded system. On two recorded evenings: within ±50 W 93–95 % of the time (recorded system 75–78 %).
- Home Assistant: P1 meter in the options (suggested automatically), mode select, setpoint, grid power, current action, reason, P1 status, would-be setpoint per set, decision log in diagnostics. **Shadow mode: nothing is sent to the sets.**
- Default gain 1.0 instead of 0.7/0.9 (SPEC-basis): the controller now waits for the set, so it can correct fully; this was clearly better in simulation.

### M2 – Home Assistant integration, read-only (0.2.0)
- Config flow: add a set by IP address or via discovery (`_zendure._tcp`); one ZEM installation with up to 3 sets as subentries; a known set that gets a new IP address is followed automatically.
- One reader per set (every 5 s). A set goes offline after 3 failed reads and comes back after 2 good ones; one unreachable set never blocks the others or the start of ZEM.
- A different serial number at a set's address is refused and reported as a repair issue.
- Entities per set and for the installation (English entity ids, Dutch and English names). Totals follow SPEC-meerdere-sets: capacity-weighted SOC, offline sets keep counting for energy for 5 minutes.
- Diagnostics with serial numbers and IP addresses hidden (only the first letter of pack serials, which identifies the pack type).
- Nothing is written to the sets.
- CI: core tests without Home Assistant, integration tests with Home Assistant, strict mypy, hassfest.

### M1 – Core: reading the local zenSDK API
- `core/zensdk.py`: interpret `/properties/report` (scales: 0.1 K temperatures, 0.01 V, 0.1 A with two's complement, SOC limits in 0.1 %), derive status (fault, calibration, bypass, full/empty, charging/delivering, standby), instantaneous conversion efficiency, and build commands (power in RAM, standby and SOC limits in flash, grid export). Only whitelisted properties can be written; requests stay below 512 bytes.
- `core/device_table.py`: known models and packs (SolarFlow 2400 Pro built-in battery, AB3000L), matched on model + packType + serial prefix; temperature limits with a safety margin.
- `core/client.py`: async HTTP client for one set with timeouts and clear errors.
- Tests with real reports from a SolarFlow 2400 Pro (serial numbers replaced): standby, charging 2.4 kW, delivering 0.76 kW and 2.4 kW.
- CI: ruff, mypy (strict on the core), pytest.

Sign convention: battery power + = charging, − = delivering; grid + = import.
