// Screen "Diagnose" (SPEC-ui §4.5, UI-8): download, cost export, counters, recent events.
import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { eventKind, eventText, profileStats, relDiff, type CheckMetric, type EventsView, type PlanCheckView, type ProfileView } from "./diag";
import { clock, day, sameDay } from "./format";
import { t, type Lang } from "./i18n";

export type ExportResult = { path: string; rows: number };

@customElement("zephyr-diagnostics")
export class ZephyrDiagnostics extends LitElement {
  @property({ attribute: false }) view?: EventsView;
  @property({ attribute: false }) uiLang: Lang = "en";
  @property() locale = "en";
  @property() timeZone = "UTC";
  @property({ type: Boolean }) admin = false;
  @property({ attribute: false }) download?: () => Promise<void>;
  @property({ attribute: false }) exportCosts?: () => Promise<ExportResult>;
  @property({ attribute: false }) refresh?: () => void;
  @property({ attribute: false }) planCheck?: PlanCheckView;

  @state() private busy: "download" | "export" | null = null;
  @state() private note: { text: string; error: boolean } | null = null;
  @state() private dayKind: "workday" | "weekend" = "workday";
  @state() private metric: CheckMetric = "load";

  private tr(key: string, params: Record<string, string | number> = {}): string {
    return t(this.uiLang, key, params);
  }

  private async run(kind: "download" | "export"): Promise<void> {
    if (this.busy) return;
    this.busy = kind;
    this.note = null;
    try {
      if (kind === "download") await this.download?.();
      else {
        const r = await this.exportCosts?.();
        if (r) this.note = { text: this.tr("diag.exported", { path: r.path, rows: r.rows }), error: false };
      }
    } catch (err) {
      this.note = { text: this.tr("diag.failed", { error: (err as { message?: string })?.message ?? String(err) }), error: true };
    } finally {
      this.busy = null;
    }
  }

  protected override render(): TemplateResult {
    const view = this.view;
    return html`<div class="layout">
      <section class="card tools">
        <h2>${this.tr("diag.title")}</h2>
        <p class="muted">${this.tr("diag.intro")}</p>
        <div class="buttons">
          <button type="button" class="primary" ?disabled=${!view || this.busy !== null} @click=${() => void this.run("download")}>
            ${this.tr(this.busy === "download" ? "diag.busy" : "diag.download")}
          </button>
          ${this.admin
            ? html`<button type="button" class="ghost" ?disabled=${this.busy !== null} @click=${() => void this.run("export")}>
                ${this.tr(this.busy === "export" ? "diag.busy" : "diag.export")}
              </button>`
            : nothing}
        </div>
        ${this.note ? html`<p class=${this.note.error ? "note error" : "note"} role="status">${this.note.text}</p>` : nothing}
        ${view ? this.renderCounters(view) : html`<div class="skeleton"></div>`}
      </section>
      ${this.planCheck ? this.renderCheck(this.planCheck) : nothing} ${view?.profile ? this.renderProfile(view.profile) : nothing}
      <section class="card events" aria-labelledby="events-title">
        <div class="head">
          <h2 id="events-title">${this.tr("diag.events")}</h2>
          <button type="button" class="ghost small" @click=${() => this.refresh?.()}>${this.tr("diag.refresh")}</button>
        </div>
        ${view ? this.renderEvents(view) : html`<div class="skeleton"></div>`}
      </section>
    </div>`;
  }

