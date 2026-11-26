// Screen "Besparing" (SPEC-ui §1, M6 part 2): what the battery saved, from the cost log (B38).
import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { euro, kwh } from "./format";
import { t, type Lang } from "./i18n";

export type SavingsPeriod = "today" | "week" | "month" | "year";

export interface SavingsSummary {
  /** What was paid (energy incl. VAT, without fixed costs). */
  cost: number | null;
  /** What it would have been without the battery, same house and solar. */
  cost_no_battery: number | null;
  savings_battery: number | null;
  /** Part of the battery's savings from storing solar and using it later. */
  savings_solar_via_battery: number | null;
  /** Part from charging cheap and delivering dear. */
  savings_trade: number | null;
  charge_kwh: number;
  discharge_kwh: number;
  days: number;
  quarters: number;
  incomplete_quarters: number;
}

export interface SavingsDay {
  day: string;
  savings_battery: number | null;
  /** Quarters missing or without a price: the day is not complete. */
  incomplete: boolean;
}

export interface SavingsView {
  periods: Record<SavingsPeriod, SavingsSummary>;
  days: SavingsDay[];
  saldering_until: string | null;
  /** Days the cost log has (it starts on the day ZEPHYR was installed). */
  since: string | null;
}

const roundUp = (v: number) => (v <= 0 ? 0 : Math.ceil(v * 2) / 2);

/**
 * Euro axis for the day bars. One test day with a large loss (or a large gain) would flatten the rest:
 * a value above twice the typical day is cut at the axis and drawn with an arrow and its amount.
 */
export function dayScale(days: SavingsDay[]): { top: number; bottom: number } {
  const values = days.map((d) => d.savings_battery ?? 0);
  const sizes = values.map(Math.abs).filter((v) => v > 0).sort((a, b) => a - b);
  const typical = sizes.length ? sizes[Math.floor(sizes.length * 0.75)] : 0.5;
  const cap = Math.max(0.5, typical * 2);
  const max = Math.min(cap, Math.max(0, ...values));
  const min = Math.max(-cap, Math.min(0, ...values));
  return { top: Math.max(0.5, roundUp(max)), bottom: -roundUp(-min) };
}

@customElement("zephyr-savings")
export class ZephyrSavings extends LitElement {
  @property({ attribute: false }) view?: SavingsView;
  @property({ attribute: false }) uiLang: Lang = "en";
  @property() locale = "en";
  @property() timeZone = "UTC";

  @state() private period: SavingsPeriod = "month";

  private tr(key: string, params: Record<string, string | number> = {}): string {
    return t(this.uiLang, key, params);
  }

  protected override render(): TemplateResult {
    const view = this.view;
    if (!view) return html`<div class="skeleton"></div>`;
    const s = view.periods[this.period];
    return html`<div class="layout">
      <section class="card hero" aria-labelledby="sv-title">
        <div class="head">
          <h2 id="sv-title">${this.tr("savings.title")}</h2>
          <div class="tabs" role="group" aria-label=${this.tr("savings.period")}>
            ${(["today", "week", "month", "year"] as const).map(
              (p) => html`<button type="button" class=${p === this.period ? "on" : ""} aria-pressed=${p === this.period ? "true" : "false"} @click=${() => (this.period = p)}>
                <span class="long">${this.tr(`savings.p_${p}`)}</span><span class="short">${this.tr(`savings.ps_${p}`)}</span>
              </button>`,
            )}
          </div>
        </div>
        ${this.renderHero(s)}
      </section>
      <section class="card split" aria-labelledby="sv-split">
        <h2 id="sv-split">${this.tr("savings.split_title", { period: this.tr(`savings.p_${this.period}`).toLowerCase() })}</h2>
        ${this.renderSplit(s)}
      </section>
      <section class="card days" aria-labelledby="sv-days">
        <h2 id="sv-days">${this.tr("savings.days_title")}</h2>
        ${this.renderDays(view.days)}
      </section>
      <section class="card notes" aria-labelledby="sv-notes">
        <h2 id="sv-notes">${this.tr("savings.notes_title")}</h2>
        <ul>
          <li>${this.tr("savings.note_compare")}</li>
          <li>${this.tr("savings.note_fixed")}</li>
          ${view.saldering_until ? html`<li>${this.tr("savings.note_saldering", { date: this.date(view.saldering_until) })}</li>` : nothing}
          ${view.since ? html`<li>${this.tr("savings.note_since", { date: this.date(view.since) })}</li>` : nothing}
        </ul>
      </section>
    </div>`;
  }

