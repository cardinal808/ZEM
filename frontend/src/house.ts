// Screen Stroom, card "Nu" (Bjorn 27-11): the house picture with live values and flow lines on top.
// The picture is a fixed illustration (custom_components/zephyr/frontend/house.webp); the positions
// below are in its own coordinates (1284 × 1048). A user picture with own positions comes later.
import { LitElement, css, html, nothing, svg, type TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { unsafeSVG } from "lit/directives/unsafe-svg.js";

import { flows } from "./flow";
import { percent, watts } from "./format";
import { t, type Lang } from "./i18n";
import type { HouseDevice, StroomView } from "./stroom";
import type { Now } from "./types";

export const W = 1284;
export const H = 1048;

type Pt = [number, number];
type Box = [number, number, number, number];

/** Where things are in the default picture. */
export const LAYOUT = {
  header: [20, 16, 330, 76] as Box,
  roof: {
    box: [40, 138, 270, 70] as Box,
    line: [
      [245, 208],
      [245, 341],
      [772, 341],
    ] as Pt[],
  },
  shedSolar: {
    box: [680, 34, 258, 64] as Box,
    line: [
      [772, 98],
      [772, 341],
    ] as Pt[],
  },
  sunBus: [
    [772, 341],
    [772, 912],
  ] as Pt[],
  battery: {
    box: [362, 34, 310, 64] as Box,
    line: [
      [527, 98],
      [527, 152],
    ] as Pt[],
    dot: [527, 154] as Pt,
  },
  grid: {
    box: [676, 944, 242, 86] as Box,
    line: [
      [588, 912],
      [828, 912],
    ] as Pt[],
  },
  ev: {
    box: [314, 944, 168, 62] as Box,
    line: [
      [480, 975],
      [588, 975],
      [588, 900],
    ] as Pt[],
    dot: [588, 900] as Pt,
  },
  houseBus: [
    [845, 207],
    [845, 945],
  ] as Pt[],
  floors: {
    attic: { box: [938, 250, 296, 72] as Box, y: 207 },
    first: { box: [934, 510, 308, 72] as Box, y: 441 },
    ground: { box: [932, 775, 318, 72] as Box, y: 693 },
    shed: { box: [940, 975, 298, 70] as Box, y: 0 },
  },
};

export const COLORS = {
  sun: "#ffcf1f",
  batt: "#22d3b5",
  house: "#2f8cff",
  grid: "#ff6a2b",
  ev: "#a86bff",
  exp: "#ff3b3b",
};

const ICON: Record<string, string> = {
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  batt: '<rect x="7" y="4" width="10" height="17" rx="2"/><path d="M10 2h4M12 9v6M9 12h6"/>',
  house: '<path d="M3 11l9-7 9 7M5 10v10h14V10M10 20v-5h4v5"/>',
  ev: '<path d="M5 16l1.5-5a2 2 0 0 1 2-1.5h7a2 2 0 0 1 2 1.5L19 16M4 16h16v3H4zM7 19v2M17 19v2"/>',
  grid: '<path d="M8 22L12 3l4 19M6 8h12M5 12h14M9.5 15h5M12 3V1"/>',
  export: '<circle cx="12" cy="12" r="9"/><path d="M8 15l8-6M12 9h4v4"/>',
  wash: '<rect x="4" y="3" width="16" height="18" rx="2"/><circle cx="12" cy="13" r="4.5"/><path d="M7 6h3"/>',
  leaf: '<path d="M4 20C4 10 10 4 20 4c0 10-6 16-16 16zM4 20l9-9"/>',
};

/** Consumers per floor of the picture, shown ones only. */
export function byFloor(devices: HouseDevice[]): Record<string, HouseDevice[]> {
  const out: Record<string, HouseDevice[]> = {};
  for (const d of devices) if (d.shown) (out[d.floor] ??= []).push(d);
  return out;
}

@customElement("zephyr-house")
export class ZephyrHouse extends LitElement {
  @property({ attribute: false }) now?: Now;
  @property({ attribute: false }) view?: StroomView;
  @property({ attribute: false }) uiLang: Lang = "en";
  @property() locale = "en";
  @property() base = "";

  private tr(
    key: string,
    params: Record<string, string | number> = {},
  ): string {
    return t(this.uiLang, key, params);
  }

  private w(v: number | null | undefined): string {
    return watts(v ?? 0, this.locale);
  }

  protected override render(): TemplateResult {
    const now = this.now;
    if (!now) return html`<section class="card skeleton"></section>`;
    const devices = this.view?.devices ?? [];
    const airco = now.excluded?.active ? (now.excluded.power_w ?? 0) : 0;
    const f = flows(now.solar_w, now.grid_w, now.battery_w, airco);
    const ev = devices.find((d) => d.kind === "ev") ?? null;
    const floors = byFloor(devices.filter((d) => d.kind !== "ev"));
    const known = devices
      .filter((d) => d.shown && d.kind !== "ev")
      .reduce((s, d) => s + (d.power_w ?? 0), 0);
    const rest = Math.max(0, f.house - known);
    const roofW = now.solar_external_w ?? 0;
    const shedW = now.solar_sets_w ?? 0;
    const curtail = now.curtail?.active ? now.curtail : null;
    const L = LAYOUT;
    const floorW = (key: string): number =>
      (floors[key] ?? []).reduce((s, d) => s + (d.power_w ?? 0), 0) +
      (key === "first" ? rest : 0);
    return html`<section class="card" aria-label=${this.tr("house.title")}>
      <div class="stage">
        <img src=${`${this.base}/house.webp`} alt="" draggable="false" />
        <svg viewBox="0 0 ${W} ${H}" aria-hidden="true">
          ${this.line(L.roof.line, COLORS.sun, roofW)}
          ${this.line(L.shedSolar.line, COLORS.sun, shedW)}
          ${this.line(L.sunBus, COLORS.sun, f.solar)}
          ${this.line(L.battery.line, COLORS.batt, Math.abs(f.battery))}
          ${svg`<circle cx=${L.battery.dot[0]} cy=${L.battery.dot[1]} r="6" fill=${COLORS.batt}></circle>`}
          ${this.line(L.grid.line, COLORS.grid, Math.abs(f.grid))}
          ${this.line(L.ev.line, COLORS.batt, ev?.power_w ?? 0)}
          ${svg`<circle cx=${L.ev.dot[0]} cy=${L.ev.dot[1]} r="6" fill=${COLORS.batt}></circle>`}
          ${this.line(L.houseBus, COLORS.house, f.house)}
          ${[369, 563].map((y) => svg`${this.line([[845, y], [790, y]], COLORS.house, f.house)}${this.arrowLeft(784, y, COLORS.house)}`)}
          ${(["attic", "first", "ground"] as const).map((k) => {
            const y = L.floors[k].y;
            return svg`${this.line(
              [
                [845, y],
                [925, y],
              ],
              COLORS.house,
              floorW(k),
            )}${this.arrow(930, y, COLORS.house)}`;
          })}
        </svg>
        <div class="boxes">
          ${this.box(L.header, "#23435a", "leaf", html`<b class="big">${this.tr("house.title")}</b>`, [this.tr("house.sub")], true)}
          ${this.box(
            L.roof.box,
            COLORS.sun,
            "sun",
            html`<b>${this.tr("house.roof")}</b>`,
            [
              html`<b>${this.w(roofW)}</b
                >${curtail ? html` <span class="red">${this.curtailText(curtail)}</span>` : nothing}`,
            ],
          )}
          ${this.box(L.shedSolar.box, COLORS.sun, "sun", html`<b>${this.tr("house.shed_solar")}</b>`, [html`<b>${this.w(shedW)}</b>`])}
          ${this.box(
            L.battery.box,
            COLORS.batt,
            "batt",
            html`<b class="fit"
              >${this.view?.battery_label ?? this.tr("house.battery")}</b
            >`,
            [
              html`${this.tr(f.battery > 10 ? "house.charging" : f.battery < -10 ? "house.delivering" : "house.idle")}
                <b
                  >${Math.abs(f.battery) > 10 ? this.w(Math.abs(f.battery)) : ""}</b
                >
                ${now.soc !== null ? html` | SoC ${percent(now.soc, this.locale)}` : nothing}
                ${now.curtail?.export_blocked ? html` <span class="red">${this.tr("flow.export_blocked")}</span>` : nothing}`,
            ],
          )}
          ${this.box(L.ev.box, COLORS.batt, "ev", html`<b>${this.tr("house.ev")}</b>`, [html`<b>${ev ? this.w(ev.power_w) : "–"}</b>`], !!ev)}
          ${this.box(
            L.grid.box,
            COLORS.grid,
            "grid",
            html`<b>${this.tr("house.grid")}</b>`,
            [
              html`${this.tr("house.import")}
                <b>${this.w(Math.max(0, f.grid))}</b>`,
              html`${this.tr("house.export")}
                <b>${this.w(Math.max(0, -f.grid))}</b>`,
            ],
          )}
          ${(["attic", "first", "ground", "shed"] as const).map((k) => this.floorBox(k, floors[k] ?? [], k === "first" ? rest : null, now))}
        </div>
      </div>
      ${this.bar(f, ev)} ${this.list(devices, rest)}
    </section>`;
  }

  private curtailText(c: NonNullable<Now["curtail"]>): string {
    return c.percent !== null
      ? this.tr("flow.curtailed", { pct: c.percent })
      : c.switch_on
        ? this.tr("flow.inverter_off")
        : "";
  }

  private floorBox(
    key: "attic" | "first" | "ground" | "shed",
    devs: HouseDevice[],
    rest: number | null,
    now: Now,
  ): TemplateResult {
    const parts = devs.map(
      (d) =>
        html`${d.name ?? this.tr(`stroom.kind_${d.kind}`)}
          <b class=${(d.power_w ?? 0) >= 10 ? "" : "dim"}
            >${this.w(d.power_w)}</b
          >`,
    );
    if (rest !== null)
      parts.push(html`${this.tr("house.rest")} <b>${this.w(rest)}</b>`);
    if (key === "shed" && !parts.length && now.soc !== null)
      parts.push(
        html`${this.tr("house.battery")}
          <b>${percent(now.soc, this.locale)}</b>`,
      );
    return this.box(
      LAYOUT.floors[key].box,
      key === "shed" ? COLORS.batt : COLORS.house,
      key === "shed" ? "batt" : key === "attic" ? "wash" : "house",
      html`<b>${this.tr(`settings.floors.${key}`)}</b>`,
      [
        parts.length
          ? html`${parts.map((p, i) => html`${i ? html`<span class="sep"> · </span>` : nothing}${p}`)}`
          : html`<span class="dim">–</span>`,
      ],
    );
  }

  private box(
    b: Box,
    color: string,
    icon: string,
    title: TemplateResult,
    lines: (TemplateResult | string)[],
    active = true,
  ): TemplateResult {
    const [x, y, w, h] = b;
    const style = `left:${(x / W) * 100}%;top:${(y / H) * 100}%;width:${(w / W) * 100}%;height:${(h / H) * 100}%;--c:${color}`;
    return html`<div class=${active ? "box" : "box off"} style=${style}>
      <span class="ic"
        ><svg viewBox="0 0 24 24">${unsafeSVG(ICON[icon])}</svg></span
      >
      <span class="tx"
        >${title}${lines.map((l) => html`<span class="ln">${l}</span>`)}</span
      >
    </div>`;
  }

  private line(pts: Pt[], color: string, power: number) {
    const d = `M${pts.map((p) => p.join(" ")).join(" L")}`;
    const on = power >= 10;
    return svg`<path d=${d} class="glow" stroke=${color}></path>
      <path d=${d} class=${on ? "core" : "core off"} stroke=${color}></path>
      ${on ? svg`<path d=${d} class="dots" style=${`animation-duration:${Math.max(0.5, 1.6 - power / 3000)}s`}></path>` : nothing}`;
  }

  private arrowLeft(x: number, y: number, color: string) {
    return svg`<path d=${`M${x} ${y} l12 -6 l0 12 z`} fill=${color}></path>`;
  }

  private arrow(x: number, y: number, color: string) {
    return svg`<path d=${`M${x} ${y} l-12 -6 l0 12 z`} fill=${color}></path>`;
  }

  private bar(
    f: ReturnType<typeof flows>,
    ev: HouseDevice | null,
  ): TemplateResult {
    const items: [string, string, string, string, string, boolean][] = [
      [
        "sun",
        COLORS.sun,
        this.tr("house.sun"),
        this.w(f.solar),
        this.tr("house.production"),
        f.solar >= 10,
      ],
      [
        "batt",
        COLORS.batt,
        this.tr("house.battery"),
        this.w(Math.abs(f.battery)),
        this.tr(
          f.battery > 10
            ? "house.charging_l"
            : f.battery < -10
              ? "house.delivering_l"
              : "house.idle_l",
        ),
        Math.abs(f.battery) >= 10,
      ],
      [
        "house",
        COLORS.house,
        this.tr("house.consumers"),
        this.w(f.house),
        this.tr("house.house"),
        true,
      ],
      [
        "ev",
        COLORS.ev,
        this.tr("house.ev"),
        ev ? this.w(ev.power_w) : "–",
        this.tr("house.ev_sub"),
        !!ev && (ev.power_w ?? 0) >= 10,
      ],
      [
        "grid",
        COLORS.grid,
        this.tr("house.grid"),
        this.w(Math.max(0, f.grid)),
        this.tr("house.import_l"),
        f.grid >= 10,
      ],
      [
        "export",
        COLORS.exp,
        this.tr("house.export_t"),
        this.w(Math.max(0, -f.grid)),
        this.tr("house.export_l"),
        f.grid <= -10,
      ],
    ];
    return html`<div class="bar">
      ${items.map(
        ([icon, c, title, value, sub, on]) =>
          html`<div class=${on ? "" : "off"}>
            <span class="bic" style="--c:${c}"
              ><svg viewBox="0 0 24 24">${unsafeSVG(ICON[icon])}</svg></span
            >
            <span class="bt">${title}</span><b>${value}</b
            ><span class="bs">${sub}</span>
          </div>`,
      )}
    </div>`;
  }

  /** On a phone the boxes on the picture are too small: the consumers as a list below. */
  private list(devices: HouseDevice[], rest: number): TemplateResult {
    const shown = devices.filter((d) => d.shown);
    return html`<ul class="list">
      ${shown.map(
        (d) =>
          html`<li>
            <span
              >${d.name ?? this.tr(`stroom.kind_${d.kind}`)}
              <small>${this.tr(`settings.floors.${d.floor}`)}</small></span
            ><b>${this.w(d.power_w)}</b>
          </li>`,
      )}
      <li><span>${this.tr("house.rest")}</span><b>${this.w(rest)}</b></li>
    </ul>`;
  }

  static override styles = css`
    :host {
      display: block;
      grid-column: 1 / -1;
    }
    .card {
      background: #0f1d27;
      border: 1px solid #1f3342;
      border-radius: 18px;
      padding: 14px;
      color: #eef2f5;
      font-family: var(--z-font);
    }
    .skeleton {
      min-height: 400px;
    }
    .stage {
      position: relative;
      border-radius: 12px;
      overflow: hidden;
      container-type: inline-size;
    }
    img {
      display: block;
      width: 100%;
      user-select: none;
    }
    .stage > svg {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
    }
    .glow {
      fill: none;
      stroke-width: 11;
      opacity: 0.16;
    }
    .core {
      fill: none;
      stroke-width: 3;
      opacity: 0.95;
    }
    .core.off {
      opacity: 0.3;
    }
    .dots {
      fill: none;
      stroke: #fff;
      stroke-width: 3;
      stroke-linecap: round;
      stroke-dasharray: 3 14;
      opacity: 0.85;
      animation: run 1s linear infinite;
    }
    @keyframes run {
      to {
        stroke-dashoffset: -17;
      }
    }
    .boxes {
      position: absolute;
      inset: 0;
      font-size: 1.15cqw;
    }
    .box {
      position: absolute;
      box-sizing: border-box;
      display: flex;
      align-items: center;
      gap: 0.8cqw;
      padding: 0 1cqw;
      background: rgba(12, 26, 36, 0.93);
      border: 2px solid var(--c);
      border-radius: 1.1cqw;
      color: #dbe8f2;
      overflow: hidden;
    }
    .box.off {
      opacity: 0.6;
    }
    .ic {
      flex: none;
      width: 2.6cqw;
      height: 2.6cqw;
      color: var(--c);
    }
    .ic svg,
    .bic svg {
      width: 100%;
      height: 100%;
      fill: none;
      stroke: currentColor;
      stroke-width: 1.8;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .tx {
      display: flex;
      flex-direction: column;
      min-width: 0;
      line-height: 1.3;
    }
    .tx > b {
      color: #fff;
      font-weight: 600;
      font-size: 1.1cqw;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .tx > b.fit {
      font-size: 0.95cqw;
    }
    .tx .big {
      font-size: 1.9cqw;
      font-weight: 700;
    }
    .ln {
      font-size: 1.05cqw;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .ln b {
      color: #fff;
    }
    .ln b.dim,
    .dim {
      color: #8aa0b0;
      font-weight: 400;
    }
    .red {
      color: #ff8a8a;
      font-weight: 600;
    }
    .bar {
      display: flex;
      margin-top: 12px;
      background: #0f1f2a;
      border: 1px solid #23435a;
      border-radius: 16px;
      padding: 14px 6px;
    }
    .bar > div {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      border-right: 1px solid #23435a;
      padding: 0 6px;
      min-width: 0;
    }
    .bar > div:last-child {
      border: 0;
    }
    .bar > div.off {
      opacity: 0.55;
    }
    .bic {
      width: 44px;
      height: 44px;
      box-sizing: border-box;
      padding: 9px;
      border-radius: 50%;
      border: 2px solid var(--c);
      color: var(--c);
      box-shadow: 0 0 14px color-mix(in srgb, var(--c) 35%, transparent);
      margin-bottom: 6px;
    }
    .bt {
      font-weight: 600;
    }
    .bar b {
      font-size: 18px;
    }
    .bs {
      color: #9fb3c2;
      font-size: 12px;
    }
    .list {
      display: none;
      list-style: none;
      margin: 10px 0 0;
      padding: 0;
    }
    .list li {
      display: flex;
      justify-content: space-between;
      padding: 7px 2px;
      border-bottom: 1px solid #23435a;
    }
    .list small {
      color: #9fb3c2;
    }
    @media (max-width: 700px) {
      .boxes {
        display: none;
      }
      .bar {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        row-gap: 14px;
      }
      .bar > div {
        border: 0;
        min-width: 0;
      }
      .list {
        display: block;
      }
    }
  `;
}
