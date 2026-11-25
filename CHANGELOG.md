# Changelog

## Unreleased

### 0.7.2 — fix: a slow start was taken for a second controller
- **Seen 26-11 (0.6.2):** with the previous system off, ZEPHYR went live three times and was back in shadow mode within 9 s each time ("another system controls the set"), before the set delivered anything.
- **Cause:** the set was in standby. After ZEPHYR's command (730 W) it kept reporting its old limits (output 0 W, `smartMode` 0) until the relay had closed, which takes 9–17 s from 0 W. The check for a second controller looked at the reports 6 s after a write and counted two such reports as someone else writing; the same reports were also counted as "smartMode reverted".
- **Fix:** a report that still shows the limits the set had when ZEPHYR wrote counts as "not applied yet" for up to 20 s; only a different value, or the old value after 20 s, counts as a second controller. The smartMode check waits the same way.
- Tests: `test_slow_start_is_not_a_second_controller` (fails on 0.7.0) and `test_set_that_never_applies_counts_as_second_controller`.
### 0.7.1 — planner: wear cost per kWh (PU3), backtest with wear
- **`PlannerSettings.wear_cost`** (€ per kWh delivered by the battery, default 0): weighs battery wear in the choice, not in the grid costs, so the planner does not cycle the battery for a few cents (SPEC-planner §12.3, PU3). Not yet in Home Assistant.
- **Backtest:** option `--wear` (default €0.03/kWh); runs the planner and planner + X with and without wear and shows the cost including wear for every strategy.
- Measured on 9.5 months of own data (perfect knowledge): with wear €0.03 or €0.06 in the choice, the cost including wear is lower in both years (2026 and 2027 rules) than without, for the planner and for planner + X, at a slightly higher grid cost. Details in the project (BACKTEST-1).

