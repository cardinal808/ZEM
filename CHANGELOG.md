# Changelog

## Unreleased

### 0.8.99 — New default house on Stroom (isometric, 3 or 2 storeys)
- **Stroom:** a new drawn, fictional house with a transparent background (`frontend/scripts/house_gen.py`, built to `house-3.webp` and `house-2.webp` by `house_build.py`). Choice in *Instellingen → Apparaten → Plaatje op Stroom*: **Standaard huis** (3 storeys, the default), **Alternatief huis** (2 storeys), **Oud huis** (the picture until now) or **Eigen afbeelding**, as picture buttons (`picture.style`, `stroom.house_style`). In the alternative house what is on the *Zolder* shows on the *1e verdieping* (the stored floor stays); the floor choice then has no *Zolder*.
- **Lines as in the ontwerpchat mock** (OPDRACHT-ui-huisplaatje-isometrisch): battery at the top and shed panels below it (no crossing), roof panels straight to the main line, the grid from the *Net* box, branches with an arrow to the floors with measured consumers, *Overig* into the house at the meter cupboard, the charge point level and then straight up. Labels as pills on the lines; boxes with a small caption and a colour bar.
- **Dots on the main line per piece** (`busSegments`): each piece between two connections runs the way its power goes (sum of everything above it), so charging the battery or a grid import never runs the wrong way.
- **Follows the HA theme:** light card in light mode (colours of the mock), in dark mode the panel's own card colour (no blue background) with the existing line colours. Line colours are CSS variables (`--h-*` in `theme.ts`). Phone: the house without the empty right part, the list below as before.
- Own picture (0.8.58) unchanged; removing it keeps the chosen built-in house.
- Tests: `busSegments` (the mock, sun only, battery + grid, export, below 10 W), floor boxes on their branches, `shownFloor`, texts; HA: `house_style` default/alt and an unknown style refused.

