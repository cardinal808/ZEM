// Screen Stroom, card "Nu" (Bjorn 27-11): the house picture with live values and flow lines on top.
// The picture is a fixed illustration (custom_components/zephyr/frontend/house.webp); the positions
// below are in its own coordinates (1284 × 1048). A user picture with own positions comes later.
import { element } from "./define";
import { LitElement, css, html, nothing, svg, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { unsafeSVG } from "lit/directives/unsafe-svg.js";

import { flows } from "./flow";
import { percent, watts } from "./format";
import { t, type Lang } from "./i18n";
import type { HouseDevice, HousePicture, StroomView } from "./stroom";
import type { Now } from "./types";

export const W = 1700;
export const H = 1225;

type Pt = [number, number];
type Box = [number, number, number, number];

/** x of the main line between the house and the floors in the default picture. */
const BUS = 920;

/**
 * Where things are in the default picture (Bjorn's render; the floors moved right so a main line
 * fits between the house and the floors). Every source runs to the main line; from there branches
 * go to the floors with measured consumers, into the house (the rest) and to the charge point.
 * Lines run from the source towards the main line; a flow the other way is drawn reversed.
 */
export const LAYOUT = {
  header: [20, 16, 420, 96] as Box,
  bus: [
    [BUS, 96],
    [BUS, 1145],
  ] as Pt[],
  battery: {
    box: [20, 140, 420, 84] as Box,
    line: [
      [530, 165],
      [530, 96],
      [BUS, 96],
    ] as Pt[],
    dot: [530, 165] as Pt,
    label: [545, 140] as Pt,
  },
  shedSolar: {
    box: [960, 16, 300, 70] as Box,
    line: [
      [735, 150],
      [735, 112],
      [BUS, 112],
    ] as Pt[],
    dot: [735, 150] as Pt,
  },
  roof: {
    box: [20, 340, 262, 80] as Box,
    line: [
      [600, 420],
      [BUS, 420],
    ] as Pt[],
    dot: [600, 420] as Pt,
    label: [700, 405] as Pt,
  },
  grid: {
    box: [20, 1075, 300, 100] as Box,
    line: [
      [320, 1145],
      [BUS, 1145],
    ] as Pt[],
    label: [430, 1130] as Pt,
  },
  ev: {
    box: [690, 990, 220, 76] as Box,
    line: [
      [BUS, 972],
      [685, 972],
    ] as Pt[],
    dot: [685, 972] as Pt,
  },
  home: {
    box: [940, 1060, 330, 110] as Box,
    line: [
      [BUS, 700],
      [705, 700],
    ] as Pt[],
    dot: [705, 700] as Pt,
    label: [730, 688] as Pt,
  },
  floors: {
    attic: {
      box: [1378, 265, 316, 80] as Box,
      line: [
        [BUS, 305],
        [1037, 305],
      ] as Pt[],
    },
    first: {
      box: [1378, 460, 316, 80] as Box,
      line: [
        [BUS, 500],
        [1024, 500],
      ] as Pt[],
    },
    ground: {
      box: [1378, 675, 316, 80] as Box,
      line: [
        [BUS, 715],
        [1009, 715],
      ] as Pt[],
    },
    shed: { box: [1378, 892, 316, 80] as Box, line: [] as Pt[] },
  },
};

const SOURCE_COLOR: Record<string, string> = {};

/** Colours of the flows; CSS variables (theme.ts), so they follow the light or dark theme. */
export const COLORS = {
  sun: "var(--h-sun)",
  batt: "var(--h-batt)",
  house: "var(--h-house)",
  grid: "var(--h-grid)",
  ev: "var(--h-ev)",
  exp: "var(--h-exp)",
};
Object.assign(SOURCE_COLOR, {
  sun: COLORS.sun,
  batt: COLORS.batt,
  grid: COLORS.grid,
});

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
  | "shed"
  | "home";
type FloorKey = "attic" | "first" | "ground" | "shed";
export const ITEM_KEYS: ItemKey[] = [
  "roof",
  "shed_solar",
  "battery",
  "grid",
  "ev",
  "home",
  "attic",
  "first",
  "ground",
  "shed",
];

export type Source = "sun" | "batt" | "grid";

/**
 * The source that supplies the most to the house now, for the colour of the main line. A new
 * source takes over only when it supplies at least `margin` W more than the current one, so the
 * colour does not flicker between two sources of about the same size. Charging the battery and
 * exporting are not sources. Null when nothing flows.
 */
export function dominant(
  supply: Record<Source, number>,
  current: Source | null,
  margin = 50,
): Source | null {
  const best = (Object.keys(supply) as Source[]).reduce((a, b) =>
    supply[b] > supply[a] ? b : a,
  );
  if (supply[best] < 10) return null;
  if (
    current &&
    current !== best &&
    supply[best] < supply[current] + margin &&
    supply[current] >= 10
  )
    return current;
  return best;
}

/** The flows now in words, per source: "Zon 3,2 kW → huis 0,6 kW · accu 2,4 kW". */
export function flowParts(
  paths: Record<string, number>,
): { from: Source; total: number; to: [string, number][] }[] {
  const out: { from: Source; total: number; to: [string, number][] }[] = [];
  const add = (from: Source, keys: [string, string][]) => {
    const to = keys
      .map(([k, dest]) => [dest, paths[k] ?? 0] as [string, number])
      .filter(([, w]) => w >= 10);
    if (to.length)
      out.push({ from, total: to.reduce((t, [, w]) => t + w, 0), to });
  };
  add("sun", [
    ["solar_house", "house"],
    ["solar_battery", "battery"],
    ["solar_grid", "grid"],
  ]);
  add("batt", [
    ["battery_house", "house"],
    ["battery_grid", "grid"],
  ]);
  add("grid", [
    ["grid_house", "house"],
    ["grid_battery", "battery"],
  ]);
  return out;
}
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
export function ownLine(
  box: [number, number],
  point: [number, number],
  w: number,
  h: number,
): Pt[] {
  const left = Math.min(box[0], 1 - OWN_BOX_W) * w;
  const right = left + OWN_BOX_W * w;
  const y = box[1] * h + 0.035 * w;
  const px = point[0] * w;
  const py = point[1] * h;
  const x = px < left ? left : px > right ? right : px;
  if (x === px)
    return [
      [px, y],
      [px, py],
    ];
  return [
    [x, y],
    [px, y],
    [px, py],
  ];
}

/** Built-in picture on Stroom: the default house (3 storeys), the alternative (2) or the old one. */
export type HouseStyle = "default" | "alt" | "old";

/** Size of the default and alternative house (frontend/scripts/house_gen.py). */
export const NW = 1800;
export const NH = 1150;
/** x of the main line in the default and alternative house. */
const NBUS = 1230;

/**
 * Where things are in the default (3) and alternative (2) house, in picture pixels
 * (OPDRACHT-ui-huisplaatje-isometrisch §4; points from the projection in house_gen.py).
 * Sources run to the main line; from it, branches go to the floor boxes, into the house (the
 * rest, at the meter cupboard) and to the charge point.
 */
export function houseLayout(storeys: 2 | 3) {
  const three = storeys === 3;
  return {
    storeys,
    bus: [52, 1030] as [number, number],
    battery: { from: [416, three ? 524 : 494] as Pt, y: 52 },
    shedSolar: { from: [486, three ? 437 : 407] as Pt, y: 80 },
    roof: { from: [931, three ? 354 : 399] as Pt },
    floors: (three
      ? { attic: 462, first: 640, ground: 840 }
      : { first: 560, ground: 800 }) as Partial<Record<FloorKey, number>>,
    rest: { y: three ? 750 : 705, x: 1106 },
    ev: { y: three ? 968 : 935, to: [722, three ? 912 : 884] as Pt },
    grid: { y: 1030, x: 1290 },
    boxes: {
      header: [1300, 24, 450, 132] as Box,
      home: [1300, 196, 450, 104] as Box,
      attic: [1300, 418, 450, 88] as Box,
      first: (three ? [1300, 596, 450, 88] : [1300, 504, 450, 112]) as Box,
      ground: (three ? [1300, 796, 450, 88] : [1300, 756, 450, 88]) as Box,
      grid: [1300, 990, 450, 80] as Box,
      roof: [36, 104, 280, 112] as Box,
      shed_solar: [36, 228, 280, 112] as Box,
      battery: [36, 352, 280, 172] as Box,
      shed: [36, 540, 280, 100] as Box,
      ev: [36, 980, 280, 88] as Box,
    },
    /** Dashed pointers from a box on the left to its place in the picture. */
    pointers: {
      roof: [[316, 160], three ? [600, 300] : [640, 290]] as Pt[],
      shed_solar: [
        [316, 284],
        [452, three ? 470 : 440],
      ] as Pt[],
      battery: [
        [316, 440],
        [408, three ? 520 : 490],
      ] as Pt[],
      shed: [
        [316, 590],
        [528, three ? 546 : 516],
      ] as Pt[],
      ev: [
        [316, 1010],
        [700, three ? 930 : 900],
      ] as Pt[],
    },
  };
}

/** A connection on the main line: power into the line (+ from a source, − to a consumer). */
export interface Tap {
  y: number;
  w: number;
}

/** A piece of the main line between two connections, with the power through it and its direction. */
export interface BusSegment {
  y0: number;
  y1: number;
  w: number;
  /** 1: downwards, −1: upwards, 0: (almost) nothing flows. */
  dir: 1 | -1 | 0;
}

/**
 * The pieces of the main line between its connections (OPDRACHT §3). Through each piece flows
 * the sum of everything above it: sources count +, consumers − (charging the battery and export
 * are consumers on the line side). A positive sum flows down, a negative one up; below 10 W
 * the piece gets no dots.
 */
export function busSegments(taps: Tap[], min = 10): BusSegment[] {
  const sorted = [...taps].sort((a, b) => a.y - b.y);
  const out: BusSegment[] = [];
  let sum = 0;
  for (let i = 0; i < sorted.length - 1; i++) {
    sum += sorted[i].w;
    if (sorted[i + 1].y === sorted[i].y) continue;
    out.push({
      y0: sorted[i].y,
      y1: sorted[i + 1].y,
      w: Math.abs(sum),
      dir: Math.abs(sum) < min ? 0 : sum > 0 ? 1 : -1,
    });
  }
  return out;
}

/** The floor a consumer is shown on: the alternative house has no attic, so the attic is the 1st floor. */
export function shownFloor(floor: string, storeys: 2 | 3): string {
  return storeys === 2 && floor === "attic" ? "first" : floor;
}

/** A flow line on an own picture from a spot to the Huis spot: level first, then straight. */
export function hubPath(from: Pt, hub: Pt): Pt[] {
  if (from[0] === hub[0] || from[1] === hub[1]) return [from, hub];
  return [from, [hub[0], from[1]], hub];
}

@element("zephyr-house")
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
    const style = this.view?.house_style ?? "default";
    const storeys: 2 | 3 = style === "alt" ? 2 : 3;
    return html`<section class="card" aria-label=${this.tr("house.title")}>
      ${
        own
          ? this.ownStage(own, items)
          : style === "old"
            ? this.defaultStage(items)
            : this.newStage(items, storeys)
      }
      ${this.bar(f, ev)}
      ${this.list(devices, Math.max(0, f.house - this.known(devices)), own || style === "old" ? 3 : storeys)}
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
      (floors[key] ?? []).reduce((s, d) => s + (d.power_w ?? 0), 0);
    const floor = (k: FloorKey): Item => ({
      ...this.floorItem(k, floors[k] ?? [], null, now),
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
            <b
              >${Math.abs(f.battery) > 10 ? this.w(Math.abs(f.battery)) : ""}</b
            >
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
          html`${this.tr("house.import")}
            <b>${this.w(Math.max(0, f.grid))}</b>`,
          html`${this.tr("house.export")}
            <b>${this.w(Math.max(0, -f.grid))}</b>`,
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
      home: {
        color: COLORS.house,
        icon: "house",
        title: html`<b>${this.tr("house.home")}</b>`,
        lines: [
          html`${this.tr("house.total")} <b>${this.w(f.house)}</b>`,
          html`${this.tr("house.rest_of")} <b>${this.w(rest)}</b>`,
        ],
        power: rest,
      },
      attic: floor("attic"),
      first: floor("first"),
      ground: floor("ground"),
      shed: floor("shed"),
    };
  }

  @state() private dom: Source | null = null;

  /** Colour of the main line: the source that supplies the most now (with a margin). */
  private mainColor(f: ReturnType<typeof flows>): string {
    const dom = dominant(
      {
        sun: f.solar - f.paths.solar_battery,
        batt: Math.max(0, -f.battery),
        grid: Math.max(0, f.grid),
      },
      this.dom,
    );
    if (dom !== this.dom) queueMicrotask(() => (this.dom = dom));
    return dom ? SOURCE_COLOR[dom] : COLORS.house;
  }

  /** The default house: every source runs to the main line, from there to the floors and the house. */
  private defaultStage(it: Record<ItemKey, Item>): TemplateResult {
    const L = LAYOUT;
    const now = this.now!;
    const airco = now.excluded?.active ? (now.excluded.power_w ?? 0) : 0;
    const f = flows(now.solar_w, now.grid_w, now.battery_w, airco);
    const c = this.mainColor(f);
    const rev = (pts: Pt[], yes: boolean): Pt[] =>
      yes ? [...pts].reverse() : pts;
    const bat = f.battery;
    const busOn =
      f.house >= 10 || Math.abs(bat) >= 10 || Math.abs(f.grid) >= 10;
    const tag = (at: Pt, text: string, color: string, on: boolean) =>
      on
        ? svg`<text x=${at[0]} y=${at[1]} class="tag" style=${`fill:${color}`}>${text}</text>`
        : nothing;
    const to = (key: string) => this.tr(`house.to_${key}`);
    return html`<div class="stage">
      <img src=${`${this.base}/house.webp`} alt="" draggable="false" />
      <svg viewBox="0 0 ${W} ${H}" aria-hidden="true">
        ${busOn ? this.line(L.bus, c, Math.max(f.house, Math.abs(bat), Math.abs(f.grid))) : nothing}
        ${this.line(L.roof.line, COLORS.sun, it.roof.power)}${this.dot(L.roof.dot, COLORS.sun)}
        ${this.line(L.shedSolar.line, COLORS.sun, it.shed_solar.power)}${this.dot(L.shedSolar.dot, COLORS.sun)}
        ${this.line(rev(L.battery.line, bat > 0), COLORS.batt, Math.abs(bat))}${this.dot(L.battery.dot, COLORS.batt)}
        ${this.line(rev(L.grid.line, f.grid < 0), COLORS.grid, Math.abs(f.grid))}
        ${it.ev.active ? svg`${this.line(L.ev.line, COLORS.batt, it.ev.power)}${this.dot(L.ev.dot, COLORS.batt)}` : nothing}
        ${it.home.power >= 10 ? svg`${this.line(L.home.line, c, it.home.power)}${this.dot(L.home.dot, c)}` : nothing}
        ${(["attic", "first", "ground"] as const).map((k) => {
          const ln = L.floors[k].line;
          const end = ln[ln.length - 1];
          return it[k].power >= 10
            ? svg`${this.line(ln, c, it[k].power)}${this.arrow(end[0], end[1], c)}`
            : nothing;
        })}
        ${busOn ? svg`<circle cx=${BUS} cy="96" r="8" style=${`fill:${c}`}></circle><circle cx=${BUS} cy="1145" r="8" style=${`fill:${c}`}></circle>` : nothing}
        ${tag(L.roof.label, this.w(it.roof.power), COLORS.sun, it.roof.power >= 10)}
        ${tag(L.battery.label, `${this.w(Math.abs(bat))} ${to(bat > 0 ? "battery" : "house")}`, COLORS.batt, Math.abs(bat) >= 10)}
        ${tag(L.grid.label, `${this.w(Math.abs(f.grid))} ${to(f.grid > 0 ? "house" : "grid")}`, COLORS.grid, Math.abs(f.grid) >= 10)}
        ${tag(L.home.label, `${this.tr("house.rest")} ${this.w(it.home.power)}`, c, it.home.power >= 10)}
      </svg>
      <div class="boxes">
        ${this.box(L.header, this.header(f.paths))}
        ${this.box(L.roof.box, it.roof)}
        ${this.box(L.shedSolar.box, it.shed_solar)}
        ${this.box(L.battery.box, it.battery)} ${this.box(L.grid.box, it.grid)}
        ${this.box(L.ev.box, it.ev)}
        ${this.box(L.home.box, { ...it.home, color: c })}
        ${FLOOR_KEYS.map((k) => this.box(L.floors[k].box, it[k]))}
      </div>
    </div>`;
  }

  /**
   * The default (3 storeys) or alternative (2 storeys) house: every source runs to the main line;
   * from it, branches go to the floors with measured consumers, into the house and to the charge
   * point. The main line carries dots per piece, in the direction the power goes there.
   */
  private newStage(it: Record<ItemKey, Item>, storeys: 2 | 3): TemplateResult {
    const L = houseLayout(storeys);
    const now = this.now!;
    const airco = now.excluded?.active ? (now.excluded.power_w ?? 0) : 0;
    const f = flows(now.solar_w, now.grid_w, now.battery_w, airco);
    const c = this.mainColor(f);
    const bat = f.battery;
    const devices = (this.view?.devices ?? []).filter(
      (d) => d.kind !== "ev" && d.shown,
    );
    const onFloor = (k: FloorKey) =>
      devices.filter((d) => shownFloor(d.floor, storeys) === k);
    const floorW = (k: FloorKey) =>
      onFloor(k).reduce((s, d) => s + (d.power_w ?? 0), 0);
    const floors = (Object.keys(L.floors) as FloorKey[]).map((k) => ({
      k,
      y: L.floors[k] as number,
      w: floorW(k),
    }));
    const ev = it.ev.active ? it.ev.power : 0;
    const taps: Tap[] = [
      { y: L.battery.y, w: -bat },
      { y: L.shedSolar.y, w: it.shed_solar.power },
      { y: L.roof.from[1], w: it.roof.power },
      ...floors.map((x) => ({ y: x.y, w: -x.w })),
      { y: L.rest.y, w: -it.home.power },
      { y: L.ev.y, w: -ev },
      { y: L.grid.y, w: f.grid },
    ];
    const busOn = taps.some((x) => Math.abs(x.w) >= 10);
    const B = NBUS;
    const rev = (pts: Pt[], yes: boolean): Pt[] =>
      yes ? [...pts].reverse() : pts;
    const bLine: Pt[] = [
      L.battery.from,
      [L.battery.from[0], L.battery.y],
      [B, L.battery.y],
    ];
    const sLine: Pt[] = [
      L.shedSolar.from,
      [L.shedSolar.from[0], L.shedSolar.y],
      [B, L.shedSolar.y],
    ];
    const rLine: Pt[] = [L.roof.from, [B, L.roof.from[1]]];
    const gLine: Pt[] = [
      [L.grid.x, L.grid.y],
      [B, L.grid.y],
    ];
    const eLine: Pt[] = [[B, L.ev.y], [L.ev.to[0], L.ev.y], L.ev.to];
    const oLine: Pt[] = [
      [B, L.rest.y],
      [L.rest.x, L.rest.y],
    ];
    const to = (key: string) => this.tr(`house.to_${key}`);
    const on = (w: number) => Math.abs(w) >= 10;
    const joints: [Pt, string, number][] = [
      [[B, L.battery.y], COLORS.batt, bat],
      [L.battery.from, COLORS.batt, bat],
      [[B, L.shedSolar.y], COLORS.sun, it.shed_solar.power],
      [L.shedSolar.from, COLORS.sun, it.shed_solar.power],
      [[B, L.roof.from[1]], COLORS.sun, it.roof.power],
      [L.roof.from, COLORS.sun, it.roof.power],
      [[B, L.grid.y], COLORS.grid, f.grid],
      ...floors.map((x) => [[B, x.y], c, x.w] as [Pt, string, number]),
      [[B, L.rest.y], c, it.home.power],
      [[B, L.ev.y], c, ev],
    ];
    const boxes = L.boxes;
    const floorBox = (k: FloorKey) => {
      const devs = onFloor(k);
      return this.nbox(boxes[k], {
        cap: this.tr(`settings.floors.${k}`),
        color: c,
        accent: true,
        lines: devs.length
          ? devs.map(
              (d) =>
                html`<span class=${(d.power_w ?? 0) >= 10 ? "" : "dim"}
                  >${d.name ?? this.tr(`stroom.kind_${d.kind}`)}
                  <b>${this.w(d.power_w)}</b></span
                >`,
            )
          : [html`<span class="dim">–</span>`],
      });
    };
    const label = this.view?.battery_label;
    const battState = this.tr(
      bat > 10
        ? "house.charging"
        : bat < -10
          ? "house.delivering"
          : "house.idle",
    );
    return html`<div class="stage new">
      <img
        src=${`${this.base}/house-${storeys}.webp`}
        alt=""
        draggable="false"
      />
      <svg viewBox="0 0 ${NW} ${NH}" aria-hidden="true">
        ${(["roof", "shed_solar", "battery", "ev"] as const).map((k) =>
          k === "ev" && !it.ev.active
            ? nothing
            : svg`<path d=${`M${L.pointers[k].map((q) => q.join(" ")).join(" L")}`} class="pointer2"></path>
              <circle cx=${L.pointers[k][1][0]} cy=${L.pointers[k][1][1]} r="4" class="pdot"></circle>`,
        )}
        ${
          onFloor("shed").length
            ? svg`<path d=${`M${L.pointers.shed.map((q) => q.join(" ")).join(" L")}`} class="pointer2"></path>`
            : nothing
        }
        ${busOn ? this.bus(L.bus, c, taps) : nothing}
        ${this.bead(rev(bLine, bat > 0), COLORS.batt, Math.abs(bat), bat > 0)}
        ${this.bead(sLine, COLORS.sun, it.shed_solar.power)}
        ${this.bead(rLine, COLORS.sun, it.roof.power)}
        ${this.bead(rev(gLine, f.grid < 0), COLORS.grid, Math.abs(f.grid))}
        ${floors.map((x) =>
          this.bead(
            [
              [B, x.y],
              [1288, x.y],
            ],
            c,
            x.w,
            true,
          ),
        )}
        ${this.bead(oLine, c, it.home.power, true)}
        ${this.bead(eLine, c, ev, true)}
        ${joints.map(([p, color, w]) => (on(w) ? this.joint(p, color) : nothing))}
        ${on(bat) ? this.pill([700, L.battery.y], `${this.tr("house.battery")} ${this.w(Math.abs(bat))} ${to(bat > 0 ? "battery" : "house")}`, COLORS.batt) : nothing}
        ${on(it.shed_solar.power) ? this.pill([900, L.shedSolar.y], `${this.tr("house.shed_short")} ${this.w(it.shed_solar.power)}`, COLORS.sun) : nothing}
        ${on(it.roof.power) ? this.pill([1085, L.roof.from[1]], `${this.tr("house.roof_short")} ${this.w(it.roof.power)}`, COLORS.sun) : nothing}
        ${on(it.home.power) ? this.pill([1160, L.rest.y - 34], `${this.tr("house.rest")} ${this.w(it.home.power)}`, c) : nothing}
        ${on(ev) ? this.pill([960, L.ev.y], this.w(ev), c) : nothing}
        ${on(f.grid) ? this.pill([1120, L.grid.y], `${this.tr("house.grid")} ${this.w(Math.abs(f.grid))} ${to(f.grid > 0 ? "house" : "grid")}`, COLORS.grid) : nothing}
      </svg>
      <div class="boxes">
        ${this.nbox(boxes.header, {
          cap: this.tr("house.title"),
          color: c,
          cls: "hdr",
          lines: this.header(f.paths).lines,
        })}
        ${this.nbox(boxes.home, {
          cap: this.tr("house.home"),
          color: c,
          frame: true,
          big: this.w(f.house),
          lines: [
            html`<span class="dim"
              >${this.tr("house.rest_of")} ${this.w(it.home.power)}</span
            >`,
          ],
        })}
        ${floors.map((x) => floorBox(x.k))}
        ${this.nbox(boxes.grid, {
          cap: this.tr("house.grid"),
          color: COLORS.grid,
          frame: true,
          lines: [
            f.grid >= 10
              ? html`<b class="strong" style="color:var(--h-grid)"
                  >${this.tr("house.import_t")} ${this.w(f.grid)}</b
                >`
              : f.grid <= -10
                ? html`<b class="strong" style="color:var(--h-batt)"
                    >${this.tr("house.export_t2")} ${this.w(-f.grid)}</b
                  >`
                : html`<span class="dim">${this.tr("house.grid_zero")}</span>`,
          ],
        })}
        ${this.nbox(boxes.roof, {
          cap: this.tr("house.roof_box"),
          color: COLORS.sun,
          accent: true,
          big: this.w(it.roof.power),
          lines: it.roof.lines.slice(1),
          extra: now.curtail?.active
            ? html`<span class="red">${this.curtailText(now.curtail)}</span>`
            : undefined,
        })}
        ${this.nbox(boxes.shed_solar, {
          cap: this.tr("house.shed_box"),
          color: COLORS.sun,
          accent: true,
          big: this.w(it.shed_solar.power),
          lines: [],
        })}
        ${this.nbox(boxes.battery, {
          cap: this.tr("house.battery"),
          color: COLORS.batt,
          accent: true,
          lines: [
            ...(label ? [html`<span class="dim small">${label}</span>`] : []),
            html`<b class="strong" style=${on(bat) ? "color:var(--h-batt)" : ""}
              >${battState}${on(bat) ? ` ${this.w(Math.abs(bat))}` : ""}</b
            >`,
            ...(now.soc !== null
              ? [html`<b>${percent(now.soc, this.locale)}</b>`]
              : []),
            ...(now.curtail?.export_blocked
              ? [
                  html`<span class="red"
                    >${this.tr("flow.export_blocked")}</span
                  >`,
                ]
              : []),
          ],
        })}
        ${onFloor("shed").length ? floorBox("shed") : nothing}
        ${this.nbox(boxes.ev, {
          cap: this.tr("house.ev"),
          color: c,
          accent: true,
          off: !it.ev.active,
          big: it.ev.active ? this.w(ev) : "–",
          lines: [],
        })}
      </div>
    </div>`;
  }

  /** The main line with its glow and, per piece, dots in the direction the power goes there. */
  private bus(y: [number, number], color: string, taps: Tap[]) {
    const x = NBUS;
    const d = `M${x} ${y[0]} L${x} ${y[1]}`;
    return svg`<path d=${d} class="busglow" style=${`stroke:${color}`}></path>
      <path d=${d} class="buscore" style=${`stroke:${color}`}></path>
      <path d=${d} class="busshine"></path>
      ${busSegments(taps).map((s) =>
        s.dir === 0
          ? nothing
          : this.beads(
              s.dir > 0
                ? `M${x} ${s.y0} L${x} ${s.y1}`
                : `M${x} ${s.y1} L${x} ${s.y0}`,
              color,
              s.w,
            ),
      )}`;
  }

  /** A flow line in the new houses: glow, line and moving beads; an arrow at the end if asked. */
  private bead(pts: Pt[], color: string, power: number, arrow = false) {
    if (power < 10) return nothing;
    const d = `M${pts.map((p) => p.join(" ")).join(" L")}`;
    return svg`<path d=${d} class="nglow" style=${`stroke:${color}`}></path>
      <path d=${d} class="ncore" style=${`stroke:${color}`}></path>
      ${this.beads(d, color, power)}
      ${arrow ? this.arrowAt(pts, color) : nothing}`;
  }

  private beads(d: string, color: string, power: number) {
    const dur = `animation-duration:${Math.max(0.5, 1.7 - power / 3000).toFixed(2)}s`;
    return svg`<path d=${d} class="bead" style=${`stroke:${color};${dur}`}></path>
      <path d=${d} class="beadc" style=${dur}></path>`;
  }

  /** An arrow head at the end of a line, pointing along its last piece. */
  private arrowAt(pts: Pt[], color: string) {
    const [a, b] = pts.slice(-2);
    const ang = (Math.atan2(b[1] - a[1], b[0] - a[0]) * 180) / Math.PI;
    return svg`<path d="M0 0 l-14 -8 l0 16 z" style=${`fill:${color}`}
      transform=${`translate(${b[0]} ${b[1]}) rotate(${ang.toFixed(1)})`}></path>`;
  }

  /** A connection point: white with a ring in the line's colour. */
  private joint(p: Pt, color: string) {
    return svg`<circle cx=${p[0]} cy=${p[1]} r="7" class="joint" style=${`stroke:${color}`}></circle>`;
  }

  /** A label on a line, centred on `at`. */
  private pill(at: Pt, text: string, color: string) {
    const w = text.length * 10.4 + 30;
    return svg`<g class="pill">
      <rect x=${at[0] - w / 2} y=${at[1] - 15} width=${w} height="30" rx="15" style=${`stroke:${color}`}></rect>
      <text x=${at[0]} y=${at[1] + 6.5}>${text}</text>
    </g>`;
  }

  /** A box in the new houses: a small caption, an optional large value and lines. */
  private nbox(
    b: Box,
    o: {
      cap: string;
      color: string;
      lines: (TemplateResult | string)[];
      big?: string;
      accent?: boolean;
      frame?: boolean;
      off?: boolean;
      extra?: TemplateResult;
      cls?: string;
    },
  ): TemplateResult {
    const [x, y, w, h] = b;
    const style = `left:${(x / NW) * 100}%;top:${(y / NH) * 100}%;width:${(w / NW) * 100}%;min-height:${(h / NH) * 100}%;--c:${o.color}`;
    const cls = `nbox${o.accent ? " accent" : ""}${o.frame ? " frame" : ""}${o.off ? " off" : ""}${o.cls ? ` ${o.cls}` : ""}`;
    return html`<div class=${cls} style=${style}>
      <span class="cap">${o.cap}</span>
      ${o.big !== undefined ? html`<span class="big">${o.big}</span>` : nothing}
      ${o.lines.map((l) => html`<span class="nl">${l}</span>`)}
      ${o.extra ? html`<span class="nl">${o.extra}</span>` : nothing}
    </div>`;
  }

  /** An own picture: each placed item gets its box and a line with one bend to its spot. */
  private ownStage(
    own: HousePicture,
    it: Record<ItemKey, Item>,
  ): TemplateResult {
    const w = own.width || 1600;
    const h = own.height || 1200;
    const shown = ITEM_KEYS.filter(
      (k) => !own.hidden.includes(k) && own.items[k]?.box,
    );
    const now = this.now!;
    const airco = now.excluded?.active ? (now.excluded.power_w ?? 0) : 0;
    const f = flows(now.solar_w, now.grid_w, now.battery_w, airco);
    const px = (k: ItemKey): Pt | null => {
      const p = own.items[k]?.point;
      return p && shown.includes(k) ? [p[0] * w, p[1] * h] : null;
    };
    // With a Huis spot, every flow runs through it: sources to it, consumers from it.
    const hub = px("home");
    const c = this.mainColor(f);
    const flowsSvg = hub
      ? svg`${(
          [
            ["roof", COLORS.sun, it.roof.power, false],
            ["shed_solar", COLORS.sun, it.shed_solar.power, false],
            ["battery", COLORS.batt, Math.abs(f.battery), f.battery > 0],
            ["grid", COLORS.grid, Math.abs(f.grid), f.grid < 0],
          ] as [ItemKey, string, number, boolean][]
        ).map(([k, color, power, back]) => {
          const at = px(k);
          if (!at) return nothing;
          const pts = hubPath(at, hub);
          return this.line(back ? [...pts].reverse() : pts, color, power);
        })}
        ${(["ev", "attic", "first", "ground"] as ItemKey[]).map((k) => {
          const at = px(k);
          return at && (k !== "ev" || it.ev.active)
            ? this.line(hubPath(at, hub).reverse(), c, it[k].power)
            : nothing;
        })}
        ${this.dot(hub, c)}`
      : nothing;
    return html`<div class="stage own" style=${`aspect-ratio:${w}/${h}`}>
      ${this.ownUrl ? html`<img src=${this.ownUrl} alt="" draggable="false" />` : nothing}
      <svg viewBox="0 0 ${w} ${h}" aria-hidden="true">
        ${flowsSvg}
        ${shown.map((k) => {
          const place = own.items[k];
          if (!place?.point || !place.box) return nothing;
          const pts = ownLine(place.box, place.point, w, h);
          const end = pts[pts.length - 1];
          const color = k === "home" ? c : it[k].color;
          // With a Huis spot the box only points at its spot; the flow runs on the hub lines.
          return hub
            ? svg`<path d=${`M${pts.map((q) => q.join(" ")).join(" L")}`} class="pointer" style=${`stroke:${color}`}></path>${this.dot(end, color)}`
            : svg`${this.line(pts, color, it[k].power)}${this.dot(end, color)}`;
        })}
      </svg>
      <div class="boxes">
        ${shown.map((k) => {
          const [x, y] = own.items[k]?.box ?? [0, 0];
          const item =
            k === "home"
              ? {
                  ...it.home,
                  color: c,
                  lines: [
                    ...it.home.lines,
                    ...(flowParts(f.paths).length
                      ? this.header(f.paths).lines
                      : []),
                  ],
                }
              : it[k];
          return this.placed(x, y, item);
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

  private header(paths?: Record<string, number>): Item {
    const src = (k: string) => this.tr(`house.src_${k}`);
    const dst = (k: string) => this.tr(`house.dst_${k}`);
    const parts = paths ? flowParts(paths) : [];
    return {
      color: "#23435a",
      icon: "leaf",
      title: html`<b class="big">${this.tr("house.title")}</b>`,
      lines: parts.length
        ? parts.map((p) =>
            p.to.length === 1
              ? html`${src(p.from)} <b>${this.w(p.total)}</b> →
                  ${dst(p.to[0][0])}`
              : html`${src(p.from)} <b>${this.w(p.total)}</b> →
                  ${p.to.map(([d, w], i) => html`${i ? " · " : ""}${dst(d)} ${this.w(w)}`)}`,
          )
        : [this.tr("house.sub")],
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
    return html`<div
      class=${it.active === false ? "box off" : "box"}
      style=${style}
    >
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
    return svg`<path d=${d} class="glow" style=${`stroke:${color}`}></path>
      <path d=${d} class="core" style=${`stroke:${color}`}></path>
      <path d=${d} class="dots" style=${`animation-duration:${Math.max(0.5, 1.6 - power / 3000)}s`}></path>`;
  }

  private dot(p: Pt, color: string) {
    return svg`<circle cx=${p[0]} cy=${p[1]} r="6" style=${`fill:${color}`}></circle>`;
  }

  /** An arrow pointing right with its tip at (x, y). */
  private arrow(x: number, y: number, color: string) {
    return svg`<path d=${`M${x} ${y} l-16 -9 l0 18 z`} style=${`fill:${color}`}></path>`;
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
  private list(
    devices: HouseDevice[],
    rest: number,
    storeys: 2 | 3,
  ): TemplateResult {
    const shown = devices.filter((d) => d.shown);
    return html`<ul class="list">
      ${shown.map(
        (d) =>
          html`<li>
            <span
              >${d.name ?? this.tr(`stroom.kind_${d.kind}`)}
              <small
                >${this.tr(`settings.floors.${shownFloor(d.floor, storeys)}`)}</small
              ></span
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
      /* Picture plus totals bar fit in one screen: 1700/1225 is the default picture's aspect ratio. */
      --house-max: calc((100vh - 300px) * var(--house-ar, 1.3878) + 30px);
    }
    .card {
      container: house / inline-size;
      max-width: var(--house-max);
      margin: 0 auto;
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 18px;
      padding: 14px;
      color: var(--z-text);
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
    .stage > svg .pointer {
      fill: none;
      stroke-width: 2;
      opacity: 0.7;
    }
    .stage > svg text.tag {
      font: 700 26px var(--z-font);
      paint-order: stroke;
      stroke: #0b1620;
      stroke-width: 7px;
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
      background: var(--h-box);
      border: 1px solid var(--z-border);
      border-radius: 16px;
      padding: 14px 6px;
    }
    .bar > div {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      border-right: 1px solid var(--z-border);
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
      color: var(--z-muted);
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
      border-bottom: 1px solid var(--z-border);
    }
    .list small {
      color: var(--z-muted);
    }
    /* The default and alternative house (OPDRACHT-ui-huisplaatje-isometrisch). */
    .nglow,
    .busglow {
      fill: none;
      stroke-width: 15;
      opacity: 0.16;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .busglow {
      stroke-width: 19;
    }
    .ncore {
      fill: none;
      stroke-width: 5.5;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .buscore {
      fill: none;
      stroke-width: 9;
      stroke-linecap: round;
    }
    .busshine {
      fill: none;
      stroke: #fff;
      stroke-width: 2;
      opacity: 0.55;
    }
    .bead,
    .beadc {
      fill: none;
      stroke-linecap: round;
      stroke-linejoin: round;
      stroke-dasharray: 0.01 30;
      animation: bead 1.4s linear infinite;
    }
    .bead {
      stroke-width: 11;
    }
    .beadc {
      stroke: #fff;
      stroke-width: 6;
    }
    @keyframes bead {
      from {
        stroke-dashoffset: 30;
      }
      to {
        stroke-dashoffset: 0;
      }
    }
    .joint {
      fill: #fff;
      stroke-width: 3;
    }
    .pointer2 {
      fill: none;
      stroke: var(--z-muted);
      stroke-width: 1.4;
      stroke-dasharray: 4 4;
      opacity: 0.8;
    }
    .pdot {
      fill: var(--z-muted);
    }
    .pill rect {
      fill: var(--h-pill);
      stroke-width: 1.6;
    }
    .pill text {
      font: 600 18px var(--z-font);
      fill: var(--z-text);
      text-anchor: middle;
    }
    .nbox {
      position: absolute;
      box-sizing: border-box;
      display: flex;
      flex-direction: column;
      gap: 0.15cqw;
      padding: 0.8cqw 1cqw 0.8cqw 1.3cqw;
      background: var(--h-box);
      border: 1px solid var(--z-border);
      border-radius: 0.9cqw;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
      color: var(--z-text);
      font-size: max(11px, 1.05cqw);
      line-height: 1.35;
      overflow: hidden;
    }
    .nbox.accent::before {
      content: "";
      position: absolute;
      left: 0;
      top: 16%;
      bottom: 16%;
      width: max(3px, 0.3cqw);
      border-radius: 3px;
      background: var(--c);
    }
    .nbox.frame {
      border: 2px solid var(--c);
    }
    .nbox.off {
      opacity: 0.6;
    }
    .nbox .cap {
      font-size: max(11px, 0.85cqw);
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--z-muted);
    }
    .nbox .big {
      font-size: max(14px, 1.45cqw);
      font-weight: 700;
    }
    .nbox .nl {
      font-weight: 600;
    }
    .nbox .nl .dim,
    .nbox .nl.dim {
      color: var(--z-muted);
      font-weight: 500;
    }
    .nbox.hdr .nl {
      font-size: max(11px, 0.95cqw);
    }
    .nbox .small {
      font-size: max(11px, 0.85cqw);
    }
    .nbox .strong {
      font-size: max(12px, 1.2cqw);
    }
    @container house (max-width: 680px) {
      .stage > svg,
      .boxes {
        display: none;
      }
      /* Without lines and boxes the empty right part of the new houses is not needed. */
      .stage.new img {
        width: 150%;
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
