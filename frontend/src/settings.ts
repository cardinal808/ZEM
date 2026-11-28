// Screen "Instellingen" (SPEC-ui §4.4; UI-6 reading, UI-7 changing).
// Live fields save at once; sources and corrections are collected and saved together, because ZEPHYR restarts for them.
import type { AppliancesView } from "./appliances";
import "./house-editor";
import type { HouseDevice, HousePicture } from "./stroom";

interface HouseDraft {
  floor: string;
  shown: boolean;
  from: string;
  until: string;
  after: boolean;
}
import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { t, type Lang } from "./i18n";
import {
  choiceLabel,
  searchChoices,
  wrongDomain,
  entityChoices,
  parseNumber,
  resolveEntity,
  sameValue,
  stepInterval,
  toggleChoice,
  type EntityChoice,
  type SetResult,
} from "./settings-edit";

export interface SourceStatus {
  state: "unset" | "missing" | "ok" | "unavailable";
  entities?: string[];
  interval_s?: number | null;
  price_slots?: number | null;
  mode?: string;
  action?: string | null;
  no_step?: boolean;
  step_kwh?: number | null;
  step_interval_s?: number | null;
}

type States = Record<string, { attributes?: Record<string, unknown> }>;
export type SaveSettings = (
  changes: Record<string, unknown>,
  reset: string[],
) => Promise<SetResult>;
const RESET = Symbol("reset");

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
  domain: string;
  multiple: boolean;
  value: unknown;
  modified: boolean;
  choices?: { value: string; label: string | null }[];
  active?: boolean;
  in_use?: number | null;
  status?: SourceStatus | null;
  show_if?: { key: string; values: string[] } | null;
  /** Subtab within a long group (0.8.85). */
  section?: string | null;
}

export interface SettingsGroup {
  key: string;
  fields: SettingField[];
  modified: number;
}

export interface VacationView {
  active: boolean;
  /** Switched on by hand (else: on by itself because nobody is home). */
  manual: boolean;
  auto: boolean;
  until: string | null;
  started: string | null;
  entities?: { switch: string | null; until: string | null };
}

/**
 * A field with a condition is only shown when the other field (as entered, before saving) has one
 * of the values; "*" means filled in. Hidden values are kept, not cleared.
 */
export function fieldVisible(f: SettingField, valueOf: (key: string) => unknown): boolean {
  if (!f.show_if) return true;
  const v = valueOf(f.show_if.key);
  if (f.show_if.values.includes("*"))
    return Array.isArray(v) ? v.length > 0 : v !== null && v !== undefined && v !== "";
  return typeof v === "string" && f.show_if.values.includes(v);
}

/** The subtabs of a group, in the order of their first field; empty when the group has none. */
export function groupSections(fields: SettingField[]): string[] {
  const out: string[] = [];
  for (const f of fields) if (f.section && !out.includes(f.section)) out.push(f.section);
  return out;
}

/** The changes to save: hidden fields are left out (they are not used, so they never block saving). */
export function draftToSave(
  draft: Record<string, unknown>,
  visible: (key: string) => boolean,
): Record<string, unknown> {
  return Object.fromEntries(Object.entries(draft).filter(([k]) => visible(k)));
}

export interface SettingsView {
  groups: SettingsGroup[];
  house?: HouseDevice[];
  house_picture?: HousePicture | null;
  vacation?: VacationView | null;
  supplier: string;
  tariffs_source: string | null;
  can_edit: boolean;
}

/** Number with as many decimals as the step allows (at most 5), in the user's notation. */
export function formatNumber(
  value: number,
  step: number | string | null,
  locale: string,
): string {
  const digits =
    typeof step === "number" && step < 1
      ? Math.min(5, Math.max(0, Math.ceil(-Math.log10(step) - 1e-9)))
      : step === "any"
        ? 5
        : 0;
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  }).format(value);
}

/**
 * The value in the input. A tariff field that the supplier's table fills shows the amount in use
 * (greyed out), not the own value behind it (0.8.74).
 */
export function controlValue(f: SettingField, shown: unknown): unknown {
  if (f.tariff && f.active === false && f.in_use !== undefined && f.in_use !== null) return f.in_use;
  return shown;
}

@customElement("zephyr-settings")
export class ZephyrSettings extends LitElement {
  @property({ attribute: false }) view?: SettingsView;
  @property({ attribute: false }) uiLang: Lang = "en";
  @property() locale = "en";
  @property({ attribute: false }) friendlyName: (
    entityId: string,
  ) => string | undefined = () => undefined;
  @property({ attribute: false }) states?: States;
  @property({ attribute: false }) save?: SaveSettings;

  @state() private group = 0;
  /** Open this group once (set from a link elsewhere in the panel). */
  @property({ attribute: false }) openGroup: string | null = null;
  private openedFor: string | null = null;

  private applyOpenGroup(changed: Map<string, unknown>): void {
    if (
      (changed.has("openGroup") || changed.has("view")) &&
      this.openGroup &&
      this.view &&
      this.openedFor !== this.openGroup
    ) {
      // "group" or "group:section" (a link to a subtab, e.g. planner:curtail).
      const [key, section] = this.openGroup.split(":");
      const i = this.view.groups.findIndex((g) => g.key === key);
      if (i >= 0) {
        this.group = i;
        if (section) this.sectionOf = { ...this.sectionOf, [key]: section };
        this.openedFor = this.openGroup;
      }
    }
  }
  @state() private tip: string | null = null;
  /** Chosen subtab per group (kept while switching groups). */
  @state() private sectionOf: Record<string, string> = {};
  /** Unsaved changes of fields that need a restart (value, or RESET for the standard value). */
  @state() private draft: Record<string, unknown> = {};
  @state() private errors: Record<string, string> = {};
  @state() private busy = false;
  @state() private saved: string | null = null;
  @state() private restarting = false;
  private savedTimer?: number;