  private date(iso: string): string {
    return new Intl.DateTimeFormat(this.locale, { day: "numeric", month: "long", year: "numeric", timeZone: this.timeZone }).format(new Date(iso));
  }

  private renderHero(s: SavingsSummary): TemplateResult {
    if (s.cost === null || s.cost_no_battery === null || s.savings_battery === null)
      return html`<p class="muted">${this.tr("savings.no_data")}</p>`;
    const saved = s.savings_battery;
    const loss = saved < 0;
    const max = Math.max(s.cost, s.cost_no_battery, 0.01);
    return html`<div class="big ${loss ? "loss" : "win"}">
        <span class="amount">${loss ? "−" : ""}${euro(Math.abs(saved), this.locale)}</span>
        <span class="label">${this.tr(loss ? "savings.lost" : "savings.saved")}</span>
      </div>
      <div class="compare">
        <div class="row">
          <span class="name">${this.tr("savings.without")}</span>
          <span class="bar"><i class="nb" style="width:${(Math.max(0, s.cost_no_battery) / max) * 100}%"></i></span>
          <span class="val">${euro(s.cost_no_battery, this.locale)}</span>
        </div>
        <div class="row">
          <span class="name">${this.tr("savings.paid")}</span>
          <span class="bar"><i class="paid" style="width:${(Math.max(0, s.cost) / max) * 100}%"></i></span>
          <span class="val">${euro(s.cost, this.locale)}</span>
        </div>
      </div>
      ${s.incomplete_quarters
        ? html`<p class="warn">${this.tr("savings.incomplete", { n: s.incomplete_quarters, total: s.quarters })}</p>`
        : nothing}`;
  }

