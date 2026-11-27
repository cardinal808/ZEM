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

/** One second: [s before now, P1 W, target W, setpoint W (+ charging), battery W (+ charging), steering]. */
export type RegSample = [
  number,
  number | null,
  number,
  number,
  number | null,
  boolean,
];

export interface RegulationView {
  window_s: number;
  band_w: number;
  samples: RegSample[];
  follow_w: number | null;
  peaks: number;
  recovery_s: number | null;
}

/** A consumer in view: an appliance with a plug (B36) or the airco (B41). */
export interface HouseDevice {
  id: string;
  /** null for the airco: the panel names it. */
  name: string | null;
  kind: string;
  floor: "attic" | "first" | "ground" | "shed" | "outside" | string;
  shown: boolean;
  power_w: number | null;
  today_kwh: number | null;
}

/** Name of a consumer: its own name, or the kind's text. */
export function deviceName(
  d: HouseDevice,
  tr: (key: string) => string,
): string {
  return d.name ?? tr(`stroom.kind_${d.kind}`);
}

/** Rows of "Verbruikers vandaag": the shown consumers by kWh today (largest first), then the rest of the house. */
export function deviceRows(
  devices: HouseDevice[],
  rest: number | null,
): { id: string; device: HouseDevice | null; kwh: number | null }[] {
  const rows = devices
    .filter((d) => d.shown)
    .map((d) => ({
      id: d.id,
      device: d as HouseDevice | null,
      kwh: d.today_kwh,
    }))
    .sort((a, b) => (b.kwh ?? -1) - (a.kwh ?? -1));
  if (rest !== null) rows.push({ id: "rest", device: null, kwh: rest });
  return rows;
}

export interface StroomView {
  devices?: HouseDevice[];
  rest_today_kwh?: number | null;
  today: StroomToday;
  zero: ZeroView | null;
  regulation?: RegulationView | null;
  live: boolean;
  airco_set: boolean;
}

/** SVG path through the points; a gap (null) breaks the line. */
export function linePath(
  points: [number, number | null][],
  x: (t: number) => number,
  y: (v: number) => number,
): string {
  let d = "";
  let pen = false;
  for (const [t, v] of points) {
    if (v === null) {
      pen = false;
      continue;
    }
    d += `${pen ? "L" : "M"}${x(t).toFixed(1)},${y(v).toFixed(1)}`;
    pen = true;
  }
  return d;
}

/** Axis label with sign: +600 W, 0 W, −1.250 W. */
export function signedW(v: number, locale: string): string {
  const n = Math.round(v);
  return `${n > 0 ? "+" : n < 0 ? "−" : ""}${Math.abs(n).toLocaleString(locale)} W`;
}

