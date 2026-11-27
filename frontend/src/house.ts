// Screen Stroom, card "Nu" (Bjorn 27-11): the house picture with live values and flow lines on top.
// The picture is a fixed illustration (custom_components/zephyr/frontend/house.webp); the positions
// below are in its own coordinates (1284 × 1048). A user picture with own positions comes later.
import { LitElement, css, html, nothing, svg, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { unsafeSVG } from "lit/directives/unsafe-svg.js";

import { flows } from "./flow";
import { percent, watts } from "./format";
import { t, type Lang } from "./i18n";
import type { HouseDevice, HousePicture, StroomView } from "./stroom";
import type { Now } from "./types";

export const W = 1614;
export const H = 1225;

type Pt = [number, number];
type Box = [number, number, number, number];

/**
 * Where things are in the default picture (Bjorn's clean render, widened on the right with
 * background so the floor boxes sit next to their floor). Every line runs from its box to the
 * spot it belongs to; a dot marks that spot.
 */
export const LAYOUT = {
  header: [20, 16, 420, 70] as Box,
  battery: {
    box: [20, 126, 420, 84] as Box,
    line: [
      [440, 166],
      [530, 166],
      [530, 172],
    ] as Pt[],
    dot: [530, 174] as Pt,
  },
  shedSolar: {
    box: [860, 16, 300, 70] as Box,
    line: [
      [860, 51],
      [735, 51],
      [735, 158],
    ] as Pt[],
    dot: [735, 160] as Pt,
  },
  roof: {
    box: [20, 340, 262, 80] as Box,
    line: [
      [282, 380],
      [318, 380],
    ] as Pt[],
    dot: [320, 380] as Pt,
  },
  grid: {
    box: [20, 1100, 270, 90] as Box,
    line: [
      [290, 1145],
      [370, 1145],
      [370, 1002],
    ] as Pt[],
    dot: [370, 1000] as Pt,
  },
  ev: {
    box: [705, 1110, 230, 70] as Box,
    line: [
      [705, 1145],
      [685, 1145],
      [685, 972],
    ] as Pt[],
    dot: [685, 970] as Pt,
  },
  floors: {
    attic: { box: [1262, 215, 330, 80] as Box, line: [[1262, 255], [1226, 255]] as Pt[] },
    first: { box: [1262, 442, 330, 80] as Box, line: [[1262, 482], [1238, 482]] as Pt[] },
    ground: { box: [1262, 692, 330, 80] as Box, line: [[1262, 732], [1246, 732]] as Pt[] },
    shed: { box: [1262, 945, 330, 80] as Box, line: [[1262, 985], [1214, 985]] as Pt[] },
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

export type ItemKey =
  | "roof"
  | "shed_solar"
  | "battery"
  | "grid"
  | "ev"
  | "attic"
  | "first"
  | "ground"
  | "shed";
type FloorKey = "attic" | "first" | "ground" | "shed";
export const ITEM_KEYS: ItemKey[] = ["roof", "shed_solar", "battery", "grid", "ev", "attic", "first", "ground", "shed"];
const FLOOR_KEYS: FloorKey[] = ["attic", "first", "ground", "shed"];
/** Width of a box on an own picture, as a part of the picture's width. */
export const OWN_BOX_W = 0.24;

interface Item {
  color: string;
  icon: string;
  title: TemplateResult;
  lines: (TemplateResult | string)[];
  active?: boolean;
  power: number;
}

/**
 * The line of an item on an own picture, in picture pixels: from the middle of the box's left or
 * right edge (the side towards the spot), level to the spot's x, then straight to the spot.
 */
export function ownLine(box: [number, number], point: [number, number], w: number, h: number): Pt[] {
  const left = Math.min(box[0], 1 - OWN_BOX_W) * w;
  const right = left + OWN_BOX_W * w;
  const y = box[1] * h + 0.035 * w;
  const px = point[0] * w;
  const py = point[1] * h;
  const x = px < left ? left : px > right ? right : px;
  if (x === px) return [[px, y], [px, py]];
  return [[x, y], [px, y], [px, py]];
}

@customElement("zephyr-house")
export class ZephyrHouse extends LitElement {
  @property({ attribute: false }) now?: Now;
  @property({ attribute: false }) view?: StroomView;
  @property({ attribute: false }) uiLang: Lang = "en";
  @property() locale = "en";
  @property() base = "";
  /** Signs a path of the HA API for an <img> (auth/sign_path); for an own picture. */
  @property({ attribute: false }) sign?: (path: string) => Promise<string>;

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
    const items = this.items(now, devices);
    const own = this.view?.picture ?? null;
    return html`<section class="card" aria-label=${this.tr("house.title")}>
      ${own ? this.ownStage(own, items) : this.defaultStage(items)}
      ${this.bar(f, ev)} ${this.list(devices, Math.max(0, f.house - this.known(devices)))}
    </section>`;
  }

  private known(devices: HouseDevice[]): number {
    return devices
      .filter((d) => d.shown && d.kind !== "ev")
      .reduce((s, d) => s + (d.power_w ?? 0), 0);
  }

  /** What each item of the picture shows, and how much power its line carries. */
  private items(now: Now, devices: HouseDevice[]): Record<ItemKey, Item> {
    const airco = now.excluded?.active ? (now.excluded.power_w ?? 0) : 0;
    const f = flows(now.solar_w, now.grid_w, now.battery_w, airco);
    const ev = devices.find((d) => d.kind === "ev") ?? null;
    const floors = byFloor(devices.filter((d) => d.kind !== "ev"));
    const rest = Math.max(0, f.house - this.known(devices));
    const roofW = now.solar_external_w ?? 0;
    const shedW = now.solar_sets_w ?? 0;
    const curtail = now.curtail?.active ? now.curtail : null;
    const floorW = (key: string): number =>
      (floors[key] ?? []).reduce((s, d) => s + (d.power_w ?? 0), 0) +
      (key === "first" ? rest : 0);
    const floor = (k: FloorKey): Item => ({
      ...this.floorItem(k, floors[k] ?? [], k === "first" ? rest : null, now),
      power: k === "shed" ? 0 : floorW(k),
    });
    return {
      roof: {
        color: COLORS.sun,
        icon: "sun",
        title: html`<b>${this.tr("house.roof")}</b>`,
        lines: [
          html`<b>${this.w(roofW)}</b
            >${curtail ? html` <span class="red">${this.curtailText(curtail)}</span>` : nothing}`,
        ],
        power: roofW,
      },
      shed_solar: {
        color: COLORS.sun,
        icon: "sun",
        title: html`<b>${this.tr("house.shed_solar")}</b>`,
        lines: [html`<b>${this.w(shedW)}</b>`],
        power: shedW,
      },
      battery: {
        color: COLORS.batt,
        icon: "batt",
        title: html`<b class="fit"
          >${this.view?.battery_label ?? this.tr("house.battery")}</b
        >`,
        lines: [
          html`${this.tr(f.battery > 10 ? "house.charging" : f.battery < -10 ? "house.delivering" : "house.idle")}
            <b>${Math.abs(f.battery) > 10 ? this.w(Math.abs(f.battery)) : ""}</b>
            ${now.soc !== null ? html` | SoC ${percent(now.soc, this.locale)}` : nothing}
            ${now.curtail?.export_blocked ? html` <span class="red">${this.tr("flow.export_blocked")}</span>` : nothing}`,
        ],
        power: Math.abs(f.battery),
      },
      grid: {
        color: COLORS.grid,
        icon: "grid",
        title: html`<b>${this.tr("house.grid")}</b>`,
        lines: [
          html`${this.tr("house.import")} <b>${this.w(Math.max(0, f.grid))}</b>`,
          html`${this.tr("house.export")} <b>${this.w(Math.max(0, -f.grid))}</b>`,
        ],
        power: Math.abs(f.grid),
      },
      ev: {
        color: COLORS.batt,
        icon: "ev",
        title: html`<b>${this.tr("house.ev")}</b>`,
        lines: [html`<b>${ev ? this.w(ev.power_w) : "–"}</b>`],
        active: !!ev,
        power: ev?.power_w ?? 0,
      },
      attic: floor("attic"),
      first: floor("first"),
      ground: floor("ground"),
      shed: floor("shed"),
    };
  }

  /** The default house: fixed places for every box and line. */
  private defaultStage(it: Record<ItemKey, Item>): TemplateResult {
    const L = LAYOUT;
    const placed: [ItemKey, { box: Box; line: Pt[]; dot?: Pt }][] = [
      ["roof", L.roof],
      ["shed_solar", L.shedSolar],
      ["battery", L.battery],
      ["grid", L.grid],
      ["ev", L.ev],
    ];
    return html`<div class="stage">
      <img src=${`${this.base}/house.webp`} alt="" draggable="false" />
      <svg viewBox="0 0 ${W} ${H}" aria-hidden="true">
        ${placed.map(([k, p]) =>
          k === "ev" && !it.ev.active
            ? nothing
            : svg`${this.line(p.line, it[k].color, it[k].power)}${p.dot ? this.dot(p.dot, it[k].color) : nothing}`,
        )}
        ${(["attic", "first", "ground"] as const).map((k) => {
          const ln = L.floors[k].line;
          const end = ln[ln.length - 1];
          return it[k].power >= 10
            ? svg`${this.line(ln, COLORS.house, it[k].power)}${this.arrowLeft(end[0], end[1], COLORS.house)}`
            : nothing;
        })}
      </svg>
      <div class="boxes">
        ${this.box(L.header, this.header())}
        ${placed.map(([k, p]) => this.box(p.box, it[k]))}
        ${FLOOR_KEYS.map((k) => this.box(L.floors[k].box, it[k]))}
      </div>
    </div>`;
  }

  /** An own picture: each placed item gets its box and a line with one bend to its spot. */
  private ownStage(own: HousePicture, it: Record<ItemKey, Item>): TemplateResult {
    const w = own.width || 1600;
    const h = own.height || 1200;
    const shown = ITEM_KEYS.filter(
      (k) => !own.hidden.includes(k) && own.items[k]?.box,
    );
    return html`<div class="stage own" style=${`aspect-ratio:${w}/${h}`}>
      ${this.ownUrl ? html`<img src=${this.ownUrl} alt="" draggable="false" />` : nothing}
      <svg viewBox="0 0 ${w} ${h}" aria-hidden="true">
        ${shown.map((k) => {
          const place = own.items[k];
          if (!place?.point || !place.box) return nothing;
          const pts = ownLine(place.box, place.point, w, h);
          const end = pts[pts.length - 1];
          return svg`${this.line(pts, it[k].color, it[k].power)}${this.dot(end, it[k].color)}`;
        })}
      </svg>
      <div class="boxes">
        ${shown.map((k) => {
          const [x, y] = own.items[k]?.box ?? [0, 0];
          return this.placed(x, y, it[k]);
        })}
      </div>
    </div>`;
  }

  @state() private ownUrl: string | null = null;
  private ownSigned = -1;

  protected override willUpdate(): void {
    const own = this.view?.picture;
    if (!own || !this.sign || own.version === this.ownSigned) return;
    this.ownSigned = own.version;
    void this.sign(`/api/zephyr/house_picture?v=${own.version}`).then(
      (url) => (this.ownUrl = url),
      () => (this.ownSigned = -1),
    );
  }

  private header(): Item {
    return {
      color: "#23435a",
      icon: "leaf",
      title: html`<b class="big">${this.tr("house.title")}</b>`,
      lines: [this.tr("house.sub")],
      power: 0,
    };
  }

  private curtailText(c: NonNullable<Now["curtail"]>): string {
    return c.percent !== null
      ? this.tr("flow.curtailed", { pct: c.percent })
      : c.switch_on
        ? this.tr("flow.inverter_off")
        : "";
  }

  private floorItem(
    key: FloorKey,
    devs: HouseDevice[],
    rest: number | null,
    now: Now,
  ): Omit<Item, "power"> {
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
    return {
      color: key === "shed" ? COLORS.batt : COLORS.house,
      icon: key === "shed" ? "batt" : key === "attic" ? "wash" : "house",
      title: html`<b>${this.tr(`settings.floors.${key}`)}</b>`,
      lines: [
        parts.length
          ? html`${parts.map((p, i) => html`${i ? html`<span class="sep"> · </span>` : nothing}${p}`)}`
          : html`<span class="dim">–</span>`,
      ],
    };
  }

  /** A box on an own picture: its top left corner at (x, y), fractions of the picture. */
  private placed(x: number, y: number, it: Item): TemplateResult {
    const style = `left:${Math.min(x, 1 - OWN_BOX_W) * 100}%;top:${y * 100}%;width:${OWN_BOX_W * 100}%;--c:${it.color}`;
    return this.boxHtml(style, it);
  }

  private box(b: Box, it: Item): TemplateResult {
    const [x, y, w, h] = b;
    const style = `left:${(x / W) * 100}%;top:${(y / H) * 100}%;width:${(w / W) * 100}%;min-height:${(h / H) * 100}%;--c:${it.color}`;
    return this.boxHtml(style, it);
  }

  private boxHtml(style: string, it: Item): TemplateResult {
    return html`<div class=${it.active === false ? "box off" : "box"} style=${style}>
      <span class="ic"
        ><svg viewBox="0 0 24 24">${unsafeSVG(ICON[it.icon])}</svg></span
      >
      <span class="tx"
        >${it.title}${it.lines.map((l) => html`<span class="ln">${l}</span>`)}</span
      >
    </div>`;
  }

  private line(pts: Pt[], color: string, power: number) {
    const d = `M${pts.map((p) => p.join(" ")).join(" L")}`;
    // No power, no line: a faint line over the picture only looks blurred (Bjorn 27-11).
    if (power < 10) return nothing;
    return svg`<path d=${d} class="glow" stroke=${color}></path>
      <path d=${d} class="core" stroke=${color}></path>
      <path d=${d} class="dots" style=${`animation-duration:${Math.max(0.5, 1.6 - power / 3000)}s`}></path>`;
  }

  private dot(p: Pt, color: string) {
    return svg`<circle cx=${p[0]} cy=${p[1]} r="6" fill=${color}></circle>`;
  }

  private arrowLeft(x: number, y: number, color: string) {
    return svg`<path d=${`M${x} ${y} l12 -6 l0 12 z`} fill=${color}></path>`;
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
      /* Picture plus totals bar fit in one screen: 1614/1225 is the picture's aspect ratio. */
      --house-max: calc((100vh - 300px) * var(--house-ar, 1.3176) + 30px);
    }
    .card {
      container: house / inline-size;
      max-width: var(--house-max);
      margin: 0 auto;
      background: #0f1d27;
      border: 1px solid #1f3342;
      border-radius: 18px;
      padding: 14px;
      color: #eef2f5;
      font-family: var(--z-font);
      /* Next to the today cards: as high as they are, the bar at the bottom. */
      box-sizing: border-box;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 14px;
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
      font-size: max(11px, 1.15cqw);
    }
    .box {
      position: absolute;
      box-sizing: border-box;
      display: flex;
      align-items: center;
      gap: 0.8cqw;
      padding: 0.4cqw 1cqw;
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
      width: max(18px, 2.6cqw);
      height: max(18px, 2.6cqw);
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
      font-size: max(11.5px, 1.1cqw);
      overflow: hidden;
    }
    .ln b {
      white-space: nowrap;
    }
    .tx > b.fit {
      font-size: max(11px, 0.95cqw);
      white-space: normal;
    }
    .tx .big {
      font-size: max(16px, 1.9cqw);
      font-weight: 700;
    }
    .ln {
      font-size: max(11px, 1.05cqw);
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
    @container house (max-width: 680px) {
      .stage > svg,
      .boxes {
        display: none;
      }
      .list {
        display: block;
      }
    }
    @container house (max-width: 640px) {
      .bar {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        row-gap: 14px;
      }
      .bar > div {
        border: 0;
        min-width: 0;
      }
    }
  `;
}
