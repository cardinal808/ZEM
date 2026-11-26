// Screen "Instellingen" (SPEC-ui §4.4, UI-6: reading; changing follows in UI-7).
import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { t, type Lang } from "./i18n";

export interface SourceStatus {
  state: "unset" | "missing" | "ok";
  entities?: string[];
  interval_s?: number | null;
  price_slots?: number | null;
}

export interface SettingField {
  key: string;
  kind: "number" | "bool" | "select" | "entity" | "entities";
  default: unknown;
  unit: string | null;
  min: number | null;
  max: number | null;
  step: number | string | null;
  options: string[];
  device_class: string | null;
  optional: boolean;
  reload: boolean;
  tariff: boolean;
  value: unknown;
  modified: boolean;
  choices?: { value: string; label: string | null }[];
  active?: boolean;
  in_use?: number | null;
  status?: SourceStatus | null;
}

export interface SettingsGroup {
  key: string;
  fields: SettingField[];
  modified: number;
}

export interface SettingsView {
  groups: SettingsGroup[];
  supplier: string;
  tariffs_source: string | null;
  can_edit: boolean;
}

/** Number with as many decimals as the step allows (at most 5), in the user's notation. */
export function formatNumber(value: number, step: number | string | null, locale: string): string {
  const digits = typeof step === "number" && step < 1 ? Math.min(5, Math.max(0, Math.ceil(-Math.log10(step) - 1e-9))) : step === "any" ? 5 : 0;
  return new Intl.NumberFormat(locale, { minimumFractionDigits: 0, maximumFractionDigits: digits }).format(value);
}

@customElement("zephyr-settings")
export class ZephyrSettings extends LitElement {
  @property({ attribute: false }) view?: SettingsView;
  @property({ attribute: false }) uiLang: Lang = "en";
  @property() locale = "en";
  @property({ attribute: false }) friendlyName: (entityId: string) => string | undefined = () => undefined;

  @state() private group = 0;
  @state() private tip: string | null = null;

  private tr(key: string, params: Record<string, string | number> = {}): string {
    return t(this.uiLang, key, params);
  }

  private label(key: string): string {
    return this.tr(`settings.fields.${key}.label`);
  }

  protected override render(): TemplateResult {
    const view = this.view;
    if (!view) return html`<div class="card skeleton" aria-hidden="true"></div>`;
    const index = Math.min(this.group, view.groups.length - 1);
    const current = view.groups[index];
    return html`<div class="layout">
      <nav class="card groups" aria-label=${this.tr("settings.title")}>
        ${view.groups.map(
          (g, i) => html`<button
            type="button"
            class=${i === index ? "on" : ""}
            aria-current=${i === index ? "true" : "false"}
            @click=${() => {
              this.group = i;
              this.tip = null;
            }}
          >
            <span>${this.tr(`settings.groups.${g.key}`)}</span>
            ${g.modified ? html`<span class="badge">${this.tr("settings.modified_n", { n: g.modified })}</span>` : nothing}
          </button>`,
        )}
      </nav>
      <section class="card fields" aria-labelledby="group-title">
        <div class="head">
          <h2 id="group-title">${this.tr(`settings.groups.${current.key}`)}</h2>
        </div>
        <p class="note">
          ${view.can_edit ? this.tr("settings.coming") : this.tr("settings.readonly")}
          ${view.can_edit ? html`<a href="/config/integrations/integration/zephyr">${this.tr("settings.open_options")}</a>` : nothing}
        </p>
        ${current.key === "sources" ? html`<p class="muted">${this.tr("settings.reload_note")}</p>` : nothing}
        ${current.key === "tariffs" && view.supplier !== "own"
          ? html`<p class="muted">${this.tr("settings.supplier_note", { source: view.tariffs_source ?? "–" })}</p>`
          : nothing}
        <ul>
          ${current.fields.map((f) => this.renderField(f))}
        </ul>
      </section>
    </div>`;
  }

