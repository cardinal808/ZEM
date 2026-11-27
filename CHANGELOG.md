# Changelog

## Unreleased

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