  private renderCounters(view: EventsView): TemplateResult {
    if (!view.sets.length) return html`<p class="muted">${this.tr("diag.no_sets")}</p>`;
    const n = (v: number | null) => (v === null ? "–" : new Intl.NumberFormat(this.locale).format(v));
    return html`<h3>${this.tr(view.shadow ? "diag.counters_shadow" : "diag.counters")}</h3>
      ${view.shadow ? html`<p class="note">${this.tr("diag.shadow_counts")}</p>` : nothing}
      <table>
        <thead>
          <tr>
            <th scope="col">${this.tr("diag.set")}</th>
            <th scope="col">${this.tr("diag.ram")}</th>
            <th scope="col">${this.tr("diag.flash")}</th>
            <th scope="col">${this.tr("diag.relay")}</th>
            <th scope="col">${this.tr("diag.failed_col")}</th>
          </tr>
        </thead>
        <tbody>
          ${view.sets.map(
            (s) => html`<tr>
                <th scope="row">${s.number}</th>
                <td>${n(s.ram_24h)}</td>
                <td>${n(s.flash_24h)}</td>
                <td>${n(s.relay_24h)}</td>
                <td class=${s.failed_24h ? "bad" : ""}>${n(s.failed_24h)}</td>
              </tr>
              ${s.last_error
                ? html`<tr>
                    <td colspan="5" class="lasterror">${this.tr("diag.last_error", { error: s.last_error })}</td>
                  </tr>`
                : nothing}`,
          )}
        </tbody>
      </table>
      <p class="muted small">${this.tr("diag.counters_note")}</p>`;
  }

  private renderCheck(pc: PlanCheckView): TemplateResult {
    const metrics: CheckMetric[] = ["load", "solar", "import", "export", "cost"];
    const fmt = (m: CheckMetric, v: number, sign = false) => {
      const s = sign && v > 0 ? "+" : v < 0 ? "−" : "";
      const a = Math.abs(v);
      return m === "cost"
        ? `${s}€ ${new Intl.NumberFormat(this.locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(a)}`
        : `${s}${new Intl.NumberFormat(this.locale, { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(a)} kWh`;
    };
    const days = pc.days.filter((d) => d[this.metric]);
    const top = Math.max(0.1, ...days.flatMap((d) => [d[this.metric]?.expected ?? 0, d[this.metric]?.actual ?? 0].map(Math.abs)));
    const dayLabel = (iso: string) =>
      new Intl.DateTimeFormat(this.locale, { weekday: "short", day: "numeric", timeZone: "UTC" }).format(new Date(`${iso}T12:00:00Z`));
    return html`<section class="card check" aria-labelledby="pc-title">
      <h2 id="pc-title">${this.tr("diag.check_title")}</h2>
      <p class="muted">${this.tr("diag.check_intro", { n: pc.summary.days })}</p>
      ${pc.summary.days === 0
        ? html`<p class="note">${this.tr("diag.check_none")}</p>`
        : html`<table class="ctable">
            <thead>
              <tr>
                <th scope="col"></th>
                <th scope="col">${this.tr("diag.check_expected")}</th>
                <th scope="col">${this.tr("diag.check_actual")}</th>
                <th scope="col">${this.tr("diag.check_diff")}</th>
                <th scope="col">${this.tr("diag.check_daily")}</th>
              </tr>
            </thead>
            <tbody>
              ${metrics.map((m) => {
                const r = pc.summary[m];
                if (!r) return nothing;
                const rel = relDiff(r);
                return html`<tr class=${m === this.metric ? "on" : ""} @click=${() => (this.metric = m)}>
                  <th scope="row"><button type="button" class="linkish" aria-pressed=${m === this.metric ? "true" : "false"}>${this.tr(`diag.m_${m}`)}</button></th>
                  <td>${fmt(m, r.expected)}</td>
                  <td>${fmt(m, r.actual)}</td>
                  <td class=${rel !== null && Math.abs(rel) > 0.15 ? "warnc" : ""}>
                    ${fmt(m, r.diff, true)}${rel !== null ? html` <small>(${rel > 0 ? "+" : "−"}${Math.round(Math.abs(rel) * 100)} %)</small>` : nothing}
                  </td>
                  <td>${r.mean_abs_day !== undefined ? fmt(m, r.mean_abs_day) : "–"}</td>
                </tr>`;
              })}
            </tbody>
          </table>
          <h3>${this.tr("diag.check_per_day", { metric: this.tr(`diag.m_${this.metric}`).toLowerCase() })}</h3>
          <div class="cbars" role="img" aria-label=${this.tr("diag.check_per_day", { metric: this.tr(`diag.m_${this.metric}`) })}>
            ${days.map((d) => {
              const r = d[this.metric] as { expected: number; actual: number; diff: number };
              const partial = d.quarters < d.of - 4;
              return html`<div class="cday" title=${`${dayLabel(d.date)}: ${this.tr("diag.check_expected").toLowerCase()} ${fmt(this.metric, r.expected)}, ${this.tr("diag.check_actual").toLowerCase()} ${fmt(this.metric, r.actual)}${partial ? ` (${this.tr("diag.check_partial", { n: d.quarters, of: d.of })})` : ""}`}>
                <div class="cpair">
                  <i class="exp" style=${`height:${(Math.abs(r.expected) / top) * 100}%`}></i>
                  <i class=${partial ? "act part" : "act"} style=${`height:${(Math.abs(r.actual) / top) * 100}%`}></i>
                </div>
                <span>${dayLabel(d.date)}</span>
              </div>`;
            })}
          </div>
          <div class="plegend">
            <span><i class="sw exp"></i>${this.tr("diag.check_expected")}</span>
            <span><i class="sw act"></i>${this.tr("diag.check_actual")}</span>
          </div>`}
    </section>`;
  }

