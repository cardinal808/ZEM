// Plan screen: three buttons under "Prijzen en plan" (B36, Bjorn 27-11): tap to plan a run, again for a second
// wash, again to clear. The window and "after the washing" are set in Instellingen → Apparaten.
import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { clock, dateFormat, euro, sameDay } from "./format";
import { t, type Lang } from "./i18n";
import type { Quarter } from "./plan";

export interface ApplianceItem {
  id: string;
  name: string;
  kind: string;
  plug: boolean;
  running: boolean | null;
  profile: "learned" | "default" | string;
  runs_seen: number;
  kwh: number;
  minutes: number;
  profile_w?: number[];
  window: { from: string | null; until: string };
  after_washer?: boolean;
}

export interface PlannedRunView {
  index: number;
  appliance: string;
  window_start: string;
  window_end: string;
  fixed_start: string | null;
  /** Name of the appliance this run waits for (a dryer after the washer). */
  after: string | null;
  best_start: string | null;
  cost?: number;
  cost_now?: number;
  saving?: number;
  kwh?: number;
  minutes?: number;
}

export interface AppliancesView {
  revision: number;
  appliances: ApplianceItem[];
  planned: PlannedRunView[];
}

export interface PlanOptions {
  runs?: number;
}

export const WASHER = "washer";

/** Runs of one appliance, earliest advised start first. */
export function runsOf(view: AppliancesView, id: string): PlannedRunView[] {
  return view.planned
    .filter((p) => p.appliance === id)
    .sort(
      (a, b) =>
        (a.best_start ?? "9999").localeCompare(b.best_start ?? "9999") ||
        a.index - b.index,
    );
}

/** What a tap does: the washer goes 0 → 1 → 2 → off, the others 0 → 1 → off. */
export function tapAction(kind: string, planned: number): "plan" | "clear" {
  const max = kind === WASHER ? 2 : 1;
  return planned >= max ? "clear" : "plan";
}

/** Minutes of the local day for "HH:MM[:SS]". */
const mins = (hhmm: string): number => {
  const [h, m] = hhmm.split(":").map(Number);
  return h * 60 + m;
};

/**
 * Expected cost of one run when nothing is planned: the cheapest start (per quarter) within the
 * appliance's window, at the quarter buy prices, with the learned profile or an even spread.
 * Only quarters still to come count; null when the window has no known prices.
 */
export function estimateCost(
  quarters: Quarter[],
  a: ApplianceItem,
  nowMs: number,
  timeZone: string,
): number | null {
  const fmt = dateFormat("en-GB", {
    timeZone,
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  });
  const minutes = Math.max(1, a.minutes);
  const perMinute =
    a.profile_w && a.profile_w.length
      ? a.profile_w.map((w) => w / 60000)
      : Array<number>(minutes).fill(a.kwh / minutes);
  const span = perMinute.length;
  const prices = new Map<number, number>();
  for (const q of quarters)
    if (q.buy !== null) prices.set(new Date(q.start).getTime(), q.buy);
  const from = a.window.from ? mins(a.window.from) : null;
  const until = mins(a.window.until);
  const inside = (m: number): boolean =>
    from === null
      ? true
      : from <= until
        ? m >= from && m <= until
        : m >= from || m <= until;
  let best: number | null = null;
  for (const q of quarters) {
    const start = new Date(q.start).getTime();
    if (start + 15 * 60_000 <= nowMs || q.buy === null) continue;
    if (from === null && start - nowMs > 24 * 3600_000) continue;
    const s = mins(fmt.format(new Date(start)));
    if (!inside(s) || !inside((s + span) % 1440)) continue;
    let cost = 0;
    let known = true;
    for (let i = 0; i < span; i++) {
      const at = start + i * 60_000;
      const price = prices.get(at - (at % (15 * 60_000)));
      if (price === undefined) {
        known = false;
        break;
      }
      cost += perMinute[i] * price;
    }
    if (known && (best === null || cost < best)) best = cost;
  }
  return best;
}

@customElement("zephyr-appliances")
export class ZephyrAppliances extends LitElement {
  @property({ attribute: false }) view?: AppliancesView;
  @property({ attribute: false }) quarters: Quarter[] = [];
  @property({ attribute: false }) uiLang: Lang = "en";
  @property() locale = "en";
  @property() timeZone = "UTC";
  @property({ type: Number }) clockMs = Date.now();
  @property({ attribute: false }) plan?: (
    id: string,
    options: PlanOptions,
  ) => Promise<void>;
  @property({ attribute: false }) clear?: (id: string) => Promise<void>;
  @state() private busy: string | null = null;

  private tr(
    key: string,
    params: Record<string, string | number> = {},
  ): string {
    return t(this.uiLang, key, params);
  }

