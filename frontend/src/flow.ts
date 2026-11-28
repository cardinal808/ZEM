// Screen "Stroom" (SPEC-ui §1, M6 part 2): power flow between solar, grid, house and battery, now.
import { element } from "./define";
import { LitElement, css, html, nothing, svg, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";

import { percent, watts } from "./format";
import { t, type Lang } from "./i18n";
import type { Now } from "./types";

export interface Flows {
  solar: number;
  /** + = import, − = export. */
  grid: number;
  /** + = charging, − = delivering. */
  battery: number;
  house: number;
  /** Air conditioner outside the battery (part of the house), 0 without. */
  airco: number;
  /** W per path (≥ 0), the direction is in the key. */
  paths: Record<
    | "solar_house"
    | "solar_battery"
    | "solar_grid"
    | "grid_house"
    | "grid_battery"
    | "battery_house"
    | "battery_grid",
    number
  >;
}

/**
 * Who feeds whom, from the three measured powers (house = grid + solar − battery).
 * Solar goes first to the house, then to the battery, then to the grid; the battery
 * delivers to the house first, the rest to the grid; the grid fills what is left.
 */
export function flows(
  solarW: number | null,
  gridW: number | null,
  batteryW: number | null,
  aircoW = 0,
): Flows {
  const solar = Math.max(0, solarW ?? 0);
  const grid = gridW ?? 0;
  const battery = batteryW ?? 0;
  const house = Math.max(0, grid + solar - battery);
  const charge = Math.max(0, battery);
  const deliver = Math.max(0, -battery);
  const solarHouse = Math.min(solar, house);
  const solarBattery = Math.min(solar - solarHouse, charge);
  const solarGrid = Math.max(0, solar - solarHouse - solarBattery);
  const batteryHouse = Math.min(deliver, house - solarHouse);
  const batteryGrid = Math.max(0, deliver - batteryHouse);
  const gridHouse = Math.max(0, house - solarHouse - batteryHouse);
  const gridBattery = Math.max(0, charge - solarBattery);
  return {
    solar,
    grid,
    battery,
    house,
    airco: Math.min(Math.max(0, aircoW), house),
    paths: {
      solar_house: solarHouse,
      solar_battery: solarBattery,
      solar_grid: solarGrid,
      grid_house: gridHouse,
      grid_battery: gridBattery,
      battery_house: batteryHouse,
      battery_grid: batteryGrid,
    },
  };
}

type Node = "solar" | "grid" | "house" | "battery";
const POS: Record<Node, [number, number]> = {
  solar: [320, 92],
  grid: [104, 250],
  house: [536, 250],
  battery: [320, 408],
};
const HUB: [number, number] = [320, 250];
const R = 50;

/** A curve from one node to another that bends through the hub, so all flows meet in the middle. */
function curve(from: Node, to: Node): string {
  const [x1, y1] = POS[from];
  const [x2, y2] = POS[to];
  const edge = (
    x: number,
    y: number,
    tx: number,
    ty: number,
  ): [number, number] => {
    const d = Math.hypot(tx - x, ty - y) || 1;
    return [x + ((tx - x) / d) * (R + 6), y + ((ty - y) / d) * (R + 6)];
  };
  const [sx, sy] = edge(x1, y1, HUB[0], HUB[1]);
  const [ex, ey] = edge(x2, y2, HUB[0], HUB[1]);
  return `M${sx.toFixed(1)},${sy.toFixed(1)} Q${HUB[0]},${HUB[1]} ${ex.toFixed(1)},${ey.toFixed(1)}`;
}

const ICONS: Record<Node, string> = {
  solar:
    "M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0-5v2.5m0 15V22M2 12h2.5m15 0H22M4.9 4.9l1.8 1.8m10.6 10.6 1.8 1.8M4.9 19.1l1.8-1.8m10.6-10.6 1.8-1.8",
  grid: "M9 2 6 22m9-20 3 20M5.5 8h13M4.5 14h15M12 2v20",
  house: "M3.5 11.5 12 4.5l8.5 7M6 10v9.5h12V10M10 19.5v-5h4v5",
  battery:
    "M8 5.5h8a1.5 1.5 0 0 1 1.5 1.5v12.5A1.5 1.5 0 0 1 16 21H8a1.5 1.5 0 0 1-1.5-1.5V7A1.5 1.5 0 0 1 8 5.5zM10 3h4",
};

@element("zephyr-flow")
export class ZephyrFlow extends LitElement {
  @property({ attribute: false }) now?: Now;
  @property({ attribute: false }) uiLang: Lang = "en";
  @property() locale = "en";
  /** Narrow screen: the drawing shrinks, so its text is set larger and the sun's label goes beside it. */
  @state() private narrow = false;
  private media?: MediaQueryList;
  private onMedia = () => (this.narrow = Boolean(this.media?.matches));

  override connectedCallback(): void {
    super.connectedCallback();
    this.media = window.matchMedia("(max-width: 600px)");
    this.media.addEventListener("change", this.onMedia);
    this.onMedia();
  }

  override disconnectedCallback(): void {
    this.media?.removeEventListener("change", this.onMedia);
    super.disconnectedCallback();
  }

  private tr(
    key: string,
    params: Record<string, string | number> = {},
  ): string {
    return t(this.uiLang, key, params);
  }

  protected override render(): TemplateResult {
    const now = this.now;
    if (!now) return html`<div class="skeleton"></div>`;
    const airco = now.excluded?.active ? (now.excluded.power_w ?? 0) : 0;
    const f = flows(now.solar_w, now.grid_w, now.battery_w, airco);
    const p = f.paths;
    const max = Math.max(500, ...Object.values(p));
    const route = (
      key: keyof Flows["paths"],
      from: Node,
      to: Node,
      cls: string,
    ) => {
      const w = p[key];
      const d = curve(from, to);
      if (w < 10) return svg`<path d=${d} class="track"></path>`;
      const share = Math.min(1, w / max);
      const dots = 2 + Math.round(share * 3);
      const dur = (3.2 - share * 1.8).toFixed(2);
      return svg`<path d=${d} class="track lit ${cls}" style=${`stroke-width:${2 + share * 3}`}></path>
        ${Array.from(
          { length: dots },
          (_, i) => svg`<circle r=${3 + share * 2.5} class=${`dot ${cls}`}>
          <animateMotion dur=${`${dur}s`} repeatCount="indefinite" begin=${`-${((i * Number(dur)) / dots).toFixed(2)}s`} path=${d}></animateMotion>
        </circle>`,
        )}`;
    };
    const soc = now.soc;
    const circ = 2 * Math.PI * (R - 4);
    return html`<section class="card" aria-labelledby="fl-title">
      <div class="head">
        <h2 id="fl-title">${this.tr("flow.title")}</h2>
        ${now.live ? nothing : html`<span class="chip">${this.tr("flow.shadow_chip")}</span>`}
      </div>
      <svg
        viewBox=${this.narrow ? "0 0 640 620" : "0 0 640 540"}
        class=${this.narrow ? "stage narrow" : "stage"}
        role="img"
        aria-label=${this.summary(f)}
      >
        <defs>
          <radialGradient id="glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" class="glow0"></stop>
            <stop offset="100%" class="glow1"></stop>
          </radialGradient>
        </defs>
        <circle cx=${HUB[0]} cy=${HUB[1]} r="150" fill="url(#glow)"></circle>
        ${route("solar_house", "solar", "house", "sun")}
        ${route("solar_battery", "solar", "battery", "sun")}
        ${route("solar_grid", "solar", "grid", "sun")}
        ${route("grid_house", "grid", "house", "grid")}
        ${route("grid_battery", "grid", "battery", "grid")}
        ${route("battery_house", "battery", "house", "bat")}
        ${route("battery_grid", "battery", "grid", "bat")}
        <circle cx=${HUB[0]} cy=${HUB[1]} r="5" class="hub"></circle>
        ${this.node(
          "solar",
          this.tr("flow.solar"),
          watts(f.solar, this.locale),
          now.curtail?.active && now.curtail.percent !== null
            ? this.tr("flow.curtailed", { pct: now.curtail.percent })
            : now.curtail?.active && now.curtail.switch_on
              ? this.tr("flow.inverter_off")
              : f.solar < 10
                ? this.tr("flow.none")
                : now.solar_estimated
                  ? this.tr("flow.estimated")
                  : "",
          f.solar >= 10,
        )}
        ${this.node(
          "grid",
          this.tr(
            Math.abs(f.grid) < 30
              ? "flow.grid"
              : f.grid > 0
                ? "flow.grid_in"
                : "flow.grid_out",
          ),
          watts(Math.abs(f.grid), this.locale),
          Math.abs(f.grid) < 30 ? this.tr("flow.balanced") : "",
          Math.abs(f.grid) >= 30,
        )}
        ${this.node("house", this.tr("flow.house"), watts(f.house, this.locale), f.airco >= 10 ? this.tr("flow.airco", { w: watts(f.airco, this.locale) }) : "", true)}
        ${this.node(
          "battery",
          this.tr(
            f.battery > 10
              ? "flow.charging"
              : f.battery < -10
                ? "flow.delivering"
                : "flow.battery",
          ),
          watts(Math.abs(f.battery), this.locale),
          now.curtail?.export_blocked
            ? `${soc !== null ? `${percent(soc, this.locale)} · ` : ""}${this.tr("flow.export_blocked")}`
            : soc !== null
              ? percent(soc, this.locale)
              : "",
          Math.abs(f.battery) > 10,
        )}
        ${
          soc !== null
            ? svg`<circle cx=${POS.battery[0]} cy=${POS.battery[1]} r=${R - 4} class="socring"
              stroke-dasharray=${`${(circ * Math.max(0, Math.min(100, soc))) / 100} ${circ}`}
              transform=${`rotate(-90 ${POS.battery[0]} ${POS.battery[1]})`}></circle>`
            : nothing
        }
      </svg>
      <p class="sum">${this.summary(f)}</p>
    </section>`;
  }

  private summary(f: Flows): string {
    const parts: string[] = [];
    const p = f.paths;
    const w = (v: number) => watts(v, this.locale);
    if (p.solar_house >= 10)
      parts.push(this.tr("flow.s_solar_house", { w: w(p.solar_house) }));
    if (p.battery_house >= 10)
      parts.push(this.tr("flow.s_battery_house", { w: w(p.battery_house) }));
    if (p.grid_house >= 10)
      parts.push(this.tr("flow.s_grid_house", { w: w(p.grid_house) }));
    if (p.solar_battery >= 10)
      parts.push(this.tr("flow.s_solar_battery", { w: w(p.solar_battery) }));
    if (p.grid_battery >= 10)
      parts.push(this.tr("flow.s_grid_battery", { w: w(p.grid_battery) }));
    if (p.solar_grid + p.battery_grid >= 10)
      parts.push(
        this.tr("flow.s_export", { w: w(p.solar_grid + p.battery_grid) }),
      );
    if (!parts.length) return this.tr("flow.s_idle");
    const text = parts.join("; ");
    return `${text.charAt(0).toUpperCase()}${text.slice(1)}.`;
  }

  private node(
    n: Node,
    label: string,
    value: string,
    sub: string,
    active: boolean,
  ): TemplateResult {
    const [x, y] = POS[n];
    const k = this.narrow ? 1.7 : 1;
    // Sun: label above (wide) or beside it (narrow); the others below their circle.
    const beside = n === "solar" && this.narrow;
    const tx = beside ? x + R + 16 : x;
    const ty = beside ? y - 30 : n === "solar" ? y - R - 44 : y + R + 26 * k;
    const anchor = beside ? "start" : "middle";
    return svg`<g class=${`node ${n}${active ? " active" : ""}`} text-anchor=${anchor}>
      <circle cx=${x} cy=${y} r=${R + 8} class="halo"></circle>
      <circle cx=${x} cy=${y} r=${R} class="disc"></circle>
      <circle cx=${x} cy=${y} r=${R - 4} class="ring"></circle>
      <g transform=${`translate(${x - 22} ${y - 22}) scale(1.833)`}><path d=${ICONS[n]} class="icon"></path></g>
      <text x=${tx} y=${ty} class="label" text-anchor=${anchor}>${label.toUpperCase()}</text>
      <text x=${tx} y=${ty + 26 * k} class="value" text-anchor=${anchor}>${value}</text>
      ${sub ? svg`<text x=${tx} y=${ty + 44 * k} class="sub" text-anchor=${anchor}>${sub}</text>` : nothing}
    </g>`;
  }

  static override styles = css`
    :host {
      display: block;
      color: var(--z-text);
      font-family: var(--z-font);
    }
    .card {
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 20px;
      padding: 20px 24px 22px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      max-width: 760px;
      margin: 0 auto;
    }
    .head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 20px;
    }
    .chip {
      padding: 3px 10px;
      border-radius: 999px;
      background: var(--z-info-bg);
      font-size: 12px;
      color: var(--z-muted);
    }
    .stage {
      width: 100%;
      height: auto;
      overflow: visible;
    }
    .glow0 {
      stop-color: var(--z-charge);
      stop-opacity: 0.08;
    }
    .glow1 {
      stop-color: var(--z-charge);
      stop-opacity: 0;
    }
    .track {
      fill: none;
      stroke: var(--z-border);
      stroke-width: 2;
      stroke-linecap: round;
    }
    .track.lit {
      opacity: 0.55;
    }
    .track.sun,
    .dot.sun {
      stroke: var(--z-solar);
      fill: var(--z-solar);
    }
    .track.grid,
    .dot.grid {
      stroke: var(--z-hold-b, var(--z-muted));
      fill: var(--z-hold-b, var(--z-muted));
    }
    .track.bat,
    .dot.bat {
      stroke: var(--z-deliver);
      fill: var(--z-deliver);
    }
    .track.lit {
      fill: none;
    }
    .dot {
      stroke: none !important;
      filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.15));
    }
    .hub {
      fill: var(--z-border);
    }
    .halo {
      fill: none;
      stroke: transparent;
      stroke-width: 10;
    }
    .disc {
      fill: var(--z-card);
      stroke: var(--z-border);
      stroke-width: 1.5;
    }
    .ring {
      fill: none;
      stroke: var(--z-track);
      stroke-width: 5;
    }
    .solar.active .ring {
      stroke: var(--z-solar);
    }
    .grid.active .ring {
      stroke: var(--z-hold-b, var(--z-muted));
    }
    .house .ring {
      stroke: var(--z-charge);
    }
    .battery.active .ring {
      stroke: var(--z-track);
    }
    .solar.active .halo {
      stroke: var(--z-solar);
      opacity: 0.18;
    }
    .battery.active .halo {
      stroke: var(--z-deliver);
      opacity: 0.18;
    }
    .socring {
      fill: none;
      stroke: var(--z-export);
      stroke-width: 5;
      stroke-linecap: round;
    }
    .icon {
      fill: none;
      stroke: var(--z-text);
      stroke-width: 1.4;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    text {
      fill: var(--z-text);
    }
    .label {
      font-size: 12px;
      letter-spacing: 0.08em;
      fill: var(--z-muted);
      font-weight: 600;
    }
    .value {
      font-family: var(--z-font-head);
      font-size: 24px;
      font-weight: 700;
    }
    .sub {
      font-size: 13px;
      fill: var(--z-muted);
    }
    .sum {
      margin: 0;
      font-size: 14px;
      line-height: 1.5;
      color: var(--z-muted);
      text-align: center;
    }
    .skeleton {
      height: 420px;
      border-radius: 16px;
      background: var(--z-track);
    }
    @media (prefers-reduced-motion: reduce) {
      .dot {
        display: none;
      }
      .track.lit {
        opacity: 1;
      }
    }
    @media (max-width: 600px) {
      .card {
        padding: 14px;
      }
      /* The drawing shrinks with the screen; the text in it should not. */
      .label {
        font-size: 20px;
      }
      .value {
        font-size: 36px;
      }
      .sub {
        font-size: 20px;
      }
      .head {
        flex-wrap: wrap;
      }
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "zephyr-flow": ZephyrFlow;
  }
}