  protected override willUpdate(changed: Map<string, unknown>): void {
    // A fresh view after a restart: the drafts are saved, the note can go.
    if (changed.has("view") && changed.get("view") !== undefined)
      this.restarting = false;
    this.applyOpenGroup(changed);
  }

  private get editable(): boolean {
    return Boolean(this.view?.can_edit && this.save);
  }

  private shown(f: SettingField): unknown {
    if (!(f.key in this.draft)) return f.value;
    const v = this.draft[f.key];
    return v === RESET ? f.default : v;
  }

  private isModified(f: SettingField): boolean {
    // A chosen entity is a choice, not a change from a standard: no dot, no "standard: empty".
    if (f.kind === "entity" || f.kind === "entities") return false;
    if (!(f.key in this.draft)) return f.modified;
    const v = this.draft[f.key];
    return (
      v !== RESET &&
      !sameValue(v, f.default) &&
      !(f.optional && (v === null || v === ""))
    );
  }

  private change(f: SettingField, value: unknown): void {
    const { [f.key]: _old, ...errors } = this.errors;
    this.errors = errors;
    if (f.reload) {
      const { [f.key]: _prev, ...rest } = this.draft;
      this.draft = sameValue(value, f.value)
        ? rest
        : { ...rest, [f.key]: value };
      return;
    }
    if (sameValue(value, f.value)) return;
    void this.send({ [f.key]: value }, [], f.key);
  }

  private reset(f: SettingField): void {
    if (f.reload) {
      this.draft = { ...this.draft, [f.key]: RESET };
      return;
    }
    void this.send({}, [f.key], f.key);
  }

  /** An error on another subtab: open that subtab, so the message is seen. */
  private showErrorSection(keys: string[]): void {
    for (const key of keys) {
      const f = this.fieldByKey(key);
      const g = this.view?.groups.find((x) => x.fields.some((y) => y.key === key));
      if (f?.section && g) {
        this.sectionOf = { ...this.sectionOf, [g.key]: f.section };
        return;
      }
    }
  }

  private localError(f: SettingField, code: string): void {
    this.errors = { ...this.errors, [f.key]: code };
    this.requestUpdate();
  }

  private async send(
    changes: Record<string, unknown>,
    reset: string[],
    key: string | null,
  ): Promise<boolean> {
    if (!this.save || this.busy) return false;
    this.busy = true;
    try {
      const result = await this.save(changes, reset);
      if (!result.ok) {
        this.errors = {
          ...this.errors,
          ...(result.errors ?? { base: "failed" }),
        };
        this.showErrorSection(Object.keys(result.errors ?? {}));
        return false;
      }
      if (key) {
        this.saved = key;
        window.clearTimeout(this.savedTimer);
        this.savedTimer = window.setTimeout(() => (this.saved = null), 2500);
      }
      return true;
    } catch {
      this.errors = { ...this.errors, [key ?? "base"]: "failed" };
      return false;
    } finally {
      this.busy = false;
    }
  }

  private async saveDraft(): Promise<void> {
    const changes: Record<string, unknown> = {};
    const reset: string[] = [];
    const visible = (key: string) => {
      const f = this.fieldByKey(key);
      return !f || this.visible(f);
    };
    for (const [key, value] of Object.entries(draftToSave(this.draft, visible))) {
      if (value === RESET) reset.push(key);
      else changes[key] = value;
    }
    const { base: _base, ...errors } = this.errors;
    this.errors = errors;
    if (await this.send(changes, reset, null)) {
      this.draft = {};
      this.restarting = true;
    }
  }

  private cancelDraft(): void {
    this.draft = {};
    this.errors = {};
  }

  private tr(
    key: string,
    params: Record<string, string | number> = {},
  ): string {
    return t(this.uiLang, key, params);
  }

  private label(key: string): string {
    return this.tr(`settings.fields.${key}.label`);
  }

  protected override render(): TemplateResult {
    const view = this.view;
    if (!view)
      return html`<div class="card skeleton" aria-hidden="true"></div>`;
    const index = Math.min(this.group, view.groups.length - 1);
    const current = view.groups[index];
    return html`<div class="layout">
      <nav class="card groups" aria-label=${this.tr("settings.title")}>
        ${view.groups.map(
          (g, i) =>
            html`<button
              type="button"
              class=${i === index ? "on" : ""}
              aria-current=${i === index ? "true" : "false"}
              @click=${() => {
                this.group = i;
                this.tip = null;
              }}
            >
              <span>${this.tr(`settings.groups.${g.key}`)}</span>
              ${this.groupSub(g)}

            </button>`,
        )}
      </nav>
      <section class="card fields" aria-labelledby="group-title">
        <div class="head">
          <h2 id="group-title">${this.tr(`settings.groups.${current.key}`)}</h2>
        </div>
        ${view.can_edit ? nothing : html`<p class="note">${this.tr("settings.readonly")}</p>`}
        ${this.restarting ? html`<p class="note" role="status">${this.tr("settings.restarting")}</p>` : nothing}
        ${current.fields.some((f) => f.reload) ? html`<p class="muted">${this.tr("settings.reload_note")}</p>` : nothing}
        ${
          current.key === "tariffs" && view.supplier !== "own"
            ? html`<p class="muted">
                ${this.tr("settings.supplier_note", { source: view.tariffs_source ?? "–" })}
              </p>`
            : nothing
        }
        ${current.key === "vacation" && view.vacation ? this.renderVacation(view.vacation, view.can_edit) : nothing}
        ${
          current.key === "house"
            ? html`<zephyr-house-editor
                .picture=${view.house_picture ?? null}
                .canEdit=${view.can_edit}
                .uiLang=${this.uiLang}
                .call=${this.houseCall}
                .sign=${this.sign}
                .changed=${this.reload}
              ></zephyr-house-editor>`
            : nothing
        }
        ${current.key === "house" ? this.renderHouse(view.house ?? [], view.can_edit) : nothing}
        ${this.renderSections(current)}
        <ul>
          ${this.sectionFields(current).map((f) => this.renderField(f))}
        </ul>
        ${this.renderBar()}
      </section>
    </div>`;
  }

