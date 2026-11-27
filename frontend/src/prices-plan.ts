// Card "Prijzen en plan" (SPEC-ui §4.2, design A, approved 26-11).
import {
  LitElement,
  css,
  html,
  nothing,
  svg,
  type PropertyValues,
  type TemplateResult,
} from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { clock, day, euro, kwh, percent } from "./format";
import { t, type Lang } from "./i18n";
import {
  bands,
  bar,
  currentIndex,
  dayOf,
  pastSocLines,
  days,
  quartersOf,
  scale,
  socPoints,
  spreadPct,
  sunLane,
  stats,
  ticks,
  type Period,
  type PlanView,
  type PriceStats,
  type Quarter,
  runBars,
  type RunInput,
} from "./plan";
import { actionFill } from "./theme";

const PERIOD_KEY = "zephyr.period";
const PERIODS: [Period, string][] = [
  ["today", "plan.today"],
  ["tomorrow", "plan.tomorrow"],
  ["both", "plan.both"],
];

export function storedPeriod(): Period {
  try {
    const value = window.localStorage.getItem(PERIOD_KEY);
    return value === "tomorrow" || value === "both" ? value : "today";
  } catch {
    return "today";
  }
}

@customElement("zephyr-prices-plan")
export class ZephyrPricesPlan extends LitElement {
  @property({ attribute: false }) view?: PlanView;
  @property({ attribute: false }) uiLang: Lang = "en";
  @property() locale = "en";
  @property() timeZone = "UTC";
  @property({ type: Boolean }) narrow = false;
  /** Planned appliance runs, drawn as bars under the solar lane (B36). */
  @property({ attribute: false }) runs: RunInput[] = [];

  /** Chosen period; the panel keeps it, so the cards below follow it too. */
  @property({ attribute: false }) period: Period = storedPeriod();
  @state() private sel: number | null = null;

  private scrolledFor = "";

  private tr(
    key: string,
    params: Record<string, string | number> = {},
  ): string {
    return t(this.uiLang, key, params);
  }

  private pick(period: Period): void {
    this.period = period;
    this.dispatchEvent(
      new CustomEvent<Period>("zephyr-period", {
        detail: period,
        bubbles: true,
        composed: true,
      }),
    );
    this.sel = null;
    this.scrolledFor = "";
    try {
      window.localStorage.setItem(PERIOD_KEY, period);
    } catch {
      // Private mode or blocked storage: the choice just is not remembered.
    }
  }

  protected override updated(_changed: PropertyValues<this>): void {
    // On a narrow screen the chart scrolls; start 2 hours before now (SPEC-ui §2).
    const wrap = this.renderRoot.querySelector<HTMLElement>(".scroll");
    const quarters = this.visible();
    const key = `${this.period}|${this.view?.now ?? ""}`;
    if (
      !wrap ||
      wrap.scrollWidth <= wrap.clientWidth ||
      this.scrolledFor === key
    )
      return;
    this.scrolledFor = key;
    const now = currentIndex(quarters);
    if (now > 0)
      wrap.scrollLeft =
        (Math.max(0, now - 8) / quarters.length) * wrap.scrollWidth;
  }

  private visible(): Quarter[] {
    return this.view
      ? quartersOf(this.view.quarters, this.period, this.timeZone)
      : [];
  }

