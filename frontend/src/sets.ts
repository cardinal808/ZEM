// Screen "Accu" (one set) / "Sets" (several): sets, batteries in the set, cell balance (SPEC-ui §4.3, UI-4).
import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import { clock, day, euro, kwh, percent, sameDay, signedWatts } from "./format";
import { t, type Lang } from "./i18n";
import { actionFill } from "./theme";

export interface PackDay {
  day: string;
  max_mv: number | null;
  status: CellStatus | null;
  full: boolean;
}

export type CellStatus = "good" | "balancing" | "imbalance";

export interface Pack {
  index: number;
  model: string | null;
  built_in: boolean;
  number: number;
  capacity_kwh: number | null;
  soc: number;
  energy_kwh: number | null;
  power_w: number;
  temp: number | null;
  cell_min_v: number | null;
  cell_max_v: number | null;
  cell_delta_mv: number | null;
  cell_judged: boolean;
  cell_status: CellStatus | null;
  history: PackDay[];
}

export interface SetInfo {
  id: string;
  number: number;
  model: string;
  online: boolean;
  status: string | null;
  soc: number | null;
  capacity_kwh: number | null;
  energy_kwh: number | null;
  power_w: number | null;
  solar_w: number | null;
  enclosure_temp: number | null;
  limits: { min: number | null; max: number | null } | null;
  last_full: string | null;
  relays_24h: number | null;
  packs: Pack[];
}

export interface Activity {
  action: string;
  start: string;
  end: string;
}

export interface SetsView {
  now: string;
  sets: SetInfo[];
  activity_24h: Activity[];
}

/** Display name of a pack: "Ingebouwd", "AB3000L 2" (number only when the model occurs more than once). */
export function packName(pack: Pack, packs: Pack[], lang: Lang): string {
  if (pack.built_in) return t(lang, "sets.built_in");
  if (!pack.model) return t(lang, "sets.pack", { n: pack.index + 1 });
  const same = packs.filter((p) => p.model === pack.model).length;
  return same > 1 ? `${pack.model} ${pack.number}` : pack.model;
}

/** One local day from \`zephyr/battery_days\` (kWh at the inverter's AC side). */
export interface BatteryDay {
  date: string;
  solar_battery: number;
  grid_battery: number;
  battery_house: number;
  battery_grid: number;
  soc_min: number | null;
  soc_max: number | null;
  cycles: number | null;
  quarters: number;
}

export interface BatteryDaysView {
  days: BatteryDay[];
  week: {
    solar_battery: number;
    grid_battery: number;
    charged: number;
    delivered: number;
    cycles: number | null;
    efficiency: number | null;
    grid_price: number | null;
  };
  usable_kwh: number | null;
}

/** Heights (px) of the four parts of each day's bar: charged up, delivered down, on one scale. */
export function dayBars(
  days: BatteryDay[],
  half: number,
): { solar: number; grid: number; house: number; export: number }[] {
  const top = Math.max(
    0.5,
    ...days.map((d) => Math.max(d.solar_battery + d.grid_battery, d.battery_house + d.battery_grid)),
  );
  const h = (v: number): number => Math.round((Math.max(v, 0) / top) * half * 10) / 10;
  return days.map((d) => ({
    solar: h(d.solar_battery),
    grid: h(d.grid_battery),
    house: h(d.battery_house),
    export: h(d.battery_grid),
  }));
}

export interface Summary {
  packs: number;
  online: boolean;
  socMin: number | null;
  socMax: number | null;
  /** Warmest inverter (enclosure) over the sets. */
  inverter: number | null;
  /** Largest cell difference judged right now (near full, small current); null when none is judged now. */
  now: { pack: Pack; mv: number; status: CellStatus } | null;
  /** Largest judged difference of the most recent judged day, when nothing is judged now. */
  lastDay: { day: string; mv: number; status: CellStatus } | null;
  /** Pack with the most imbalance days in the last 7 days, and how many. */
  imbalance: { pack: Pack; days: number; lastDay: string; mv: number } | null;
  /** No judged day in the last 7 days and nothing judged now. */
  notFull: boolean;
  offline: SetInfo[];
}