  private activeSection(g: SettingsGroup): string | null {
    const all = groupSections(g.fields);
    if (!all.length) return null;
    const chosen = this.sectionOf[g.key];
    return chosen && all.includes(chosen) ? chosen : all[0];
  }

  private sectionFields(g: SettingsGroup): SettingField[] {
    const active = this.activeSection(g);
    return active ? g.fields.filter((f) => f.section === active) : g.fields;
  }

  /** Under the group name in the menu: its subtabs, or a short line from the translations. */
  private groupSub(g: SettingsGroup): TemplateResult | typeof nothing {
    const sections = groupSections(g.fields);
    const text = sections.length
      ? sections.map((s) => this.tr(`settings.sections.${s}`).toLowerCase()).join(" · ")
      : this.tr(`settings.group_sub.${g.key}`);
    return text && text !== `settings.group_sub.${g.key}` ? html`<small>${text}</small>` : nothing;
  }

  private renderSections(g: SettingsGroup): TemplateResult | typeof nothing {
    const sections = groupSections(g.fields);
    if (sections.length < 2) return nothing;
    const active = this.activeSection(g);
    return html`<div class="subtabs" role="tablist" aria-label=${this.tr(`settings.groups.${g.key}`)}>
      ${sections.map((s) => {
        const changed = g.fields.some((f) => f.section === s && (this.isModified(f) || f.key in this.draft));
        return html`<button
          type="button"
          role="tab"
          aria-selected=${s === active ? "true" : "false"}
          class=${s === active ? "on" : ""}
          @click=${() => {
            this.sectionOf = { ...this.sectionOf, [g.key]: s };
            this.tip = null;
          }}
        >
          ${this.tr(`settings.sections.${s}`)}${changed ? html`<i class="dot" aria-hidden="true"></i>` : nothing}
        </button>`;
      })}
    </div>`;
  }

  /** For the own house picture: a websocket call, a signed URL, and loading the settings again. */
  @property({ attribute: false }) houseCall?: (msg: Record<string, unknown>) => Promise<unknown>;
  @property({ attribute: false }) sign?: (path: string) => Promise<string>;
  @property({ attribute: false }) reload?: () => Promise<void>;
  @property({ attribute: false }) saveHouse?: (
    floors: Record<string, string>,
    hidden: string[],
  ) => Promise<void>;
  @state() private houseDraft: Record<string, HouseDraft> | null = null;
  @property({ attribute: false }) appliances?: AppliancesView;
  @property({ attribute: false }) saveAppliances?: (
    updates: Record<string, unknown>[],
  ) => Promise<void>;