  private when(iso: string): string {
    const today = sameDay(iso, this.clockMs, this.timeZone);
    return `${this.tr(today ? "appl.today" : "appl.tomorrow")} ${clock(iso, this.locale, this.timeZone)}`;
  }

  private async tap(a: ApplianceItem, planned: number): Promise<void> {
    if (this.busy) return;
    this.busy = a.id;
    try {
      if (tapAction(a.kind, planned) === "clear") await this.clear?.(a.id);
      else await this.plan?.(a.id, {});
    } finally {
      this.busy = null;
    }
  }

  protected override render(): TemplateResult | typeof nothing {
    const v = this.view;
    if (!v || !v.appliances.length) return nothing;
    return html`<div
      class="row"
      role="group"
      aria-label=${this.tr("appl.title")}
    >
      ${v.appliances.map((a) => this.button(a, runsOf(v, a.id)))}
    </div>`;
  }

  private button(a: ApplianceItem, runs: PlannedRunView[]): TemplateResult {
    const on = runs.length > 0;
    const starts = runs
      .map((r) => r.fixed_start ?? r.best_start)
      .filter((s): s is string => !!s);
    const cost = runs.reduce((sum, r) => sum + (r.cost ?? 0), 0);
    const saving = runs.reduce((sum, r) => sum + (r.saving ?? 0), 0);
    const after = runs.find((r) => r.after)?.after ?? null;
    let line: string;
    let extra: string | null = null;
    if (!on) {
      const est = estimateCost(this.quarters, a, this.clockMs, this.timeZone);
      line =
        est === null
          ? this.tr("appl.tap")
          : this.tr("appl.per_run", { euro: euro(est, this.locale) });
    } else if (!starts.length) {
      line = this.tr("appl.calculating");
    } else {
      const times = starts.map((s, i) =>
        i === 0 ? this.when(s) : clock(s, this.locale, this.timeZone),
      );
      line = `${this.tr("appl.start")} ${times.join(` ${this.tr("appl.and")} `)} · ${euro(cost, this.locale)}`;
      extra = after
        ? this.tr("appl.after_wash")
        : saving >= 0.01
          ? this.tr("appl.cheaper", { euro: euro(saving, this.locale) })
          : null;
    }
    const label = on ? `${a.name} ${runs.length}×` : a.name;
    const next =
      tapAction(a.kind, runs.length) === "clear"
        ? "appl.tap_clear"
        : on
          ? "appl.tap_more"
          : "appl.tap_plan";
    return html`<button
      type="button"
      class=${`b${on ? " on" : ""}`}
      aria-pressed=${on ? "true" : "false"}
      ?disabled=${this.busy === a.id}
      title=${this.tr(next)}
      @click=${() => void this.tap(a, runs.length)}
    >
      <b
        >${label}${a.running ? html`<span class="dot" title=${this.tr("appl.running")}></span>` : nothing}</b
      >
      <span>${line}</span>
      ${extra ? html`<em class=${after ? "muted" : ""}>${extra}</em>` : nothing}
    </button>`;
  }

  static override styles = css`
    :host {
      display: block;
    }
    .row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }
    .b {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 1px;
      min-width: 150px;
      padding: 9px 16px;
      border-radius: 14px;
      border: 1px solid var(--z-border);
      background: var(--z-card);
      color: var(--z-text);
      font: inherit;
      text-align: left;
      cursor: pointer;
    }
    .b:disabled {
      opacity: 0.6;
      cursor: progress;
    }
    .b b {
      font-size: 15px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .b span {
      font-size: 12.5px;
      color: var(--z-muted);
    }
    .b em {
      font-style: normal;
      font-size: 12px;
      font-weight: 600;
      color: var(--z-good-text);
    }
    .b em.muted {
      color: var(--z-muted);
    }
    .b.on {
      background: color-mix(in srgb, var(--z-charge) 10%, var(--z-card));
      border-color: color-mix(in srgb, var(--z-charge) 50%, var(--z-card));
    }
    .b.on b {
      color: var(--z-charge);
    }
    .b.on span {
      color: var(--z-text);
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--z-charge);
      display: inline-block;
      animation: pulse 1.6s ease-in-out infinite;
    }
    @keyframes pulse {
      50% {
        opacity: 0.3;
      }
    }
    @media (max-width: 600px) {
      .b {
        min-width: 0;
        flex: 1 1 100%;
      }
    }
  `;
}

/** Group of an appliance kind for texts and icons: both dryer kinds are "dryer". */
export function iconKey(kind: string): string {
  if (kind.startsWith("dryer")) return "dryer";
  return ["washer", "dishwasher"].includes(kind) ? kind : "other";
}
