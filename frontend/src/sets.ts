// Screen "Accu" (one set) / "Sets" (several): sets, batteries in the set, cell balance (SPEC-ui §4.3, UI-4).
import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import { clock, day, kwh, percent, sameDay, signedWatts } from "./format";
import { t, type Lang } from "./i18n";
import { actionFill } from "./theme";

export interface PackDay {
  day: string;
  max_mv: number | null;
  status: CellStatus | null;
  full: boolean;
}

export type CellStatus = "good" | "watch" | "high" | "edge";

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

export interface Summary {
  packs: number;
  online: boolean;
  socMin: number | null;
  socMax: number | null;
  warmest: number | null;
  /** Largest judged cell difference; null when no pack is in the judged window. */
  worst: { pack: Pack; mv: number; status: CellStatus } | null;
  /** Largest difference of any pack (also near full/empty). */
  largest: number | null;
  offline: SetInfo[];
}

export function summarize(sets: SetInfo[]): Summary {
  const packs = sets.flatMap((s) => s.packs);
  const socs = packs.map((p) => p.soc);
  const temps = packs.map((p) => p.temp).filter((v): v is number => v !== null);
  let worst: Summary["worst"] = null;
  for (const p of packs) {
    if (p.cell_delta_mv === null || p.cell_status === null || p.cell_status === "edge") continue;
    if (!worst || p.cell_delta_mv > worst.mv) worst = { pack: p, mv: p.cell_delta_mv, status: p.cell_status };
  }
  const deltas = packs.map((p) => p.cell_delta_mv).filter((v): v is number => v !== null);
  return {
    packs: packs.length,
    online: sets.every((s) => s.online),
    socMin: socs.length ? Math.min(...socs) : null,
    socMax: socs.length ? Math.max(...socs) : null,
    warmest: temps.length ? Math.max(...temps) : null,
    worst,
    largest: deltas.length ? Math.max(...deltas) : null,
    offline: sets.filter((s) => !s.online),
  };
}

@customElement("zephyr-sets")
export class ZephyrSets extends LitElement {
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
    const allPacks = view.sets.flatMap((s) => s.packs);
    return html`
      ${this.renderSummary(sum, view.sets)}
      ${view.sets.map(
        (s) => html`<div class="row">
          ${this.renderSet(s, view.sets.length)} ${this.renderPacks(s)}
        </div>`,
      )}
      ${allPacks.length ? this.renderBalance(view.sets) : nothing} ${view.sets.length === 1 ? this.renderActivity(view) : nothing}
    `;
  }

  private stat(label: string, value: string): TemplateResult {
    return html`<div class="stat"><span class="cap">${label}</span><span class="value">${value}</span></div>`;
  }

  private renderSummary(sum: Summary, sets: SetInfo[]): TemplateResult {
    const packs = sets.flatMap((s) => s.packs);
    let line: string;
    if (sum.offline.length) line = this.tr("sets.offline_line", { sets: sum.offline.map((s) => this.tr("sets.set", { n: s.number })).join(", ") });
    else if (sum.worst?.status === "high")
      line = this.tr("sets.line_high", { pack: packName(sum.worst.pack, packs, this.uiLang), mv: sum.worst.mv });
    else if (sum.worst?.status === "watch")
      line = this.tr("sets.line_watch", { pack: packName(sum.worst.pack, packs, this.uiLang), mv: sum.worst.mv });
    else if (!sum.worst && sum.largest !== null) line = this.tr("sets.line_edge");
    else line = this.tr("sets.line_ok");
    const cells = sum.worst
      ? `${this.num(sum.worst.mv)} mV`
      : sum.largest !== null
        ? `${this.num(sum.largest)} mV*`
        : "–";
    return html`<section class="card summary" aria-label=${this.tr("sets.summary")}>
      ${this.stat(this.tr("sets.batteries"), this.tr(sum.online ? "sets.all_online" : "sets.some_offline", { n: sum.packs }))}
      ${this.stat(
        this.tr("sets.soc_spread"),
        sum.socMin === null ? "–" : sum.socMin === sum.socMax ? percent(sum.socMin, this.locale) : `${this.num(sum.socMin)}–${percent(sum.socMax as number, this.locale)}`,
      )}
      ${this.stat(this.tr("sets.warmest"), sum.warmest === null ? "–" : `${this.num(sum.warmest)} °C`)}
      ${this.stat(this.tr("sets.largest_delta"), cells)}
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
                  ${status ? html`<span class="tag ${status}">${this.tr(`sets.cell.${status}`)}</span>` : nothing}
                </dd>
              </div>
            </dl>
          </div>`;
        })}
      </div>
      <p class="text small">${this.tr("sets.cell_note")}</p>
    </section>`;
  }

  private renderBalance(sets: SetInfo[]): TemplateResult {
    const first = sets.find((s) => s.packs.length)?.packs[0];
    const days = first?.history ?? [];
    return html`<section class="card" aria-label=${this.tr("sets.balance_title")}>
      <div class="head">
        <h2>${this.tr("sets.balance_title")}</h2>
        <span class="muted">${this.tr("sets.balance_note")}</span>
      </div>
      <div class="table" role="table">
        <div class="tr" role="row">
          <span role="columnheader"></span>
          ${days.map((d) => html`<span role="columnheader" class="dh">${day(`${d.day}T12:00:00Z`, this.locale, this.timeZone)}</span>`)}
        </div>
        ${sets.flatMap((s) =>
          s.packs.map(
            (p) => html`<div class="tr" role="row">
              <span role="rowheader" class="rh">${sets.length > 1 ? `${s.number} · ` : ""}${packName(p, s.packs, this.uiLang)}</span>
              ${p.history.map(
                (d) => html`<span
                  role="cell"
                  class="cell ${d.status ?? "none"}"
                  title=${d.max_mv === null ? this.tr("sets.no_judged") : `${d.max_mv} mV · ${this.tr(`sets.cell.${d.status}`)}`}
                  >${d.max_mv === null ? "–" : this.num(d.max_mv)}${d.full ? html` <span aria-label=${this.tr("sets.full_day")}>▲</span>` : nothing}</span
                >`,
              )}
            </div>`,
          ),
        )}
      </div>
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
    .tag.watch,
    .cell.watch {
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
    }
    .tag.high,
    .cell.high {
      background: var(--z-bad-bg);
      color: var(--z-bad-text);
    }
    .tag.edge {
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
    .cell.none {
      background: var(--z-track);
      color: var(--z-muted);
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