  private renderProfile(p: ProfileView): TemplateResult {
    const d = p[this.dayKind];
    const st = profileStats(d);
    const nf = (v: number, digits = 1) => new Intl.NumberFormat(this.locale, { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v);
    const hasAirco = d.airco.some((v) => v > 0) || p.workday.airco.some((v) => v > 0);
    return html`<section class="card profile" aria-labelledby="profile-title">
      <div class="head">
        <h2 id="profile-title">${this.tr("diag.profile")}</h2>
        <div class="tabs" role="group">
          ${(["workday", "weekend"] as const).map(
            (k) => html`<button type="button" class=${this.dayKind === k ? "on" : ""} aria-pressed=${this.dayKind === k ? "true" : "false"} @click=${() => (this.dayKind = k)}>
              ${this.tr(`diag.${k}`)}
            </button>`,
          )}
        </div>
      </div>
      <p class="muted">${this.tr("diag.profile_source", { source: p.source, hours: p.hours })}</p>
      ${st.learned === 0
        ? html`<p class="note">${this.tr(`diag.profile_empty_${this.dayKind}`, { mean: nf(p.mean, 2) })}</p>`
        : html`<p class="sum">
              ${this.tr("diag.profile_total", { kwh: nf(st.total) })}${hasAirco ? html` · ${this.tr("diag.profile_airco", { kwh: nf(st.aircoTotal) })}` : nothing}
            </p>
            <div class="pchart" role="img" aria-label=${this.tr("diag.profile_total", { kwh: nf(st.total) })}>
              <div class="paxis"><span>${nf(st.top)}</span><span>0</span></div>
              <div class="pbars">
                ${d.house.map((h, i) => {
                  const a = d.airco[i] ?? 0;
                  return html`<div class=${d.counts[i] >= d.min_count ? "pcol" : "pcol none"} title=${this.tr("diag.profile_hour", { hour: i, house: nf(h, 2), airco: nf(a, 2), n: d.counts[i] })}>
                    ${a > 0 ? html`<i class="air" style="height:${(a / st.top) * 100}%"></i>` : nothing}
                    <i class="house" style="height:${(h / st.top) * 100}%"></i>
                  </div>`;
                })}
              </div>
              <div class="pticks">${[0, 6, 12, 18, 23].map((h) => html`<span style="left:${((h + 0.5) / 24) * 100}%">${String(h).padStart(2, "0")}</span>`)}</div>
            </div>
            <div class="plegend">
              <span><i class="sw house"></i>${this.tr("diag.profile_house")}</span>
              ${hasAirco ? html`<span><i class="sw air"></i>${this.tr("diag.profile_airco_legend")}</span>` : nothing}
              <span><i class="sw house faint"></i>${this.tr("diag.profile_learned", { n: st.learned, mean: nf(p.mean, 2) })}</span>
            </div>`}
    </section>`;
  }

  private renderEvents(view: EventsView): TemplateResult {
    if (!view.events.length) return html`<p class="muted">${this.tr("diag.no_events")}</p>`;
    const nowIso = new Date().toISOString();
    return html`<ol>
      ${view.events.map((e) => {
        const kind = eventKind(e);
        const when = sameDay(e.time, nowIso, this.timeZone)
          ? clock(e.time, this.locale, this.timeZone)
          : `${day(e.time, this.locale, this.timeZone)} ${clock(e.time, this.locale, this.timeZone)}`;
        return html`<li>
          <time datetime=${e.time}>${when}</time>
          <span class="kind k-${kind}">${this.tr(`diag.kind.${kind}`)}</span>
          <span class="text">${eventText(e, this.uiLang, this.locale)}</span>
        </li>`;
      })}
    </ol>`;
  }

  static override styles = css`
    :host {
      display: block;
      color: var(--z-text);
      font-family: var(--z-font);
    }
    .layout {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: flex-start;
    }
    .card {
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 16px;
      padding: 20px 24px;
      min-width: 0;
      box-sizing: border-box;
    }
    .tools {
      flex: 1 1 320px;
      max-width: 440px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .events {
      flex: 999 1 480px;
    }
    .check {
      flex: 999 1 480px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .ctable td,
    .ctable th {
      padding: 8px 6px;
    }
    .ctable tbody tr {
      cursor: pointer;
    }
    .ctable tr.on {
      background: var(--z-info-bg);
    }
    .ctable small {
      color: var(--z-muted);
      font-weight: 400;
    }
    .warnc {
      color: var(--z-warn-text);
      font-weight: 700;
    }
    .linkish {
      min-height: 0;
      padding: 0;
      border: 0;
      background: none;
      color: inherit;
      font: inherit;
      font-weight: 600;
      cursor: pointer;
    }
    .cbars {
      display: flex;
      gap: 6px;
      height: 130px;
      align-items: stretch;
    }
    .cday {
      flex: 1 1 0;
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
    }
    .cday span {
      font-size: 10px;
      color: var(--z-muted);
      text-align: center;
      white-space: nowrap;
      overflow: hidden;
    }
    .cpair {
      flex: 1;
      display: flex;
      align-items: flex-end;
      gap: 2px;
      border-bottom: 1px solid var(--z-border);
    }
    .cpair i {
      flex: 1;
      border-radius: 2px 2px 0 0;
    }
    i.exp,
    .sw.exp {
      background: transparent;
      border: 2px dashed var(--z-muted);
      border-bottom: 0;
      box-sizing: border-box;
    }
    i.act,
    .sw.act {
      background: var(--z-charge);
    }
    i.act.part {
      opacity: 0.45;
    }
    .profile {
      flex: 999 1 480px;
      display: flex;
      flex-direction: column;
      gap: 10px;
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
      font-weight: 500;
    }
    .tabs button.on {
      background: var(--z-text);
      color: var(--z-on-text);
      font-weight: 600;
    }
    .sum {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
    }
    .pchart {
      position: relative;
      height: 150px;
      margin: 6px 0 28px 40px;
    }
    .paxis {
      position: absolute;
      left: -40px;
      top: -6px;
      bottom: -6px;
      width: 34px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      align-items: flex-end;
      font-size: 11px;
      color: var(--z-muted);
    }
    .pbars {
      display: flex;
      align-items: flex-end;
      gap: 3px;
      height: 100%;
      border-bottom: 1px solid var(--z-border);
    }
    .pcol {
      flex: 1 1 0;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
    }
    .pcol i {
      display: block;
      width: 100%;
    }
    .pcol .house {
      background: var(--z-charge);
      border-radius: 0 0 2px 2px;
    }
    .pcol .air {
      background: repeating-linear-gradient(45deg, var(--z-deliver) 0 2px, transparent 2px 5px);
      border: 1px solid var(--z-deliver);
      border-bottom: 0;
      box-sizing: border-box;
      border-radius: 2px 2px 0 0;
    }
    .pcol.none i {
      opacity: 0.35;
    }
    .pticks {
      position: absolute;
      left: 0;
      right: 0;
      bottom: -18px;
      font-size: 11px;
      color: var(--z-muted);
    }
    .pticks span {
      position: absolute;
      transform: translateX(-50%);
    }
    .plegend {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 14px;
      font-size: 12px;
      color: var(--z-muted);
    }
    .plegend span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .sw {
      width: 12px;
      height: 12px;
      border-radius: 3px;
      display: inline-block;
    }
    .sw.house {
      background: var(--z-charge);
    }
    .sw.faint {
      opacity: 0.35;
    }
    .sw.air {
      background: repeating-linear-gradient(45deg, var(--z-deliver) 0 2px, transparent 2px 4px);
      border: 1px solid var(--z-deliver);
      box-sizing: border-box;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 20px;
    }
    h3 {
      margin: 8px 0 0;
      font-size: 14px;
    }
    .head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
    }
    .muted {
      margin: 0;
      font-size: 13px;
      color: var(--z-muted);
      line-height: 1.5;
    }
    .small {
      font-size: 12px;
    }
    .buttons {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    button {
      min-height: 44px;
      padding: 0 16px;
      border-radius: 10px;
      font: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    button.small {
      min-height: 36px;
      padding: 0 12px;
      font-size: 13px;
    }
    .primary {
      border: 0;
      background: var(--z-text);
      color: var(--z-on-text);
    }
    .ghost {
      border: 1px solid var(--z-border);
      background: transparent;
      color: var(--z-text);
    }
    button:focus-visible {
      outline: 2px solid var(--z-charge);
      outline-offset: 2px;
    }
    :disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .note {
      margin: 0;
      padding: 10px 14px;
      border-radius: 10px;
      background: var(--z-info-bg);
      font-size: 13px;
      overflow-wrap: anywhere;
    }
    .note.error {
      color: var(--z-bad-text, #b3261e);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      font-variant-numeric: tabular-nums;
    }
    th,
    td {
      padding: 6px 4px;
      text-align: right;
      border-bottom: 1px solid var(--z-border);
    }
    thead th {
      color: var(--z-muted);
      font-weight: 500;
      font-size: 12px;
    }
    th:first-child {
      text-align: left;
    }
    td.bad {
      color: var(--z-bad-text, #b3261e);
      font-weight: 700;
    }
    .lasterror {
      text-align: left;
      color: var(--z-muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    ol {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    li {
      display: grid;
      grid-template-columns: auto auto 1fr;
      gap: 4px 12px;
      align-items: baseline;
      padding: 10px 0;
      border-top: 1px solid var(--z-border);
      font-size: 14px;
      line-height: 1.45;
    }
    time {
      color: var(--z-muted);
      font-variant-numeric: tabular-nums;
      font-size: 13px;
      white-space: nowrap;
    }
    .kind {
      font-size: 11px;
      padding: 1px 8px;
      border-radius: 999px;
      background: var(--z-info-bg);
      white-space: nowrap;
    }
    .k-warning {
      background: var(--z-warn-bg, var(--z-info-bg));
      color: var(--z-warn-text, var(--z-text));
    }
    .k-airco {
      background: var(--z-deliver-bg, var(--z-info-bg));
    }
    .skeleton {
      min-height: 120px;
      border-radius: 10px;
      background: var(--z-info-bg);
    }
    @media (max-width: 700px) {
      .card {
        padding: 16px;
      }
      .tools {
        max-width: none;
      }
      li {
        grid-template-columns: auto 1fr;
      }
      li .text {
        grid-column: 1 / -1;
      }
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "zephyr-diagnostics": ZephyrDiagnostics;
  }
}