const STATUS_FOR = (mv: number): CellStatus => (mv <= 30 ? "good" : mv <= 100 ? "balancing" : "imbalance");

export function summarize(sets: SetInfo[]): Summary {
  const packs = sets.flatMap((s) => s.packs);
  const socs = packs.map((p) => p.soc);
  const temps = sets.map((s) => s.enclosure_temp).filter((v): v is number => v !== null);
  let now: Summary["now"] = null;
  for (const p of packs) {
    if (!p.cell_judged || p.cell_delta_mv === null || p.cell_status === null) continue;
    if (!now || p.cell_delta_mv > now.mv) now = { pack: p, mv: p.cell_delta_mv, status: p.cell_status };
  }
  let lastDay: Summary["lastDay"] = null;
  const days = packs[0]?.history.map((d) => d.day) ?? [];
  for (let i = days.length - 1; i >= 0 && !lastDay; i--) {
    const values = packs.map((p) => p.history[i]?.max_mv).filter((v): v is number => v !== null && v !== undefined);
    if (values.length) {
      const mv = Math.max(...values);
      lastDay = { day: days[i], mv, status: STATUS_FOR(mv) };
    }
  }
  let imbalance: Summary["imbalance"] = null;
  for (const p of packs) {
    const bad = p.history.filter((d) => d.status === "imbalance");
    if (!bad.length) continue;
    const last = bad[bad.length - 1];
    if (!imbalance || bad.length > imbalance.days) imbalance = { pack: p, days: bad.length, lastDay: last.day, mv: last.max_mv as number };
  }
  const judgedDays = packs.some((p) => p.history.some((d) => d.max_mv !== null));
  return {
    packs: packs.length,
    online: sets.every((s) => s.online),
    socMin: socs.length ? Math.min(...socs) : null,
    socMax: socs.length ? Math.max(...socs) : null,
    inverter: temps.length ? Math.max(...temps) : null,
    now,
    lastDay,
    imbalance,
    notFull: !now && !judgedDays,
    offline: sets.filter((s) => !s.online),
  };
}

@customElement("zephyr-sets")
export class ZephyrSets extends LitElement {
  @property({ attribute: false }) days?: BatteryDaysView;
  @property({ attribute: false }) view?: SetsView;
  @property({ attribute: false }) uiLang: Lang = "en";
  @property() locale = "en";
  @property() timeZone = "UTC";

  private tr(key: string, params: Record<string, string | number> = {}): string {
    return t(this.uiLang, key, params);
  }