  protected override render(): TemplateResult {
    const view = this.view;
    if (!view) {
      return html`<section class="card">
        <div class="skeleton" aria-hidden="true"></div>
      </section>`;
    }
    const quarters = this.visible();
    const todayQs = dayOf(view.quarters, 0, this.timeZone);
    const tomorrowQs = dayOf(view.quarters, 1, this.timeZone);
    const today = stats(todayQs);
    const tomorrow = stats(tomorrowQs);
    const now = currentIndex(view.quarters);
    const nowQ = now >= 0 ? view.quarters[now] : undefined;
    const title =
      this.period === "today"
        ? "plan.title_today"
        : this.period === "tomorrow"
          ? "plan.title_tomorrow"
          : "plan.title_both";
    return html`<section class="card" aria-label=${this.tr("plan.title")}>
      <div class="head">
        <h2>${this.tr("plan.title")} · ${this.tr(title)}</h2>
        <div class="tabs" role="group" aria-label=${this.tr("plan.period")}>
          ${PERIODS.map(
            ([period, key]) =>
              html`<button
                type="button"
                class=${this.period === period ? "on" : ""}
                aria-pressed=${this.period === period ? "true" : "false"}
                @click=${() => this.pick(period)}
              >
                ${this.tr(key)}
              </button>`,
          )}
        </div>
      </div>
      <div class="prices">
        <div class="cell now">
          <span class="cap"
            >${this.tr("plan.now", { time: nowQ ? clock(nowQ.start, this.locale, this.timeZone) : "–" })}</span
          >
          <span class="value"
            >${nowQ?.buy != null ? euro(nowQ.buy, this.locale) : "–"}</span
          >
          <span class="sub">${this.tr("plan.per_kwh")}</span>
        </div>
        ${this.statCell(todayQs, today, "plan.today")}
        ${this.statCell(tomorrowQs, tomorrow, "plan.tomorrow", true)}
      </div>
      ${this.notes(view, tomorrow)}
      ${quarters.length ? this.chart(quarters) : html`<p class="empty">${this.tr("plan.no_quarters")}</p>`}
      ${this.legend()}
      <slot></slot>
    </section>`;
  }

  private spreadText(s: PriceStats): string {
    const low = s.min.buy as number;
    const high = s.max.buy as number;
    const pct = spreadPct(low, high);
    // Around zero or below a percentage says nothing: then the difference in euro.
    return pct === null
      ? this.tr("plan.spread", { value: euro(high - low, this.locale) })
      : this.tr("plan.spread", { value: `${pct} %` });
  }

  private statCell(
    quarters: Quarter[],
    s: PriceStats | null,
    label: string,
    tomorrow = false,
  ): TemplateResult {
    const dayLabel = quarters.length
      ? day(quarters[0].start, this.locale, this.timeZone)
      : "";
    if (!s) {
      return html`<div class="cell">
        <span class="cap">${this.tr(label)} · ${dayLabel}</span>
        <span class="value small">${this.tr("plan.unknown")}</span>
        <span class="sub">${tomorrow ? this.tr("plan.expected_at") : ""}</span>
      </div>`;
    }
    const known =
      tomorrow && this.view?.tomorrow_known_at
        ? ` · ${this.tr("plan.known_at", { time: clock(this.view.tomorrow_known_at, this.locale, this.timeZone) })}`
        : "";
    return html`<div class="cell">
      <span class="cap">${this.tr(label)} · ${dayLabel}</span>
      <span class="value"
        >${euro(s.min.buy as number, this.locale)} –
        ${euro(s.max.buy as number, this.locale)}<span
          class="spread"
          title=${this.tr("plan.spread_title")}
          >${this.spreadText(s)}</span
        ></span
      >
      <span class="sub"
        >${this.tr("plan.stats", {
          avg: euro(s.avg, this.locale),
          low: clock(s.min.start, this.locale, this.timeZone),
          high: clock(s.max.start, this.locale, this.timeZone),
        })}${known}</span
      >
    </div>`;
  }

  private notes(
    view: PlanView,
    tomorrow: PriceStats | null,
  ): TemplateResult | typeof nothing {
    const notes: TemplateResult[] = [];
    if (view.state === "no_prices")
      notes.push(html`<p class="note warn">${this.tr("plan.no_prices")}</p>`);
    if (view.state === "price_reserve")
      notes.push(html`<p class="note">${this.tr("plan.reserve")}</p>`);
    if (!tomorrow && this.period !== "today")
      notes.push(html`<p class="note">${this.tr("plan.indicative")}</p>`);
    return notes.length ? html`${notes}` : nothing;
  }