  private renderHouse(
    devices: HouseDevice[],
    canEdit: boolean,
  ): TemplateResult {
    if (!devices.length)
      return html`<p class="muted">${this.tr("stroom.devices_hint")}</p>`;
    const appl = new Map(
      (this.appliances?.appliances ?? []).map((x) => [x.id, x]),
    );
    const hm = (v: string | null | undefined): string => (v ?? "").slice(0, 5);
    const initial = (d: HouseDevice): HouseDraft => {
      const x = appl.get(d.id);
      return {
        floor: d.floor,
        shown: d.shown,
        from: hm(x?.window.from),
        until: hm(x?.window.until),
        after: !!x?.after_washer,
      };
    };
    const draft: Record<string, HouseDraft> =
      this.houseDraft ??
      Object.fromEntries(devices.map((d) => [d.id, initial(d)]));
    const set = (id: string, patch: Partial<HouseDraft>) => {
      this.houseDraft = { ...draft, [id]: { ...draft[id], ...patch } };
    };
    const diff = (d: HouseDevice, k: keyof HouseDraft) =>
      draft[d.id][k] !== initial(d)[k];
    const changed = devices.some((d) =>
      (Object.keys(draft[d.id]) as (keyof HouseDraft)[]).some((k) =>
        diff(d, k),
      ),
    );
    const floors = ["attic", "first", "ground", "shed", "outside"];
    const save = async () => {
      const updates = devices
        .filter(
          (d) =>
            appl.has(d.id) &&
            (diff(d, "from") || diff(d, "until") || diff(d, "after")),
        )
        .map((d) => ({
          id: d.id,
          window_from: draft[d.id].from,
          window_until: draft[d.id].until || "20:00",
          ...(appl.get(d.id)?.kind.startsWith("dryer")
            ? { after_washer: draft[d.id].after }
            : {}),
        }));
      if (devices.some((d) => diff(d, "floor") || diff(d, "shown")))
        await this.saveHouse?.(
          Object.fromEntries(devices.map((d) => [d.id, draft[d.id].floor])),
          devices.filter((d) => !draft[d.id].shown).map((d) => d.id),
        );
      if (updates.length) await this.saveAppliances?.(updates);
      this.houseDraft = null;
    };
    return html`<p class="muted">${this.tr("settings.house_note")}</p>
      <ul class="house">
        ${devices.map((d) => {
          const x = appl.get(d.id);
          const dr = draft[d.id];
          return html`<li>
            <div class="hname">
              <b>${d.name ?? this.tr(`stroom.kind_${d.kind}`)}</b>
              <small
                >${
                  x
                    ? x.profile === "learned"
                      ? this.tr("settings.appl_learned", { n: x.runs_seen })
                      : this.tr("settings.appl_default")
                    : this.tr("settings.appl_airco")
                }</small
              >
            </div>
            <div class="hfields">
              ${
                x
                  ? html`<label
                        >${this.tr("settings.appl_from")}<input
                          type="time"
                          .value=${dr.from}
                          ?disabled=${!canEdit}
                          @input=${(e: Event) => set(d.id, { from: (e.target as HTMLInputElement).value })}
                      /></label>
                      <label
                        >${this.tr("settings.appl_until")}<input
                          type="time"
                          .value=${dr.until}
                          ?disabled=${!canEdit}
                          @input=${(e: Event) => set(d.id, { until: (e.target as HTMLInputElement).value })}
                      /></label>`
                  : nothing
              }
              <label
                >${this.tr("settings.house_floor")}<select
                  .value=${dr.floor}
                  ?disabled=${!canEdit}
                  @change=${(e: Event) => set(d.id, { floor: (e.target as HTMLSelectElement).value })}
                >
                  ${floors.map((f) => html`<option value=${f} ?selected=${f === dr.floor}>${this.tr(`settings.floors.${f}`)}</option>`)}
                </select></label
              >
              <label class="check"
                ><input
                  type="checkbox"
                  .checked=${dr.shown}
                  ?disabled=${!canEdit}
                  @change=${(e: Event) => set(d.id, { shown: (e.target as HTMLInputElement).checked })}
                />${this.tr("settings.appl_shown")}</label
              >
              ${
                x?.kind.startsWith("dryer")
                  ? html`<label class="check wide"
                      ><input
                        type="checkbox"
                        .checked=${dr.after}
                        ?disabled=${!canEdit}
                        @change=${(e: Event) => set(d.id, { after: (e.target as HTMLInputElement).checked })}
                      /><span
                        ><b>${this.tr("settings.appl_after")}</b> —
                        ${this.tr("settings.appl_after_help")}</span
                      ></label
                    >`
                  : nothing
              }
            </div>
          </li>`;
        })}
      </ul>
      ${
        changed && canEdit
          ? html`<div class="vacrow">
              <button type="button" class="primary" @click=${() => void save()}>
                ${this.tr("settings.save")}
              </button>
              <button
                type="button"
                class="ghost"
                @click=${() => (this.houseDraft = null)}
              >
                ${this.tr("settings.discard")}
              </button>
            </div>`
          : nothing
      }`;
  }

  @property({ attribute: false }) setVacation?: (
    on: boolean,
    until: string | null,
  ) => Promise<void>;
  @state() private vacUntil: string | null = null;

