// Screen "Stroom" (M6): the flow now, how well the meter stayed at zero today, energy per route and the airco.
import { LitElement, css, html, nothing, svg, type TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import "./flow";
import { euro, kwh, percent, watts } from "./format";
import { t, type Lang } from "./i18n";
import type { Now } from "./types";

export type RouteKey =
  | "solar_house"
  | "solar_battery"
  | "solar_grid"
  | "grid_house"
  | "grid_battery"
  | "battery_house"
  | "battery_grid";

export interface StroomToday {
  routes: Record<RouteKey, number>;
  house_kwh: number;
  solar_kwh: number;
  self_use: number | null;
  own_source: number | null;
  grid_battery_price: number | null;
  airco: {
    kwh: number;
    share: number | null;
    solar_kwh: number;
    grid_kwh: number;
    grid_cost: number | null;
    grid_price: number | null;
  } | null;
  /** Start (UTC ISO) of the last closed quarter. */
  last_quarter: string | null;
  quarters: number;
}

/** One 5-minute cell: [steering s, in band s, import Wh, export Wh]; null = no data. */
export type ZeroCell = [number, number, number, number] | null;

export interface ZeroView {
  date: string | null;
  band_w: number;
  bucket_s: number;
  score: number | null;
  steering_s: number;
  import_kwh: number;
  export_kwh: number;
  mean_dev_w: number | null;
  buckets: ZeroCell[];
}

export interface StroomView {
  today: StroomToday;
  zero: ZeroView | null;
  live: boolean;
  airco_set: boolean;
}

/** Goal for the share of steering time within the band (PLAN-M4b). */
export const ZERO_GOAL = 0.8;

export type CellKind = "none" | "idle" | "good" | "import" | "export";

/** Colour of a 5-minute cell: mostly in band, else the side it mostly missed to; not steering = idle. */
export function cellKind(cell: ZeroCell): CellKind {
  if (!cell) return "none";
  const [steering, inBand, imp, exp] = cell;
  if (steering < 30) return "idle";
  if (inBand / steering >= 0.8) return "good";
  return imp >= exp ? "import" : "export";
}

/** Rows per source for "Energie per route", in the screen's order. */
export const ROUTE_GROUPS: [string, [RouteKey, string][]][] = [
  [
    "solar",
    [
      ["solar_house", "house"],
      ["solar_battery", "battery"],
      ["solar_grid", "grid"],
    ],
  ],
  [
    "grid",
    [
      ["grid_house", "house"],
      ["grid_battery", "battery"],
    ],
  ],
  [
    "battery",
    [
      ["battery_house", "house"],
      ["battery_grid", "grid"],
    ],
  ],
];

@customElement("zephyr-stroom")
export class ZephyrStroom extends LitElement {
  @property({ attribute: false }) now?: Now;
  @property({ attribute: false }) view?: StroomView;
  @property({ attribute: false }) uiLang: Lang = "en";
  @property() locale = "en";
  @property() timeZone = "UTC";

  private tr(
    key: string,
    params: Record<string, string | number> = {},
  ): string {
    return t(this.uiLang, key, params);
  }

  protected override render(): TemplateResult {
    const v = this.view;
    return html`<div class="layout">
      <zephyr-flow
        .now=${this.now}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
      ></zephyr-flow>
      ${v ? this.renderZero(v) : html`<section class="card skeleton"></section>`}
      ${v ? this.renderRoutes(v.today) : nothing}
      ${v && v.airco_set ? this.renderAirco(v.today) : nothing}
    </div>`;
  }

  private renderZero(v: StroomView): TemplateResult {
    const z = v.zero;
    const score = z?.score ?? null;
    const good = score !== null && score >= ZERO_GOAL;
    return html`<section class="card" aria-labelledby="zr-title">
      <div>
        <h2 id="zr-title">${this.tr("stroom.zero_title")}</h2>
        <p class="sub">
          ${this.tr("stroom.zero_sub", { band: z?.band_w ?? 50 })}
        </p>
      </div>
      ${
        score === null
          ? html`<p class="empty">
              ${this.tr(v.live ? "stroom.zero_empty" : "stroom.zero_shadow")}
            </p>`
          : html`<div class="row">
              <span class="big">${percent(score * 100, this.locale)}</span>
              <span class=${good ? "pill good" : "pill warn"}
                >${this.tr(good ? "stroom.zero_good" : "stroom.zero_low", { goal: percent(ZERO_GOAL * 100, this.locale) })}</span
              >
            </div>`
      }
      ${z ? this.strip(z) : nothing}
      <div class="legend">
        <span
          ><i class="k good"></i
          >${this.tr("stroom.zero_in", { band: z?.band_w ?? 50 })}</span
        >
        <span><i class="k import"></i>${this.tr("stroom.zero_import")}</span>
        <span><i class="k export"></i>${this.tr("stroom.zero_export")}</span>
        <span><i class="k idle"></i>${this.tr("stroom.zero_idle")}</span>
      </div>
      ${
        z && score !== null
          ? html`<div class="facts">
              <span
                ><span class="k-l">${this.tr("stroom.zero_imported")}</span
                ><b>${kwh(z.import_kwh, this.locale, 2)}</b></span
              >
              <span
                ><span class="k-l">${this.tr("stroom.zero_exported")}</span
                ><b>${kwh(z.export_kwh, this.locale, 2)}</b></span
              >
              <span
                ><span class="k-l">${this.tr("stroom.zero_mean")}</span
                ><b>${watts(z.mean_dev_w ?? 0, this.locale)}</b></span
              >
            </div>`
          : nothing
      }
    </section>`;
  }

  private strip(z: ZeroView): TemplateResult {
    const n = z.buckets.length || 288;
    const w = 360 / n;
    const cells = z.buckets.map((cell, i) => {
      const kind = cellKind(cell);
      return kind === "none"
        ? nothing
        : svg`<rect x=${(i * w).toFixed(2)} y="2" width=${(w + 0.3).toFixed(2)} height="22" class=${`c ${kind}`}></rect>`;
    });
    const label = this.tr("stroom.zero_strip");
    return html`<svg
      class="strip"
      viewBox="0 0 360 40"
      role="img"
      aria-label=${label}
    >
      <rect x="0" y="2" width="360" height="22" class="frame-bg"></rect>
      ${cells}
      <rect x="0" y="2" width="360" height="22" rx="3" class="frame"></rect>
      ${[0, 6, 12, 18, 24].map(
        (h) =>
          svg`<text x=${Math.min(358, Math.max(1, h * 15))} y="37" text-anchor=${h === 0 ? "start" : h === 24 ? "end" : "middle"}>${String(h).padStart(2, "0")}:00</text>`,
      )}
    </svg>`;
  }

  private renderRoutes(d: StroomToday): TemplateResult {
    const max = Math.max(0.5, ...Object.values(d.routes));
    const until = d.last_quarter
      ? new Date(
          new Date(d.last_quarter).getTime() + 15 * 60_000,
        ).toLocaleTimeString(this.locale, {
          hour: "2-digit",
          minute: "2-digit",
          timeZone: this.timeZone,
        })
      : null;
    return html`<section class="card" aria-labelledby="rt-title">
      <div>
        <h2 id="rt-title">${this.tr("stroom.routes_title")}</h2>
        <p class="sub">
          ${until ? this.tr("stroom.routes_sub", { until }) : this.tr("stroom.routes_none")}
        </p>
      </div>
      ${ROUTE_GROUPS.map(
        ([src, rows]) =>
          html`<div class="grp">${this.tr(`stroom.src_${src}`)}</div>
            ${rows.map(
              ([key, to]) =>
                html`<div class="route">
                  <span>→ ${this.tr(`stroom.to_${to}`)}</span>
                  <div class="bar">
                    <div
                      class=${`fill ${src}`}
                      style=${`width:${Math.min(100, (d.routes[key] / max) * 100)}%`}
                    ></div>
                  </div>
                  <span class="num">${kwh(d.routes[key], this.locale)}</span>
                </div>`,
            )}`,
      )}
      <div class="facts">
        ${
          d.self_use !== null
            ? html`<span
                ><span class="k-l">${this.tr("stroom.self_use")}</span
                ><b>${percent(d.self_use * 100, this.locale)}</b></span
              >`
            : nothing
        }
        ${
          d.own_source !== null
            ? html`<span
                ><span class="k-l">${this.tr("stroom.own_source")}</span
                ><b>${percent(d.own_source * 100, this.locale)}</b></span
              >`
            : nothing
        }
        ${
          d.grid_battery_price !== null
            ? html`<span
                ><span class="k-l">${this.tr("stroom.grid_battery_price")}</span
                ><b>${euro(d.grid_battery_price, this.locale)}/kWh</b></span
              >`
            : nothing
        }
      </div>
    </section>`;
  }

  private renderAirco(d: StroomToday): TemplateResult {
    const a = d.airco;
    const max = a ? Math.max(0.1, a.solar_kwh, a.grid_kwh) : 1;
    return html`<section class="card" aria-labelledby="ac-title">
      <div>
        <h2 id="ac-title">${this.tr("stroom.airco_title")}</h2>
        <p class="sub">${this.tr("stroom.airco_sub")}</p>
      </div>
      ${
        !a
          ? html`<p class="empty">${this.tr("stroom.routes_none")}</p>`
          : html`<div class="row">
                <span class="big">${kwh(a.kwh, this.locale)}</span>
                ${a.share !== null ? html`<span class="muted">${this.tr("stroom.airco_share", { share: percent(a.share * 100, this.locale) })}</span>` : nothing}
              </div>
              <div class="grp">${this.tr("stroom.airco_fed")}</div>
              ${(
                [
                  ["solar", a.solar_kwh],
                  ["grid", a.grid_kwh],
                ] as const
              ).map(
                ([src, value]) =>
                  html`<div class="route">
                    <span>${this.tr(`stroom.src_${src}`)}</span>
                    <div class="bar">
                      <div
                        class=${`fill ${src}`}
                        style=${`width:${(value / max) * 100}%`}
                      ></div>
                    </div>
                    <span class="num">${kwh(value, this.locale)}</span>
                  </div>`,
              )}
              ${
                a.grid_cost !== null
                  ? html`<div class="facts">
                      <span
                        ><span class="k-l">${this.tr("stroom.airco_cost")}</span
                        ><b>${euro(a.grid_cost, this.locale)}</b></span
                      >
                      ${
                        a.grid_price !== null
                          ? html`<span
                              ><span class="k-l"
                                >${this.tr("stroom.airco_price")}</span
                              ><b
                                >${euro(a.grid_price, this.locale)}/kWh</b
                              ></span
                            >`
                          : nothing
                      }
                    </div>`
                  : nothing
              }`
      }
    </section>`;
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
      align-items: start;
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
    .skeleton {
      min-height: 220px;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 18px;
    }
    .sub,
    .empty,
    .muted {
      margin: 2px 0 0;
      color: var(--z-muted);
      font-size: 13px;
    }
    .row {
      display: flex;
      gap: 14px;
      align-items: baseline;
      flex-wrap: wrap;
    }
    .big {
      font-family: var(--z-font-head);
      font-size: 40px;
      font-weight: 600;
      line-height: 1;
    }
    .pill {
      border-radius: 99px;
      padding: 2px 10px;
      font-size: 12px;
      font-weight: 600;
    }
    .pill.good {
      background: var(--z-good-bg);
      color: var(--z-good-text);
    }
    .pill.warn {
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
    }
    .strip {
      width: 100%;
      max-width: 520px;
      display: block;
    }
    .strip text {
      font-size: 9.5px;
      fill: var(--z-muted);
      font-family: var(--z-font);
    }
    .frame-bg {
      fill: var(--z-bg);
    }
    .frame {
      fill: none;
      stroke: var(--z-border);
    }
    .c.good,
    .k.good {
      fill: var(--z-bar);
      background: var(--z-bar);
      opacity: 0.6;
    }
    .c.import,
    .k.import {
      fill: var(--z-deliver);
      background: var(--z-deliver);
    }
    .c.export,
    .k.export {
      fill: var(--z-export);
      background: var(--z-export);
    }
    .c.idle,
    .k.idle {
      fill: var(--z-track);
      background: var(--z-track);
    }
    .legend {
      display: flex;
      gap: 6px 14px;
      flex-wrap: wrap;
      font-size: 12px;
      color: var(--z-muted);
    }
    .legend .k {
      display: inline-block;
      width: 12px;
      height: 8px;
      border-radius: 2px;
      margin-right: 5px;
    }
    .facts {
      display: flex;
      gap: 8px 22px;
      flex-wrap: wrap;
      margin-top: 4px;
    }
    .facts > span {
      display: flex;
      flex-direction: column;
    }
    .k-l {
      color: var(--z-muted);
      font-size: 12px;
    }
    .grp {
      font-size: 11.5px;
      color: var(--z-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-top: 4px;
    }
    .route {
      display: grid;
      grid-template-columns: 90px minmax(0, 1fr) 70px;
      gap: 8px;
      align-items: center;
      font-size: 13.5px;
    }
    .bar {
      height: 12px;
      border-radius: 6px;
      background: var(--z-track);
      overflow: hidden;
    }
    .fill {
      height: 100%;
      border-radius: 6px;
    }
    .fill.solar {
      background: var(--z-solar);
    }
    .fill.grid {
      background: var(--z-bar);
    }
    .fill.battery {
      background: var(--z-deliver);
    }
    .num {
      text-align: right;
      font-variant-numeric: tabular-nums;
    }
    @media (max-width: 900px) {
      .layout {
        grid-template-columns: minmax(0, 1fr);
      }
    }
    @media (max-width: 600px) {
      .card {
        padding: 16px;
      }
      .big {
        font-size: 34px;
      }
    }
  `;
}