/** Symmetric axis limit for the P1 deviation chart: at least 200 W, rounded up to 100 W. */
export function devLimit(samples: RegSample[]): number {
  let m = 200;
  for (const [, g, target] of samples)
    if (g !== null) m = Math.max(m, Math.abs(g - target));
  return Math.ceil(m / 100) * 100;
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
      ${v && (v.devices?.length || v.airco_set) ? this.renderDevices(v) : nothing}
      ${v?.regulation ? this.renderRegulation(v.regulation, v.live) : nothing}
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

  private renderRegulation(r: RegulationView, live: boolean): TemplateResult {
    // A narrower drawing on a phone keeps the labels readable (the view refreshes every few seconds).
    const narrow =
      typeof window !== "undefined" &&
      window.matchMedia?.("(max-width: 600px)").matches;
    const W = narrow ? 360 : 760;
    const L = narrow ? 50 : 52;
    const R = W - 8;
    const win = r.window_s;
    const x = (t: number): number => L + ((t + win) / win) * (R - L);
    // top: P1 minus its target (0 W, or the airco), with the band
    const T0 = 14;
    const H1 = 110;
    const lim = devLimit(r.samples);
    const y1 = (v: number): number =>
      T0 + H1 / 2 - (Math.max(-lim, Math.min(lim, v)) / lim) * (H1 / 2);
    // bottom: setpoint and battery, + charging
    const T2 = T0 + H1 + 34;
    const H2 = 90;
    let lo = 0;
    let hi = 0;
    for (const [, , , sp, b] of r.samples) {
      lo = Math.min(lo, sp, b ?? 0);
      hi = Math.max(hi, sp, b ?? 0);
    }
    const span = Math.max(500, Math.ceil((hi - lo) / 250) * 250);
    const base = Math.floor(lo / 250) * 250;
    const y2 = (v: number): number => T2 + H2 - ((v - base) / span) * H2;
    const dev = linePath(
      r.samples.map(([t, g, target]) => [t, g === null ? null : g - target]),
      x,
      y1,
    );
    const sp = linePath(
      r.samples.map(([t, , , s]) => [t, s]),
      x,
      y2,
    );
    const bat = linePath(
      r.samples.map(([t, , , , b]) => [t, b]),
      x,
      y2,
    );
    const idle: TemplateResult[] = [];
    let from: number | null = null;
    r.samples.forEach(([t, , , , , steer], i) => {
      const last = i === r.samples.length - 1;
      if (!steer && from === null) from = t;
      if ((steer || last) && from !== null) {
        idle.push(
          svg`<rect x=${x(from)} y=${T0} width=${Math.max(1, x(t) - x(from))} height=${T2 + H2 - T0} class="idle"></rect>`,
        );
        from = null;
      }
    });
    const ticks2 = [base, base + span / 2, base + span];
    const label = this.tr("stroom.reg_title");
    return html`<section class="card wide" aria-labelledby="rg-title">
      <div>
        <h2 id="rg-title">${label}</h2>
        <p class="sub">${this.tr("stroom.reg_sub")}</p>
      </div>
      ${
        r.samples.length < 2
          ? html`<p class="empty">${this.tr("stroom.reg_empty")}</p>`
          : html`<svg
                class="reg"
                viewBox="0 0 ${W} ${T2 + H2 + 22}"
                role="img"
                aria-label=${label}
              >
                ${idle}
                <rect
                  x=${L}
                  y=${y1(r.band_w)}
                  width=${R - L}
                  height=${y1(-r.band_w) - y1(r.band_w)}
                  class="band"
                ></rect>
                <line
                  x1=${L}
                  x2=${R}
                  y1=${y1(0)}
                  y2=${y1(0)}
                  class="axis"
                ></line>
                ${[lim, 0, -lim].map(
                  (v) =>
                    svg`<text x=${L - 6} y=${y1(v) + 3} text-anchor="end">${signedW(v, this.locale)}</text>`,
                )}
                <text x=${L} y=${T0 - 3} class="cap">
                  ${this.tr("stroom.reg_p1")}
                </text>
                <path d=${dev} class="dev"></path>
                ${ticks2.map(
                  (
                    v,
                  ) => svg`<line x1=${L} x2=${R} y1=${y2(v)} y2=${y2(v)} class="grid"></line>
                  <text x=${L - 6} y=${y2(v) + 3} text-anchor="end">${signedW(v, this.locale)}</text>`,
                )}
                <text x=${L} y=${T2 - 5} class="cap">
                  ${this.tr("stroom.reg_battery")}
                </text>
                <path d=${sp} class="sp"></path>
                <path d=${bat} class="bat"></path>
                ${[
                  [
                    -win,
                    this.tr("stroom.reg_ago", { m: Math.round(win / 60) }),
                  ],
                  [
                    -win / 2,
                    this.tr("stroom.reg_ago", { m: Math.round(win / 120) }),
                  ],
                  [0, this.tr("stroom.reg_now")],
                ].map(
                  ([t, text]) =>
                    svg`<text x=${x(t as number)} y=${T2 + H2 + 16} text-anchor=${t === 0 ? "end" : t === -win ? "start" : "middle"}>${text}</text>`,
                )}
              </svg>
              <div class="legend">
                <span><i class="k dev"></i>${this.tr("stroom.reg_dev")}</span>
                <span><i class="k band"></i>±${r.band_w} W</span>
                <span><i class="k sp"></i>${this.tr("stroom.reg_sp")}</span>
                <span><i class="k bat"></i>${this.tr("stroom.reg_bat")}</span>
                <span
                  ><i class="k idle"></i
                  >${this.tr(live ? "stroom.reg_idle" : "stroom.reg_shadow")}</span
                >
              </div>
              <div class="facts">
                <span
                  ><span class="k-l">${this.tr("stroom.reg_recovery")}</span
                  ><b
                    >${r.recovery_s === null ? "–" : this.tr("stroom.reg_seconds", { s: r.recovery_s.toLocaleString(this.locale) })}</b
                  ></span
                >
                <span
                  ><span class="k-l">${this.tr("stroom.reg_follow")}</span
                  ><b
                    >${r.follow_w === null ? "–" : watts(r.follow_w, this.locale)}</b
                  ></span
                >
                <span
                  ><span class="k-l">${this.tr("stroom.reg_peaks")}</span
                  ><b>${r.peaks}</b></span
                >
              </div>`
      }
    </section>`;
  }

  private renderDevices(v: StroomView): TemplateResult {
    const tr = (k: string): string => this.tr(k);
    const rows = deviceRows(v.devices ?? [], v.rest_today_kwh ?? null);
    const max = Math.max(0.5, ...rows.map((r) => r.kwh ?? 0));
    const a = v.today.airco;
    return html`<section class="card" aria-labelledby="dv-title">
      <div>
        <h2 id="dv-title">${this.tr("stroom.devices_title")}</h2>
        <p class="sub">${this.tr("stroom.devices_sub")}</p>
      </div>
      ${rows.map(
        (r) =>
          html`<div class="route dev">
            <span
              >${r.device ? deviceName(r.device, tr) : this.tr("stroom.rest")}${
                r.device && r.device.power_w !== null && r.device.power_w >= 10
                  ? html` <span class="live"
                      >${watts(r.device.power_w, this.locale)}</span
                    >`
                  : nothing
              }</span
            >
            <div class="bar">
              <div
                class=${r.device ? "fill house" : "fill grid"}
                style=${`width:${Math.min(100, ((r.kwh ?? 0) / max) * 100)}%`}
              ></div>
            </div>
            <span class="num"
              >${r.kwh === null ? "–" : kwh(r.kwh, this.locale)}</span
            >
          </div>`,
      )}
      <div class="facts">
        ${
          a
            ? html`<span
                ><span class="k-l">${this.tr("stroom.airco_not_battery")}</span
                ><b
                  >${this.tr("stroom.airco_fed_line", { solar: kwh(a.solar_kwh, this.locale), grid: kwh(a.grid_kwh, this.locale) })}${
                    a.grid_cost !== null
                      ? ` · ${euro(a.grid_cost, this.locale)}`
                      : ""
                  }</b
                ></span
              >`
            : nothing
        }
        <span
          ><span class="k-l">${this.tr("stroom.house_total")}</span
          ><b>${kwh(v.today.house_kwh, this.locale)}</b></span
        >
      </div>
      ${(v.devices ?? []).some((d) => d.kind !== "airco") ? nothing : html`<p class="muted small">${this.tr("stroom.devices_hint")}</p>`}
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
    .wide {
      grid-column: 1 / -1;
    }
    .reg {
      width: 100%;
      max-width: 1000px;
      display: block;
    }
    .reg text {
      font-size: 10px;
      fill: var(--z-muted);
      font-family: var(--z-font);
    }
    .reg .cap {
      font-size: 10.5px;
    }
    .reg .band,
    .k.band {
      fill: var(--z-good-bg);
      background: var(--z-good-bg);
    }
    .reg .idle {
      fill: var(--z-track);
      opacity: 0.45;
    }
    .reg .axis,
    .reg .grid {
      stroke: var(--z-border);
    }
    .reg path {
      fill: none;
      stroke-width: 1.8;
      stroke-linejoin: round;
    }
    .reg .dev {
      stroke: var(--z-bar);
    }
    .reg .sp {
      stroke: var(--z-charge);
      stroke-dasharray: 5 3;
    }
    .reg .bat {
      stroke: var(--z-deliver);
    }
    .k.dev {
      background: var(--z-bar);
    }
    .k.sp {
      background: var(--z-charge);
    }
    .k.bat {
      background: var(--z-deliver);
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
    .fill.house {
      background: var(--z-charge);
    }
    .route.dev {
      grid-template-columns: 150px minmax(0, 1fr) 70px;
    }
    .live {
      color: var(--z-charge);
      font-size: 12px;
      font-weight: 600;
    }
    .small {
      font-size: 12px;
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
      .reg.narrow text {
        font-size: 9.5px;
      }
      .big {
        font-size: 34px;
      }
    }
  `;
}