  private num(value: number, digits = 0): string {
    return new Intl.NumberFormat(this.locale, { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
  }

  protected override render(): TemplateResult {
    const view = this.view;
    if (!view) return html`<div class="card skeleton" aria-hidden="true"></div>`;
    if (!view.sets.length) return html`<section class="card"><p class="text">${this.tr("sets.none")}</p></section>`;
    const sum = summarize(view.sets);
    return html`
      ${this.renderSummary(sum, view.sets)}
      ${view.sets.map(
        (s) => html`<div class="row">
          ${this.renderSet(s, view.sets.length)} ${this.renderPacks(s)}
        </div>`,
      )}
      ${this.days ? this.renderDays(this.days) : nothing} ${view.sets.length === 1 ? this.renderActivity(view) : nothing}
    `;
  }

  private stat(label: string, value: string): TemplateResult {
    return html`<div class="stat"><span class="cap">${label}</span><span class="value">${value}</span></div>`;
  }

  private renderSummary(sum: Summary, sets: SetInfo[]): TemplateResult {
    const packs = sets.flatMap((s) => s.packs);
    let line: string;
    if (sum.offline.length) line = this.tr("sets.offline_line", { sets: sum.offline.map((s) => this.tr("sets.set", { n: s.number })).join(", ") });
    else if (sum.imbalance && sum.imbalance.days >= 3)
      line = this.tr("sets.line_persistent", { pack: packName(sum.imbalance.pack, packs, this.uiLang), days: sum.imbalance.days });
    else if (sum.now?.status === "imbalance")
      line = this.tr("sets.line_now", { pack: packName(sum.now.pack, packs, this.uiLang), mv: sum.now.mv });
    else if (sum.imbalance)
      line = this.tr("sets.line_recent", {
        pack: packName(sum.imbalance.pack, packs, this.uiLang),
        day: day(`${sum.imbalance.lastDay}T12:00:00Z`, this.locale, this.timeZone),
        mv: sum.imbalance.mv,
      });
    else if (sum.notFull) line = this.tr("sets.line_not_full");
    else line = this.tr("sets.line_ok");
    const cells = sum.now
      ? `${this.num(sum.now.mv)} mV · ${this.tr(`sets.cell.${sum.now.status}`)}`
      : sum.lastDay
        ? `${this.num(sum.lastDay.mv)} mV · ${this.tr(`sets.cell.${sum.lastDay.status}`)}`
        : "–";
    return html`<section class="card summary" aria-label=${this.tr("sets.summary")}>
      ${this.stat(this.tr("sets.batteries"), this.tr(sum.online ? "sets.all_online" : "sets.some_offline", { n: sum.packs }))}
      ${this.stat(
        this.tr("sets.soc_spread"),
        sum.socMin === null ? "–" : sum.socMin === sum.socMax ? percent(sum.socMin, this.locale) : `${this.num(sum.socMin)}–${percent(sum.socMax as number, this.locale)}`,
      )}
      ${this.stat(this.tr("sets.inverter"), sum.inverter === null ? "–" : `${this.num(sum.inverter)} °C`)}
      ${this.stat(sum.now || !sum.lastDay ? this.tr("sets.largest_delta") : this.tr("sets.largest_delta_day", { day: day(`${sum.lastDay.day}T12:00:00Z`, this.locale, this.timeZone) }), cells)}
      <p class="line"><strong>${this.tr("sets.in_short")}</strong> ${line}</p>
    </section>`;
  }

  private renderSet(s: SetInfo, count: number): TemplateResult {
    const soc = s.soc ?? 0;
    const status = s.online ? (s.status ?? "standby") : "offline";
    const dl = (label: string, value: string): TemplateResult => html`<div><dt>${label}</dt><dd>${value}</dd></div>`;
    const lastFull = s.last_full
      ? sameDay(s.last_full, Date.now(), this.timeZone)
        ? `${this.tr("sets.today")} ${clock(s.last_full, this.locale, this.timeZone)}`
        : day(s.last_full, this.locale, this.timeZone)
      : this.tr("sets.unknown");
    return html`<article class="card set">
      <div class="head">
        <div>
          <h2>${this.tr("sets.set", { n: s.number })}</h2>
          <span class="muted"
            >${s.model}${s.packs.length ? ` · ${this.tr("sets.packs_n", { n: s.packs.length })}` : ""}${s.capacity_kwh
              ? ` · ${kwh(s.capacity_kwh, this.locale)}`
              : ""}</span
          >
        </div>
        <span class="chip ${status}">${this.tr(`sets.status.${status}`)}</span>
      </div>
      ${s.soc === null
        ? html`<p class="text">${this.tr("battery.unknown")}</p>`
        : html`<div class="big-row">
              <span class="big">${percent(soc, this.locale)}</span>
              ${s.energy_kwh !== null && s.capacity_kwh
                ? html`<span class="muted">${this.tr("battery.of", { energy: kwh(s.energy_kwh, this.locale), capacity: kwh(s.capacity_kwh, this.locale) })}</span>`
                : nothing}
            </div>
            <div class="bar" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow=${Math.round(soc)} aria-label=${this.tr("battery.title")}>
              <div class="fill" style="width:${soc}%"></div>
              ${s.limits?.min != null ? html`<div class="mark" style="left:${s.limits.min}%"></div>` : nothing}
              ${s.limits?.max != null ? html`<div class="mark" style="left:${s.limits.max}%"></div>` : nothing}
            </div>`}
      <dl>
        ${dl(this.tr("sets.power"), s.power_w === null ? "–" : signedWatts(s.power_w, this.locale))}
        ${s.solar_w ? dl(this.tr("sets.solar"), signedWatts(s.solar_w, this.locale).replace("+", "")) : nothing}
        ${dl(this.tr("sets.inverter"), s.enclosure_temp === null ? "–" : `${this.num(s.enclosure_temp)} °C`)}
        ${dl(this.tr("sets.last_full"), lastFull)}
        ${dl(this.tr("sets.switches"), s.relays_24h === null ? "–" : this.tr("sets.switches_n", { n: s.relays_24h }))}
        ${dl(
          this.tr("sets.limits"),
          s.limits?.min != null && s.limits?.max != null ? `${this.num(s.limits.min)}–${this.num(s.limits.max)} %` : "–",
        )}
      </dl>
      <div class="foot">
        <span>${count >= 3 ? this.tr("sets.max_sets") : ""}</span>
        ${count < 3 ? html`<a class="button" href="/config/integrations/integration/zephyr">${this.tr("sets.add")}</a>` : nothing}
      </div>
    </article>`;
  }

  private renderPacks(s: SetInfo): TemplateResult {
    if (!s.packs.length) return html``;
    return html`<section class="card packs" aria-label=${this.tr("sets.in_set")}>
      <div class="head">
        <h2>${this.tr("sets.in_set")}</h2>
        <span class="muted">${this.tr("sets.pack_power_note")}</span>
      </div>
      <div class="grid">
        ${s.packs.map((p) => {
          const status = p.cell_status;
          return html`<div class="pack ${s.online ? "" : "off"}">
            <div class="ph"><strong>${packName(p, s.packs, this.uiLang)}</strong><span class="muted">${p.capacity_kwh ? kwh(p.capacity_kwh, this.locale, 2) : this.tr("sets.unknown_type")}</span></div>
            <div class="big-row">
              <span class="mid">${percent(p.soc, this.locale)}</span>
              ${p.energy_kwh !== null ? html`<span class="muted">${kwh(p.energy_kwh, this.locale, 2)}</span>` : nothing}
            </div>
            <div class="bar thin"><div class="fill" style="width:${p.soc}%"></div></div>
            <dl>
              <div><dt>${this.tr("sets.power")}</dt><dd>${signedWatts(p.power_w, this.locale)}</dd></div>
              <div><dt>${this.tr("sets.temp")}</dt><dd>${p.temp === null ? "–" : `${this.num(p.temp)} °C`}</dd></div>
              <div>
                <dt>${this.tr("sets.cells")}</dt>
                <dd>${p.cell_min_v === null || p.cell_max_v === null ? "–" : `${this.num(p.cell_min_v, 2)}–${this.num(p.cell_max_v, 2)} V`}</dd>
              </div>
              <div>
                <dt>${this.tr("sets.cell_delta")}</dt>
                <dd class="delta">
                  ${p.cell_delta_mv === null ? "–" : `${this.num(p.cell_delta_mv)} mV`}
                  ${status
                    ? html`<span class="tag ${status}">${this.tr(`sets.cell.${status}`)}</span>`
                    : p.cell_delta_mv !== null
                      ? html`<span class="tag none" title=${this.tr("sets.not_judged_title")}>${this.tr("sets.not_judged")}</span>`
                      : nothing}
                </dd>
              </div>
            </dl>
          </div>`;
        })}
      </div>
      <p class="text small">${this.tr("sets.cell_note")}</p>
    </section>`;
  }

  private renderDays(v: BatteryDaysView): TemplateResult {
    const HALF = 80;
    const bars = dayBars(v.days, HALF);
    const k = (x: number): string => this.num(x, 1);
    const todayIso = v.days[v.days.length - 1]?.date;
    const row = (label: string, sub: string | null, cell: (d: BatteryDay) => string): TemplateResult =>
      html`<div class="tr" role="row">
        <span role="rowheader" class="rh">${label}${sub ? html`<small>${sub}</small>` : nothing}</span>
        ${v.days.map((d) => {
          const text = d.quarters ? cell(d) : "–";
          return html`<span role="cell" class="cell val ${text === "–" ? "empty" : ""}">${text}</span>`;
        })}
      </div>`;
    const w = v.week;
    const first = v.days[0]?.date;
    const dayName = (iso: string): string => day(`${iso}T12:00:00Z`, this.locale, this.timeZone);
    const weekParts = [
      this.tr("sets.days_week_charged", { kwh: k(w.charged), solar: k(w.solar_battery), grid: k(w.grid_battery) }),
      this.tr("sets.days_week_delivered", { kwh: k(w.delivered) }),
      w.cycles === null ? null : this.tr("sets.days_week_cycles", { n: this.num(w.cycles, 1) }),
      w.efficiency === null ? null : this.tr("sets.days_week_efficiency", { pct: percent(w.efficiency * 100, this.locale) }),
      w.grid_price === null ? null : this.tr("sets.days_week_price", { price: euro(w.grid_price, this.locale) }),
    ].filter((x): x is string => x !== null);
    return html`<section class="card" aria-label=${this.tr("sets.days_title")}>
      <div class="head">
        <h2>${this.tr("sets.days_title")}</h2>
        <div class="legend">
          <span><i style="background:var(--z-solar)"></i>${this.tr("sets.days_solar")}</span>
          <span><i style="background:var(--z-charge)"></i>${this.tr("sets.days_grid")}</span>
          <span><i style="background:var(--z-deliver)"></i>${this.tr("sets.days_house")}</span>
          <span><i style="background:var(--z-export)"></i>${this.tr("sets.days_export")}</span>
        </div>
      </div>
      <span class="muted">${this.tr("sets.days_note")}</span>
      <div class="table" role="table">
        <div class="tr" role="row">
          <span role="columnheader"></span>
          ${v.days.map((d) => html`<span role="columnheader" class="dh ${d.date === todayIso ? "today" : ""}">${dayName(d.date)}</span>`)}
        </div>
        <div class="tr bars" aria-hidden="true">
          <span class="rh axis"><small>${this.tr("sets.days_up")}</small><small>${this.tr("sets.days_down")}</small></span>
          ${bars.map(
            (b, i) => html`<div class="daybar" style="--half:${HALF}px">
              <div class="up">
                <i style="height:${b.solar}px;background:var(--z-solar)"></i
                ><i style="height:${b.grid}px;background:var(--z-charge)"></i>
              </div>
              <div class="dn">
                <i style="height:${b.house}px;background:var(--z-deliver)"></i
                ><i style="height:${b.export}px;background:var(--z-export)"></i>
              </div>
              <span class="sr">${dayName(v.days[i].date)}</span>
            </div>`,
          )}
        </div>
        ${row(this.tr("sets.days_charged"), this.tr("sets.days_charged_sub"), (d) => k(d.solar_battery + d.grid_battery))}
        ${row(this.tr("sets.days_delivered"), this.tr("sets.days_delivered_sub"), (d) => k(d.battery_house + d.battery_grid))}
        ${row(this.tr("sets.days_cycles"), null, (d) => (d.cycles === null ? "–" : this.num(d.cycles, 2)))}
        ${row(this.tr("sets.days_soc"), this.tr("sets.days_soc_sub"), (d) =>
          d.soc_min === null || d.soc_max === null ? "–" : `${this.num(d.soc_min)}–${percent(d.soc_max, this.locale)}`,
        )}
      </div>
      <div class="week">
        <span class="rh">${this.tr("sets.days_week")}<small>${first && todayIso ? `${dayName(first)} – ${dayName(todayIso)}` : ""}</small></span>
        <span>${weekParts.join(" · ")}</span>
      </div>
      <p class="text small">
        ${this.tr("sets.days_explain", { usable: v.usable_kwh === null ? "–" : k(v.usable_kwh) })}
      </p>
    </section>`;
  }

  private renderActivity(view: SetsView): TemplateResult {
    const end = new Date(view.now).getTime();
    const start = end - 24 * 3600_000;
    const pct = (iso: string): number => Math.max(0, Math.min(100, ((new Date(iso).getTime() - start) / (end - start)) * 100));
    const totals = { charge: 0, deliver: 0 };
    return html`<section class="card" aria-label=${this.tr("sets.activity_title")}>
      <div class="head">
        <h2>${this.tr("sets.activity_title")}</h2>
        <div class="legend">
          <span><i style="background:${actionFill("charge")}"></i>${this.tr("action.charge")}</span>
          <span><i style="background:${actionFill("deliver")}"></i>${this.tr("action.deliver")}</span>
          <span><i style="background:${actionFill("hold")}"></i>${this.tr("action.hold")}</span>
        </div>
      </div>
      <div class="activity" aria-hidden="true">
        ${view.activity_24h.map((a) => {
          if (a.action in totals) totals[a.action as keyof typeof totals] += 1;
          const left = pct(a.start);
          return html`<div
            title="${clock(a.start, this.locale, this.timeZone)}–${clock(a.end, this.locale, this.timeZone)} · ${this.tr(`action.${a.action}`)}"
            style="left:${left}%;width:${pct(a.end) - left}%;background:${actionFill(a.action)}"
          ></div>`;
        })}
      </div>
      <div class="hours">
        ${[0, 4, 8, 12, 16, 20].map((h) => html`<span>${clock(new Date(start + h * 3600_000).toISOString(), this.locale, this.timeZone)}</span>`)}
        <span>${this.tr("plan.now_short")}</span>
      </div>
      ${view.activity_24h.length ? nothing : html`<p class="text small">${this.tr("sets.no_activity")}</p>`}
    </section>`;
  }

  static override styles = css`
    :host {
      display: flex;
      flex-direction: column;
      gap: 20px;
      color: var(--z-text);
      font-family: var(--z-font);
    }
    .card {
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 16px;
      padding: 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      min-width: 0;
    }
    .skeleton {
      min-height: 300px;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 20px;
    }
    .head {
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      justify-content: space-between;
      gap: 8px 12px;
    }
    .muted {
      font-size: 13px;
      color: var(--z-muted);
    }
    .text {
      margin: 0;
      font-size: 14px;
      line-height: 1.5;
      color: var(--z-muted);
    }
    .text.small {
      font-size: 13px;
    }
    .summary {
      flex-direction: row;
      flex-wrap: wrap;
      align-items: center;
      gap: 16px 32px;
    }
    .stat {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .cap {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--z-muted);
    }
    .value {
      font-family: var(--z-font-head);
      font-size: 24px;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    .line {
      flex: 1 1 300px;
      margin: 0;
      font-size: 14px;
      line-height: 1.5;
      color: var(--z-muted);
    }
    .line strong {
      color: var(--z-text);
    }
    .row {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: stretch;
    }
    .set {
      flex: 1 1 340px;
      max-width: 460px;
    }
    .packs {
      flex: 999 1 520px;
    }
    .chip {
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
      white-space: nowrap;
      background: var(--z-track);
    }
    .chip.charging {
      background: var(--z-charge);
      color: #fff;
    }
    .chip.discharging {
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
    }
    .chip.offline,
    .chip.fault {
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
    }
    .big-row {
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 4px 10px;
    }
    .big {
      font-family: var(--z-font-head);
      font-size: 34px;
      font-weight: 700;
    }
    .mid {
      font-family: var(--z-font-head);
      font-size: 26px;
      font-weight: 700;
    }
    .bar {
      position: relative;
      height: 12px;
      background: var(--z-track);
      border-radius: 6px;
      overflow: hidden;
    }
    .bar.thin {
      height: 8px;
    }
    .fill {
      height: 100%;
      background: var(--z-text);
      border-radius: 6px;
    }
    .mark {
      position: absolute;
      top: 0;
      bottom: 0;
      border-left: 2px solid var(--z-card);
    }
    dl {
      margin: 0;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px 16px;
    }
    dt {
      font-size: 12px;
      color: var(--z-muted);
    }
    dd {
      margin: 0;
      font-weight: 600;
      font-variant-numeric: tabular-nums;
    }
    .foot {
      margin-top: auto;
      padding-top: 12px;
      border-top: 1px solid var(--z-border);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      font-size: 13px;
      color: var(--z-muted);
    }
    .button {
      min-height: 44px;
      display: inline-flex;
      align-items: center;
      padding: 0 16px;
      border-radius: 999px;
      border: 1px solid var(--z-border);
      text-decoration: none;
      font-size: 14px;
      color: var(--z-text);
    }
    .button:focus-visible {
      outline: 2px solid var(--z-charge);
      outline-offset: 2px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 12px;
    }
    .pack {
      border: 1px solid var(--z-border);
      border-radius: 12px;
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .pack.off {
      opacity: 0.6;
    }
    .ph {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 8px;
    }
    .pack dl {
      font-size: 14px;
      gap: 8px 12px;
    }
    .delta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;
    }
    .tag {
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 600;
    }
    .tag.good,
    .cell.good {
      background: var(--z-good-bg);
      color: var(--z-good-text);
    }
    .tag.balancing,
    .cell.balancing {
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
    }
    .tag.imbalance,
    .cell.imbalance {
      background: var(--z-bad-bg);
      color: var(--z-bad-text);
    }
    .tag.none {
      background: var(--z-track);
      color: var(--z-muted);
    }
    .table {
      display: flex;
      flex-direction: column;
      gap: 6px;
      overflow-x: auto;
    }
    .tr {
      display: grid;
      grid-template-columns: 130px repeat(7, minmax(52px, 1fr));
      gap: 6px;
      align-items: center;
    }
    .dh {
      text-align: center;
      font-size: 12px;
      color: var(--z-muted);
    }
    .rh {
      font-size: 14px;
      font-weight: 600;
    }
    .cell {
      min-height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      font-variant-numeric: tabular-nums;
    }
    .cell.val {
      background: var(--z-track);
      font-weight: 400;
      font-size: 14px;
    }
    .cell.val.empty {
      color: var(--z-muted);
    }
    .cell.val {
      white-space: nowrap;
    }
    .dh.today {
      color: var(--z-text);
      font-weight: 600;
    }
    .rh small {
      display: block;
      font-size: 12px;
      font-weight: 400;
      color: var(--z-muted);
    }
    .rh.axis {
      align-self: stretch;
      display: flex;
      flex-direction: column;
      justify-content: space-around;
    }
    .daybar {
      position: relative;
      height: calc(var(--half) * 2 + 8px);
      border-top: 0;
      background: linear-gradient(var(--z-border), var(--z-border)) 0 calc(var(--half) + 4px) / 100% 1px no-repeat;
    }
    .daybar .up,
    .daybar .dn {
      position: absolute;
      left: 25%;
      right: 25%;
      display: flex;
    }
    .daybar .up {
      bottom: calc(var(--half) + 4px);
      flex-direction: column-reverse;
    }
    .daybar .dn {
      top: calc(var(--half) + 5px);
      flex-direction: column;
    }
    .daybar i {
      display: block;
    }
    .daybar .up i:last-child {
      border-radius: 4px 4px 0 0;
    }
    .daybar .dn i:last-child {
      border-radius: 0 0 4px 4px;
    }
    .sr {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
    }
    .week {
      display: grid;
      grid-template-columns: 130px 1fr;
      gap: 6px;
      align-items: center;
      border-top: 1px solid var(--z-border);
      padding-top: 12px;
      font-size: 14px;
    }
    @media (max-width: 600px) {
      .tr {
        grid-template-columns: 84px repeat(7, minmax(64px, 1fr));
      }
      .week {
        grid-template-columns: 1fr;
      }
    }
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 13px;
      color: var(--z-muted);
    }
    .legend span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .legend i {
      width: 14px;
      height: 14px;
      border-radius: 3px;
      display: inline-block;
    }
    .activity {
      position: relative;
      height: 22px;
      border-radius: 6px;
      overflow: hidden;
      background: var(--z-track);
    }
    .activity div {
      position: absolute;
      top: 0;
      bottom: 0;
    }
    .hours {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: var(--z-muted);
      font-variant-numeric: tabular-nums;
    }
    @media (max-width: 700px) {
      .card {
        padding: 16px;
      }
      .set {
        max-width: none;
      }
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "zephyr-sets": ZephyrSets;
  }
}