  private renderVacation(v: VacationView, canEdit: boolean): TemplateResult {
    const fmt = (iso: string) =>
      new Intl.DateTimeFormat(this.locale, {
        weekday: "short",
        day: "numeric",
        month: "long",
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date(iso));
    const status = v.active
      ? v.auto
        ? this.tr("settings.vac_auto", {
            since: v.started ? fmt(v.started) : "–",
          })
        : v.until
          ? this.tr("settings.vac_until", { until: fmt(v.until) })
          : this.tr("settings.vac_open")
      : this.tr("settings.vac_off");
    const until = this.vacUntil ?? (v.until ? v.until.slice(0, 16) : "");
    return html`<div class=${v.active ? "vac on" : "vac"}>
      <div class="vachead">
        <span class="vacdot" aria-hidden="true"></span>
        <div>
          <strong
            >${this.tr(v.active ? "settings.vac_active" : "settings.vac_home")}</strong
          >
          <p>${status}</p>
        </div>
      </div>
      ${
        canEdit
          ? html`<div class="vacrow">
                <label for="vac-until"
                  >${this.tr("settings.vac_until_label")}</label
                >
                <input
                  id="vac-until"
                  type="datetime-local"
                  .value=${until}
                  @change=${(e: Event) => (this.vacUntil = (e.target as HTMLInputElement).value || null)}
                />
                ${
                  v.active
                    ? html`<button
                        type="button"
                        class="ghost"
                        @click=${() => void this.setVacation?.(false, null)}
                      >
                        ${this.tr("settings.vac_stop")}
                      </button>`
                    : html`<button
                        type="button"
                        class="primary"
                        @click=${() => void this.setVacation?.(true, until || null)}
                      >
                        ${this.tr("settings.vac_start")}
                      </button>`
                }
              </div>
              <p class="muted">${this.tr("settings.vac_help")}</p>`
          : nothing
      }
    </div>`;
  }

  private renderBar(): TemplateResult | typeof nothing {
    const n = Object.keys(
      draftToSave(this.draft, (key) => {
        const f = this.fieldByKey(key);
        return !f || this.visible(f);
      }),
    ).length;
    const base = this.errors.base;
    if (!n && !base) return nothing;
    return html`<div
      class="bar"
      role="region"
      aria-label=${this.tr("settings.pending", { n })}
    >
      ${base ? html`<p class="error" role="alert">${this.tr(`settings.errors.${base}`)}</p>` : nothing}
      ${
        n
          ? html`<div class="barrow">
              <span
                >${this.tr(n === 1 ? "settings.pending_one" : "settings.pending", { n })}</span
              >
              <span class="buttons">
                <button
                  type="button"
                  class="ghost"
                  ?disabled=${this.busy}
                  @click=${() => this.cancelDraft()}
                >
                  ${this.tr("settings.cancel")}
                </button>
                <button
                  type="button"
                  class="primary"
                  ?disabled=${this.busy}
                  @click=${() => void this.saveDraft()}
                >
                  ${this.tr(this.busy ? "settings.saving" : "settings.save_restart")}
                </button>
              </span>
            </div>`
          : nothing
      }
    </div>`;
  }

  private fieldByKey(key: string): SettingField | undefined {
    return this.view?.groups.flatMap((g) => g.fields).find((x) => x.key === key);
  }

  private visible(f: SettingField): boolean {
    return fieldVisible(f, (key) => {
      const other = this.fieldByKey(key);
      return other ? this.shown(other) : undefined;
    });
  }

  /** Limit set but no rated power: ZEPHYR cannot limit in % (a warning at the rated power). */
  private curtailWarning(f: SettingField): boolean {
    if (f.key !== "curtail_inverter_w" || !this.visible(f)) return false;
    const number = this.view?.groups
      .flatMap((g) => g.fields)
      .find((x) => x.key === "curtail_number");
    return !!number && !!this.shown(number) && !this.shown(f);
  }

  private renderField(f: SettingField): TemplateResult {
    const open = this.tip === f.key;
    const id = `f-${f.key}`;
    if (!this.visible(f)) return html``;
    return html`${
        f.key === "curtail_switch"
          ? html`<li class="subhead"><b>${this.tr("settings.curtail_head")}</b></li>`
          : nothing
      }
      <li class=${f.active === false ? "inactive" : ""}>
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
            ${this.isModified(f) ? html`<span class="dot" title=${this.defaultText(f)}></span>` : nothing}
            ${f.key in this.draft ? html`<span class="pending">${this.tr("settings.not_saved")}</span>` : nothing}
            ${this.saved === f.key ? html`<span class="saved" role="status">${this.tr("settings.saved")}</span>` : nothing}
          </div>
          <span class="help">${this.tr(`settings.fields.${f.key}.help`)}</span>
          ${
            open
              ? html`<div class="more" role="note">${this.tr(`settings.fields.${f.key}.more`, {
                  in_use: f.in_use === undefined || f.in_use === null ? "–" : this.display(f, f.in_use),
                })}</div>`
              : nothing
          }
          ${this.meta(f)}
          ${this.errors[f.key] ? html`<span class="error" role="alert">${this.errorText(f, this.errors[f.key])}</span>` : nothing}
          ${this.curtailWarning(f) ? html`<span class="warnline" role="note">${this.tr("settings.curtail_rated_missing")}</span>` : nothing}
        </div>
        <div class="control">${this.control(f, id)}</div>
      </li>`;
  }

  @state() private domainErrors: Record<string, string> = {};

  private errorText(f: SettingField, code: string): string {
    if (code === "entity_domain")
      return this.tr("settings.errors.entity_domain", {
        domain: this.domainErrors[f.key] ?? f.domain,
      });
    if (code === "out_of_range" && f.min !== null && f.max !== null)
      return this.tr("settings.errors.range", {
        min: formatNumber(f.min, f.step, this.locale),
        max: formatNumber(f.max, f.step, this.locale),
        unit: f.unit ? ` ${f.unit}` : "",
      });
    return this.tr(`settings.errors.${code}`);
  }

  private defaultText(f: SettingField): string {
    return this.tr("settings.default", { value: this.display(f, f.default) });
  }

  private display(f: SettingField, value: unknown): string {
    if (
      value === null ||
      value === undefined ||
      value === "" ||
      (Array.isArray(value) && !value.length)
    )
      return this.tr("settings.none");
    if (f.kind === "bool")
      return this.tr(value ? "settings.yes" : "settings.no");
    if (f.kind === "number")
      return `${formatNumber(Number(value), f.step, this.locale)}${f.unit ? ` ${f.unit}` : ""}`;
    if (f.kind === "select") {
      if (f.key === "tariff_supplier")
        return (
          f.choices?.find((c) => c.value === value)?.label ??
          this.tr("settings.own")
        );
      if (Array.isArray(value))
        return (value as string[])
          .map((v) => this.tr(`settings.options.${v}`))
          .join(", ");
      return this.tr(`settings.options.${String(value)}`);
    }
    const ids = Array.isArray(value) ? (value as string[]) : [String(value)];
    return ids.map((e) => this.friendlyName(e) ?? e).join(", ");
  }

  private meta(f: SettingField): TemplateResult | typeof nothing {
    const parts: string[] = [];
    const modified = this.isModified(f);
    if (modified) parts.push(this.defaultText(f));
    const st = f.status;
    if (st) {
      if (st.state === "unset") parts.push(this.tr("settings.status.unset"));
      else if (st.state === "missing")
        parts.push(
          this.tr("settings.status.missing", {
            entities: (st.entities ?? []).join(", "),
          }),
        );
      else if (st.state === "unavailable")
        parts.push(this.tr("settings.status.unavailable"));
      else if (st.mode !== undefined)
        parts.push(
          st.action
            ? this.tr("settings.status.climate", {
                mode: this.tr(`settings.options.${st.mode}`),
                action: this.tr(`settings.actions.${st.action}`),
              })
            : this.tr(`settings.options.${st.mode}`),
        );
      else if (st.no_step) parts.push(this.tr("settings.status.no_step"));
      else if (st.step_interval_s != null && st.step_kwh != null)
        parts.push(
          this.tr("settings.status.steps", {
            every: stepInterval(st.step_interval_s, this.locale),
            kwh: formatNumber(st.step_kwh, 0.01, this.locale),
          }),
        );
      else if (st.interval_s != null)
        parts.push(
          this.tr("settings.status.interval", {
            s: formatNumber(st.interval_s, 0.1, this.locale),
          }),
        );
      else if (st.price_slots != null)
        parts.push(this.tr("settings.status.slots", { n: st.price_slots }));
      else parts.push(this.tr("settings.status.ok"));
    }
    const canReset =
      modified &&
      this.editable &&
      !(f.key in this.draft && this.draft[f.key] === RESET);
    if (!parts.length && !canReset) return nothing;
    const cls =
      st && st.state !== "ok" && st.state !== "unset" ? "meta warn" : "meta";
    return html`<span class=${cls}
      >${parts.join(" · ")}${
        canReset
          ? html` <button
              type="button"
              class="link"
              ?disabled=${this.busy}
              @click=${() => this.reset(f)}
            >
              ${this.tr("settings.reset")}
            </button>`
          : nothing
      }</span
    >`;
  }

  private control(f: SettingField, id: string): TemplateResult {
    const disabled =
      !this.editable ||
      this.busy ||
      (f.active === false && f.tariff);
    const value = controlValue(f, this.shown(f));
    switch (f.kind) {
      case "bool":
        return html`<button
          id=${id}
          type="button"
          role="switch"
          class="switch"
          aria-checked=${value ? "true" : "false"}
          ?disabled=${disabled}
          @click=${() => this.change(f, !value)}
        >
          <span></span>
        </button>`;
      case "number":
        return html`<span class="num">
          <input
            id=${id}
            type="text"
            inputmode="decimal"
            .value=${value === null || value === undefined ? "" : formatNumber(Number(value), f.step, this.locale)}
            ?disabled=${disabled}
            aria-invalid=${this.errors[f.key] ? "true" : "false"}
            @change=${(e: Event) => this.numberChanged(f, e.target as HTMLInputElement)}
            @keydown=${(e: KeyboardEvent) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
          />${f.unit ? html`<span class="unit">${f.unit}</span>` : nothing}
        </span>`;
      case "select":
        if (f.multiple)
          return this.multi(f, id, (value as string[] | null) ?? [], disabled);
        return html`<select
          id=${id}
          ?disabled=${disabled}
          @change=${(e: Event) => this.change(f, (e.target as HTMLSelectElement).value)}
        >
          ${(
            f.choices ?? f.options.map((o) => ({ value: o, label: null }))
          ).map(
            (c) =>
              html`<option value=${c.value} ?selected=${c.value === value}>
                ${c.label ?? (f.key === "tariff_supplier" ? this.tr("settings.own") : this.tr(`settings.options.${c.value}`))}
              </option>`,
          )}
        </select>`;
      case "entities":
        return this.entities(f, id, (value as string[] | null) ?? [], disabled);
      default:
        return this.entity(f, id, (value as string | null) ?? null, disabled);
    }
  }

  private numberChanged(f: SettingField, input: HTMLInputElement): void {
    const n = parseNumber(input.value, this.locale);
    if (n === null) {
      if (!input.value.trim() && f.optional) this.change(f, null);
      else this.localError(f, input.value.trim() ? "not_a_number" : "required");
      return;
    }
    this.change(f, n);
  }

  private multi(
    f: SettingField,
    id: string,
    value: string[],
    disabled: boolean,
  ): TemplateResult {
    return html`<div
      id=${id}
      class="chips"
      role="group"
      aria-label=${this.label(f.key)}
    >
      ${f.options.map(
        (o) =>
          html`<button
            type="button"
            class="chip"
            aria-pressed=${value.includes(o) ? "true" : "false"}
            ?disabled=${disabled}
            @click=${() => {
              const next = toggleChoice(value, o, f.options);
              if (next.length) this.change(f, next);
              else this.localError(f, "choose_one");
            }}
          >
            ${this.tr(`settings.options.${o}`)}
          </button>`,
      )}
    </div>`;
  }

  private choices(f: SettingField): EntityChoice[] {
    return entityChoices(this.states, f.domain, f.device_class);
  }

  @state() private pickFor: string | null = null;
  @state() private pickQuery = "";
  @state() private pickIndex = 0;

  /** Entity picker with its own list: filters on any part of the name and the id (works in the apps too). */
  private picker(
    f: SettingField,
    id: string,
    text: string,
    disabled: boolean,
    pick: (entityId: string | null, raw: string) => void,
  ): TemplateResult {
    const choices = this.choices(f);
    const open = this.pickFor === id;
    const hits = open ? searchChoices(choices, this.pickQuery) : [];
    const commit = (raw: string) => {
      this.pickFor = null;
      const other = wrongDomain(raw, f.domain);
      const resolved = resolveEntity(raw, choices);
      if (!resolved && other) {
        this.domainErrors = { ...this.domainErrors, [f.key]: f.domain };
        this.localError(f, "entity_domain");
        return;
      }
      pick(resolved, raw);
    };
    const choose = (c: EntityChoice) => {
      this.pickFor = null;
      pick(c.id, c.id);
    };
    return html`<span class="pickwrap">
      <input
        id=${id}
        class="pick"
        type="text"
        role="combobox"
        aria-expanded=${open && hits.length ? "true" : "false"}
        aria-controls=${`${id}-list`}
        aria-autocomplete="list"
        placeholder=${this.tr("settings.choose_entity")}
        autocomplete="off"
        .value=${open ? this.pickQuery : text}
        ?disabled=${disabled}
        aria-invalid=${this.errors[f.key] ? "true" : "false"}
        @focus=${(e: Event) => {
          this.pickFor = id;
          this.pickQuery = "";
          this.pickIndex = 0;
          (e.target as HTMLInputElement).select();
        }}
        @input=${(e: Event) => {
          this.pickQuery = (e.target as HTMLInputElement).value;
          this.pickIndex = 0;
        }}
        @keydown=${(e: KeyboardEvent) => {
          if (!open) return;
          if (e.key === "ArrowDown")
            this.pickIndex = Math.min(hits.length - 1, this.pickIndex + 1);
          else if (e.key === "ArrowUp")
            this.pickIndex = Math.max(0, this.pickIndex - 1);
          else if (e.key === "Enter") {
            if (hits[this.pickIndex] && this.pickQuery.trim())
              choose(hits[this.pickIndex]);
            else commit(this.pickQuery);
          } else if (e.key === "Escape") this.pickFor = null;
          else return;
          e.preventDefault();
        }}
        @blur=${() => {
          if (this.pickFor !== id) return;
          const raw = this.pickQuery;
          this.pickFor = null;
          if (raw.trim()) commit(raw);
        }}
      />
      ${
        open && hits.length
          ? html`<ul class="picklist" id=${`${id}-list`} role="listbox">
              ${hits.map(
                (c, i) =>
                  html`<li
                    role="option"
                    aria-selected=${i === this.pickIndex ? "true" : "false"}
                    class=${i === this.pickIndex ? "on" : ""}
                    @mousedown=${(e: Event) => {
                      e.preventDefault(); // keep the focus until the choice is made
                      choose(c);
                    }}
                  >
                    <span>${c.name}</span><small>${c.id}</small>
                  </li>`,
              )}
            </ul>`
          : nothing
      }
    </span>`;
  }

  private entity(
    f: SettingField,
    id: string,
    value: string | null,
    disabled: boolean,
  ): TemplateResult {
    const current = value
      ? (this.choices(f).find((c) => c.id === value) ?? {
          id: value,
          name: this.friendlyName(value) ?? value,
        })
      : null;
    return html`<span class="entityrow">
      ${this.picker(
        f,
        id,
        current ? choiceLabel(current) : "",
        disabled,
        (entityId, raw) => {
          if (entityId) this.change(f, entityId);
          else if (!raw.trim()) {
            if (f.optional) this.change(f, null);
            else this.localError(f, "required");
          } else this.localError(f, "entity_missing");
        },
      )}
      ${
        value && f.optional
          ? html`<button
              type="button"
              class="clear"
              ?disabled=${disabled}
              aria-label=${this.tr("settings.clear")}
              @click=${() => this.change(f, null)}
            >
              ×
            </button>`
          : nothing
      }
    </span>`;
  }

  private entities(
    f: SettingField,
    id: string,
    value: string[],
    disabled: boolean,
  ): TemplateResult {
    return html`<div class="multi">
      ${
        value.length
          ? html`<ul class="chips">
              ${value.map(
                (e) =>
                  html`<li class="chip on">
                    <span>${this.friendlyName(e) ?? e}</span>
                    <button
                      type="button"
                      class="x"
                      ?disabled=${disabled}
                      aria-label=${`${this.tr("settings.remove")}: ${this.friendlyName(e) ?? e}`}
                      @click=${() =>
                        this.change(
                          f,
                          value.filter((v) => v !== e),
                        )}
                    >
                      ×
                    </button>
                  </li>`,
              )}
            </ul>`
          : nothing
      }
      ${this.picker(f, id, "", disabled, (entityId, raw) => {
        if (entityId) {
          if (!value.includes(entityId)) this.change(f, [...value, entityId]);
        } else if (raw.trim()) this.localError(f, "entity_missing");
      })}
    </div>`;
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
    .groups button {
      flex-direction: column;
      align-items: flex-start;
      justify-content: center;
      gap: 1px;
      text-align: left;
    }
    .groups small {
      font-size: 12px;
      font-weight: 400;
      color: var(--z-muted);
    }
    .groups button.on small {
      color: inherit;
      opacity: 0.7;
    }
    .subtabs {
      display: flex;
      gap: 2px;
      padding: 4px;
      align-self: flex-start;
      max-width: 100%;
      overflow-x: auto;
      border: 1px solid var(--z-border);
      border-radius: 999px;
      background: var(--z-track);
    }
    .subtabs button {
      display: flex;
      align-items: center;
      gap: 6px;
      min-height: 36px;
      padding: 0 16px;
      border: 0;
      border-radius: 999px;
      background: transparent;
      color: var(--z-text);
      font: inherit;
      font-weight: 600;
      white-space: nowrap;
      cursor: pointer;
    }
    .subtabs button.on {
      background: var(--z-text);
      color: var(--z-on-text);
    }
    .subtabs button:focus-visible {
      outline: 2px solid var(--z-charge);
      outline-offset: 2px;
    }
    .subtabs .dot {
      display: inline-block;
      width: 7px;
      height: 7px;
    }
    .groups button:focus-visible,
    .info:focus-visible {
      outline: 2px solid var(--z-charge);
      outline-offset: 2px;
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
    .vac {
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding: 14px 16px;
      border-radius: 12px;
      border: 1px solid var(--z-border);
      background: var(--z-bg);
      margin-bottom: 8px;
    }
    .vac.on {
      border-color: var(--z-charge);
      background: var(--z-info-bg);
    }
    .vachead {
      display: flex;
      gap: 12px;
      align-items: flex-start;
    }
    .vachead p {
      margin: 2px 0 0;
      font-size: 13px;
      color: var(--z-muted);
    }
    .vacdot {
      width: 12px;
      height: 12px;
      margin-top: 4px;
      border-radius: 50%;
      background: var(--z-muted);
      flex: none;
    }
    .vac.on .vacdot {
      background: var(--z-charge);
    }
    .vacrow {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px 12px;
      font-size: 14px;
    }
    .vacrow input {
      min-width: 220px;
      min-height: 40px;
      padding: 0 10px;
      border: 1px solid var(--z-border);
      border-radius: 10px;
      background: var(--z-card);
      color: var(--z-text);
      font: inherit;
    }
    .vacrow button {
      min-height: 40px;
      padding: 0 16px;
      border-radius: 10px;
      font: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    .pending,
    .saved {
      font-size: 11px;
      padding: 1px 8px;
      border-radius: 999px;
      background: var(--z-info-bg);
      color: var(--z-muted);
    }
    .saved {
      color: var(--z-good-text, var(--z-text));
      background: var(--z-good-bg, var(--z-info-bg));
    }
    .error {
      margin: 0;
      font-size: 13px;
      color: var(--z-bad-text, #b3261e);
    }
    [aria-invalid="true"] {
      border-color: var(--z-bad-text, #b3261e);
    }
    .link {
      padding: 0;
      border: 0;
      background: none;
      color: var(--z-charge);
      font: inherit;
      font-weight: 600;
      cursor: pointer;
    }
    ul.house {
      list-style: none;
      margin: 0 0 8px;
      padding: 0;
    }
    ul.house li {
      display: grid;
      grid-template-columns: 200px 1fr;
      gap: 10px 20px;
      padding: 14px 0;
      border-bottom: 1px solid var(--z-border);
    }
    .hname {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      text-align: left;
      justify-self: stretch;
      justify-content: flex-start;
    }
    .hname small {
      color: var(--z-muted);
      font-size: 12px;
      font-weight: 400;
    }
    .hfields {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 10px 14px;
      align-items: end;
    }
    .hfields label {
      font-weight: 400;
      text-align: left;
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-size: 12.5px;
      color: var(--z-muted);
    }
    .hfields input[type="time"] {
      min-height: 40px;
      padding: 0 10px;
      border: 1px solid var(--z-border);
      border-radius: 10px;
      background: var(--z-card);
      color: var(--z-text);
      font: inherit;
    }
    .hfields label.check {
      flex-direction: row;
      align-items: center;
      gap: 8px;
      min-height: 40px;
      color: var(--z-text);
      font-size: 13.5px;
    }
    .hfields label.wide {
      grid-column: 1 / -1;
    }
    .hfields input[type="checkbox"] {
      width: 20px;
      height: 20px;
      min-width: 0;
      min-height: 0;
      margin: 0;
      accent-color: var(--z-charge);
    }
    @media (max-width: 700px) {
      ul.house li {
        grid-template-columns: 1fr;
      }
    }
    .hfields select {
      min-height: 40px;
      padding: 0 10px;
      border: 1px solid var(--z-border);
      border-radius: 10px;
      background: var(--z-card);
      color: var(--z-text);
      font: inherit;
    }
    li.subhead {
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding: 14px 0 0;
    }
    .warnline {
      color: var(--z-warn-text, #7a4a06);
      background: var(--z-warn-bg, #fdf0dc);
      border-radius: 8px;
      padding: 6px 10px;
      font-size: 12.5px;
    }
    .pickwrap {
      position: relative;
      display: inline-block;
      flex: 1 1 auto;
      min-width: 0;
    }
    .pickwrap .pick {
      width: 100%;
    }
    .picklist {
      position: absolute;
      z-index: 5;
      left: 0;
      right: 0;
      top: calc(100% + 4px);
      margin: 0;
      padding: 0;
      list-style: none;
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 10px;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
      max-height: 300px;
      overflow: auto;
    }
    .picklist li {
      display: flex;
      flex-direction: column;
      padding: 8px 10px;
      border-top: 1px solid var(--z-border);
      cursor: pointer;
    }
    .picklist li:first-child {
      border-top: 0;
    }
    .picklist li.on,
    .picklist li:hover {
      background: color-mix(in srgb, var(--z-charge) 10%, var(--z-card));
    }
    .picklist small {
      color: var(--z-muted);
      font-size: 11.5px;
      word-break: break-all;
    }
    .entityrow {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    input.pick {
      width: 280px;
      max-width: 70vw;
      text-align: left;
    }
    .clear,
    .x {
      width: 32px;
      height: 32px;
      padding: 0;
      border: 0;
      border-radius: 50%;
      background: transparent;
      color: var(--z-muted);
      font-size: 18px;
      cursor: pointer;
    }
    .multi {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 8px;
      max-width: 360px;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 6px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 2px;
      min-height: 36px;
      padding: 0 12px;
      border: 1px solid var(--z-border);
      border-radius: 999px;
      background: var(--z-bg);
      color: var(--z-text);
      font: inherit;
      font-size: 13px;
      cursor: pointer;
    }
    li.chip {
      padding: 0 2px 0 12px;
      border-top: 1px solid var(--z-border);
    }
    .chip[aria-pressed="true"],
    .chip.on {
      background: var(--z-info-bg);
      border-color: var(--z-charge);
      font-weight: 600;
    }
    .bar {
      position: sticky;
      bottom: 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 12px 14px;
      border-radius: 12px;
      background: var(--z-card);
      border: 1px solid var(--z-charge);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    }
    .barrow {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      font-size: 14px;
    }
    .buttons {
      display: flex;
      gap: 8px;
    }
    .buttons button {
      min-height: 40px;
      padding: 0 16px;
      border-radius: 10px;
      font: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    .ghost {
      border: 1px solid var(--z-border);
      background: transparent;
      color: var(--z-text);
    }
    .primary {
      border: 0;
      background: var(--z-text);
      color: var(--z-on-text);
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
      .groups small {
        display: none;
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