  private chart(quarters: Quarter[]): TemplateResult {
    const n = quarters.length;
    const s = scale(quarters);
    const now = currentIndex(quarters);
    const pct = (i: number): string => `${((i / n) * 100).toFixed(3)}%`;
    const dayIdx = days(quarters, this.timeZone);
    const split =
      dayIdx.length > 1
        ? quarters.findIndex(
            (q) =>
              new Date(q.start).getTime() >=
              new Date(dayOf(quarters, 1, this.timeZone)[0].start).getTime(),
          )
        : -1;
    const marks: { q: Quarter; i: number; kind: string }[] = [];
    for (let d = 0; d < dayIdx.length; d++) {
      const dq = dayOf(quarters, d, this.timeZone);
      const st = stats(dq);
      if (!st) continue;
      marks.push({
        q: st.min,
        i: quarters.indexOf(st.min),
        kind: "plan.lowest",
      });
      marks.push({
        q: st.max,
        i: quarters.indexOf(st.max),
        kind: "plan.highest",
      });
    }
    const tickIdx = ticks(
      quarters,
      this.period === "both" ? 6 : 3,
      this.timeZone,
    );
    const focus = this.sel !== null && this.sel < n ? this.sel : null;
    const pts = socPoints(quarters, this.view?.soc_now ?? null);
    const pastLines = pastSocLines(quarters, this.view?.soc_now ?? null);
    const zero = s.lo < 0 ? ((0 - s.lo) / (s.hi - s.lo)) * 100 : null;
    return html`<div class="scroll">
      <div class="chart ${n > 100 ? "wide" : ""}">
        <div class="axis left" aria-hidden="true">
          <span>${euro(s.hi, this.locale)}</span
          ><span>${euro((s.hi + s.lo) / 2, this.locale)}</span
          ><span>${euro(s.lo, this.locale)}</span>
        </div>
        <div class="axis right" aria-hidden="true">
          <span>100 %</span><span>50 %</span><span>0 %</span>
        </div>
        <div
          class="plot"
          tabindex="0"
          role="img"
          aria-label=${this.summary(quarters)}
          @pointermove=${(e: PointerEvent) => this.hover(e, n)}
          @pointerleave=${() => (this.sel = null)}
          @keydown=${(e: KeyboardEvent) => this.key(e, n, now)}
          @blur=${() => (this.sel = null)}
        >
          <div class="grid" style="top:0"></div>
          <div class="grid" style="top:50%"></div>
          ${zero !== null ? html`<div class="zero" style="bottom:${zero}%"></div>` : nothing}
          ${quarters.map((q, i) => {
            if (q.buy === null) return nothing;
            const b = bar(q.buy, s);
            const cls = `bar${q.past ? " past" : ""}${q.indicative ? " ind" : ""}${i === now ? " cur" : ""}${i === focus ? " focus" : ""}`;
            return html`<div
              class=${cls}
              style="left:${pct(i)};width:${pct(1)};bottom:${b.bottom}%;height:${b.height}%"
            ></div>`;
          })}
          <svg
            viewBox="0 0 ${n} 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            ${pastLines.map((p) => svg`<polyline class="halo" points=${p}></polyline><polyline class="soc measured" points=${p}></polyline>`)}
            ${pts ? svg`<polyline class="halo" points=${pts}></polyline><polyline class="soc" points=${pts}></polyline>` : nothing}
          </svg>
          ${
            split > 0
              ? html`<div class="split" style="left:${pct(split)}"></div>
                  <span class="dayname" style="left:calc(${pct(split)} + 6px)"
                    >${day(quarters[split].start, this.locale, this.timeZone)}</span
                  >`
              : nothing
          }
          ${marks.map(({ q, i }) => {
            const left = Math.min(94, Math.max(6, ((i + 0.5) / n) * 100));
            const b = bar(q.buy as number, s);
            return html`<span
              class="mark"
              style="left:${left}%;bottom:calc(${b.bottom + b.height}% + 6px)"
              >${euro(q.buy as number, this.locale)} ·
              ${clock(q.start, this.locale, this.timeZone)}</span
            >`;
          })}
          ${
            now >= 0
              ? html`<div class="nowline" style="left:${pct(now)}"></div>
                  <span class="nowpill" style="left:${pct(now)}"
                    >${this.tr("plan.now_short")}</span
                  >`
              : nothing
          }
          ${focus !== null ? this.tooltip(quarters[focus], focus, n) : nothing}
        </div>
        <div class="band" aria-hidden="true">
          ${bands(quarters).map(
            (b) =>
              html`<div
                class=${b.past ? "seg past" : "seg"}
                style="flex:${b.count} 1 0;background:${b.action ? actionFill(b.action) : "transparent"}"
              ></div>`,
          )}
        </div>
        ${this.sun(quarters)} ${this.runLane(quarters)}
        <div class="ticks" aria-hidden="true">
          ${tickIdx.map((i) => html`<span style="left:${pct(i)}">${clock(quarters[i].start, this.locale, this.timeZone)}</span>`)}
        </div>
      </div>
    </div>`;
  }