  private renderField(f: SettingField): TemplateResult {
    const open = this.tip === f.key;
    const id = `f-${f.key}`;
    return html`<li class=${f.active === false ? "inactive" : ""}>
      <div class="text">
        <div class="labelrow">
          <label for=${id}>${this.label(f.key)}</label>
          <button
            type="button"
            class=${open ? "info on" : "info"}
            aria-expanded=${open ? "true" : "false"}
            aria-label=${this.tr("settings.more", { label: this.label(f.key) })}
            @click=${() => (this.tip = open ? null : f.key)}
          >
            i
          </button>
          ${f.modified ? html`<span class="dot" title=${this.defaultText(f)}></span>` : nothing}
        </div>
        <span class="help">${this.tr(`settings.fields.${f.key}.help`)}</span>
        ${open ? html`<div class="more" role="note">${this.tr(`settings.fields.${f.key}.more`)}</div>` : nothing}
        ${this.meta(f)}
      </div>
      <div class="control">${this.control(f, id)}</div>
    </li>`;
  }

  private defaultText(f: SettingField): string {
    return this.tr("settings.default", { value: this.display(f, f.default) });
  }

  private display(f: SettingField, value: unknown): string {
    if (value === null || value === undefined || value === "" || (Array.isArray(value) && !value.length)) return this.tr("settings.none");
    if (f.kind === "bool") return this.tr(value ? "settings.yes" : "settings.no");
    if (f.kind === "number") return `${formatNumber(Number(value), f.step, this.locale)}${f.unit ? ` ${f.unit}` : ""}`;
    if (f.kind === "select") {
      if (f.key === "tariff_supplier") return f.choices?.find((c) => c.value === value)?.label ?? this.tr("settings.own");
      if (Array.isArray(value)) return (value as string[]).map((v) => this.tr(`settings.options.${v}`)).join(", ");
      return this.tr(`settings.options.${String(value)}`);
    }
    const ids = Array.isArray(value) ? (value as string[]) : [String(value)];
    return ids.map((e) => this.friendlyName(e) ?? e).join(", ");
  }

  private meta(f: SettingField): TemplateResult | typeof nothing {
    const parts: string[] = [];
    if (f.modified) parts.push(this.defaultText(f));
    if (f.tariff && f.active === false && f.in_use !== undefined && f.in_use !== null)
      parts.push(this.tr("settings.in_use", { value: this.display(f, f.in_use) }));
    const st = f.status;
    if (st) {
      if (st.state === "unset") parts.push(this.tr("settings.status.unset"));
      else if (st.state === "missing") parts.push(this.tr("settings.status.missing", { entities: (st.entities ?? []).join(", ") }));
      else if (st.interval_s != null) parts.push(this.tr("settings.status.interval", { s: formatNumber(st.interval_s, 0.1, this.locale) }));
      else if (st.price_slots != null) parts.push(this.tr("settings.status.slots", { n: st.price_slots }));
      else parts.push(this.tr("settings.status.ok"));
    }
    if (!parts.length) return nothing;
    const cls = st?.state === "missing" ? "meta warn" : "meta";
    return html`<span class=${cls}>${parts.join(" · ")}</span>`;
  }