### 0.7.0 — M5, step 3: planner core and backtest (no change in Home Assistant yet)
- **Planner core** `core/planner.py` (SPEC-planner §1, §3): per price slot one action — charge from the grid (L), hold (H), deliver (N) or, when allowed, export at full power (X, off by default, B12) — with the lowest total cost over the horizon. Dynamic programming backwards over the energy in the battery (40 steps, linear interpolation) and the previous action (switching costs €0.02 per charge start, €0.005 per hold start), then a forward pass from the real energy. End value: the cheapest price in the horizon × discharge efficiency. Solar surplus goes into the battery first; with a negative export price surplus solar earns nothing and X is not used. Load margin steers the choice only.
- Tests: within €0.005 of brute force on random scenarios (with and without X), cheap charging / expensive delivering, no charging when the spread does not cover the losses, holding for the evening peak, 192 quarters in well under a second.
- **Backtest** `tools/backtest.py` (§12.2): real quarter prices, P1 per hour, a solar counter and (optional) battery counters; house consumption derived per hour; strategies no battery, zero meter, planner, planner + X, with 2026 rules (net metering) and 2027 rules, using the tariff table (default Zonneplan). Price horizon as in practice (tomorrow from 13:00, before that today's pattern). Data stays private (B18). Smoke test on synthetic files.
- Not yet: the planner in Home Assistant (mode Dynamic Forecasting), consumption profile and solar forecast (perfect knowledge in the backtest for now), efficiency per power band, calibration penalty, PU1–PU6.

### 0.6.3 — tuning: aim for 5 W import while delivering (was 15 W)
- **Seen in the live test of 25-11 (0.5.4) next to the previous system:** ZEPHYR averaged +13 W on the grid while delivering; the previous system ±0 W (alternating import and export). Within the dead zone of ±25 W around the target, ZEPHYR does not correct, so with a target of 15 W the grid stayed between −10 and +40 W, mostly on the import side.
- **Change:** `target_grid_deliver` 15 → 5 W. With net metering (saldering) a little export costs nothing; smaller than 5 W makes little sense with commands in steps of 30 W.
- Simulator (slow-starting set, varying load with meter noise, 5 × 30 min): average grid +20 → +10 W, import 12.3 → 8.7 Wh, export 2.6 → 3.9 Wh, the same number of writes, within ±50 W 96 → 97 %.

### 0.6.2 — fix: counters emptied when switching live/shadow
- **Seen in the third live test (25-11, 0.5.4):** 33 successful live writes, but the counter showed 5 RAM writes after switching back to shadow mode.
- **Cause:** switching between live and shadow mode started the per-set bookkeeping over, and the write and relay counters with it. The flash safety net (PLAN-M4b §2.7) lost its history too, so after a switch it could allow more flash writes than 10 per hour / 50 per 24 hours.
- **Fix:** the counters (RAM, flash per cause, skipped, relay) now survive the switch; only the write bookkeeping starts over. The 0 W written when switching off (or when HA stops) now counts as a RAM write.
- Tests: `test_counters_survive_switching_live_and_back` (core) and `test_counters_keep_live_writes_after_switching_off` (HA); both fail on 0.5.4.
### 0.6.1 — M5, step 2: tariff table (B28)
- **Choose your energy supplier** in the options instead of entering tariffs: ZEPHYR then takes the supplier's margins, solar bonus and VAT on export after net metering, plus the country's energy tax and VAT per date, from its **tariff table** (`custom_components/zephyr/data/tariffs.json`). "Own tariffs" stays possible; the fixed costs per month apply in both cases.
- **Only checked amounts:** a supplier is listed once a user of that supplier has checked the amounts against an invoice (`verified`). The first entry is Zonneplan (checked against an invoice on 25-11-2026): margin €0.02 incl. VAT on import and export, 10 % solar bonus.
- **Kept up to date:** the table ships with every version; ZEPHYR fetches the newest one from GitHub once a month, when the supplier choice changes, and at startup when due (at most one attempt a day). Without a connection: the newest of the stored and the shipped table. No scraping of supplier websites.
- **Maintained with pull requests:** a format check runs in CI (`tests/core/test_tariff_table.py`): dates ascending, amounts in range, a link to the supplier's tariff page and the date it was checked.
- The tariffs in use and their source (supplier, period, date checked, table date) are in the cost sensors' attributes and in the diagnostics (`costs.tariffs`: origin of the table, last fetch, last error).

### 0.6.0 — M5, step 1: cost log with own tariffs (B38)
- **Cost log per quarter:** grid import and export, battery charged and delivered (AC), solar and the Nord Pool price at the start of the quarter. Costs in three situations: **actual**, **without battery** (the battery's exchange removed, netted per quarter) and **without battery and solar** (needs the solar counter). Savings split into solar (direct / exported) and battery, the battery part again into **solar via the battery** (two pools, solar and grid, conversion losses included) and the **price difference** (trade). Also in shadow mode: then it shows the costs of the current system.
- **Own tariffs** in the options: energy tax (default €0.09161, NL 2026), supplier margin on import and on export, VAT (21 %), fixed costs per month (optional, shown next to the totals). All-in import = (market + margin + energy tax) × (1 + VAT). **Net metering** for quarters before 1-1-2027: export at market incl. VAT plus energy tax incl. VAT; export above the year's import loses that part (yearly correction in the year total). **Solar bonus** (optional, %): extra over (market + export margin) for export between sunrise and sunset when that amount is positive, as Zonneplan's Zonnebonus (10 %); not part of net metering. The supplier table (B28) follows.
- **Energy:** the P1 power integrated every second (a P1 older than 10 s is a gap), or optionally the meter's kWh counters (tariff 1 + 2, suggested for DSMR), which then win. A quarter is complete when ≥ 95 % of it was measured.
- **Entities** `sensor.zephyr_costs_today|month|year` and `sensor.zephyr_savings_today|month|year` (€, `state_class: total`, `last_reset`), with the breakdown, kWh, effective price per kWh, mean import price and quarters without price or incomplete as attributes.
- **Action `zephyr.export_costs`** (start, end; default this month): all stored quarters as CSV in `config/zephyr/`; returns the path and the number of rows.
- Storage: quarters per month (24 months), day totals without limit; written at unload/reload too. Diagnostics: tariffs, pools, today, this month, the last 8 quarters. Test dashboard: a cost card.
- Specification: `SPEC-kosten` (replaces SPEC-planner §8). Plan fields (planned action and cost) are stored empty until the planner.

### 0.5.4 — fix: live control over- and undershot
- **Seen in the second live test (25-11, 0.5.3):** the start was right (no doubling), but then 510 → 940 W (export ~440 W), back to 390 W, 140 W (import ~340 W), and so on.
- **Cause:** 0.5.3 compared the set's report with the P1 value of 1.5 s earlier, assuming the report always lags that much. Here the report was nearly fresh, so a new battery value was set against an old P1 value from before the set had started.
- **Fix:** no fixed shift any more. After each command live control waits until the set has reached it (as in 0.5.3) **and then 2 s longer** (`after_reach`), so P1 and the report show the same state, whatever the report lag. Clearly-worse cases (export) still react at once.
- Simulator, varying load: with a report lag of 0.2 s 19 writes instead of 37, no stop to 0 W (was 2), 76 % within ±50 W (was 62 %); the same with lags of 1.5 and 3 s. New scenario `test_fresh_reports_do_not_cause_overshoot` (fails on 0.5.3).

### 0.5.3 — fix: live control doubled every start
- **Seen in the first live test (25-11):** house ~530 W, ZEPHYR commanded 520 W, then 1030 W, then 1290 W; the set exported ~700 W, ZEPHYR went to 0 W, the relay opened and the cycle started again about every 25 s.
- **Cause:** live control trusted its last command once the settle time (~5.6 s) had passed. A set starting from 0 W with the relay open needs 9–11 s before power shows in the report, so P1 still showed the full demand and ZEPHYR added it a second time. When stopping, the report still showed the old power while P1 already showed the export, so ZEPHYR stopped completely.
- **Fix:** live control now works from the **measured** power of the set, with P1 taken 1.5 s earlier so both describe the same moment (as the twin does), and after a command it **waits until the set has reached it** (or 15 s, `reach_timeout`) before correcting again, unless things get clearly worse (export).
- Simulator: a set model with a slow start after the relay opened (`relay_off_on_zero`); scenarios `tests/scenarios/test_live_start.py` (the first fails without the fix). With a realistic slow set the simulator shows no doubling and no on/off cycle; accuracy and grid energy are as before, with fewer writes.

### 0.5.2 — M4b, step 3: test dashboard
- **Test dashboard** `dashboards/zephyr-test.yaml` (standard cards only): the switch "ZEPHYR controls the battery", the mode, write-test buttons (deliver 300 W, charge 300 W, stop; shown only in Standby with the switch off), a graph of grid, battery and ZEPHYR's target, the current state and the counters. How to add it: see the README.
- **`binary_sensor.zephyr_expensive_hour`**: on in one of the most expensive hours; attributes: price now, next expensive hour, charging for the reserve now and in which slots. Unavailable without a price sensor.
- The write and relay counters per set are now enabled by default (new installations), with the flash writes per cause and `flash_paused` as attributes.
- README: live control and the test dashboard.

### 0.5.1 — M4b, step 2: expensive hours, reserve, safety
- **Deliver only in the most expensive hours** (zero-meter control, optional). Choose a Nord Pool price sensor in the options (the custom integration with `raw_today` / `raw_tomorrow`; suggested automatically). ZEPHYR then delivers only in the N most expensive hours of the day (default 4; quarter-hour prices count as N × 4 quarters), optionally only above a minimum price. Outside those hours the battery stays at 0 W in RAM and charges from solar as usual. Without prices: no delivering, and the reason says so. Without a price sensor nothing changes.
- **Reserve** (default 20 %, soft like the buffer of B37): below the reserve ZEPHYR charges from the grid in the cheapest hours before the next expensive block, just enough to reach it. In the expensive hours the reserve may be used down to the minimum SOC; it never stops delivering. 0 = off.
- **A second controller is detected**: while live, if the set twice in 5 minutes reports limits ZEPHYR did not write, ZEPHYR stops writing, switches back to shadow mode and raises a repair notice.
- **Flash safety net**: more than 10 flash writes per set in an hour (or 50 in 24 hours) and standby becomes 0 W in RAM until the count drops. Flash writes per cause (standby, SOC limits, write test) and `flash_paused` in the diagnostics.
- **smartMode check**: reports with `smartMode` 0 while ZEPHYR's last command was in RAM are counted (`control.live.writes.*.smartmode_reverted_24h`).
- Diagnostics: `control.price` with the decision (expensive now, next expensive hour, reserve charging slots).

### 0.5.0 — M4b, step 1: live control
- **`switch.zephyr_control` ("ZEPHYR controls the battery")**, off by default. Switching it on is refused (with the reason) when the P1 is not reporting, a set is offline, reports an error or a different serial number, or a write test runs. Switching it off writes 0 W once (RAM) and then nothing more, so the current system can take over.
- **Taking over without a dip** (B35): going live, ZEPHYR continues from the power the set delivers or charges now, not from 0 W.
- **Writer**: per set one request at a time; a newer command replaces one that waits; a failed write is not retried (the next step sends the current setpoint). Successful and failed writes, the last error and the duration are in the diagnostics (`control.live.writes`).
- **After a restart** (test phase, option *Live control off after a restart*, on by default): the switch stays off and a repair notice says so. With the option off, the switch comes back as it was.
- **Home Assistant stops, or ZEPHYR is reloaded while live**: all sets get 0 W first.
- **Write test**: action `zephyr.test_command` (power in W, + charging / − delivering; duration ≤ 60 s). Only in shadow mode with the mode Standby; writes the command in RAM, then standby (flash). The reports during the test are in the diagnostics (`control.live.test`).
- Not yet in this step (PLAN-M4b): detecting a second controlling system, the flash safety net, "only the N most expensive hours" with a reserve, and the test dashboard.

### 0.4.12
- **Shadow mode with a virtual set (twin).** Until now ZEPHYR computed from the real set's power, which the current system decides. Its loop never closed: every step corrected an error it did not cause, so the shadow counters said little about live control (seen at a tester: ~400 writes per hour). Now a virtual set carries out ZEPHYR's commands (start-up, ramp and report lag as measured) and ZEPHYR works with a virtual grid: measured P1 − real set + twin. The house and the solar panels stay real.
  - The real set's power is known from a report 1–3 s old, so P1 and the twin are taken `twin_delay` (1.5 s) earlier to match it. Without that, every change by the other system showed as a short spike that ZEPHYR chased.
  - Simulation, half an hour with noise, a kettle and a cloud, another controller driving the set: 86–110 shadow writes against 98 for ZEPHYR live, the same direction swaps, grid energy within a few Wh. With a grid charge by the other system the twin still charges only from solar, as live.
  - Replay of the tester's decision log (14 min): 28 writes and no direction swap, against 46 when following the real set.
  - Diagnostics: `control.twin` with grid import and export since the start, measured (current system) and virtual (ZEPHYR), and the real and virtual battery power. The decision log has `p1` and `battery` of the twin next to `p1_measured` and `battery_real`.
  - The relay counter now counts the twin's direction swaps and standby: what ZEPHYR would switch, not what the current system switches.
- **No direction swap for a small demand** (`reverse_min_power` 250 W, `reverse_window` 120 s). A set that was charging or delivering in the last 2 minutes only swaps for at least 250 W; below that it idles at 0 W. Seen in shadow mode: charging ~1.9 kW from solar, a 2.1 kW load for ~40 s. ZEPHYR stopped the charging (right), then delivered 110–190 W for 20 s and swapped back (two relay switches for ~1 Wh, and 16 s of exported solar on the way back). Now the charging stops and resumes at once. After 2 minutes idle the normal minimum of 100 W holds again (evening: delivering after a day of charging).
- **Swapping direction takes `switch_delay`, not longer.** Two things restarted the 10 s wait one sample after it began: the start hysteresis (two samples above `min_power`) and the step filter, which held the rise of the grid caused by ZEPHYR's own stop of the charging. Simulation: delivering 21 s after a large load instead of 11 s. The step filter now also lets the rise through while the last direction was charging; a short peak is still not delivered for, because the swap waits `switch_delay`.
- **Minimum change per power command** (`min_command_step` 30 W, was 20 W or 5 %). Changes of 10–20 W wait for the 60 s refresh, which now sends the latest setpoint. In live control the dead zone already keeps steps at ≥ 30 W; in shadow mode this removes the 10 W writes on meter noise (seen: −180, −170, −180, −190 W within 10 s), so the shadow counters come closer to what live control would write.

### 0.4.11
- ZEPHYR logo and icon. From Home Assistant 2026.3 they show on the integrations page and in HACS (light and dark variants, in `brand/`). Also at the top of the README.

### 0.4.10
- The refresh after 60 s is also skipped when the set reports a limit within 10 W of ZEPHYR's setpoint. In shadow mode the current system writes exact values (such as 296 W) while ZEPHYR rounds to 10 W; that caused a "write" every minute (seen at a tester: about 60 of 68 writes per hour).

### 0.4.9
- Shadow mode: when the grid is in balance, ZEPHYR's setpoint follows what the set really does (decided by the current system) and counts no write. Before, the setpoint of an earlier step stayed visible (seen at a tester: −410 W while the set delivered 150 W with the grid at +25 W). Live control is unchanged.
- Relay switches: sets that do not report `acStatus` (SolarFlow 2400 AC+) show *unknown* instead of 0, with the attribute `relay_reported: false`.

### 0.4.8
- Step filter only while delivering or idle. While the battery charges from solar, a rise of the grid power (a cloud over the panels or a load switching on) now lowers the charging at once. Before, the rise was held for up to 10 s and the charge setpoint could even go up, charging from the grid (seen in shadow mode at noon: +2.2 kW import with the charge setpoint raised).

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