  /** Planned appliance runs as bars on the time axis (SPEC-ui-planner §1.2); a fixed start has a lock. */
  private runLane(quarters: Quarter[]): TemplateResult | typeof nothing {
    const bars = runBars(quarters, this.runs);
    if (!bars.length) return nothing;
    const n = quarters.length;
    const rows = Math.max(...bars.map((b) => b.row)) + 1;
    return html`<div
      class="runlane"
      style="height:${rows * 20}px"
      aria-label=${this.tr("plan.runs_label")}
    >
      ${bars.map(
        (b) =>
          html`<div
            class="run"
            style="left:${((b.left / n) * 100).toFixed(3)}%;width:${((b.width / n) * 100).toFixed(3)}%;top:${b.row * 20}px"
            title=${b.name}
          >
            ${b.fixed ? "🔒 " : ""}${b.name}
          </div>`,
      )}
    </div>`;
  }

  /** Lane under the action band: solar per quarter as a small bar (design A, Bjorn 26-11); a green top = solar to spare. */
  private sun(quarters: Quarter[]): TemplateResult | typeof nothing {
    const lane = sunLane(quarters);
    if (!lane) return nothing;
    return html`<div class="sunlane" aria-hidden="true">
      ${lane.map(
        (q) =>
          html`<div class="sq">
            ${q.height > 0 ? html`<i class=${`${q.past ? "" : "fut"}${q.over ? " over" : ""}`} style="height:${q.height}%"></i>` : nothing}
          </div>`,
      )}
    </div>`;
  }

  private hover(e: PointerEvent, n: number): void {
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const i = Math.floor(((e.clientX - rect.left) / rect.width) * n);
    this.sel = Math.max(0, Math.min(n - 1, i));
  }

  private key(e: KeyboardEvent, n: number, now: number): void {
    const step = e.shiftKey ? 4 : 1;
    if (e.key === "ArrowRight")
      this.sel = Math.min(n - 1, (this.sel ?? Math.max(now, 0)) + step);
    else if (e.key === "ArrowLeft")
      this.sel = Math.max(0, (this.sel ?? Math.max(now, 0)) - step);
    else if (e.key === "Escape") this.sel = null;
    else return;
    e.preventDefault();
  }