### 0.8.98 — Start from idle on the P1 alone, report age in the log
- **Fix: on/off cycles at a small solar surplus** (diagnosis 28-11, 11:44–12:52): after a command to 0 W the set kept reporting 169 W for up to 37 s while P1 had already moved 165 W. From that lagging value a surplus of 50 W became a start at 170 W, an import, a stop and a new start: 15 times in an hour. Live and idle by its own command, the controller now starts from the P1 alone. A start then needs a surplus of at least the minimum power plus the charging target (≈ 130 W export); at 40–50 W the battery stays idle.
- **Log:** every decision carries what the sets report on the AC side (`ac`: grid input, home output), `report_age_s` (since the last good read) and `content_age_s` (since the report's content last changed). For 30 s after a command each new report is logged too (`report_only`), so it shows how fast the set follows.
- Tests: no start at 50 W surplus with a lagging report, a start with the surplus (not surplus + report), delivering from the P1 alone, the new log fields.

### 0.8.97 — Built-in battery named after its set
- **Accu:** the built-in battery is called after the set's model without *SolarFlow* (*2400 Pro*, *AIO 2400*) instead of *Ingebouwd*, in the pack cards and *In het kort*. Unknown model: *Ingebouwd* as before (`builtInName`).
- Tests: `packName` with the set model, `builtInName`.

### 0.8.96 — Forecast band bare like the expected price
- **Fix** (OPDRACHT-band-prijsverwachting): ha-jeroen-nl gives `market` bare but `low` and `high` **all-in** (its `_row`: `low=all_in(p.low)`). ZEPHYR added its own tariff on top once more: expected € 0.47, band € 0.66–0.82 (28-11). The reader now turns an all-in band back into bare prices on the line through the sensor's (`market`, `price`) pairs, so `low ≤ market ≤ high` and *laag* plans with the real p10 again.
- **Check in the reader:** a band that still does not hold `market` is dropped for that quarter (`market` as `low` and `high`), with a note in `planner.price_forecast.issues`; `band_all_in` counts the converted quarters.
- **Kept runs** for the backtest from before this version: their all-in band is replaced by `market` (the error per day ahead stays right, *inside band* only counts from now on).
- Tests: the real row shape (made-up values), a band that does not hold the expected price, `buy_low ≤ buy ≤ buy_high` in the view, the run repair.

### 0.8.95 — Price forecast in one small line
- **Prijzen en plan:** the three notes of the jeroen.nl forecast are one small grey line under the price cells: *Verwacht ma 30 nov · € 0,33 – € 0,47 · gem. € 0,40 · laagst 23:45 · hoogst 08:00 · plan rekent mee · bron: jeroen.nl*. No dashes, no link; the source in a smaller font. The mode is a short phrase (`forecastMode`): *plan rekent mee*, *alleen ter info* or *zou nu laden*. The 80 % band is no longer in the text (the dashed line and band stay in the chart).
- Tests: `forecastMode`, the texts in both languages.

### 0.8.94 — Twin P1 at the moment of the measurement, measured P1 in shadow mode
- **Twin without jumps on a slow meter** (OPDRACHT-p1-profiel §7.2): the virtual P1 pairs the P1 measurement with the real battery power and the twin **at the moment of that measurement** (last 60 s kept), not with the power now. On a DSMR 4 (every 10 s) a step of the current controller between two measurements no longer makes the virtual P1 jump (seen at Peter: −43 W measured, virtual −158 W). A repeat of the same value by the integration keeps the moment of the measurement it repeats. Fast meters: unchanged.
- Decisions in shadow mode also carry `battery_real_at_p1` and `p1_age_s`.
- **Card *Nu* in shadow mode** (§7.3): under the P1 value *Berekend · gemeten +42 W*, with the explanation as a tooltip (*what the meter would show if ZEPHYR were in control*). `now.grid_measured_w` in the websocket. The direction (*afname*/*teruglevering*) and exact W were already there since 0.8.92.
- Tests: virtual P1 with a step of the other controller between two DSMR 4 measurements, a repeated value, `grid_measured_w`.

### 0.8.93 — Reload without 0 W, no 0 W when HA stops, slow band without export
- **Reload hands over** (`handover.py`): a reload (a setting that needs one, a set added) no longer leaves the sets at 0 W. The unload parks the running engine (setpoint, P1, `acMode`, twin, counters, live state); the new setup takes it over and goes on live at once: no 0 W, no relay switch, no wait for the P1, no `p1_missing`. Nobody takes over within 120 s (a failed setup): 0 W then. Different sets than before: fresh start, the old sets to 0 W.
- **0 W only where it belongs:** switching *ZEPHYR stuurt de accu* off, a second controller, disabling or removing the integration. **Not** when Home Assistant stops, restart or not (nobody shuts HA down; at a power cut there is no time to send it).
- **Log:** the hand-over with the options that asked for the reload (`handover`, `changed`), in the live history and the log.
- **Slow P1 profile** (OPDRACHT-p1-profiel §7.4): the dead zone while delivering is −20…+55 W (`slow_export_band` 20 W), so a 10 s meter no longer sits on 30–45 W export for minutes. The medium profile already had −20…+30 W.
- **P1 hiccups** (§7.1): an unavailable or unknown P1 holds the last setpoint (as before) and is counted: `control.p1_profile` `invalid_1h`, `invalid_24h`, `invalid_longest_24h_s`, `invalid_now`.
- Tests: reload while live (no power command, no `acMode`, no late 0 W), unload without a new setup (0 W after 120 s), disable and remove (0 W), HA stop (nothing), the slow band (−35 W corrects, +40 W and −15 W not), P1 hiccups, the reload reason.

### 0.8.92 — Card Nu: five fixed rows
- **The card *Nu* no longer jumps:** always the same five rows in the same order, at least 0 W, right-aligned and in W: *Zon → huis*, *Accu → huis*, *Net → huis*, and below a line *… → accu* and *… → net* with their source in front (*Zon → accu*, *Net → accu*, *Zon + net → accu*; *Zon → net*, *Accu → net*, *Zon + accu → net*). With nothing flowing the usual source (the sun), grey. Replaces the flows in words (`nowRows`, from the same measurement as the P1 value).
- Tests: `nowRows` (vitest).

### 0.8.91 — Panel: solar savings, estimated quarters, price forecast, backfill SOC, one-time element registration
- **Besparing — zon en accu** (OPDRACHT-besparing-zon): with a solar counter the screen shows the saving of solar + battery, three bars (without solar and battery / without battery / paid), the split *Zon* (used directly, exported, of which solar bonus; after 2027 a note) and *Accu* (solar stored, price difference), solar kWh and the share used yourself, and stacked day bars (solar yellow under the battery) with a switch *Alleen accu*. Without a solar counter the screen stays as it was.
- **Geschatte kwartieren** (OPDRACHT-ui-geschatte-kwartieren): a neutral notice "x quarters estimated (…)", with the provisional prices; the warning "amounts too low" only for quarters without data. Days with estimated quarters are hatched.
- **Prijsvoorspelling** (OPDRACHT-ui-prijsvoorspelling): the jeroen.nl forecast as a dashed line with its band over the chart, a line per day past the chart (mean, dearest and cheapest quarter), the reason line ("with the forecast ZEPHYR would … now", or that the plan takes it into account) and the credit "Verwachting: Bron: jeroen.nl" with a link.
- **Terugrekenen:** optional battery SOC sensor (caps the pools) and the warning when the counters belong to another Zendure integration.
- **Fix:** the panel's elements are registered only once (`define.ts`). When HA loaded the panel module a second time, `zephyr-prices-plan has already been used with this registry` stopped the module.

### 0.8.90 — Settings: subtabs in Bronnen and Planner
- **Subtabs** (`Field.section`, in `settings/get` as `section`): *Bronnen* → *Meter · Prijzen · Zon · Tellers*; *Planner* → *Plan · Afknijpen*. Same look as *Vandaag · Morgen · 48 uur*; an orange dot on a subtab with a changed field; on a phone they scroll sideways. The chosen subtab is kept per group; saving stays per group (drafts on other subtabs are kept). An error on another subtab opens that subtab.
- **Moved:** *Kalibratie na dagen* to *Accu en grenzen*; the workday sensor to *Bronnen → Tellers*.
- **Menu:** a short line under each group (its subtabs, or e.g. *min, max, kalibratie*); hidden on a phone.
- The link *afknijpen staat uit* on Plan opens *Planner → Afknijpen* (`group:section`).
- Tests: `groupSections` (vitest); every field of a group with sections has one, every section has a name (HA).

### 0.8.89 — Cost log: the older months are filled once too
- The one-off fill of 0.8.80 (missing quarters made, incomplete ones filled, missing prices interpolated) only touched the current month. Now every stored month before it gets the same, once; each month is evaluated again on its own (the current month's pools stay), and its days are summed anew. Days worked out from hourly statistics are left alone. Diagnostics: `costs.history_filled.older_months`.
### 0.8.88 — Terugrekenen: pools capped by the battery's content, warning for Gielz counters
- **Pools capped** (TOETS-besparing bevinding 5): the backfill (`zephyr/savings/backfill`) takes an optional `soc_entity`; its hourly mean × the installation's capacity caps the pools, as in the cost log, so conversion losses of stored solar land in *Zon bewaard* instead of *Prijsverschil*. The total does not change. The answer says `capped_by_soc`.
- **Warning** (bevinding 11): when the charge or discharge counter belongs to another Zendure integration (Gielz), the answer holds `warnings: ["pv_in_battery_counters"]`: those counters include the set's own PV, so on summer days that PV counts as battery. The panel can show it (UI chat).
### 0.8.87 — Devices: `via_device_id` instead of the deprecated `via_device`
- HA 2026.11 warns that `via_device` stops working in 2027.8. The set and appliance devices now link to the installation device with `via_device_id` where HA supports it; older versions (down to 2026.1, `hacs.json`) keep `via_device`. Test: every set device hangs under the installation device.

### 0.8.86 — Planner: price forecast of jeroen.nl as an optional source (indicative)
- **Optional, off by default** (OPDRACHT-prijsvoorspelling-jeroen): new settings *price forecast (entity)*, *use in the plan* (off / indicative / take into account), *forecast days* (0–2, default 1) and *value from the band* (low / middle, default low). ZEPHYR reads only the sensor of the HACS integration ha-jeroen-nl (the user's own API key) and fetches nothing from jeroen.nl.
- **Reader** (`core/price_forecast.py`): only quarters with `forecast: true`; the bare `market`, `low`, `high` are priced with ZEPHYR's own tariffs (the sensor's all-in `price` is not used). Units recognised (€/kWh, €/MWh, cents); slots by UTC start, days of 92/100 quarters work. Without `low`/`high`: `market`, with a note. A value but nothing readable: repair issue `price_forecast_format`.
- **Merge:** forecast quarters only from the end of the last known Nord Pool price on, without a gap, never for the running quarter, not when older than 36 h; they replace today's pattern for tomorrow, up to local midnight after the known prices plus the chosen days. Always indicative: not in the totals.
- **Indicative:** the plan's actions stay as without the forecast; a second plan with it goes to the diagnostics (`planner.price_forecast.compare`: first action and expected cost with and without).
- **Take into account** (Bjorn 28-11: the level can be off, the trend is clear; mostly for the day after tomorrow): selectable now. The planner plans with the forecast days; blocks on forecast quarters stay indicative (not in the totals). In the diagnostics the prices of forecast quarters are left out of the timeline (private).
- **Backtest store:** one forecast run a day (after 06:00) in ZEPHYR's own storage, 120 days; private: diagnostics show only summaries (slots used, first/last, run time, reason) and the quality per day ahead (mean error, share inside the band, 30 days, against the real prices of the cost log).
- **Panel data:** `price_forecast` in the plan view (slots with market, low, high and all-in buy prices, source "jeroen.nl" with link, mode, comparison) for the dashed line with band; the chart itself follows in the UI chat. The planner plans again when the forecast sensor changes.
- Tests: reader, units, merge (Nord Pool wins, gap, stale, no known price), 92/100 quarters, the expensive Monday morning (charges Sunday night only with the forecast, not when low is under the break-even), HA indicative (actions unchanged, summaries only, run kept, repair issue). The test data are made up with the sensor's shape: the real forecast stays private.

### 0.8.85 — Diagnostics: energy balance per day and a price check against EnergyZero
- **Energy balance** (TOETS-besparing voorstel 6, `core/cost_checks.py`): per day of the last 7, charged × η_in − delivered ÷ η_out against the change of the battery's energy (ΔSOC × capacity); `suspect` when they differ by more than 0.3 kWh and 10 % of the throughput. Diagnostics `costs.energy_balance`.
- **Price check** (voorstel 4): the quarter prices of yesterday and today against EnergyZero's hour prices; an hour is listed when its mean differs by more than € 0.03 and 25 %, or one quarter by more than € 0.05 and 50 % (as 25-11 23:45). Interpolated prices are left out. Fetched when the diagnostics are downloaded, at most once an hour. Diagnostics `costs.price_check`.
### 0.8.84 — Battery efficiency (RTE): only from the first SoC on
- **Bug (Bjorn 28-11, RTE 65 % instead of ~86 %):** the efficiency counted all energy in the window but took the stored energy from the first quarter that had a SoC. Bjorn's cost log charged 4,96 kWh in the night of 25/26-11 before its first SoC (92 % after that charge), so that charge was counted twice as "put in". Now only the energy between the first and the last quarter with a SoC counts (a quarter's SoC is at its end). With his export: 83,5 % over 3 days (the set's own counters give 86 % over 7 weeks).
- **Days:** `week.efficiency_days` (from the first to the last quarter with a SoC). The card *Accu* on Plan shows *RTE 84 % · 3 dagen* while the cost log is shorter than 7 days; the screen Accu adds *(3 dagen)* to the efficiency.
- The per-day bars and totals still show all energy.
- Tests: charge before the first SoC and delivery after the last SoC do not count (core).

### 0.8.83 — Savings: the battery's content at the start and end of a period (day boundary)
- **Day boundary** (TOETS-besparing bevinding 2, SPEC-kosten §5): energy charged and still in the battery at the end of a period was counted as cost, its earnings fell in the next period; days and *Today* / *This week* swung with the state of charge. Now the battery's content is valued at what it cost (grid energy at its buy price, solar at the export revenue given up) and the change over the period counts in the battery saving (solar part in *Zon bewaard*, grid part in *Prijsverschil*). Over a longer period it adds up to 0.
- The pools keep `grid_value` (what the grid energy in the battery cost); before 0.8.83 that was not kept, so the grid energy in the battery at the update starts at the mean buy price of the last week. Per quarter `content` (solar and grid value after it); per day `content.start` / `content.end`, refreshed after a correction.
- Summary: `battery_content_change`, `battery_content_end`; `savings_battery`, `savings` and the sensors include the change.

### 0.8.82 — Plan: P1 value on the card Nu, RTE on the card Accu
- **Card *Nu*:** right of the action the P1 value, always in W with a sign (*+1.100 W · afname* in red, *−350 W · teruglevering* in green, within ±50 W grey). Same measurement as the flows below it.
- **Card *Accu*:** *RTE 86 % · 7 dagen* between the limits and the sets: the round-trip efficiency from `zephyr/battery_days` (same figure as on the screen Accu), *RTE –* with too little energy. Refreshed at most every 15 minutes.
- Tests: `p1Display` (vitest).

### 0.8.81 — Savings: what the solar panels saved, split (backend of OPDRACHT-besparing-zon)
- **Per quarter** (with a solar counter and a price): `solar_direct_value` (solar the house used directly × buy price), `solar_export_value` (export without battery × export price, bonus included) and `solar_bonus_value` (the solar bonus part). Direct + export = Z0 − Z1 = `savings_solar`. `Tariffs.bonus()` gives the bonus per kWh.
- **Day totals and summary:** the three sums, `savings_total` (solar + battery, only when every priced quarter has solar), `solar_direct_kwh`, `self_consumption` (share of the solar the house used, directly or later from the battery).
- **Panel data** (`savings_view`): per period `cost_no_solar`, `savings_solar`, `savings_total`, the three values, `solar_kwh`, `solar_direct_kwh`, `export_kwh`, `self_consumption`, `includes_solar` (null without solar); per day `savings_solar`. The screen follows in the UI chat.
- **Sensors** `sensor.zephyr_savings_today|month|year`: attributes `solar`, `battery`, `total`.
- **History:** once after the update the three values are worked out for all stored quarters from their stored prices and kWh, and added to the day totals. Days worked out from hourly statistics get them with the next run of *terugrekenen*.

### 0.8.80 — Cost log: quarters while HA was off, the history once, and always a price (steps 2 and 3)
- **HA was off** (eis 3): at the next close the missed quarters get a record (`last_closed` is kept). Import/export: interpolated between the quarter before and the rate after, scaled on the P1 counter difference over the whole interruption (which also sets this quarter's share, so the day equals the meter); the battery from the own counters' restart gap (T2), else interpolated; external solar only by day, scaled on the solar counter. Price from Nord Pool of that day, else filled. Status `estimated`, cause `ha_off`; diagnostics `costs.missed_quarters`. Longer than a month: not filled, logged.
- **History once** (eis 5): after the update the stored current month is filled once: missing quarters made, incomplete ones filled between their neighbours, missing prices interpolated; the month is evaluated again and its days are summed anew. Diagnostics `costs.history_filled`.
- **Always a price** (eis 2): no price at closing → between the last known price and the next one on the sensor (else the 7-day mean), `price_source: interpolated`, counted at once. Retried at every quarter and on every update of the price sensor; after an hour EnergyZero's hour price. A real price replaces the guess and the cost log is evaluated again from there (`reevaluate` now also replaces the price and corrects import/export).
- **Midnight:** test for 23:45–00:45 with a sensor that rolls `raw_today` over at midnight: 23:45 keeps the price it opened with, 00:00–00:45 the new day's. The 0.379 of 25-11 could not be reproduced without that night's sensor data; a wrong price there would now at least be replaced only by a real one, never left empty.

### 0.8.79 — Cost log: unmeasured parts of a quarter are filled (step 1 of OPDRACHT-onvolledige-kwartieren)
- **The coverage follows the source.** With the own energy counters (`battery_source: counters`) the battery part of a quarter is complete, also when the set's power readings had a gap; such quarters no longer count as incomplete (the bulk of the "7 of 57" on 28-11).
- **Fill instead of leaving out** (`core/quarter_fill.py`): a flow measured over less than 95 % of the quarter (P1 away without meter counters, set readings away without own counters, no solar counter reading) gets the missing part filled: between the neighbour quarters; at closing time the quarter's own rate stands in for the next quarter, and once that closed the fill is redone between the real neighbours (`reevaluate`). No neighbours: the own rate, else the mean of the same quarter over 7 days. Solar only in daylight.
- **Per quarter:** `status` (`measured` / `estimated` / `missing`), `fill` (method per flow: `interpolated`, `own_rate`, `history`, `counter`), `fill_kwh`, `fill_causes` (`p1`, `set`, `solar_counter`), `measured_share`, `solar_ext_kwh`. A quarter corrected after a counter gap (T3) becomes `estimated` with method `counter`. `missing` only when nothing could fill it; only then the amounts are too low.
- **Totals:** per day `estimated`, `incomplete` (= missing), counts per cause and method and the kWh added per flow. Sensors and panel data: `estimated_quarters`, `missing_quarters`, `price_interpolated_quarters`; `incomplete_quarters` now counts only missing quarters (and those without a price). Diagnostics: `costs.fill_by_day` for the last 7 days.
- Next steps: quarters while HA was off (step 2) and the price always filled (step 3).

### 0.8.78 — Planner: its memory survives a restart
- **Bug (28-11):** a save of the planner scheduled before it loaded its store at the start (a plan run asked for while Home Assistant was still starting) left a pending write, and `Store.async_load` returns a pending write instead of the file. The planner so loaded its own empty start state, and every restart lost the calibration count (the 21 days began again at each start), the consumption profile (filled again from the recorder), the price reserve and the expectations for tomorrow.
- Saves before the load are now held back and done right after it; the start of a new calibration count is saved at once.
- Test: a save before the start, then a restart across a quarter: the calibration count and the profile stay.

### 0.8.77 — Settings: amounts in the fields, no counters in the menu, better info texts
- **Menu:** no more *x gewijzigd* per group; the orange dot on a changed field stays.
- **Tariffs from the supplier's table:** the greyed-out fields show the amount in use (e.g. *Opslag inkoop* 0,01653 instead of 0); the line *in gebruik: …* is gone. With own tariffs the fields show and edit your own values as before.
- **Info texts (i) for all 38 fields** rewritten (NL and EN, `VOORSTEL-tooltips.md`): what to fill in, where to find it, a common value or example (e.g. *Btw*: statutory rate, 21 % in the Netherlands), and what higher or lower does. No internal decision codes any more. *Energiebelasting* shows the amount in use in its text.
- Tests: `controlValue`, info text with the amount in use (vitest).

### 0.8.76 — Second controller: no false alarm for a set catching up, every mismatch in the log
- **False alarm (28-11):** ZEPHYR sent A and a few seconds later B; a slow set still showed A. Only "still the limits from before B" counted as not yet applied, so A counted as foreign, and twice in 5 minutes stopped live control. A report equal (within 20 W) to a command ZEPHYR itself sent in the last 30 s now counts as a set catching up. The writer keeps its last 6 limits for this.
- **Every mismatch in the 48-hour log** as event `foreign_report`, also when it does not stop live control: set, limits sent and reported, seconds after the command, the limits before, the last commands with their age, the age of the report, smartMode sent/reported, acMode, acStatus, packState, SOC, power and the number of mismatches in the window.
- Tests: the earlier-command check; the second-controller test checks the two log events.

### 0.8.75 — Log over 48 hours, kept over restarts
- The control log (decisions on a change of setpoint or reason, and events such as live, shadow, calibration and a write test) covers the last 48 hours instead of the last 500 lines, and survives restarts and updates. Until now a restart emptied it, so the reason for something before the restart was gone (28-11).
- Once a minute the new lines are appended to one file per UTC hour under `.storage/zephyr_log/<entry>/`; files older than 48 hours are removed. Appends keep the disk writes small (a Store rewrites its whole file). On a stop of Home Assistant and at an unload the rest is written; a reload reads the files only after that.
- At most 40 000 lines (about 6 MB). Diagnostics: `control.decisions` holds the whole 48 hours (was the last 200), `control.log` gives `since`, `lines` and `from_before_start`. The panel's *Gebeurtenissen* now also shows events from before a restart.
- Tests: the log over a reload (HA), removing old files and skipping broken lines.
### 0.8.74 — Live control: resume does not give up, the reason for shadow is kept
- **Bug (28-11):** after a restart ZEPHYR tried to go live again for 10 minutes. When the P1 or a set was not there in time it gave up: the switch stayed off and that state was saved, so the next restart did not resume either. Now:
  - the switch keeps what the user wants (`wanted_live`) apart from its state, over restarts; a start that cannot go live yet keeps that wish;
  - after 10 minutes the repair issue `live_not_resumed` comes as before, but ZEPHYR keeps trying every 30 s and goes live by itself; the issue then disappears.
  - Switching off by hand or a second controller (L4) turns the wish off; those stay off.
- **Why live stopped, kept over restarts:** the last 20 switches between live and shadow with time and reason (`user`, `resumed`, `unload`, `second_controller` with the limits sent and reported, `not_resumed` with the blockers, `ha_restart`) in Store `zephyr.<entry>.live`. In diagnostics under `control.live.history` (with `wanted`), and as attributes `last_shadow_at`, `last_shadow_reason`, `wanted_live` and `resuming` of `switch.zephyr_control`.
- Tests: resume after more than 10 minutes, the wish over a restart (both ways), the history over a restart, the reason for a second controller.
### 0.8.73 — Installation device: *ZEPHYR Applicatie*
- The installation device (the one HA lists under *Apparaten die niet tot een sub-item behoren*; that heading is HA's own) is now called **ZEPHYR Applicatie** (EN *ZEPHYR Application*, a translated device name) with type **Regeling en planner** (EN *Control and planner*; was *Installation*). Display names of its entities follow (*ZEPHYR Applicatie Modus*).
- **Entity ids do not change:** existing ones stay as registered; a new installation still gets `zephyr_…` (the installation entities suggest `zephyr_<English name>` themselves, `InstallationIds`), not `zephyr_applicatie_…`.
- Tests: name, type and ids in English and Dutch (HA).

### 0.8.72 — Diagnose: tidier layout
- **Top:** one wide bar with *Diagnose downloaden* and *Kostenlogboek exporteren*.
- **Planner:** *Plan tegen werkelijkheid* and *Verbruiksprofiel* side by side and equally high; *Apparaatprofielen* below over the full width.
- **Meting en set:** *Energietellers* on the left; *Korte pieken* with *Schrijfacties* (now its own card, was inside the download card) on the right. The gaps list shows the last 5, with *Toon alle n gaten*.
- **Logboek:** *Gebeurtenissen* over the full width. Two columns from 900 px, one below.

### 0.8.71 — Accu: the inverter in the summary, what the battery did per day
- **Summary:** *Warmste accu* is replaced by *Omvormer* (the set's enclosure temperature; with more sets the warmest).
- **What the battery did per day · last 7 days** replaces *Celverschil per dag* (at full the cells always differ a lot, so the grid was red every day and said little). Per local day from the cost log's closed quarters: a bar with charged up (solar / grid) and delivered down (house / grid) on one scale, and rows *Geladen*, *Geleverd*, *Cycli* (delivered ÷ usable capacity between the limits) and the lowest–highest SoC. Below: the week with charged (solar · grid), delivered, cycles, round-trip efficiency (delivered ÷ charged, corrected for the change in SoC; shown only from 2 kWh and between 50 and 98 %) and the mean price of what went from the grid into the battery.
- New websocket command `zephyr/battery_days` (core `battery_days.py`); the cell balance per pack stays in the pack cards and the summary.
- Tests: `battery_days` (core: routes per local day, SoC range, efficiency with the change in storage, hourly backfill skipped), the command (HA), `dayBars` and the inverter in the summary (vitest).

### 0.8.70 — Stroom: *Regeling* and *Nul op de meter* swapped
- *Regeling · laatste 10 minuten* now comes before *Nul op de meter vandaag*: on a wide panel the regulation chart gets the wide column under the house picture (it was hard to read in the narrow one), *Nul op de meter* moves to the narrow column. On a phone *Regeling* comes first.

### 0.8.69 — Panel: card Nu without double figures, version in the header, spread vs. the mean
- **Card *Nu*:** below the action the flows now, from one measurement and in the same words as on *Stroom* (*Accu 440 W → huis · Net 10 W → huis*). The separate *Net* line is gone (it came from a later reading than the control's sentence, so two grid figures could differ). The control's sentence shows only when it adds something (full/empty, blocked, P1 problem, temperature, calibrating …); problems in the warning colour. Sentences that repeat the action (*Levert … aan het huis*, *Laadt … uit zonne-overschot*, *Plan: …*) are hidden.
- **Header:** *Stuurt* is now *Actief* (EN *Active*). The clock is replaced by the running version (`panel.py` passes it in the panel config). When HACS has a newer version (its update entity, found by the release URL), admins get a button *Update x*: after confirming, `update.install`; with a link to the release notes. Once installed but not yet running: *Herstart nodig* (restart HA after confirming). Others see the version and *update x* as text.
- **Snel laden / Snel ontladen** buttons removed from *Plan* (left over from the first test scenario); the modes themselves stay.
- **Spread** in the price row: the highest price above the day's mean in % (was: above the lowest). Example 28-11: mean € 0,36, highest € 0,41 → 14 % (was 26 %). Mean around zero or below: the difference in euro.
- Tests: `nowNote`, `zephyrUpdate`, `versionState` (vitest); the SOC-line test for *Morgen* no longer depends on the time it runs.

### 0.8.68 — Calibration safety net (SPEC-planner §3.5)
- ZEPHYR remembers when the battery was last full (SOC ≥ 99 %, or the set's own calibration — `socStatus` 1 → 0 — ended), kept over restarts. New setting *Planner: calibration after days* (default 21, 0 = off).
- From half that period on the planner gets a growing incentive (up to €0.30) to reach 100 % when it is cheap (solar, a cheap night hour); from the last day on it is a hard requirement (€2), so the planner picks the cheapest moment in the horizon. "Reached" counts anywhere in the horizon, not only at its end (a second layer in the planner).
- While a calibration is due, the set's upper SOC limit is 100 % (flash write, cause `calibration`); once full, ZEPHYR does not deliver from the battery until the set finished calibrating, at most 2 hours; then the user's limit returns and the count restarts.
- Diagnostics `planner.calibration` (last full, days, penalty, active, resting, set calibrating) and the decision log (`calibration_on`/`_off`).

### 0.8.67 — Buffer refilled when it pays (B37)
- The buffer is now a **reserve at the bottom of the battery** instead of a smaller battery: the planner never plans to deliver from it, but sees how full it is and refills it. Energy in the buffer is worth the mean buy price of the horizon (× discharge efficiency), so the planner charges it from the grid only in an hour that is clearly cheaper (with the grid-charge threshold and wear as before); solar fills it for free. Planned delivery stops at min_SOC + buffer as before; the regulator may still use the buffer when the load is higher than expected.
- Plan state attribute and diagnostics `buffer`: size and content (kWh), *short*, and when and how it is refilled (`refill_at`, `refill_by` grid/solar), or `reason: no_cheap_moment` when it is not refilled in the horizon ("buffer not refilled").
- With a buffer of 0 % nothing changes.

### 0.8.66 — Settings: fields only when they apply
- A field can have a condition (`show_if` in `settings_schema.py`, sent by `settings/get`): the panel shows it only when another field, as entered and before saving, has a given value; otherwise it is hidden (not greyed out) and its stored value is kept, so switching back brings it back.
- *P1-sensor* only with P1 source *one sensor*; *P1 afname* and *P1 teruglevering* only with *two sensors* (Bjorn, Peter: one P1 sensor, two empty fields). The three inverter fields only with *ZEPHYR knijpt af* (replaces greying them out, SPEC-ui-planner §2.3). The air-conditioner climate entity and its modes only when the energy counter is filled in.
- Hidden fields are left out when saving, so a wrong entity in a hidden field never blocks saving. A climate entity without the counter is now kept instead of refused in the panel (it is hidden and not used); the options flow of HA still asks for the counter and is unchanged.
- Tests: every condition names an existing field and choice (HA); visibility while switching, `*` = filled in, hidden fields not saved (vitest).

### 0.8.65 — DSMR version found via the meter counters or by name
- Diagnostics `control.p1_profile.dsmr_version`: besides the P1 sensor's own device, ZEPHYR now looks on the device of the meter counters for the cost log (a P1 power sensor can be a template, e.g. `p1_meter_dsmr_version` of a HomeWizard), and last for the one sensor whose id ends in `dsmr_version` (DSMR integration: `sensor.dsmr_version`). Several by name: left unknown.

### 0.8.64 — P1 profile: slow meters (DSMR 4) without the step filter
- **P1 profile** from the measured meter interval (OPDRACHT-p1-profiel): fast (≤ 2 s), medium (≤ 7 s), slow (≤ 25 s), too slow. Medium until 10 intervals are known; a change only after 10 minutes in the new range and 20 % past the bound (slow → medium below 5.6 s).
- **Slow profile:** the step filter (B20) is off. With one sample per 10 s it held a real rise for a whole extra sample; on such a meter a boiling-water tap's peak is mostly not seen anyway.
- **Times follow the interval:** *P1 stale* after 3 × the interval (was 2.5 ×; a DSMR 4 gap of 20 s no longer comes close), the check for a second controller over at least 2 samples. Lost after 6 × and the hold at a balanced P1 stayed as they were; one decision per new sample and the slow control (B26) too.
- **Diagnostics** `control.p1_profile`: interval, samples, profile and since when, step filter on/off, the times in use, *P1 stale* per 24 h, timestamp source, and the DSMR version of a HomeWizard P1 meter.

### 0.8.63 — Appliance plugs: only real runs leave the house profile
- Since 0.8.54 all energy of an appliance's plug was taken out of the house profile; on a plug that also feeds a boiling-water tap (a dishwasher plug with a Quooker), the tap's pulses left the profile too, while nothing plans them. Now only **real runs** count: live, an on-period counts once it lasts 10 minutes (then from its start, ending after 5 minutes off); the first fill from the recorder uses the energy per hour of the runs found in the plug's history (the planner waits up to 30 s for them). Short pulses stay house use.
- **Appliance without a plug:** its usual runs are already in the house profile, so a planned run now counts for half on top of it (SPEC-geplande-verbruikers §3.2). The run's full kWh is still shown (`kwh`), with `counted_kwh`.

### 0.8.62 — Solar forecast from the Energy dashboard
- Without a forecast sensor, ZEPHYR now takes the solar forecast of Home Assistant's **Energy dashboard**: every forecast integration set there (Forecast.Solar, Solcast, Open-Meteo, Helios Forecast if it provides one, …), summed over the solar sources. Read at the start and every 30 minutes. Per hour (or the source's own step) and without the 10/90 % bounds; Solcast via its sensor stays the richer choice (half hours and bounds, B32).
- The planner and the day-ahead history (23:00, B31) use the same forecast; its source is in the diagnostics (`planner.inputs.solar_forecast_source`, `solar.forecast_source`, `energy:<integrations>`).
- Settings text for *Solar forecast* says what an empty field does.

### 0.8.61 — Settings suggest sources by integration
- **P1:** a power sensor of a smart-meter reader (DSMR, DSMR Reader, P1 Monitor, SlimmeLezer, the HomeWizard P1 meter — not its plugs) is suggested whatever its name; per-phase sensors are skipped. The name hints stay as fallback.
- **Solar counter:** a production counter of an inverter integration (SolarEdge, SolarEdge Modbus, Enphase, Fronius, SMA, Growatt, Huawei, GoodWe, Solax, Sungrow, Solarman, FoxESS, APsystems, Hoymiles, OpenDTU) wins over a name match; forecast sensors are skipped.
- **Meter counters for the cost log:** without per-tariff counters, the import and export total of a meter reader (e.g. HomeWizard P1).

### 0.8.60 — Prices from Home Assistant's own Nord Pool integration
- The price sensor may now also be the **current price of the Nord Pool integration that ships with Home Assistant** (until now only the HACS Nord Pool with `raw_today`). ZEPHYR fetches today and tomorrow with the action `nordpool.get_prices_for_date` (bare price per MWh, converted to €/kWh) at the start, when the sensor appears and every 15 minutes while a day is missing (tomorrow around 13:00); a new day starts a new plan. Control, planner, cost log, curtailing and the panel read them as before.
- Settings suggest that sensor when there is no HACS Nord Pool. Diagnostics: `prices` (area, days, last error).

### 0.8.58 — Stroom: flows on an own picture
- On an own picture, place the item *Huis* (the meter cupboard) with its spot: then every flow runs through that spot like the main line on the default picture: roof and shed panels, battery and grid to *Huis* (battery and grid reverse when charging or exporting), and from *Huis* to the floors and the charge point, with moving dots and the colour of the biggest source. Each box then only points at its spot with a thin line.
- The *Huis* box shows the total, the rest and the flows in words. Without a *Huis* spot the picture works as before.
- Test: the line from a spot to *Huis* (vitest).

### 0.8.57 — Stroom: all power flows on the house picture
- New default picture: the floors moved right so a **main line** runs between the house and the floors. Every source runs to it (battery and shed panels along the top, roof panels straight across, grid from the *Net* box); from it branches go to floors with a measured consumer, into the house (the rest, labelled *Overig*) and to the charge point. Moving dots show the direction: battery charging/delivering and grid import/export reverse their line (Bjorn 27-11: the battery's 540 W "went nowhere").
- The main line, its branches and the *Huis* box take the colour of the source that supplies the most now (sun yellow, battery green, grid red); another source takes over only when it is 50 W bigger. Grid is red now.
- Watts on the lines (*540 W → huis*, *200 W → net*), and the flows in words in the *Nu* box (*Zon 3,2 kW → huis 600 W · accu 2,4 kW · net 200 W*).
- *Overig* is no longer put on the 1st floor: a new *Huis* box shows the total and the rest; on an own picture *Huis* is an item to place.
- Tests: the dominant source with its margin and the flows per source (vitest).

### 0.8.56 — Energy counters saved from the event loop (flaky tests fixed)
- The energy counters' save every 5 minutes was given to Home Assistant as a plain lambda; HA ran it in a worker thread, which scheduled the store's timer on the event loop from there. The loop's timer heap is not thread-safe: now and then it broke with "list changed size during iteration" (the known flaky HA test, a different test each time; in a running HA possibly a rare error in the log). Now a `@callback` method on the event loop.
- HA tests: a guard fails any test in which a timer is scheduled from another thread.

### 0.8.55 — Write and relay counters over a restart; no 0 W at a restart
- **A restart of Home Assistant no longer sets the sets to 0 W** while live: they keep their last command and ZEPHYR takes over again after the start (B35, B47). 0 W opened the relay and drew from the grid for the minute of the restart. A real stop still writes 0 W.
- **Counters kept over a restart** (OPDRACHT-tellers-relais-flash): the write and relay events of the last 24 hours and the totals per day (7 days) are stored (`zephyr.<entry>.writes`, every 5 minutes, at a stop and an unload). The 1 h and 24 h windows run on after a restart.
- **Live, a write counts once the set accepted it**; a queued command that a newer one replaced counts as `superseded`. RAM + flash now match `writes.ok`. In shadow mode the counters stay what ZEPHYR would send.
- **Relay in three kinds:** `relay` (changes of `acStatus` in the reports, as before; the last one is kept over a restart), `relay_commanded` (commands that turn the direction against the reported `acMode`) and `pack_state` (changes between idle, charging and delivering). Per day `relay_mismatch` when relay and commanded differ by more than 2.
- **`flash_by_cause`** with every cause, also at 0: standby, SOC limits, `startup` (SOC limits when a set is first seen), `gridReverse`, write test. Per day in `days`.
- The decision log's `sent` is only true when commands were really sent.

### 0.8.54 — Appliance plugs left out of the house profile
- The consumption profile no longer holds what the appliances on a smart plug used (B36): planned runs are added on top, so a planned wash was counted twice. Live, every closed quarter subtracts the plug energy (integrated from the plug's power); the first fill from the recorder subtracts the plugs' hourly mean power (an hour without plug statistics counts as 0). Vacation hours keep the plugs in, as before.
- When the set of plugs changes, the profile is filled again from the recorder once (like a changed air-conditioner counter, B41). Appliances without a plug (e.g. a dishwasher) leave the profile as it is.
- Diagnostics: `planner.appliance_plugs`.

### 0.8.53 — Stroom: own picture
- *Instellingen → Apparaten → Plaatje op Stroom*: choose *Standaard huis* or *Eigen afbeelding*. An own picture (JPG, PNG or WebP) is scaled down in the panel (max 1800 px wide) and stays in this Home Assistant (`.storage`), never in the repo; it is served only to logged-in users (signed URL).
- Placing: pick an item (roof and shed panels, battery, grid, charge point, the four floors), tap where its box goes, then where its line connects; the next unplaced item follows. Items can be hidden or placed again; positions are kept as fractions, so another picture of a similar layout keeps them.
- On *Stroom* each placed item gets its box and a line with one bend to its spot (only drawn with power); the card keeps the picture's own proportions and still fits the screen.
- Tests: upload, refusing a non-image, clamped positions, serving only with a login, removing (HA); the line and the next item to place (vitest).

### 0.8.52 — Stroom: clean house picture, cards line up
- New base picture from Bjorn without lines or text (no more smudge on the roof), widened on the right so each floor has its box next to it. Every line runs from its box to its spot (panels, battery, meter, car, floor) and is only drawn with power.
- Wide panel: the *Nu* card is as high as *Energie per route* and *Verbruikers vandaag* together, so the bottoms line up (Bjorn 27-11, 90 % zoom).

### 0.8.51 — Stroom: house picture fits the screen
- The *Nu* card (picture and totals bar) is never taller than the screen; the picture shrinks with its proportions (Bjorn 27-11: the bar fell off the screen).
- Wide panel (≥ 1200 px): the picture on the left, *Energie per route* and *Verbruikers vandaag* next to it.
- Text in the boxes has a minimum size (11 px); a box grows instead of cutting text. Below 680 px picture width the boxes give way to the list, as on a phone.
- A line without power (< 10 W) is no longer drawn: the faint line over the picture looked blurred. Arrows go with their line.

### 0.8.50 — Stroom: the house picture as *Nu*
- *Stroom* opens with an illustrated house (a generic illustration, not a real house) instead of the flow diagram: straight power lines from the roof panels, the panels on the shed, the battery, the grid and the charge point, with a box per floor (*Zolder*, *1e verdieping*, *Begane grond*, *Schuur*) showing the consumers on it and their power now; arrows towards a floor show power going in. Lines glow and move from 10 W.
- The battery box names the set: product and packs, e.g. *SolarFlow 2400 Pro + 3 × AB3000L* (no serial numbers).
- A bar under the picture: sun, battery, consumers, charge point, grid import and export.
- On a phone the boxes on the picture give way to a list below it.
- Tests: consumers per floor in vitest, the battery label in the HA test.

### 0.8.49 — Curtailing at a negative export price in the panel; entity picker
- *Plan* (SPEC-ui-planner §2.1): a negative export price is drawn in red below the zero line (and in the legend); a quarter in which the planner curtails gets a crossed-out panel mark; the tooltip says what happens ("Terugleverprijs −€0,04: zonoverschot 0,6 kWh wordt afgeknepen" or "Teruglevering kost €0,03 (geen afknijpen ingesteld)"). With curtailing off and negative prices ahead: one notice with the hours and the expected cost, and a link to the setting.
- *Stroom*, *Nu* (§2.2): while curtailing, the solar node says *Afgeknepen tot 45 %* or *Omvormer uit*, the battery *Teruglevering geblokkeerd*.
- *Instellingen → Planner* (§2.3): the three inverter fields under *Omvormer buiten de sets (kies één)*, only usable with *ZEPHYR knijpt af*; a warning when a limit is set without the rated power.
- **Entity picker** for all entity fields: its own list (instead of the browser's `datalist`, which shows nothing in the Android app and only matches the start in Safari), filtering on any part of the name and the id, with arrow keys and Enter; an id of another domain says which domain the field expects.
- Text fixes (§5) in the panel and in HA's options.
- *Morgen* on its own (Bjorn 27-11): no *nu* mark and no highlighted first quarter (now is not in view), and the SOC line starts at the first quarter's value instead of the SOC now.
- Tests: negative prices ahead, search and wrong domain, the view *morgen* in vitest.

### 0.8.48 — Plan: 48 hours fast again
- Bjorn 27-11: the Plan screen, and above all *48 uur*, reacted slowly. Measured in the test page: switching to 48 hours took ~3.7 s, now ~30 ms.
- Cause: finding the start of the second day looked up that day once per quarter (192 × 192 date formats), and every date format created a new `Intl.DateTimeFormat`.
- Formatters are now cached (`format.dateFormat`, `format.numberFormat`), and the second day is looked up once.

### 0.8.47 — Diagnose: short peaks and appliance profiles
- Card **Korte pieken** (B20, SPEC-ui-planner §3): energy from the grid during the short peaks ZEPHYR does not follow, today (kWh and count) and the mean per day, with bars for the last 14 days and an explanation behind (i).
- Card **Apparaatprofielen** (SPEC-ui-planner §1.3): per appliance learned or standard profile, runs seen, kWh and duration per run, plug yes/no, running now, and the learned profile as a small chart (W per minute). Empty: where to add appliances.
- Tests: short-peak figures in vitest.

### 0.8.46 — Plan: appliance buttons; Instellingen: Apparaten
- Under *Prijzen en plan* one button per appliance (B36). A tap plans a run in the appliance's window; the washing machine goes 1× → 2× → off, the others 1× → off. Nothing planned: the expected cost of one run (cheapest start in the window at the quarter prices). Planned: the advised start(s), the cost of the run(s) and how much cheaper than starting now; a dryer planned along shows *na de was*.
- Planned runs appear in the chart as bars under the solar lane (a fixed start with a lock); the tooltip shows the appliances' kWh in that quarter.
- *Instellingen*: the group *Huis in beeld* becomes **Apparaten**: per appliance *Niet vóór* / *Klaar om* (the window), floor and shown on *Stroom*; for a dryer **Altijd na de was**.
- Dryer *Altijd na de was* (`after_washer`, also in the appliance's options in HA): planning the washing machine plans one dryer run after the last wash (if none is planned yet); clearing the washing clears that dryer run too.
- A run's `cost` and `cost_now` are now the run's own cost (the plan with the run minus without it), not the whole plan's.
- New `zephyr/appliances/update` (admin): window and `after_washer` per appliance from the panel, one reload. `zephyr/appliances` gives `after_washer`.
- Tests: run cost as its own share; dryer along and cleared with the washing, settings from the panel; buttons, estimate and run bars in vitest.

### 0.8.45 — Stroom: consumers today; Instellingen: house view
- *Stroom*: the card *Airco vandaag* becomes **Verbruikers vandaag**: kWh today per appliance with a plug (B36 appliances) and the airco (B41), largest first, with the power now when it runs, then *Overig huis* (house today minus the consumers). Below: the airco's sun/grid split and cost, and the house total.
- kWh today per plug is integrated from its power (W or kW; a reading counts until the next one, split at midnight, unavailable stops counting); kept over a restart on the same day. The airco's kWh comes from the cost log.
- *Instellingen* has a group **Huis in beeld**: per consumer shown yes/no and its floor (attic, first floor, ground floor, shed, outside), for the house picture that follows. Defaults: washer and dryer on the attic, the rest on the ground floor.
- `zephyr/stroom` gives `devices` and `rest_today_kwh`; `zephyr/settings/get` gives `house`; new `zephyr/house/layout` (admin). `core/devices.py` (`DayEnergy`), `stroom_devices.py` (store `zephyr.<entry>.house`).
- Tests: energy per day (midnight, unavailable, restart); in HA a plug of 2 kW for half an hour and a floor set from the panel; rows and names in vitest.

### 0.8.44 — Notice for entities of another Zendure integration
- A repair notice lists every setting that uses an entity of another Zendure integration (by integration, device maker or a `zendure` entity name), with what to use instead: set PV is read by ZEPHYR itself (otherwise counted twice), the inverter's counter for solar energy, the smart meter for P1 and cost counters, `sensor.zephyr_energy_charged`/`_discharged` for the battery. Checked at start and after every settings change.
- Diagnostics: all options and the list `foreign_entities`.

### 0.8.43 — Panel data for appliances, curtailing and short peaks
- New websocket commands `zephyr/appliances`, `zephyr/appliances/plan` and `zephyr/appliances/clear` (one run by index, one appliance, or all) for the panel (SPEC-ui-planner §4.1). The view gives per appliance the profile (watt per minute when learned), window and plug, and per planned run the advised start and saving.
- `zephyr/plan`: per future quarter `curtail_kwh` (surplus the planner counts as curtailed at a negative export price) and `export_cost` (what exporting it costs when nothing curtails); `curtail_mode` in the head.
- `zephyr/subscribe` (`now`): `curtail` (active, percent, switch, export blocked) and `appliances_revision`; appliance changes now trigger an update.
- `zephyr/events`: `peaks`, the short peaks per day the step filter left to the grid (B20).

### 0.8.42 — Live control stays live after a restart
- **A new installation starts in shadow mode** (as before). **Once you switch live control on, it stays on**: after a restart or reload of Home Assistant ZEPHYR goes live again by itself as soon as it can (P1 reporting, sets online), trying every 5 s for up to 10 minutes. If it cannot, it stays in shadow mode and shows a repair issue *ZEPHYR did not resume live control* with the reasons. Switching it off yourself stays off.
- The test-phase setting *Live control off after a restart* now defaults to **off**, and is turned off once for existing installations (config entry 1.2). Switch it on again to keep the old behaviour.
- Tests: new installation in shadow, live after a restart, the setting on, a set that stays away, the migration.

### 0.8.41 — Planned appliances: dishwasher, washing machine, dryer (B36)
- **New subentry *Appliance*** (ZEPHYR → Add appliance): name, kind (dishwasher, washing machine, dryer heat pump / condenser, other), optional smart-plug power and energy sensor, standard window (*from* — empty = from now — and *done by*; a time before the start = the next day). Dishwasher defaults to now → 07:00, the others 08:00 → 20:00.
- **Per appliance:** `button.zephyr_<name>_plan` (one run in the standard window; press again for another), `button.zephyr_<name>_clear`, `sensor.zephyr_<name>_planned` (number of runs; windows, kWh per run, profile source), `sensor.zephyr_<name>_best_start` (timestamp; cost, cost when started at once, saving, all starts) and, with a plug, `binary_sensor.zephyr_<name>_running`. Actions `zephyr.plan_appliance` (runs, start after, done before, fixed start) and `zephyr.clear_appliance`.
- **Planner:** every planned run gets the start that makes the **whole plan** cheapest (battery, solar, prices; candidates every 15 min in the window; a later start only when it saves at least €0.02), runs of one appliance one after another, a dryer after the planned wash. The plan then counts the runs in the expected use (timeline `appliances`). Battery energy left at the end of the horizon is valued at the mean buy price, so a late run on the battery does not look free.
- **Profiles:** first estimate per kind; with a plug, learned from the **recorder history at once** (raw history of the last 10 days) and from every later run (median per minute after 3 runs, last 20 kept). A run seen on the plug in its window fulfils the planned run; planned runs disappear after their window.
- Not yet: subtracting the appliances from the learned house profile (so typical runs stay in it and an announced run counts on top), automatic start, the panel card (UI chat).
- Diagnostics `appliances`. Tests: profiles, run detection, learned profile, windows, best start, two washes in a row, dryer after washer, the planner on solar; in HA the buttons and action, a run on the plug, learning from the recorder.

### 0.8.40 — Inverter power limit at a negative export price
- With *ZEPHYR curtails*, new optional settings **Inverter power limit** (a number entity in %, e.g. `number.solaredge_modbus_active_power_limit`) and **Inverter rated power** (W).
- While the export price is negative ZEPHYR sets the limit every 10 s so the inverter produces what the house and the batteries take: wanted production = solar now (solar power sensors) + measured grid power − 50 W, plus the power the sets could still charge (not when full), as % of the rated power. Written only on a change of at least 2 % (or to 0 / 100 %); back to 100 % when the price is no longer negative. Not fully off, because the import price is often still positive then.
- The planner counts the surplus as curtailed with a switch or with this limit (both need *ZEPHYR curtails*).
- Diagnostics `curtail`: `number_set`, `rated_w`, `limit_written`. Engine: `p1_now` (measured grid power).
- Tests: the wanted % and when to write; in HA the limit at a negative price and back to 100 %.

### 0.8.39 — Diagnose: energy counters
- New card **Energietellers** in Diagnose for ZEPHYR's own counters per set (SPEC-tellers T1/T2): charged, delivered and solar (kWh since the start), the part filled in after gaps (kWh and %), failed reads, an open gap (set unreachable or restart), and the latest gaps with duration, method (interpolated / from the state of charge / nothing to fill in) and kWh. With more sets also the installation's totals.
- `zephyr/events` gives `energy` (the counters' diagnostics).
- Tests: estimated share and gap order in vitest.

### 0.8.38 — Stroom: card Regeling, last 10 minutes
- New card on *Stroom*: the last 10 minutes of the controller, one sample per second.
  - Top: P1 against its target (0 W, or the airco), with the ±50 W band.
  - Bottom: the setpoint asked of the sets (dashed) and the battery power measured (+ charging).
  - Time ZEPHYR did not steer to zero is shaded.
- Below the chart: median recovery after a peak (> 150 W, back within the band), mean difference between asked and actual battery power while steering, number of peaks.
- *Stroom* refreshes every 5 s while open; on a phone the chart is drawn narrower so the labels stay readable.
- `zephyr/stroom` gives `regulation`; `core/stroom.RegulationLog`.
- Tests: window and one sample per second, peaks and recovery with an airco target; chart helpers in vitest.
### 0.8.37 — Short peaks counted (PLANNING 1.3)
- The step filter (B20) leaves short peaks (a boiling-water tap, a kettle) to the grid for up to 10 s; ZEPHYR now counts the energy of those peaks: the part of the grid power the controller did not see while a peak was held (not while charging, where the filter does not apply).
- Diagnostics `control.p1_filter`: `peak_kwh` (since the start), and per local day `kwh` and `holds` (last 14 days, in memory). Basis for the panel (Besparing) later.
- Tests: a 2 kW peak of 6 s counted; per day in the HA diagnostics.

### 0.8.36 — Solar now from inverters the sets do not see
- Bjorn 27-11: *Nu* showed sun 0 W at noon, because ZEPHYR only knew the PV on the Zendure set. The house was too low by the same amount.
- New option **Zonnepanelen-vermogen** (Instellingen → Bronnen, also in the options flow): one or more power sensors (W or kW) of inverters that are not on a set, e.g. SolarEdge. They are added up and added to the sets' PV. Live, no reload. ZEPHYR's own sensors are skipped (the sets' PV is already counted).
- Without a power sensor ZEPHYR estimates the power from the solar energy counter (step / time between steps, fading out when the counter stops); *Nu* then says *geschat*.
- `now` gives `solar_sets_w`, `solar_external_w` and `solar_estimated` next to `solar_w`.
- Tests: W/kW, unavailable sensors, counter estimate; in HA two inverters added to the sets' PV.

### 0.8.35 — Surplus solar at a negative export price (PLANNING 1.1/1.2)
- **Planner:** surplus solar at a negative export price now **costs money** unless something curtails it. Before, the planner assumed it was always curtailed, while a SolarEdge (or any inverter outside the sets) simply keeps exporting. Now it makes room in the battery before such hours when that pays.
- **New setting** *Surplus solar at a negative price* (planner): **Off** (default; exported, costs money) / **Another system curtails** (e.g. an export limiter with its own negative-price mode; the planner counts the surplus as curtailed) / **ZEPHYR curtails**.
- **ZEPHYR curtails:** at the start of every quarter with a negative export price (market price with the tariffs, as in the cost log) ZEPHYR blocks export of the sets' own panels (`gridReverse` 2, back to 1 afterwards; only on a change, at most once a minute, counted as a flash write and riding along with a command of the same step) and turns on the new optional **inverter curtail switch** (off again after). A template switch can drive any limiter or script. Without a switch only the sets' panels are blocked and the planner still counts the inverter's surplus as exported.
- With saldering (2026) the export price includes the energy tax and is rarely negative (48 quarters in the 2026 prices); without saldering (2027) it was 308 quarters.
- Backtest 2027 rules (2-2 to 18-11-2026, learned use, Solcast, wear €0.03, nothing really curtailed): the planner that knows the surplus costs money €245.33 incl. wear, the old assumption €246.19 (−€0.86/year, 3 fewer charge starts). Small, as expected from the few negative quarters. `tools/backtest.py --curtail` plans with the old assumption.
- Diagnostics: `curtail` (mode, export price now, negative, blocked, last error).
- Tests: planner step and choice with and without curtailing; `gridReverse` in the engine (once, again after 60 s, riding along); in HA the switch and `gridReverse` at a negative price and back.

### 0.8.34 — Screen Stroom
- New screen **Stroom** after *Plan*, with four cards:
  - **Nu:** the live flow between sun, grid, house and battery (SOC ring, airco part of the house).
  - **Nul op de meter vandaag:** share of the steering time the meter stayed within ±50 W of its target (0 W, or the airco's power when the airco is kept out of the battery), with a 5-minute strip over the day, energy imported and exported while steering, and the mean deviation. Goal 80 %. Only live steering counts (not shadow, charging or holding). Kept over a restart on the same day.
  - **Energie per route vandaag:** sun → house/battery/grid, grid → house/battery, battery → house/grid, split per closed quarter of the cost log; share of the sun used yourself, share of the house from own sources, mean price of grid → battery.
  - **Airco vandaag** (when set up, B41): kWh, share of the house, fed by sun or grid, cost of its grid power.
- `zephyr/stroom` websocket command; `core/stroom.py` (route split, zero score).
- Tests: route split and airco share, zero score (band, gaps, new day, restart); websocket in HA; strip colours in vitest.
### 0.8.32 — Cost log on the own energy counters, corrected after a gap (SPEC-tellers T3)
- **Charged, delivered and set PV per quarter now come from the own energy counters** (the change of the installation totals between the quarter boundaries), like the grid import and export from the P1 counters. The meter of 0.8.26 stays as the fallback (first quarter after a start, no counters). Each quarter says which one it used: `battery_source` = `counters` or `meter`.
- **Correction after a gap:** when the counters fill a gap, the filled energy is spread over the closed quarters of the gap by time, and the cost log of the current month is **evaluated again** from the first corrected quarter up to now (costs, the three situations, the pools of solar/grid in the battery, saldering part), with the day totals updated. Corrected quarters get `estimated: true` and `corrected_at`. The quarter in which the set returns no longer gets the whole fill as a jump.
- Limits: gaps that started more than 48 hours ago (or quarters from before this version, or in an earlier month) are not corrected; their energy is left out of the current quarter. The tariffs of the day are used again for the new evaluation.
- Every quarter now also keeps the inputs for a correction: `pools` (before the quarter), `stored_kwh`, `daylight`, `coverage`. CSV export: `battery_source`, `estimated`, `corrected_at`.
- Diagnostics: `costs.gap_corrections` (the last gaps, kWh, whether corrected).
- Tests: shares of a gap per quarter; a corrected log equals one that measured the energy (costs, pools); day totals; quarters without inputs; in HA quarters from the counters and a gap over a quarter boundary corrected without a jump.

### 0.8.30 — Weekend profile and solar day total (diagnostics 27-11)
- **Load profile:** an hour of a day type that has not been learned yet (the weekend after a first install) now takes the other day type's hour, before the flat mean. Saturday's plan keeps the shape of the day (quiet night, busy evening) instead of the same 0.6 kWh every hour.
- **Solar history:** a missing hourly reading of the solar counter (e.g. a restart) no longer drops the whole day: the step between the readings around it is spread evenly over the hours. On 26-11 the real production stayed empty because of one missing hour.
- Tests: the vacation test now uses the fixed test day too (it failed on a real date other than 26-11).

### 0.8.29 — Recharge below the minimum starts right below min_SOC
- **Recharging below the minimum** (self-consumption in standby, SPEC-basis §10) started only at min_SOC − 1: with min_SOC 10 % and a set that reports whole percents, at 8 %. It now starts as soon as the SOC is below min_SOC (9 % with 10 %) and goes on up to min_SOC, with the same gentle power (default 300 W). Delivering still waits until min_SOC + 2 (hysteresis), so the battery does not swing around the minimum.
- Tests: recharge at 9 % and 5 % with min_SOC 10 %, none at 10 %.

### 0.8.28 — Energy counters fill their gaps (SPEC-tellers T2)
- When a set reports again after more than 60 s, the gap is **filled**:
  - **interpolate** (gap ≤ 15 min, same direction, power before and after within 20 % or 200 W): the power linearly between the report before and after; checked against the change of the energy in the packs (Σ capacity × SOC per pack), within the SOC resolution (1 % of the capacity) + 2 %;
  - **from the SOC** otherwise: the packs' gain divided by the charge efficiency (0.92), or their loss times the delivery efficiency (0.88), minus what was already counted during the hold. Net only; a change within the SOC resolution fills nothing;
  - set PV in the gap: the last power held by daylight (sun at the middle of the gap), 0 at night; off-grid: the last power held when it was above 0.
- **A restart of Home Assistant is a gap** from the last stored state: the counters now store their last powers, pack energy and direction too, in wall-clock time.
- Filled energy counts in the counters and in `estimated_kwh`; every gap is logged (start, end, seconds, method, kWh per counter, pack change, restart) in `last_gap` and the diagnostics (last 10). Not yet in the cost log (T3).
- Tests: short gap interpolated, other power and long gaps from the SOC, SOC drop, interpolation that disagrees with the packs, set PV by day and night, restart, unknown pack capacity; in HA a gap filled when the set returns.

### 0.8.27 — Own energy counters per set (SPEC-tellers T1)
- **New sensors** (kWh, `total_increasing`, usable in the Energy dashboard): per set `sensor.zephyr_set_<n>_energy_charged` and `_energy_discharged` (from `outputPackPower` / `packInputPower`, AC), `_solar_energy` (only for sets with PV inputs); for the installation `sensor.zephyr_energy_charged`, `_energy_discharged` and `_solar_energy`. Diagnostic, disabled by default: off-grid, battery side (DC) charged/discharged, from the grid, to the house.
- ZEPHYR integrates the powers of every read itself (zenSDK has no energy counters). A read that fails keeps the last power for **60 s** after the last good report; after that a **gap** starts, recorded (start, end, powers, energy in the packs) but not yet filled (T2). The installation totals add the increases of the sets, so a set that disappears or is replaced never makes them drop.
- States are kept in `zephyr.<entry>.counters` (every 5 minutes and on unload); a restart continues from the stored state. Entities write their state only when the rounded value changes (recorder).
- Diagnostics: `energy_counters` (totals, per set the counters, failed reads, open gap, the last gaps).
- Tests: constant power for a quarter, hold within and beyond 60 s, a long pause between reports, set PV as solar, totals with a replaced set, restore; in HA the sensors, hold, reload and diagnostics.

### 0.8.26 — Cost log: battery from the pack powers, set PV once (B44 T0)
- **No double count of the sets' own PV.** The cost log took the battery from the set's net exchange with the house (`gridInputPower − outputHomePower`), which includes the PV inputs of the set, and also counted those PV inputs as solar. 500 W from the set's own panels counted as 500 W *delivered from the battery* plus 500 W solar: the house use 500 W too high and the savings too high. Now: charged = Σ `outputPackPower`, delivered = Σ `packInputPower` (AC, MEET-zensdk W1), set PV only as solar. Without PV nothing changes.
- **Hold of 60 s per set:** a set that cannot be read keeps its last pack and PV power in the cost log for 60 s after its last good report, also when the controller already counts it as offline. With several sets an unreadable set no longer drops out silently: the battery coverage of the quarter (`complete`) only counts while every set is counted.
- Regulation unchanged (still the set's net exchange with the house).
- Tests: set PV with an idle battery, hold within and beyond 60 s, coverage with a missing set. Spec: `SPEC-tellers.md` (own energy counters, T1–T4 follow).

### 0.8.25 — Live: safer second-controller stop, set left alone while calibrating
From the check before going live (26-11, `TOETS-live-basis.md`).
- **Second controller detected:** ZEPHYR now writes 0 W once before going back to shadow mode, as when the switch is turned off by hand. Before, the set stayed at ZEPHYR's last power (for example 2 kW delivering).
- **Set calibrates itself (`socStatus` 1) or is in bypass (`pass` > 0):** ZEPHYR writes nothing to it: no 0 W, no standby after 5 minutes, no SOC limits, also not when stopping (SPEC-basis §8). Its own limit changes then no longer count as a second controller; neither do those of a set reporting a fault.
- `tools/replay_opname.py`: the entity ids of the recording are required options, no defaults from one installation.
- Tests: live scenarios for the basic functions with the slow 2400 Pro model (`tests/scenarios/test_live_basics.py`: zero on the meter, battery full from solar then standby and delivering in the evening, hysteresis when full, empty, Standby, fast charge/discharge, `socLimit`); no commands to a calibrating or bypassed set; 0 W after a second controller; a calibrating set stays live.

### 0.8.24 — Diagnose: plan tegen werkelijkheid; Instellingen: vakantie
- Diagnose has a card **Plan tegen werkelijkheid** for the last 14 days (from `zephyr/plan_check`): expected against actual for house use, sun, import, export and costs, with the difference in %, plus a small pair of bars per day.
- Instellingen has a group **Vakantie**: status (on by hand, automatic, since when, until when), a *Terug op* time and buttons to start or stop. The panel switches ZEPHYR's own vacation switch and end-time entity, so automations and the panel go one way (B42). The option *vakantie bij afwezigheid* moved into this group.
- `zephyr/settings/get` returns the vacation state and its two entities.
- Tests: vacation in the settings view; difference % of the plan check.

### 0.8.23 — Besparing: prices from EnergyZero for working out earlier days
- Bjorn's first run (26-11): 48 days worked out, but 1 138 of the hours had no price, because his Nord Pool sensor has no `state_class` and so no hourly statistics in HA.
- The form *Eerdere dagen terugrekenen* now offers **EnergyZero (marktprijs NL per uur)**: ZEPHYR fetches the bare Dutch day-ahead market price per hour from EnergyZero's public API (no key), one request per day, only when you press *Terugrekenen*. Default when the price sensor has no `state_class`; a sensor with statistics can still be chosen.
- Days EnergyZero gives no prices for are named in the result (*probeer het later nog eens*); the rest goes on.
- The last choices of the form are kept in the browser.
- Tests: EnergyZero answer and query; in HA a run with a working and a failing day (mocked), the sensor's statistics not asked.

### 0.8.22 — Besparing: days before the cost log worked out from hourly statistics
- **Screen *Besparing* → *Eerdere dagen terugrekenen*** (administrators, with P1 counters set): for the days before the cost log, ZEPHYR works out the savings again from Home Assistant's hourly statistics: grid import and export (the P1 counters), the battery's charge and discharge counters (for example those of the previous integration), solar and the price sensor. Every hour goes through the same calculation as a quarter of the cost log, so all days use one method (Bjorn, 26-11, choice 2).
- Those days are marked: hatched in the day chart, *teruggerekend per uur* on hover, and a line in *Wat telt mee*. Hours without a counter reading do not count (the day is then incomplete); hours without a price get no amount. Working out again replaces the previous run; *Teruggerekende dagen weghalen* removes them. Days the cost log measured itself are never touched.
- Websocket `zephyr/savings/backfill`; `zephyr/savings` adds `measured_since`, `backfilled_days`, `can_backfill`, `hourly` per day.
- **Card *Nu*:** the battery chip from 0.8.18 is gone again; the card *Accu* right next to it already shows the percentage (Bjorn, 26-11).
- New core module `core/backfill.py`. Tests: a day worked out like the cost log, night charging and missing hours, counters per hour; in HA a run, a second run, clearing and the errors.
### 0.8.21 — Plan against reality (B38)
- The planner keeps the **day-ahead plan**: every new plan overwrites what it expects for tomorrow (per quarter: use without the air conditioner, solar, grid import and export, cost, SOC); at midnight that is fixed, so a day is compared with the plan as it stood at the end of the day before. Only with tomorrow's real prices (not the indicative pattern). Stored with the planner (survives a restart).
- Every cost quarter gets `ahead_load_kwh`, `ahead_excluded_kwh`, `ahead_solar_kwh`, `ahead_import_kwh`, `ahead_export_kwh`, `ahead_cost`, `ahead_soc` (also in the CSV export, with `excluded_kwh` and `vacation`). Day totals add the expectation and the matching measured values over the quarters that have both, plus the absolute error per quarter for use and solar.
- New websocket `zephyr/plan_check` (`days`, default 14): per day expected / measured / difference for use, solar, import, export and cost, the SOC at the end of the day, and a summary over the finished days (mean absolute difference per day). Diagnostics: `costs.plan_check` (7 days).
- Tests: day totals and summary in the core; the day-ahead plan in the cost quarter and the websocket in HA.

### 0.8.20 — Panel: screen *Besparing* (M6 part 2)
- New menu item **Besparing**: what the battery saved, from the cost log (B38).
  - *Vandaag / Deze week / Deze maand / Dit jaar*: the amount saved (green) or lost (orange), with bars *Zonder accu* and *Betaald*; a warning when quarters are incomplete (HA off, no price).
  - **Where it comes from:** *Zon bewaard* (solar stored and used later) and *Prijsverschil* (cheap charging, dear delivering), with kWh charged and delivered and the saving per delivered kWh.
  - **Per day, last 30 days:** a bar per day; incomplete days lighter. One outlier (such as a test day) is cut at twice the typical day and drawn with an arrow and its amount, so the other days stay readable.
  - **What counts:** comparison with and without battery, fixed costs left out, net metering until 2027, since when the cost log runs.
- On a phone the period buttons read *Vandaag / Week / Maand / Jaar*.
- Websocket `zephyr/savings`.
- Tests: `zephyr/savings` (periods, week from Monday, incomplete and short days), day scale with an outlier, texts NL/EN.

### 0.8.19 — Holidays from Workday
- New optional setting **Workday sensor** (*Werkdag-sensor*, planner group): a `binary_sensor` of the Workday integration. When set, the planner asks Workday (`workday.check_date`) per day whether it is a workday, so a public holiday such as Christmas or King's Day counts as a *weekend* day: in the plan for today and the next two days, and when learning the load profile (live and from the recorder). Without the setting nothing changes: Saturday and Sunday are weekend.
- Setup suggests the Workday sensor when there is one. If Workday does not answer, the weekday decides.
- Diagnostics: `planner.inputs.day_types` shows the day type per day.
- Tests: `day_type_of` with holidays; the planner with a mocked `workday.check_date`.

### 0.8.18 — Panel: battery % in Nu, spread, use profile in Diagnose
- **Card *Nu*:** a battery chip next to the action (*46 %*, orange at 20 % or less), so on a phone it is clear at once how full the battery is.
- **Prices:** today and tomorrow show the **spread** as a percentage of the cheapest quarter (*spread 81 %*), with an explanation on hover; with prices around zero or below, the difference in euro.
- **Diagnose → Verbruiksprofiel:** the learned use per hour the planner works with, *Werkdag* and *Weekend*: house in blue, the air conditioner hatched on top (B41), day totals, and hours not learned yet lighter (there the planner uses the mean, which the screen names). An empty weekend says so.
- `zephyr/events` adds `profile` (source, hours, mean, per day type house/air conditioner/counts/min_count).
- Tests: profile in the events view (with the air conditioner apart), spread percentage, profile sums.

### 0.8.17 — Panel: solar in the action band (SPEC-ui-airco §3.2, UI-A3)
- **Solar lane under the action band** (design A, Bjorn 26-11): a small yellow bar per quarter, height = solar relative to the sunniest quarter in view; full yellow = measured, lighter = forecast. A **green top** marks *solar to spare*: more solar than the house and the air conditioner use, so the battery can charge from solar. Legend *Zon* and *Zon over (accu kan laden)*.
- Quarter details also show the air conditioner: *Airco 0,30 kWh (niet uit de accu)*; *huis* is now the house without the air conditioner, in the past as well as in the plan.
- `zephyr/plan`: every quarter has `excluded` (kWh of the air conditioner outside the battery, B41): from the planner for the future, from the cost log for the past; `load` of a past quarter is the house minus the air conditioner, like the planner's.
- Tests: plan view with the air conditioner (past and future), the solar lane.

### 0.8.16 — Panel: Blokken and Waarom follow the chosen period
- The cards *Blokken* and *Waarom dit plan* now follow *Vandaag / Morgen / 48 uur* like the chart (Bjorn, 26-11). *Vandaag*: what is still to come today, a block over midnight included. *Morgen*: every block that touches tomorrow (or *Nog geen blokken voor morgen*). *48 uur*: everything still to come. The cheapest charge time and the most expensive moment are taken from the same period; the plan's reason (about now) is left out for *Morgen*. Titles say which period.
- The period is kept by the panel (`zephyr-prices-plan` reports a change); still remembered in the browser.
- Test: `blocksFor` for the three periods, also over midnight.
### 0.8.15 — Vacation (B42)
- **`switch.zephyr_vacation`** (*Vacation*) with **`datetime.zephyr_vacation_until`** (*Vacation until*): set an end and the switch goes off by itself at that moment.
- **Option *Vacation when nobody is home*** (default off): on by itself after 24 hours with nobody home (`zone.home` = 0), off as soon as someone is back.
- **Planner while away:** uses the learned vacation use, else the **standby use** (lowest night hour of the normal profile); the air conditioner counts as off. After the end the normal profile applies again, so the battery is charged for the return home at the cheapest moment.
- **Learning:** vacation hours go into a separate **vacation profile** (stored, used next time), not into the house or air-conditioner profile. The recorder fill skips past vacations (periods kept 400 days).
- **Cost log:** quarters while away get `vacation: true`.
- Diagnostics: `planner.vacation`, `planner.vacation_profile`, `inputs.vacation`. Panel: the option in Settings (Planner).
- Tests: state, end, automatic, periods, base load; Home Assistant: switch + end, plan before/after the end, learning apart, away via `zone.home`, cost log flag.

### 0.8.13 — Panel: fixes after the first test of UI-8
- **Snel laden / Snel ontladen stay in place.** In a fast mode the buttons used to swap places, so a second tap could switch from fast discharge straight back to fast charge (seen in Bjorn's diagnostics of 26-11). Now both buttons keep their place; the running one reads *… stoppen* and goes back to the mode it came from, with a line *Daarna terug naar …*. After a tap the buttons wait until the new mode shows (at most 5 s).
- **Diagnose in shadow mode:** the counters are what ZEPHYR *would* send; the screen now says so (*Opdrachten, laatste 24 uur (schaduw)*). `zephyr/events` adds `shadow`.

### 0.8.12 — Panel: Diagnose and control (SPEC-ui §4.1, §4.2, §4.5; UI-8, UI-A4)
- **Header:** for administrators the mode is a choice list and *Rekent mee* / *Stuurt* a button. Turning live control on asks first and lists why it cannot start now (set offline, P1 silent, …); turning it off is immediate. The panel uses ZEPHYR's own entities (`select` mode, `switch` control), the same path as automations.
- **Plan:** buttons *Snel laden* and *Snel ontladen*; during a fast mode a line what it does and *Stoppen, terug naar …* (the mode it came from).
- **Screen *Diagnose*:** *Diagnose downloaden* (HA's diagnostics of the installation), *Kostenlogboek exporteren* (`zephyr.export_costs`, shows file and number of quarters), writes per set over 24 hours (power, flash, relay, failed, last error) and the **last 100 events**: other reason, other mode, live on/off, write test, second controller, flash writes, and the air conditioner going outside the battery and back (UI-A4).
- Websocket `zephyr/events` (`core/events.py` makes events from the decision log). `zephyr/subscribe` adds `entities` and `previous_mode`. The decision log keeps the reason's parameters (`reason_params`), so an event has its full sentence.
- Tests: events from the log (changes only, flash, air conditioner, limit 100, older lines), `zephyr/events`, entities in the snapshot; frontend: event sentences, fast buttons, live blockers in NL/EN.

### 0.8.11 — Panel: change settings (SPEC-ui §3.4, UI-7; SPEC-ui-airco §3.3, UI-A2)
- **Screen *Instellingen* is now editable for administrators.** Battery limits, tariffs, planner, zero meter and test phase save at once and go live **without a reload**: the engine gets the new limits, the planner plans again, a new supplier fetches the tariff table. *Standaard terugzetten* next to every changed field; an error shows under the field (for example *Kies een waarde van 5 tot en met 50 %*).
- **Sources and corrections** (P1, prices, solar, counters, air conditioner) are collected and saved together with *Bewaren en herstarten*, because ZEPHYR restarts for them. Rules over several fields (P1 pair, air conditioner) are checked first.
- Entity fields: pick or type an entity (filtered on domain and device class), clear with ×; counters as chips. Air-conditioner modes as a multi-select; at least one mode (switch off by clearing the counter).
- **Status next to the air-conditioner fields:** the counter's rhythm (*elke 8,5 min een stap van 0,25 kWh*, or *nog geen meting*), the climate entity's mode and action (*Verwarmen · draait*, *niet beschikbaar*).
- **Websocket `zephyr/settings/set`** (administrators): `changes` and `reset`, checked with the same ranges, steps and rules as the options flow (`settings_schema.apply_changes`); answers `ok`, `changed`, `reload` or `errors` per field.
- **Options:** a change of only live fields no longer reloads the installation, also from HA's options flow. New check in the options flow: a climate entity needs the air conditioner's energy counter (`excluded_needs_counter`).
- Tests: every field once through `settings/set` (live without reload, sources with reload), errors, administrators only, settings reach engine/planner/tariffs, air-conditioner status, options-flow check; frontend: number input in NL/EN, entity choice, multi-select, texts for every error.
### 0.8.10 — Planner actions: recalculate, reset profile, get plan
- **`zephyr.recalculate`**: a new plan now (for the panel and automations; otherwise every quarter and on new prices).
- **`zephyr.reset_profile`** (PT9): forgets the learned consumption (house and air conditioner). By default fills it again from the recorder (`refill: true`); with `refill: false` it starts empty and learns from the coming hours. Returns the source and the number of hours.
- **`zephyr.get_plan`** (response only): state, figures, blocks and the quarters of the current plan, for automations and templates.
- Without a running planner (no price sensor) the actions give a clear error.
- Tests: all three actions in Home Assistant.

### 0.8.9 — Planner without the air conditioner (B41, steps 2 and 3)
- **The consumption profile is the house without the air conditioner** while it ran in a mode the battery may not feed; the air conditioner is learned apart (`excluded_profile`). Before, its heating (~2 kWh/h at midday) counted as house use the battery would cover, so the plan charged and held more than needed.
- **Solar in the plan follows the control:** with the air conditioner running, solar first covers the rest of the house; the battery only gets a surplus once the air conditioner is covered too (`solar_for_planner`, SPEC-airco §5).
- **First fill from the recorder** takes the air conditioner's hourly counter out of the house, times the share of the hour the climate entity was in a blocked mode (`hvac_mode` history). A profile learned before the air conditioner was set is **filled again once** (Bjorn: 64 h with the air conditioner in it); with too few recorder hours the old profile stays.
- **Cost log:** per quarter `excluded_kwh`, the air conditioner's kWh while it was excluded (from the counter steps); the profile learns from it.
- Plan timeline per quarter: `excluded` (kWh, expected), for the panel's chart (SPEC-ui-airco §2.2). Diagnostics: `planner.excluded_profile`, `control.excluded_load.energy_total_kwh`.
- Tests: solar rule, blocked share, history hour, energy total; Home Assistant: first fill with climate history, refill when the air conditioner is added, live learning, cost log field.

### 0.8.8 — Panel: air conditioner in the card *Nu* (SPEC-ui-airco §3.1, UI-A1)
- **Card *Nu*:** while the air conditioner runs in an excluded mode a line *Airco 1,8 kW · niet uit de accu*; when the battery covers only part of it, also *(1,1 kW nu buiten de accu)*. In an allowed mode *Airco verwarmen · mag uit de accu*. A *schatting* chip with an explanation while the power estimate is starting or fading. No line without a running air conditioner.
- **Settings:** the three air-conditioner fields move to a new group *Correcties* (they correct what the battery covers, they are not a source).
- Websocket `zephyr/subscribe`: section `excluded` (active, power, part outside the battery, mode, action, estimate quality).
- Removed a leftover conflict marker from the changelog.
- Tests: snapshot with and without climate entity; frontend: the airco line in all states.

### 0.8.7 — Cell balance judged near full (SPEC-celbalans.md)
- **Correction of 0.8.4.** The cell difference of LiFePO4 says little in the middle of the charge (the voltage curve is flat there); an imbalance shows near full. The panel now judges the cell difference only when a battery is **near full** (SOC ≥ 95 % or highest cell ≥ 3.40 V) **with a small current** (≤ 0.1 C: ≈ 290 W for an AB3000L, 240 W for the built-in battery, 200 W for an unknown type).
- Labels: **Good** (≤ 30 mV), **Balancing** (≤ 100 mV, normal near full; the set works it away) and **Imbalance** (> 100 mV). Outside a judged moment the value is shown with *judged when full*.
- **Per day** the largest judged difference; days without a judged moment stay empty. The history of 0.8.4 (measured mid-curve) is dropped at the update.
- **In short:** *stays out of balance* on 3 or more of the last 7 days (advice: let the set charge fully a few times, then Zendure), *out of balance now*, *was out of balance on …*, or *not (nearly) full this week*. The summary shows the cell difference now, or of the last judged day.
- Written on the clean side: own thresholds from public LiFePO4 knowledge and own measurements; a separate review compares with other projects functionally (`OPDRACHT-toets-celbalans.md`).
- Tests: judged moment (SOC, cell voltage, current per type), labels, the diagnostics of 26-11 (50/120/70/40 mV → Balancing/Imbalance/Balancing/Balancing), history incl. dropping the old rule; frontend summary.

### 0.8.6 — Air conditioner not from the battery (B41, step 1: control)
- **New options *Air conditioner: energy counter*, *climate entity* and *not from the battery when*** (default: heating). While the air conditioner runs in such a mode, zero-meter control (also in Dynamic Forecasting) does not deliver for it: the battery only covers the rest of the house, the air conditioner takes from the grid. Solar surplus still charges the battery, and ZEPHYR never charges from the grid for it.
- **Power from a coarse energy counter** (`core/excluded_load.py`): seen live, steps of 0.25 kWh every 8-9 minutes. Power = step / time since the previous step; between steps at most step / time since the last step, so a stopped device fades out by itself. The climate entity switches at once: `hvac_action` idle/off → 0, a start begins with the power of the previous run. Without a climate entity the load is always excluded.
- Decision log: `excluded` (W) on each decision and as a parameter of *delivering*; diagnostics: section `control.excluded_load` (mode, action, estimate, mean step interval).
- Panel (Settings, Sources): the three new fields with texts; a select with several values shows them all.
- Tests: estimator (steps, fading, start/stop, counter reset), closed-loop scenarios (battery delivers only the rest, estimate above the house demand, solar surplus, stop), Home Assistant (options, climate states, diagnostics).
- Next steps (B41): planner learns the house without the air conditioner; cost log per quarter.

### 0.8.5 — Panel: screen *Instellingen*, reading (SPEC-ui §4.4, UI-6)
- **Screen *Instellingen*:** groups on the left (Battery and limits, Sources, Tariffs, Planner, Zero on the meter without planner, Test phase) with the number of changed fields; per field the label, a short help text, an **i button with more explanation** (tap, one open at a time, also with the keyboard), the value, and for a changed field a dot and *standard: …*. Sources show how they are doing (*reports every 1 s*, *96 prices in the sensor*, *not set*, *not found*); with a supplier the tariff fields show the amount *in use* from the tariff table.
- Changing settings from the panel follows in UI-7; until then the screen points to the options flow. Users who are not administrators see a read-only note.
- **`settings_schema.py`:** one list of fields (group, type, range, step, unit, standard value, reload needed). A test keeps it in step with the options flow (same keys, ranges, steps and units), another checks that the panel has NL and EN texts for every field.
- **Websocket `zephyr/settings/get`** with values, *changed* flags, source status, suppliers, tariffs in use and `can_edit` (administrator).
- Tests: schema, options-flow sync, the command for an administrator and a read-only user, texts per field; frontend: number formatting by step, texts in both languages.

### 0.8.4 — Panel: screen *Accu* / *Sets* with the batteries in the set (SPEC-ui §4.3, UI-4)
- **Screen *Accu*** (one set; *Sets* with more): a summary (batteries online, SOC spread, warmest battery, largest cell difference, one sentence *in short*), the **set card** (status, SOC with limits, kWh, power, inverter temperature, last 100 %, relay switches in 24 h, limits in the set, *+ Add set* to the integration page) and **Batteries in the set**: per battery SOC, kWh, power on the battery side, temperature, lowest–highest cell voltage and the **cell difference** with *Good* (≤ 30 mV), *Watch* (≤ 80 mV) or *High*.
- **Cell difference only judged between 20 and 90 % SOC.** LiFePO4 cells spread out near full and empty (diagnostics 26-11: 120 mV on a full AB3000L); there the value is shown as *not judged*.
- **Cell difference per day, last 7 days** per battery (highest judged value, ▲ on days the battery reached 100 %), and **what the set did in the last 24 hours** from the cost log.
- **Websocket `zephyr/sets`** (no serial numbers, B18). New **pack history** (`core/packs.py`, `pack_recorder.py`): per battery and day the largest judged cell difference and whether it was full, 14 days in `zephyr.<entry>.packs`; when each set was last full.
- The panel refreshes the screen every 10 s while it is open. Several sets are shown one below the other for now; the overview for 2–3 sets follows in UI-5.
- Tests: core (cell difference, status window, history, pruning), HA (`zephyr/sets` with the four packs of the test set, no serials in the answer), frontend (pack names, summary).

### 0.8.3 — Planner: grid-charge threshold
- **New option *Planner: grid-charge threshold*** (default **€0.01 per kWh**): charging from the grid must win at least this much per kWh before the planner plans it. It counts only in the planner's choice, not in the costs, and not for solar into the battery. Seen at a tester: 0.78 kWh charged from the grid at €0.51 at 10:30 for about a cent of gain from the solar bonus.
- Backtest (1 Oct – 18 Nov 2026, learned consumption, Solcast, wear €0.03; costs incl. wear): €0 → 96.29 / 102.96, **€0.01 → 96.21 / 102.97**, €0.02 → 96.58 / 102.81, €0.05 → 98.18 / 103.84 (net metering 2026 / 2027). €0.01 is the lowest over both rules, with about 15 % less grid charging and fewer charge starts. Backtest tool: `--grid-charge`.
- Diagnostics: `grid_charge_cost` in the planner settings. Tests: the threshold against brute force, no charge for a cent, solar charging untouched.
- Tests: the planner tests in Home Assistant now always start on 26-11-2026 in Amsterdam; they failed depending on the real time of day (prices were set for the real day before the clock was frozen).

### 0.8.2 — Panel: what happened today (SPEC-ui §3.2, UI-3)
- **Prices and plan before now** come from the cost log: the band under the chart shows what the battery actually did per quarter (charge, deliver, hold; export when the plan said X and energy went to the grid), lighter than the plan. Less than 0.05 kWh in or out of the battery counts as holding. A quarter without a record (HA was off) stays empty, with *Not recorded* in the tooltip.
- **Measured SOC** as a solid line before now, joining the dashed expected line at *now*; broken where a quarter is missing. Prices before now as they were in the cost log (falls back to the price sensor).
- **Cost log:** new field **`soc`** (state of charge at the end of the quarter, %), also as the last CSV column of `zephyr.export_costs`. Quarters recorded before this version have no SOC, so today's measured line starts at the update.
- Tests: core (action from a cost quarter, past quarters from the log, gaps), HA (a closed quarter shows up in the panel's plan), frontend (measured SOC pieces).

### 0.8.1 — Panel: prices and plan (SPEC-ui §4.2, UI-2)
- **Card *Prijzen en plan*** on the Plan screen, as approved in the design:
  - **Price line:** the all-in price now; today and tomorrow lowest–highest, mean and the times of the lowest and highest quarter; *known since hh:mm* for tomorrow, or *not known yet (usually around 13:00)*.
  - **Period:** Today | Tomorrow | 48 hours, default Today (00:00–24:00); the choice is remembered in the browser.
  - **Chart:** the all-in price per quarter as bars (past lighter, the running quarter dark, tomorrow's indicative pattern striped, negative prices below zero), the lowest and highest quarter of each day labelled, the planned action as a coloured band underneath, the expected state of charge as a dashed line, *now* marker and day boundary. Point at a quarter (or use the arrow keys) for time, buy and export price, action, SOC, solar and consumption. On a phone the chart scrolls sideways and starts 2 hours before now.
  - Notes for *No prices*, the price reserve and an indicative tomorrow; above the chart a note when the mode is not Dynamic Forecasting or ZEPHYR only calculates (shadow).
- **Cards *Blokken*** (the coming blocks with time, action, kWh and average price; *tomorrow* where it applies) and ***Waarom dit plan*** (the planner's reason, the cheapest charging block, the most expensive moment, indicative tomorrow).
- **Websocket `zephyr/plan`:** every quarter from local midnight today to the end of tomorrow (92/100 on DST days) with market, buy and sell price; from now on also action, SOC, solar, consumption and indicative; the blocks, the reason and when tomorrow's prices were first seen. Quarters before now carry the price only; what happened follows in UI-3 from the cost log. The panel fetches it when the plan changes and every 5 minutes.
- Core: `core/plan_view.py` (pure, tested incl. DST days); the planner keeps when each day's prices first appeared.
- Tests: core (quarters, past/now, indicative, DST, view), HA (`zephyr/plan` with and without price source), frontend (days, stats, bands, scale with negative prices, ticks, SOC line, blocks).

### 0.8.0 — M6: own panel in the sidebar, step 1 (SPEC-ui, UI-1)
- **Panel *ZEPHYR*** in the Home Assistant sidebar (`/zephyr`), for every user. Header with logo, menu (Plan, Sets — *Accu* with one set —, Settings, Diagnostics), the mode and whether ZEPHYR controls (*In control*) or only calculates (*Shadow*). The Plan screen shows three cards:
  - **Now:** the action with power and the reason in one sentence, the grid power, and in shadow mode a note that this is what ZEPHYR would do.
  - **Battery:** state of charge, kWh of capacity, a bar with the min/max limits and the planning buffer, sets online.
  - **Next step:** the next block of the plan with time, countdown, kWh and average price; *indicative* while tomorrow's prices are unknown; clear texts without a price source and with *No prices*.
  - The other screens follow in UI-2 … UI-8 and show *comes in a later version* for now.
- **Websocket `zephyr/subscribe`:** a snapshot of now, then an update at most every 2 s (P1, sets, new plan). On a reload the panel gets `unloaded` and subscribes again; the panel stays in the sidebar during a reload and is removed when the installation is removed or disabled.
- Light and dark follow Home Assistant; Dutch or English follows the user's language; numbers and times in the user's notation and Home Assistant's time zone. Without connection the last values stay visible (grey) with the time.
- **Frontend:** TypeScript + Lit, built with Vite to one module `custom_components/zephyr/frontend/zephyr-panel.js` (44 kB), plus the logo and the fonts Inter and Space Grotesk (SIL OFL, latin only). Source in `frontend/`; CI builds it and fails when the committed build differs.
- Manifest: `after_dependencies` frontend, http, panel_custom, websocket_api. Without Home Assistant's frontend the integration loads as before, without panel.
- Tests: panel registration (also over a reload and removal), the subscription (snapshot, update, unsubscribe, reload), without installation and without price source; frontend: number/time formatting (incl. DST) and texts.

### 0.7.10 — Planner: no "charge" with a full battery
- A planned charge slot (L) that takes nothing from the grid — the battery is already full, so it costs the same as holding — is now shown and carried out as **hold** (H). The plan, the blocks, the timeline and `sensor.zephyr_plan_action` no longer say *charge* while nothing charges; the state is *Battery full* when that is the case now. Seen at a tester: a "charge" block of 14 hours of which only the first 45 minutes charged.

### 0.7.9 — Planner: price reserve after midnight (SPEC-planner §2.1, PT2, PT6, PT12)
- **Saved prices:** every calculation saves the known prices (today and tomorrow, by start time) in ZEPHYR's storage, so also over a restart. When the source has no price for the running quarter — the HACS sensor that does not move on after 00:00, or a sensor that is empty or unavailable — the planner fills the gaps with the saved prices for the same time slots and plans as usual.
- State **`price_reserve`** (Prijzenreserve) and the reason starts with *Bewaarde prijzen (de bron heeft nog geen prijs voor nu).* While on the reserve the planner checks the source every minute; the source always wins as soon as it has prices. Saved prices are never moved to another day; without a saved price for now it stays *No prices* + N.
- Diagnostics: `price_source` (source / reserve) and `reserve_slots`.
- Tests: a night from 22:00 with a source that loses tomorrow at 23:59, goes unavailable, a reload, and the source coming back; merge and update of the reserve in `core`.

### 0.7.8 — Planner: consumption profile from the recorder at the start (SPEC-planner §2.3)
- **First fill from the recorder's hourly statistics** (last 28 days) while fewer than 48 hours have been learned: house = import − export + solar − battery per hour, from the cost log's DSMR counters, the solar counter and the hourly mean of `sensor.zephyr_power`. Only complete hours count; the fill replaces the profile from 24 hours on. Without the recorder or the counters: the cost log as before.
- Why: at a tester the profile had learned only five night hours (0.23 kWh/h) and used that for every hour of the day, so the planner saw far too little consumption.
- Diagnostics: `profile_source` (recorder, cost log, stored). Manifest: `after_dependencies: recorder`.

### 0.7.7 — Test dashboard: view *Plan*
- New view **Plan** in `dashboards/zephyr-test.yaml` (standard cards only): mode and live switch, plan now with reason next to what ZEPHYR does (live or shadow), key figures (planned grid charge and cost, export, battery empty at, expected grid cost), the blocks, a table **per hour** from the plan's timeline (actions per quarter, price, solar, consumption, grid, SOC at the end of the hour) and 24-hour history of plan vs ZEPHYR, SOC, setpoint and grid.
- Fix: the block table used a folded YAML block (`>-`), which joined the table rows into one line; now a literal block (`|-`).

### 0.7.6 — M5: mode Dynamic Forecasting carries out the plan (SPEC-planner §7)
- **New mode `dynamic_forecasting`** (Dynamische Forecasting) in `select.zephyr_mode`, only when the planner runs (a price sensor is chosen). The engine takes the plan's action for the running quarter:
  - **L** (charge from the grid): full charge power. Starts only after 2 minutes without grid charging; keeps going 10 s after the plan stops saying L; at max SOC it holds instead (the plan may still say L with a full battery).
  - **H** (hold): zero on the meter without delivering; charging from solar surplus continues.
  - **N** (deliver) and no plan: zero on the meter.
  - **X** (export, only with the option on): full deliver power, not within 2 minutes after grid charging, stops at min SOC.
  - No price for now: the plan says N, so never grid charging without a price.
- New reasons: *Plan: laadt … W uit het net*, *Plan: laden uit het net start na een pauze van 2 minuten*, *Plan: vasthouden*, *Plan: levert … W terug uit de accu*.
- The plan is recalculated on a mode change (§5).
- Shadow mode as always: the twin carries out what ZEPHYR would do; live with `switch.zephyr_control`.
- Not yet: price reserve after midnight (c), the restart check of §7 (with ZEPHYR as the only controller the next step overwrites any charge or export left from before a restart).
- Tests: `tests/core/test_engine_forecast.py`, `tests/ha/test_planner.py` (mode follows the plan in shadow; no mode without a price sensor).

### 0.7.5 — M5: the planner in Home Assistant, shadow only (SPEC-planner §2, §4, §5)
- **The plan is calculated and shown, not carried out.** With a price sensor (Nord Pool) in the options, ZEPHYR plans every quarter (at :10 s), when the prices change (tomorrow known), after a restart and, while there is no price for now, every minute. The mode *Dynamic Forecasting* that carries out the plan follows in the next step.
- **Inputs:** Nord Pool prices by start time (€/kWh, €/MWh or cents recognised), per quarter to the end of tomorrow; hour prices count for all four quarters; before tomorrow's prices are known today's pattern stands in (*indicative*, not in the totals). All-in prices from the tariff table or own tariffs (with the solar bonus in daylight). Solar from Solcast's half-hour detail of the chosen forecast sensor and its sibling (`…_forecast_today` / `…_forecast_tomorrow`); without it yesterday's production per hour, else no solar. Consumption from the learned profile (per hour, workday/weekend), learned from the cost log (house = import − export + solar − charged + delivered; complete hours only) and filled once from the last 28 days of the cost log; 0.35 kWh/h until something is learned. Battery: capacity × (max SOC − min SOC − buffer), power limits of the online sets within the settings, efficiency 0.93 per direction.
- **No price for the running quarter → no plan:** state *No prices* and action Deliver (zero on the meter), never charging on prices of another day (PT1, PT2, PT8). A price sensor with a value but no readable slots raises a repair issue (PT5).
- **Entities** (only with a price sensor, PT11): `sensor.zephyr_plan_action` (charge / hold / deliver / export; attributes `code` L/H/N/X, `blocks`, `timeline` per quarter — the last two not recorded), `sensor.zephyr_plan_state` (active, no_prices, battery_empty, battery_full), `sensor.zephyr_plan_reason` (one sentence, NL/EN), `sensor.zephyr_planned_grid_charge` (kWh, attribute `cost`), `sensor.zephyr_planned_export` (kWh, attribute `revenue`), `sensor.zephyr_battery_empty_at`, `sensor.zephyr_plan_calculated_at` (diagnostic). Diagnostics: settings, inputs, outcome, blocks, timeline and snapshots every 15 minutes (≥ 24 hours).
- **Options:** wear cost (default €0.03/kWh, B39), allow export from the battery (off, B12), load margin (0 %), buffer above the minimum SOC (0 %, B37; the planner plans as if the battery is that much smaller).
- **Cost log:** every quarter gets `plan_action` and `plan_cost` (the first plan of that quarter, B38).
- Test dashboard: card *Plan (schaduw)* and a table of the blocks.
- Days with summer/winter time step in UTC (92 / 100 quarters, PT7). Tests: `tests/core/test_forecast_plan.py`, `tests/ha/test_planner.py`.

### 0.7.4 — backtest with the Solcast forecast and cautious solar (B32)
- **Backtest:** `--sun solcast --solcast solcast.json` uses Solcast's forecast history from the integration's `solcast.json` (half-hour `pv_estimate` and `pv_estimate10`), and `--alpha` the cautious solar of SPEC-planner §12.4 (mid − α × (mid − p10) for slots more than 1 hour ahead). No change in Home Assistant.
- Measured (2-2 to 18-11, learned consumption, wear €0.03, cost incl. wear): Solcast €151.49 (2026) / €237.03 (2027), against yesterday's solar €159.14 / €243.78 and zero meter €204.84 / €265.41. Cautious solar α = 0.5 was slightly worse in both years (€152.43 / €238.09), so by the rule of §12.2 α stays 0 for now (B32).

### 0.7.3 — learned consumption profile; backtest with forecasts
- **`core/load_profile.py`** (SPEC-planner §2.3): consumption per hour of the day, separately for workdays and weekends, as a running mean (memory about 4 working weeks / 5 weekends); an hour value counts after 3 (workday) or 2 (weekend) measurements, before that the daily mean / 24; steering on the last 3 hours (ratio bounded 0.6–1.6, half of it left after 2 hours). Stored as a plain dict, so a reset is immediate. Not yet in Home Assistant.
- **Backtest:** `--load learned` (profile learned online, replanning every hour) and `--sun yesterday` (yesterday's solar as a simple, pessimistic forecast); `--rules`, `--quick`.
- Measured (2-2 to 18-11, wear €0.03, cost incl. wear): the planner stays ahead of zero meter with forecasts — 2026: perfect €149.82, learned consumption €152.69, plus yesterday's solar €159.14 (zero meter €204.84); 2027: €230.15 / €234.96 / €243.78 (zero meter €265.41). Details in the project (BACKTEST-1).

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