  private renderDays(days: SavingsDay[]): TemplateResult {
    if (!days.length) return html`<p class="muted">${this.tr("savings.no_data")}</p>`;
    const { top, bottom } = dayScale(days);
    const span = top - bottom;
    const zero = (top / span) * 100;
    const fmtDay = (d: string) =>
      new Intl.DateTimeFormat(this.locale, { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" }).format(new Date(`${d}T12:00:00Z`));
    const total = days.reduce((a, d) => a + (d.savings_battery ?? 0), 0);
    return html`<p class="muted">${this.tr("savings.days_total", { n: days.length, amount: euro(total, this.locale) })}</p>
      <div class="dchart">
        <div class="daxis" aria-hidden="true">
          <span style="top:0">${euro(top, this.locale)}</span>
          <span style="top:${zero}%">€ 0</span>
          ${bottom < 0 ? html`<span style="top:100%">−${euro(-bottom, this.locale)}</span>` : nothing}
        </div>
        <div class="dbars">
          <div class="zero" style="top:${zero}%"></div>
          ${days.map((d) => {
            const v = d.savings_battery ?? 0;
            const shown = Math.max(bottom, Math.min(top, v));
            const cut = shown !== v;
            const h = (Math.abs(shown) / span) * 100;
            const style = v >= 0 ? `top:${zero - h}%;height:${h}%` : `top:${zero}%;height:${h}%`;
            const label = `${fmtDay(d.day)}: ${d.savings_battery === null ? this.tr("savings.unknown") : euro(v, this.locale)}${d.incomplete ? ` (${this.tr("savings.day_incomplete")})` : ""}`;
            return html`<div class="dcol" title=${label} aria-label=${label}>
              <i class=${`${v >= 0 ? "win" : "loss"}${d.incomplete ? " part" : ""}${cut ? " cut" : ""}`} style=${style}></i>
              ${cut ? html`<span class=${v >= 0 ? "cutlabel up" : "cutlabel down"}>${v >= 0 ? "▲" : "▼"} ${euro(v, this.locale)}</span>` : nothing}
            </div>`;
          })}
        </div>
        <div class="dticks" aria-hidden="true">
          ${days.map((d, i) =>
            i % 7 === 0 && days.length - i > 3
              ? html`<span style="left:${((i + 0.5) / days.length) * 100}%">${new Intl.DateTimeFormat(this.locale, { day: "numeric", month: "short", timeZone: "UTC" }).format(new Date(`${d.day}T12:00:00Z`))}</span>`
              : nothing,
          )}
        </div>
      </div>
      <div class="legend">
        <span><i class="sw win"></i>${this.tr("savings.leg_win")}</span>
        <span><i class="sw loss"></i>${this.tr("savings.leg_loss")}</span>
        <span><i class="sw part"></i>${this.tr("savings.leg_part")}</span>
      </div>`;
  }

  private renderSplit(s: SavingsSummary): TemplateResult {
    const solar = s.savings_solar_via_battery;
    const trade = s.savings_trade;
    const avg = s.discharge_kwh > 0 && s.savings_battery !== null ? s.savings_battery / s.discharge_kwh : null;
    return html`<dl>
        <div>
          <dt><i class="sw solar"></i>${this.tr("savings.solar_part")}</dt>
          <dd>${solar === null ? "–" : euro(solar, this.locale)}</dd>
          <p>${this.tr("savings.solar_part_help")}</p>
        </div>
        <div>
          <dt><i class="sw trade"></i>${this.tr("savings.trade_part")}</dt>
          <dd>${trade === null ? "–" : euro(trade, this.locale)}</dd>
          <p>${this.tr("savings.trade_part_help")}</p>
        </div>
      </dl>
      <div class="facts">
        <span><b>${kwh(s.charge_kwh, this.locale)}</b> ${this.tr("savings.charged")}</span>
        <span><b>${kwh(s.discharge_kwh, this.locale)}</b> ${this.tr("savings.delivered")}</span>
        ${avg !== null ? html`<span><b>${euro(avg, this.locale)}</b> ${this.tr("savings.per_kwh")}</span>` : nothing}
      </div>`;
  }

  static override styles = css`
    :host {
      display: block;
      color: var(--z-text);
      font-family: var(--z-font);
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 16px;
    }
    .card {
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 16px;
      padding: 20px 24px;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 20px;
    }
    .head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .tabs {
      display: inline-flex;
      padding: 3px;
      border-radius: 999px;
      background: var(--z-track);
    }
    .tabs button {
      min-height: 32px;
      padding: 0 12px;
      border: 0;
      border-radius: 999px;
      background: transparent;
      color: var(--z-text);
      font: inherit;
      font-size: 13px;
      cursor: pointer;
    }
    .tabs button.on {
      background: var(--z-text);
      color: var(--z-on-text);
      font-weight: 600;
    }
    .muted {
      margin: 0;
      color: var(--z-muted);
      font-size: 13px;
    }
    .big {
      display: flex;
      align-items: baseline;
      gap: 10px;
    }
    .amount {
      font-family: var(--z-font-head);
      font-size: 44px;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    .big.win .amount {
      color: var(--z-export);
    }
    .big.loss .amount {
      color: var(--z-deliver);
    }
    .label {
      color: var(--z-muted);
      font-size: 15px;
    }
    .compare {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .row {
      display: grid;
      grid-template-columns: 110px 1fr auto;
      align-items: center;
      gap: 10px;
      font-size: 14px;
    }
    .bar {
      height: 12px;
      border-radius: 6px;
      background: var(--z-track);
      overflow: hidden;
    }
    .bar i {
      display: block;
      height: 100%;
      border-radius: 6px;
    }
    .bar .nb {
      background: var(--z-hold-a);
    }
    .bar .paid {
      background: var(--z-text);
    }
    .val {
      font-weight: 600;
      font-variant-numeric: tabular-nums;
    }
    .warn {
      margin: 0;
      padding: 8px 12px;
      border-radius: 10px;
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
      font-size: 13px;
    }
    .days,
    .notes {
      grid-column: 1 / -1;
    }
    .dchart {
      position: relative;
      height: 200px;
      margin: 6px 0 26px 56px;
    }
    .daxis span {
      position: absolute;
      left: -56px;
      width: 50px;
      transform: translateY(-50%);
      text-align: right;
      font-size: 11px;
      color: var(--z-muted);
    }
    .dbars {
      position: absolute;
      inset: 0;
      display: flex;
      gap: 3px;
    }
    .zero {
      position: absolute;
      left: 0;
      right: 0;
      border-top: 1px solid var(--z-border);
    }
    .dcol {
      position: relative;
      flex: 1 1 0;
    }
    .dcol i {
      position: absolute;
      left: 0;
      right: 0;
      border-radius: 2px;
    }
    i.win,
    .sw.win {
      background: var(--z-export);
    }
    i.loss,
    .sw.loss {
      background: var(--z-deliver);
    }
    i.part {
      opacity: 0.45;
    }
    i.loss.cut {
      border-bottom: 3px dashed var(--z-card);
    }
    i.win.cut {
      border-top: 3px dashed var(--z-card);
    }
    .cutlabel {
      position: absolute;
      left: 50%;
      transform: translateX(-50%);
      white-space: nowrap;
      font-size: 11px;
      font-weight: 700;
      color: var(--z-text);
      background: var(--z-card);
      padding: 0 4px;
      border-radius: 4px;
    }
    .cutlabel.down {
      top: calc(100% + 2px);
    }
    .cutlabel.up {
      bottom: calc(100% + 2px);
    }
    .dcol:last-child .cutlabel {
      left: auto;
      right: 0;
      transform: none;
    }
    .short {
      display: none;
    }
    .sw.part {
      background: repeating-linear-gradient(45deg, var(--z-export) 0 2px, transparent 2px 4px);
      border: 1px solid var(--z-export);
      box-sizing: border-box;
    }
    .dticks {
      position: absolute;
      left: 0;
      right: 0;
      bottom: -20px;
      font-size: 11px;
      color: var(--z-muted);
    }
    .dticks span {
      position: absolute;
      transform: translateX(-50%);
      white-space: nowrap;
    }
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 14px;
      font-size: 12px;
      color: var(--z-muted);
    }
    .legend span,
    dt {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .sw {
      width: 12px;
      height: 12px;
      border-radius: 3px;
      display: inline-block;
      flex: none;
    }
    .sw.solar {
      background: var(--z-solar);
    }
    .sw.trade {
      background: var(--z-charge);
    }
    dl {
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    dl div {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 2px 12px;
    }
    dt {
      font-weight: 600;
      font-size: 14px;
    }
    dd {
      margin: 0;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    dl p {
      grid-column: 1 / -1;
      margin: 0;
      font-size: 13px;
      color: var(--z-muted);
      line-height: 1.45;
    }
    .facts {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 16px;
      padding-top: 10px;
      border-top: 1px solid var(--z-border);
      font-size: 13px;
      color: var(--z-muted);
    }
    .facts b {
      color: var(--z-text);
    }
    .notes ul {
      margin: 0;
      padding-left: 18px;
      font-size: 13px;
      color: var(--z-muted);
      line-height: 1.5;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .skeleton {
      height: 320px;
      border-radius: 16px;
      background: var(--z-track);
    }
    @media (max-width: 900px) {
      .layout {
        grid-template-columns: 1fr;
      }

      .card {
        padding: 16px;
      }
      .amount {
        font-size: 36px;
      }
      .long {
        display: none;
      }
      .short {
        display: inline;
      }
      .row {
        grid-template-columns: 90px 1fr auto;
      }
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "zephyr-savings": ZephyrSavings;
  }
}