  private tooltip(q: Quarter, i: number, n: number): TemplateResult {
    const left = ((i + 0.5) / n) * 100;
    const side = left > 60 ? "right" : "left";
    const pos =
      side === "left"
        ? `left:calc(${left}% + 10px)`
        : `right:calc(${100 - left}% + 10px)`;
    const action = q.action
      ? this.tr(`action.${q.action}`) +
        (q.past
          ? ` (${this.tr("plan.actual")})`
          : q.indicative
            ? ` (${this.tr("plan.indicative_short")})`
            : "")
      : q.past
        ? this.tr("plan.no_record")
        : null;
    return html`<div class="tip" role="status" style=${pos}>
      <strong
        >${day(q.start, this.locale, this.timeZone)}
        ${clock(q.start, this.locale, this.timeZone)}</strong
      >
      ${
        q.buy !== null
          ? html`<span
                >${this.tr("plan.tip_buy", { price: euro(q.buy, this.locale) })}</span
              >
              <span
                >${this.tr("plan.tip_sell", { price: euro(q.sell as number, this.locale) })}</span
              >`
          : html`<span>${this.tr("plan.unknown")}</span>`
      }
      ${action ? html`<span>${action}</span>` : nothing}
      ${q.soc !== null ? html`<span>${this.tr(q.past ? "plan.tip_soc_past" : "plan.tip_soc", { soc: percent(q.soc, this.locale) })}</span>` : nothing}
      ${
        q.solar !== null && q.load !== null
          ? html`<span
              >${this.tr(q.past ? "plan.tip_energy_past" : "plan.tip_energy", { solar: kwh(q.solar, this.locale, 2), load: kwh(q.load, this.locale, 2) })}</span
            >`
          : nothing
      }
      ${q.excluded ? html`<span>${this.tr("plan.tip_airco", { kwh: kwh(q.excluded, this.locale, 2) })}</span>` : nothing}
      ${q.appliances ? html`<span>${this.tr("plan.tip_appliances", { kwh: kwh(q.appliances, this.locale, 2) })}</span>` : nothing}
    </div>`;
  }

  private summary(quarters: Quarter[]): string {
    const s = stats(quarters);
    if (!s) return this.tr("plan.title");
    return this.tr("plan.aria", {
      low: euro(s.min.buy as number, this.locale),
      low_time: clock(s.min.start, this.locale, this.timeZone),
      high: euro(s.max.buy as number, this.locale),
      high_time: clock(s.max.start, this.locale, this.timeZone),
    });
  }

  private legend(): TemplateResult {
    const item = (fill: string, key: string, cls = "sw"): TemplateResult =>
      html`<span class="li"
        ><span class=${cls} style="background:${fill}"></span
        >${this.tr(key)}</span
      >`;
    return html`<div class="legend">
      ${item("var(--z-bar)", "plan.legend_price")}
      ${item(actionFill("charge"), "action.charge")}
      ${item(actionFill("deliver"), "action.deliver")}
      ${item(actionFill("hold"), "action.hold")}
      ${item(actionFill("export"), "action.export")}
      ${item("var(--z-solar)", "plan.legend_solar")}
      ${item("var(--z-solar)", "plan.legend_solar_over", "sw over")}
      <span class="li"
        ><span class="line solid"></span
        >${this.tr("plan.legend_soc_past")}</span
      >
      <span class="li"
        ><span class="line"></span>${this.tr("plan.legend_soc")}</span
      >
      <span class="li">${this.tr("plan.legend_past")}</span>
    </div>`;
  }

