// Screen "Diagnose" (SPEC-ui §4.5, UI-8): download, cost export, counters, recent events.
import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { eventKind, eventText, type EventsView } from "./diag";
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

  @state() private busy: "download" | "export" | null = null;
  @state() private note: { text: string; error: boolean } | null = null;

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