  private control(f: SettingField, id: string): TemplateResult {
    // UI-6: shown, not yet editable (UI-7 enables them for administrators).
    const disabled = true;
    switch (f.kind) {
      case "bool":
        return html`<button id=${id} type="button" role="switch" class="switch" aria-checked=${f.value ? "true" : "false"} ?disabled=${disabled}>
          <span></span>
        </button>`;
      case "number":
        return html`<span class="num">
          <input
            id=${id}
            type="text"
            inputmode="decimal"
            .value=${f.value === null || f.value === undefined ? "" : formatNumber(Number(f.value), f.step, this.locale)}
            ?disabled=${disabled}
          />${f.unit ? html`<span class="unit">${f.unit}</span>` : nothing}
        </span>`;
      case "select":
        return html`<select id=${id} ?disabled=${disabled}>
          ${(f.choices ?? f.options.map((o) => ({ value: o, label: null }))).map(
            (c) => html`<option value=${c.value} ?selected=${c.value === f.value}>
              ${c.label ?? (f.key === "tariff_supplier" ? this.tr("settings.own") : this.tr(`settings.options.${c.value}`))}
            </option>`,
          )}
        </select>`;
      default:
        return html`<output id=${id} class="entity">${this.display(f, f.value)}</output>`;
    }
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
      border-radius: 16px;
      padding: 20px 24px;
      min-width: 0;
    }
    .skeleton {
      min-height: 300px;
    }
    .layout {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: flex-start;
    }
    .groups {
      flex: 1 1 240px;
      max-width: 300px;
      padding: 10px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .groups button {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      width: 100%;
      min-height: 44px;
      padding: 10px 14px;
      border: 0;
      border-radius: 10px;
      background: transparent;
      color: var(--z-text);
      font: inherit;
      font-size: 14px;
      text-align: left;
      cursor: pointer;
    }
    .groups button.on {
      background: var(--z-text);
      color: var(--z-on-text);
      font-weight: 600;
    }
    .groups button:focus-visible,
    .info:focus-visible {
      outline: 2px solid var(--z-charge);
      outline-offset: 2px;
    }
    .badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 999px;
      background: var(--z-info-bg);
      color: var(--z-text);
      white-space: nowrap;
    }
    .fields {
      flex: 999 1 520px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 20px;
    }
    .note {
      margin: 0;
      padding: 10px 14px;
      border-radius: 10px;
      background: var(--z-info-bg);
      font-size: 14px;
      line-height: 1.5;
    }
    .note a {
      margin-left: 6px;
      color: var(--z-charge);
      font-weight: 600;
    }
    .muted {
      margin: 0;
      font-size: 13px;
      color: var(--z-muted);
      line-height: 1.5;
    }
    ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    li {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: flex-start;
      gap: 10px 24px;
      padding: 16px 0;
      border-top: 1px solid var(--z-border);
    }
    li.inactive .control {
      opacity: 0.5;
    }
    .text {
      flex: 1 1 300px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
    }
    .labelrow {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    label {
      font-weight: 600;
      font-size: 15px;
    }
    .info {
      width: 24px;
      height: 24px;
      padding: 0;
      border-radius: 50%;
      border: 1px solid var(--z-charge);
      background: var(--z-card);
      color: var(--z-charge);
      font: inherit;
      font-size: 13px;
      font-weight: 700;
      font-style: italic;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .info.on {
      background: var(--z-charge);
      color: #fff;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--z-deliver);
    }
    .help {
      font-size: 13px;
      line-height: 1.5;
      color: var(--z-muted);
    }
    .more {
      margin-top: 6px;
      padding: 12px 14px;
      border-radius: 10px;
      background: var(--z-info-bg);
      font-size: 13px;
      line-height: 1.6;
      white-space: pre-line;
      max-width: 640px;
    }
    .meta {
      font-size: 12px;
      color: var(--z-muted);
    }
    .meta.warn {
      color: var(--z-warn-text);
    }
    .control {
      flex: 0 1 auto;
      display: flex;
      align-items: center;
      min-height: 44px;
    }
    .num {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    input,
    select {
      min-height: 40px;
      box-sizing: border-box;
      padding: 0 10px;
      border: 1px solid var(--z-border);
      border-radius: 8px;
      background: var(--z-bg);
      color: var(--z-text);
      font: inherit;
      font-size: 14px;
    }
    input {
      width: 110px;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }
    select {
      max-width: 280px;
    }
    .unit {
      font-size: 13px;
      color: var(--z-muted);
      min-width: 44px;
    }
    .entity {
      font-size: 14px;
      max-width: 320px;
      overflow-wrap: anywhere;
      text-align: right;
    }
    .switch {
      width: 48px;
      height: 28px;
      padding: 0;
      border-radius: 999px;
      border: 0;
      background: var(--z-track);
      position: relative;
      cursor: pointer;
    }
    .switch span {
      position: absolute;
      top: 3px;
      left: 3px;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: var(--z-card);
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
      transition: left 0.15s;
    }
    .switch[aria-checked="true"] {
      background: var(--z-charge);
    }
    .switch[aria-checked="true"] span {
      left: 23px;
    }
    :disabled {
      cursor: not-allowed;
    }
    @media (max-width: 700px) {
      .card {
        padding: 16px;
      }
      .groups {
        max-width: none;
        flex-direction: row;
        flex-wrap: wrap;
      }
      .groups button {
        width: auto;
      }
      .control {
        width: 100%;
      }
    }
  `;
}

declare global {
  interface HTMLElementTagNameMap {
    "zephyr-settings": ZephyrSettings;
  }
}