  // Colours come from the panel (CSS custom properties inherit into this shadow root).
  static override styles = [
    css`
      :host {
        display: block;
      }
      .card {
        background: var(--z-card);
        border: 1px solid var(--z-border);
        border-radius: 16px;
        padding: 20px 24px 18px;
        display: flex;
        flex-direction: column;
        gap: 16px;
        color: var(--z-text);
        font-family: var(--z-font);
      }
      .spread {
        margin-left: 10px;
        padding: 2px 8px;
        border-radius: 999px;
        background: var(--z-info-bg);
        font-family: var(--z-font);
        font-size: 12px;
        font-weight: 600;
        vertical-align: middle;
        white-space: nowrap;
      }
      .skeleton {
        height: 320px;
        border-radius: 12px;
        background: var(--z-track);
      }
      .head {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
      }
      h2 {
        margin: 0;
        font-family: var(--z-font-head);
        font-size: 20px;
      }
      .tabs {
        display: flex;
        gap: 4px;
        padding: 4px;
        border-radius: 999px;
        background: var(--z-bg);
        border: 1px solid var(--z-border);
      }
      .tabs button {
        min-height: 36px;
        padding: 0 16px;
        border: 0;
        border-radius: 999px;
        background: transparent;
        color: var(--z-text);
        font: inherit;
        font-size: 14px;
        cursor: pointer;
      }
      .tabs button.on {
        background: var(--z-text);
        color: var(--z-on-text);
        font-weight: 600;
      }
      .tabs button:focus-visible,
      .plot:focus-visible {
        outline: 2px solid var(--z-charge);
        outline-offset: 2px;
      }
      .prices {
        display: flex;
        flex-wrap: wrap;
        border: 1px solid var(--z-border);
        border-radius: 12px;
        overflow: hidden;
      }
      .cell {
        flex: 1 1 220px;
        padding: 12px 16px;
        display: flex;
        flex-direction: column;
        gap: 2px;
        border-left: 1px solid var(--z-border);
        margin-left: -1px;
      }
      .cell.now {
        flex: 1 1 150px;
        background: var(--z-bg);
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
        font-size: 22px;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
      }
      .value.small {
        font-size: 18px;
      }
      .sub {
        font-size: 13px;
        color: var(--z-muted);
        font-variant-numeric: tabular-nums;
      }
      .note {
        margin: 0;
        padding: 10px 14px;
        border-radius: 10px;
        background: var(--z-info-bg);
        font-size: 14px;
        line-height: 1.5;
      }
      .note.warn {
        background: var(--z-warn-bg);
        color: var(--z-warn-text);
      }
      .empty {
        margin: 0;
        color: var(--z-muted);
      }
      .scroll {
        overflow-x: auto;
        overflow-y: visible;
      }
      .chart {
        position: relative;
        padding: 26px 44px 0 52px;
      }
      .axis {
        position: absolute;
        top: 26px;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        font-size: 12px;
        color: var(--z-muted);
        font-variant-numeric: tabular-nums;
      }
      .axis.left {
        left: 0;
        width: 46px;
        text-align: right;
      }
      .axis.right {
        right: 0;
        width: 40px;
        white-space: nowrap;
      }
      .plot {
        position: relative;
        height: 220px;
        border-bottom: 1px solid var(--z-border);
        touch-action: pan-x;
      }
      .grid {
        position: absolute;
        left: 0;
        right: 0;
        border-top: 1px dashed var(--z-border);
      }
      .zero {
        position: absolute;
        left: 0;
        right: 0;
        border-top: 1px solid var(--z-muted);
      }
      .bar {
        position: absolute;
        box-sizing: border-box;
        border-left: 0.5px solid var(--z-card);
        background: var(--z-bar);
      }
      .bar.past {
        opacity: 0.4;
      }
      .bar.ind {
        background: repeating-linear-gradient(
          45deg,
          var(--z-bar) 0 3px,
          transparent 3px 6px
        );
        opacity: 0.7;
      }
      .bar.cur {
        background: var(--z-text);
        opacity: 1;
      }
      .bar.focus {
        background: var(--z-charge);
        opacity: 1;
      }
      svg {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        overflow: visible;
        pointer-events: none;
      }
      .halo,
      .soc {
        fill: none;
        stroke-linejoin: round;
        vector-effect: non-scaling-stroke;
      }
      .halo {
        stroke: var(--z-card);
        stroke-width: 7;
      }
      .soc {
        stroke: var(--z-text);
        stroke-width: 3;
        stroke-dasharray: 6 5;
      }
      .soc.measured {
        stroke-dasharray: none;
        opacity: 0.7;
      }
      .split {
        position: absolute;
        top: -20px;
        bottom: 0;
        border-left: 1px solid var(--z-border);
      }
      .dayname {
        position: absolute;
        top: -22px;
        font-size: 12px;
        font-weight: 600;
        color: var(--z-muted);
        white-space: nowrap;
      }
      .mark {
        position: absolute;
        transform: translateX(-50%);
        padding: 2px 8px;
        border-radius: 999px;
        background: var(--z-card);
        border: 1px solid var(--z-border);
        font-size: 11px;
        font-weight: 600;
        white-space: nowrap;
        font-variant-numeric: tabular-nums;
        pointer-events: none;
      }
      .nowline {
        position: absolute;
        top: -8px;
        bottom: 0;
        border-left: 2px solid var(--z-text);
        pointer-events: none;
      }
      .nowpill {
        position: absolute;
        top: -26px;
        transform: translateX(-50%);
        padding: 2px 8px;
        border-radius: 999px;
        background: var(--z-text);
        color: var(--z-on-text);
        font-size: 11px;
        font-weight: 600;
        pointer-events: none;
      }
      .tip {
        position: absolute;
        top: 8px;
        z-index: 2;
        min-width: 170px;
        padding: 10px 12px;
        border-radius: 10px;
        background: var(--z-card);
        border: 1px solid var(--z-border);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
        display: flex;
        flex-direction: column;
        gap: 2px;
        font-size: 13px;
        font-variant-numeric: tabular-nums;
        pointer-events: none;
      }
      .band {
        display: flex;
        height: 14px;
        margin-top: 6px;
        border-radius: 4px;
        overflow: hidden;
        background: var(--z-track);
      }
      .seg.past {
        opacity: 0.4;
      }
      .runlane {
        position: relative;
        margin-top: 4px;
      }
      .run {
        position: absolute;
        height: 16px;
        border-radius: 5px;
        background: repeating-linear-gradient(
          135deg,
          color-mix(in srgb, var(--z-charge) 30%, transparent) 0 4px,
          color-mix(in srgb, var(--z-charge) 18%, transparent) 4px 8px
        );
        border: 1px solid color-mix(in srgb, var(--z-charge) 60%, transparent);
        color: var(--z-text);
        font-size: 10.5px;
        line-height: 14px;
        padding: 0 4px;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        box-sizing: border-box;
      }
      .sunlane {
        display: flex;
        align-items: flex-end;
        height: 18px;
        margin-top: 2px;
        border-radius: 3px;
        overflow: hidden;
        background: var(--z-track);
      }
      .sq {
        flex: 1 1 0;
        height: 100%;
        display: flex;
        align-items: flex-end;
      }
      .sq i {
        display: block;
        width: 100%;
        background: var(--z-solar);
      }
      .sq i.fut {
        opacity: 0.55;
      }
      .sq i.over {
        box-shadow: inset 0 2px 0 var(--z-export);
      }
      .sw.over {
        box-shadow: inset 0 3px 0 var(--z-export);
      }
      .ticks {
        position: relative;
        height: 22px;
      }
      .ticks span {
        position: absolute;
        top: 5px;
        transform: translateX(-50%);
        font-size: 11px;
        color: var(--z-muted);
        white-space: nowrap;
        font-variant-numeric: tabular-nums;
      }
      .ticks span:first-child {
        transform: none;
      }
      .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 16px;
        font-size: 13px;
        color: var(--z-muted);
      }
      .li {
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }
      .sw {
        width: 14px;
        height: 14px;
        border-radius: 3px;
        display: inline-block;
      }
      .line {
        width: 18px;
        border-top: 3px dashed var(--z-text);
        display: inline-block;
      }
      .line.solid {
        border-top-style: solid;
        opacity: 0.7;
      }
      @media (max-width: 700px) {
        .card {
          padding: 16px;
        }
        /* Scroll sideways; the chart starts 2 hours before now (see updated()). */
        .chart {
          min-width: 680px;
        }
        .chart.wide {
          min-width: 1300px;
        }
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    "zephyr-prices-plan": ZephyrPricesPlan;
  }
}
