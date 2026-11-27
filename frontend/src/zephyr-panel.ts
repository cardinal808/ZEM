// ZEPHYR panel (M6, SPEC-ui). UI-1: header, menu and the three cards of *Now* on the Plan screen.
import {
  LitElement,
  css,
  html,
  nothing,
  svg,
  type PropertyValues,
  type TemplateResult,
} from "lit";
import { customElement, property, state } from "lit/decorators.js";

import {
  clock,
  euro,
  kwh,
  minutesUntil,
  percent,
  sameDay,
  signedWatts,
  watts,
} from "./format";
import { language, t, type Lang } from "./i18n";
import { aircoLine } from "./airco";
import {
  blocksFor,
  days,
  quartersOf,
  stats,
  type Period,
  type PlanBlock,
  type PlanView,
} from "./plan";
import { storedPeriod } from "./prices-plan";
import "./prices-plan";
import "./sets";
import type { SetsView } from "./sets";
import "./settings";
import type { SettingsView } from "./settings";
import type { SetResult } from "./settings-edit";
import { blockerText, fastButtons, type EventsView } from "./diag";
import "./diagnostics";
import "./savings";
import "./stroom";
import type { StroomView } from "./stroom";
import type { PlanCheckView } from "./diag";
import type { BackfillRequest, BackfillResult, SavingsView } from "./savings";
import type { ExportResult } from "./diagnostics";
import { actionFill, theme } from "./theme";
import type {
  HomeAssistant,
  Now,
  PanelInfo,
  PlanNow,
  SubscribeEvent,
} from "./types";

type View = "plan" | "stroom" | "sets" | "savings" | "settings" | "diagnostics";
type Status = "loading" | "ok" | "not_loaded" | "disconnected" | "reloading";

const DEFAULT_STATIC = "/zephyr_static";
const FONTS: [string, number, string][] = [
  ["Inter", 400, "inter-latin-400-normal.woff2"],
  ["Inter", 600, "inter-latin-600-normal.woff2"],
  ["Inter", 700, "inter-latin-700-normal.woff2"],
  ["Space Grotesk", 700, "space-grotesk-latin-700-normal.woff2"],
];

/** @font-face must live in the document, not in the shadow root. Once per page. */
function loadFonts(base: string): void {
  const id = "zephyr-fonts";
  if (document.getElementById(id)) return;
  const style = document.createElement("style");
  style.id = id;
  style.textContent = FONTS.map(
    ([family, weight, file]) =>
      `@font-face{font-family:"${family}";font-style:normal;font-weight:${weight};font-display:swap;src:url("${base}/fonts/${file}") format("woff2");}`,
  ).join("\n");
  document.head.appendChild(style);
}

@customElement("zephyr-panel")
export class ZephyrPanel extends LitElement {
  @property({ attribute: false }) hass?: HomeAssistant;
  @property({ type: Boolean }) narrow = false;
  @property({ attribute: false }) panel?: PanelInfo;

  @state() private now?: Now;
  @state() private status: Status = "loading";
  @state() private view: View = "plan";
  @state() private clockMs = Date.now();
  @state() private planView?: PlanView;
  @state() private setsView?: SetsView;
  @state() private settingsView?: SettingsView;
  @state() private period: Period = storedPeriod();
  @state() private eventsView?: EventsView;
  @state() private savingsView?: SavingsView;
  @state() private stroomView?: StroomView;
  @state() private planCheck?: PlanCheckView;
  @state() private confirmLive = false;
  @state() private controlBusy = false;
  @state() private controlError: string | null = null;
  @state() private pendingMode: string | null = null;
  private pendingTimer?: number;

  private setsTimer?: number;

  private planFor = "";
  private planBusy = false;
  private planTimer?: number;

  private unsubscribe?: () => Promise<void>;
  private subscribing = false;
  private retryTimer?: number;
  private clockTimer?: number;
  private watchedConnection?: HomeAssistant["connection"];

  private get base(): string {
    return this.panel?.config?.static ?? DEFAULT_STATIC;
  }

  private get uiLang(): Lang {
    return language(this.hass?.locale?.language ?? this.hass?.language);
  }

  private get locale(): string {
    return this.hass?.locale?.language ?? this.hass?.language ?? "en";
  }

  private get timeZone(): string {
    return (
      this.hass?.config.time_zone ??
      Intl.DateTimeFormat().resolvedOptions().timeZone
    );
  }

  private tr(
    key: string,
    params: Record<string, string | number> = {},
  ): string {
    return t(this.uiLang, key, params);
  }

  override connectedCallback(): void {
    super.connectedCallback();
    loadFonts(this.base);
    this.clockTimer = window.setInterval(
      () => (this.clockMs = Date.now()),
      30_000,
    );
    // The running quarter moves on even without a new plan.
    this.planTimer = window.setInterval(
      () => void this.loadPlan(true),
      300_000,
    );
    if (this.hass) void this.subscribe();
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    window.clearInterval(this.clockTimer);
    window.clearInterval(this.planTimer);
    window.clearInterval(this.setsTimer);
    window.clearTimeout(this.retryTimer);
    this.watch(undefined);
    void this.stop();
  }

  protected override updated(changed: PropertyValues<this>): void {
    if (!changed.has("hass") || !this.hass) return;
    this.toggleAttribute("dark", Boolean(this.hass.themes?.darkMode));
    if (this.hass.connection !== this.watchedConnection)
      this.watch(this.hass.connection);
    if (
      !this.unsubscribe &&
      !this.subscribing &&
      this.status !== "disconnected"
    )
      void this.subscribe();
  }

  // --- connection ------------------------------------------------------------

  private readonly onReady = (): void => {
    this.status = "loading";
    void this.subscribe();
  };

  private readonly onDisconnected = (): void => {
    this.unsubscribe = undefined;
    this.status = "disconnected";
  };

  private watch(connection: HomeAssistant["connection"] | undefined): void {
    this.watchedConnection?.removeEventListener("ready", this.onReady);
    this.watchedConnection?.removeEventListener(
      "disconnected",
      this.onDisconnected,
    );
    this.watchedConnection = connection;
    connection?.addEventListener("ready", this.onReady);
    connection?.addEventListener("disconnected", this.onDisconnected);
  }

  private async subscribe(): Promise<void> {
    if (!this.hass || this.subscribing || this.unsubscribe) return;
    this.subscribing = true;
    window.clearTimeout(this.retryTimer);
    try {
      this.unsubscribe =
        await this.hass.connection.subscribeMessage<SubscribeEvent>(
          (event) => this.onEvent(event),
          {
            type: "zephyr/subscribe",
          },
        );
    } catch (err) {
      if ((err as { code?: string }).code === "not_loaded")
        this.status = "not_loaded";
      this.retry(10_000);
    } finally {
      this.subscribing = false;
    }
  }

  private async stop(): Promise<void> {
    const unsubscribe = this.unsubscribe;
    this.unsubscribe = undefined;
    try {
      await unsubscribe?.();
    } catch {
      // Already closed by Home Assistant.
    }
  }

  /** Fetch prices and plan when there is a new plan (or when ``force``). */
  private async loadPlan(force = false): Promise<void> {
    const now = this.now;
    if (!this.hass || !now?.price_entity || this.planBusy) {
      if (now && !now.price_entity) this.planView = undefined;
      return;
    }
    const key = now.plan?.calculated_at ?? "none";
    if (!force && key === this.planFor) return;
    this.planBusy = true;
    try {
      this.planView = await this.hass.callWS<PlanView>({ type: "zephyr/plan" });
      this.planFor = key;
    } catch {
      // Not loaded or no price source: the cards above already say so.
    } finally {
      this.planBusy = false;
    }
  }

  private async loadSets(): Promise<void> {
    if (!this.hass || this.view !== "sets") return;
    try {
      this.setsView = await this.hass.callWS<SetsView>({ type: "zephyr/sets" });
    } catch {
      // Not loaded: the banner says so.
    }
  }

  private async loadStroom(): Promise<void> {
    if (!this.hass || this.view !== "stroom") return;
    try {
      this.stroomView = await this.hass.callWS<StroomView>({
        type: "zephyr/stroom",
      });
    } catch {
      // keep the last view; the header shows when the connection is gone
    }
  }

  private async loadSavings(): Promise<void> {
    if (!this.hass || this.view !== "savings") return;
    try {
      this.savingsView = await this.hass.callWS<SavingsView>({
        type: "zephyr/savings",
      });
    } catch {
      // Not loaded: the banner says so.
    }
  }

  private backfillSavings = async (
    req: BackfillRequest | null,
  ): Promise<BackfillResult> => {
    if (!this.hass) return { ok: false, error: "no_connection" };
    const result = await this.hass.callWS<BackfillResult>(
      req
        ? { type: "zephyr/savings/backfill", ...req }
        : { type: "zephyr/savings/backfill", clear: true },
    );
    if (result.ok) await this.loadSavings();
    return result;
  };

  private async loadSettings(): Promise<void> {
    if (!this.hass) return;
    try {
      this.settingsView = await this.hass.callWS<SettingsView>({
        type: "zephyr/settings/get",
      });
    } catch {
      // Not loaded: the banner says so.
    }
  }

  private async loadEvents(): Promise<void> {
    if (!this.hass || this.view !== "diagnostics") return;
    try {
      this.eventsView = await this.hass.callWS<EventsView>({
        type: "zephyr/events",
      });
      this.planCheck = await this.hass.callWS<PlanCheckView>({
        type: "zephyr/plan_check",
        days: 14,
      });
    } catch {
      // Not loaded: the banner says so.
    }
  }

  private get admin(): boolean {
    return Boolean(this.hass?.user?.is_admin);
  }

  /** Control through ZEPHYR's own entities (mode select, live switch), the same path as automations (SPEC-ui §3). */
  private async callService(
    domain: string,
    service: string,
    data: Record<string, unknown>,
  ): Promise<void> {
    if (!this.hass || this.controlBusy) return;
    this.controlBusy = true;
    this.controlError = null;
    try {
      await this.hass.callWS({
        type: "call_service",
        domain,
        service,
        service_data: data,
      });
    } catch (err) {
      this.controlError = (err as { message?: string })?.message ?? String(err);
    } finally {
      this.controlBusy = false;
    }
  }

  private setMode(mode: string): void {
    const entity = this.now?.entities.mode;
    if (!entity || mode === this.now?.mode) return;
    // Until the new mode shows (updates come every 2 s), the fast buttons wait: no double taps.
    this.pendingMode = mode;
    window.clearTimeout(this.pendingTimer);
    this.pendingTimer = window.setTimeout(
      () => (this.pendingMode = null),
      5000,
    );
    void this.callService("select", "select_option", {
      entity_id: entity,
      option: mode,
    });
  }

  private async setLive(on: boolean): Promise<void> {
    const entity = this.now?.entities.live;
    this.confirmLive = false;
    if (entity)
      await this.callService("switch", on ? "turn_on" : "turn_off", {
        entity_id: entity,
      });
  }

  private downloadDiagnostics = async (): Promise<void> => {
    if (!this.hass || !this.eventsView) return;
    const signed = await this.hass.callWS<{ path: string }>({
      type: "auth/sign_path",
      path: `/api/diagnostics/config_entry/${this.eventsView.entry_id}`,
    });
    const a = document.createElement("a");
    a.href = signed.path;
    a.download = "";
    document.body.appendChild(a);
    a.click();
    a.remove();
  };

  private exportCosts = async (): Promise<ExportResult> => {
    if (!this.hass) throw new Error("no connection");
    const result = await this.hass.callWS<{ response: ExportResult }>({
      type: "call_service",
      domain: "zephyr",
      service: "export_costs",
      service_data: {},
      return_response: true,
    });
    return result.response;
  };

  /** Vacation through ZEPHYR's own entities (switch and end time), like an automation would (B42). */
  private setVacation = async (
    on: boolean,
    until: string | null,
  ): Promise<void> => {
    const ent = this.settingsView?.vacation?.entities;
    if (!this.hass || !ent?.switch) return;
    this.controlError = null;
    try {
      if (on && until && ent.until)
        await this.hass.callWS({
          type: "call_service",
          domain: "datetime",
          service: "set_value",
          service_data: {
            entity_id: ent.until,
            datetime: `${until.replace("T", " ")}:00`,
          },
        });
      await this.hass.callWS({
        type: "call_service",
        domain: "switch",
        service: on ? "turn_on" : "turn_off",
        service_data: { entity_id: ent.switch },
      });
    } catch (err) {
      this.controlError = (err as { message?: string })?.message ?? String(err);
    }
    await this.loadSettings();
  };

  private saveSettings = async (
    changes: Record<string, unknown>,
    reset: string[],
  ): Promise<SetResult> => {
    if (!this.hass) return { ok: false, errors: { base: "failed" } };
    const result = await this.hass.callWS<SetResult>({
      type: "zephyr/settings/set",
      changes,
      reset,
    });
    if (result.ok) {
      if (result.reload) {
        // ZEPHYR restarts: ask again once it is back.
        window.setTimeout(() => void this.loadSettings(), 3000);
        window.setTimeout(() => void this.loadSettings(), 8000);
      } else void this.loadSettings();
    }
    return result;
  };

  private show(view: View): void {
    this.view = view;
    window.clearInterval(this.setsTimer);
    if (view === "sets") {
      void this.loadSets();
      this.setsTimer = window.setInterval(() => void this.loadSets(), 10_000);
    } else if (view === "settings") {
      void this.loadSettings();
    } else if (view === "savings") {
      void this.loadSavings();
    } else if (view === "stroom") {
      void this.loadStroom();
      this.setsTimer = window.setInterval(() => void this.loadStroom(), 60_000);
    } else if (view === "diagnostics") {
      void this.loadEvents();
      this.setsTimer = window.setInterval(() => void this.loadEvents(), 15_000);
    }
  }

  private retry(ms: number): void {
    window.clearTimeout(this.retryTimer);
    this.retryTimer = window.setTimeout(() => void this.subscribe(), ms);
  }

  private onEvent(event: SubscribeEvent): void {
    if (event.type === "now") {
      this.now = event.data;
      if (this.pendingMode === event.data.mode) this.pendingMode = null;
      this.status = "ok";
      this.clockMs = Date.now();
      void this.loadPlan();
    } else if (event.type === "unloaded") {
      // The installation reloads; the server already closed this subscription.
      this.unsubscribe = undefined;
      this.status = "reloading";
      this.retry(3_000);
    }
  }

  // --- render ----------------------------------------------------------------

  protected override render(): TemplateResult {
    return html`
      <div class="page">
        ${this.renderHeader()}
        <main>${this.renderBanner()} ${this.renderView()}</main>
      </div>
    `;
  }

  private renderHeader(): TemplateResult {
    const now = this.now;
    const oneSet = (now?.sets_total ?? 1) <= 1;
    const items: [View, string][] = [
      ["plan", "menu.plan"],
      ["stroom", "menu.stroom"],
      ["sets", oneSet ? "menu.battery" : "menu.sets"],
      ["savings", "menu.savings"],
      ["settings", "menu.settings"],
      ["diagnostics", "menu.diagnostics"],
    ];
    return html`
      <header>
        <div class="brand">
          <img src="${this.base}/logo.png" alt="" width="32" height="32" />
          <span>ZEPHYR</span>
        </div>
        <nav aria-label=${this.tr("menu.label")}>
          ${items.map(
            ([view, key]) =>
              html`<button
                type="button"
                class=${this.view === view ? "tab active" : "tab"}
                aria-current=${this.view === view ? "page" : "false"}
                @click=${() => this.show(view)}
              >
                ${this.tr(key)}
              </button>`,
          )}
        </nav>
        <div class="meta">
          ${now ? this.renderControls(now) : nothing}
          <span class="time"
            >${clock(new Date(this.clockMs).toISOString(), this.locale, this.timeZone)}</span
          >
        </div>
      </header>
    `;
  }

  private renderControls(now: Now): TemplateResult {
    const canMode = this.admin && Boolean(now.entities?.mode);
    const canLive = this.admin && Boolean(now.entities?.live);
    const liveText = this.tr(now.live ? "header.live" : "header.shadow");
    const liveTitle = this.tr(
      now.live ? "header.live_title" : "header.shadow_title",
    );
    return html`${
      canMode
        ? html`<label class="chipselect">
            <span class="sr">${this.tr("control.mode")}</span>
            <select
              class="chip"
              ?disabled=${this.controlBusy}
              @change=${(e: Event) => this.setMode((e.target as HTMLSelectElement).value)}
            >
              ${now.modes.map((m) => html`<option value=${m} ?selected=${m === now.mode}>${this.tr(`mode.${m}`)}</option>`)}
            </select>
          </label>`
        : html`<span class="chip">${this.tr(`mode.${now.mode}`)}</span>`
    }
    ${
      canLive
        ? html`<span class="livewrap">
            <button
              type="button"
              class=${now.live ? "chip live" : "chip"}
              title=${liveTitle}
              aria-pressed=${now.live ? "true" : "false"}
              aria-expanded=${this.confirmLive ? "true" : "false"}
              ?disabled=${this.controlBusy}
              @click=${() => (now.live ? void this.setLive(false) : (this.confirmLive = !this.confirmLive))}
            >
              ${liveText}
            </button>
            ${this.confirmLive && !now.live ? this.renderConfirmLive(now) : nothing}
          </span>`
        : html`<span class=${now.live ? "chip live" : "chip"} title=${liveTitle}
            >${liveText}</span
          >`
    }`;
  }

  private renderConfirmLive(now: Now): TemplateResult {
    const blocked = now.blockers.length > 0;
    return html`<div
      class="popover"
      role="dialog"
      aria-label=${this.tr("control.live_title")}
    >
      <strong>${this.tr("control.live_title")}</strong>
      <p>${this.tr(blocked ? "control.live_blocked" : "control.live_text")}</p>
      ${
        blocked
          ? html`<ul>
              ${now.blockers.map((b) => html`<li>${blockerText(b, this.uiLang)}</li>`)}
            </ul>`
          : nothing
      }
      <div class="row">
        <button
          type="button"
          class="ghost"
          @click=${() => (this.confirmLive = false)}
        >
          ${this.tr("control.cancel")}
        </button>
        <button
          type="button"
          class="primary"
          ?disabled=${blocked || this.controlBusy}
          @click=${() => void this.setLive(true)}
        >
          ${this.tr("control.live_start")}
        </button>
      </div>
    </div>`;
  }

  private renderFast(now: Now): TemplateResult | typeof nothing {
    if (!this.admin || !now.entities?.mode) return nothing;
    const buttons = fastButtons(now.mode, now.modes, now.previous_mode);
    const waiting = this.pendingMode !== null && this.pendingMode !== now.mode;
    const running = buttons.find((b) => b.active);
    return html`<div
      class="fast"
      role="group"
      aria-label=${this.tr("control.fast")}
    >
      ${buttons.map(
        (b) =>
          html`<button
            type="button"
            class=${b.active ? "primary" : "ghost"}
            aria-pressed=${b.active ? "true" : "false"}
            ?disabled=${this.controlBusy || waiting}
            @click=${() => this.setMode(b.target)}
          >
            ${b.active ? this.tr("control.stop_fast", { mode: this.tr(`control.${b.mode}`) }) : this.tr(`control.${b.mode}`)}
          </button>`,
      )}
      ${
        running
          ? html`<span class="fastnote"
              >${this.tr(`control.running_${running.mode}`)}
              ${this.tr("control.back_to", {
                mode: this.tr(`mode.${running.target}`),
              })}</span
            >`
          : nothing
      }
      ${now.live ? nothing : html`<span class="fastnote">${this.tr("control.shadow_note")}</span>`}
    </div>`;
  }

  private renderBanner(): TemplateResult | typeof nothing {
    if (this.controlError && this.status === "ok")
      return html`<div class="banner" role="alert">
        ${this.tr("control.failed", { error: this.controlError })}
        <button
          type="button"
          class="link"
          @click=${() => (this.controlError = null)}
        >
          ${this.tr("control.close")}
        </button>
      </div>`;
    switch (this.status) {
      case "not_loaded":
        return html`<div class="banner" role="status">
          ${this.tr("status.not_loaded")}
        </div>`;
      case "reloading":
        return html`<div class="banner info" role="status">
          ${this.tr("status.reloading")}
        </div>`;
      case "disconnected":
        return html`<div class="banner" role="status">
          ${this.tr("status.disconnected", { time: this.now ? clock(this.now.updated_at, this.locale, this.timeZone) : "–" })}
        </div>`;
      default:
        return nothing;
    }
  }

  private renderView(): TemplateResult {
    if (this.view === "plan") return this.renderPlan();
    if (this.view === "sets") {
      return html`<zephyr-sets
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.setsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
      ></zephyr-sets>`;
    }
    if (this.view === "settings") {
      return html`<zephyr-settings
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.settingsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .friendlyName=${(id: string) => this.hass?.states?.[id]?.attributes?.friendly_name as string | undefined}
        .states=${this.hass?.states}
        .save=${this.saveSettings}
        .setVacation=${this.setVacation}
      ></zephyr-settings>`;
    }
    if (this.view === "stroom") {
      return html`<zephyr-stroom
        class=${this.status === "ok" ? "" : "stale"}
        .now=${this.now}
        .view=${this.stroomView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
      ></zephyr-stroom>`;
    }
    if (this.view === "savings") {
      return html`<zephyr-savings
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.savingsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
        ?admin=${this.admin}
        .states=${this.hass?.states}
        .backfill=${this.backfillSavings}
      ></zephyr-savings>`;
    }
    if (this.view === "diagnostics") {
      return html`<zephyr-diagnostics
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.eventsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
        ?admin=${this.admin}
        .download=${this.downloadDiagnostics}
        .exportCosts=${this.exportCosts}
        .refresh=${() => void this.loadEvents()}
        .planCheck=${this.planCheck}
      ></zephyr-diagnostics>`;
    }
    return this.renderComing();
  }

  private renderComing(): TemplateResult {
    return html`<section class="card coming">
      ${this.tr("status.coming")}
    </section>`;
  }

  private renderPlan(): TemplateResult {
    const now = this.now;
    if (!now) {
      return html`<section class="cards" aria-busy="true">
        ${[0, 1, 2].map(() => html`<div class="card skeleton" aria-hidden="true"></div>`)}
      </section>`;
    }
    const stale = this.status === "ok" ? "" : "stale";
    return html`<section
        class="cards ${stale}"
        aria-label=${this.tr("now.title")}
      >
        ${this.renderNow(now)} ${this.renderBattery(now)}
        ${this.renderNext(now)}
      </section>
      ${this.renderFast(now)}
      ${now.price_entity ? this.renderPlanParts(now, stale) : nothing}`;
  }

  private renderPlanParts(now: Now, stale: string): TemplateResult {
    let note: string | null = null;
    if (now.mode !== "dynamic_forecasting")
      note = this.tr("plan.mode_note", { mode: this.tr(`mode.${now.mode}`) });
    else if (!now.live) note = this.tr("plan.shadow_note");
    return html`${note ? html`<div class="banner info" role="note">${note}</div>` : nothing}
      <zephyr-prices-plan
        class=${stale}
        .view=${this.planView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
        ?narrow=${this.narrow}
        .period=${this.period}
        @zephyr-period=${(e: CustomEvent<Period>) => (this.period = e.detail)}
      ></zephyr-prices-plan>
      ${this.planView ? html`<section class="duo ${stale}">${this.renderBlocks(this.planView)} ${this.renderWhy(this.planView)}</section>` : nothing}`;
  }

  private range(b: PlanBlock): string {
    const from = clock(b.start, this.locale, this.timeZone);
    const to = clock(b.end, this.locale, this.timeZone);
    const tomorrow = `${this.tr("blocks.tomorrow")} `;
    const startToday = sameDay(b.start, this.clockMs, this.timeZone);
    // The end of a block is exclusive: a block that ends at 00:00 tomorrow ends today.
    const endToday = sameDay(
      new Date(b.end).getTime() - 1,
      this.clockMs,
      this.timeZone,
    );
    return `${startToday ? "" : tomorrow}${from}–${startToday && !endToday ? tomorrow : ""}${to}`;
  }

  private shownBlocks(view: PlanView): PlanBlock[] {
    const tomorrow = days(view.quarters, this.timeZone)[1] ?? null;
    return blocksFor(
      view.blocks,
      this.period,
      new Date(this.clockMs).toISOString(),
      tomorrow,
      this.timeZone,
    );
  }

  private renderBlocks(view: PlanView): TemplateResult {
    const blocks = this.shownBlocks(view).slice(0, 12);
    return html`<article class="card">
      <h2>${this.tr(`blocks.title_${this.period}`)}</h2>
      ${
        blocks.length
          ? html`<ul class="blocks">
              ${blocks.map(
                (b) =>
                  html`<li>
                    <span class="when">${this.range(b)}</span>
                    <span
                      class="swatch"
                      style="background:${actionFill(b.action)}"
                    ></span>
                    <span class="what"
                      >${this.tr(`blocks.what_${b.action}`)}${b.indicative ? html` <em>(${this.tr("blocks.indicative")})</em>` : nothing}</span
                    >
                    <span class="detail"
                      >${this.tr(`blocks.${b.action}`, { kwh: kwh(b.kwh, this.locale), price: euro(b.price, this.locale) })}</span
                    >
                  </li>`,
              )}
            </ul>`
          : html`<p class="text">
              ${this.tr(this.period === "tomorrow" ? "blocks.none_tomorrow" : "blocks.none")}
            </p>`
      }
    </article>`;
  }

  private renderWhy(view: PlanView): TemplateResult {
    const lines: string[] = [];
    // The plan's reason is about now: not for tomorrow.
    if (view.reason && this.period !== "tomorrow")
      lines.push(view.reason[this.uiLang]);
    const blocks = this.shownBlocks(view).filter((b) => !b.indicative);
    const charge = blocks
      .filter((b) => b.action === "charge")
      .sort((a, b) => a.price - b.price)[0];
    if (charge)
      lines.push(
        this.tr("why.cheapest", {
          time: this.range(charge),
          price: euro(charge.price, this.locale),
        }),
      );
    else if (blocks.length) lines.push(this.tr("why.no_charge"));
    const future = quartersOf(view.quarters, this.period, this.timeZone).filter(
      (q) => !q.past,
    );
    const peak = stats(future)?.max;
    if (peak && peak.action === "deliver") {
      const time = `${sameDay(peak.start, this.clockMs, this.timeZone) ? "" : `${this.tr("blocks.tomorrow")} `}${clock(peak.start, this.locale, this.timeZone)}`;
      lines.push(
        this.tr("why.peak", {
          time,
          price: euro(peak.buy as number, this.locale),
        }),
      );
    }
    if (future.some((q) => q.indicative)) lines.push(this.tr("why.indicative"));
    return html`<article class="card">
      <h2>${this.tr(`why.title_${this.period}`)}</h2>
      <ul class="why">
        ${lines.map((line) => html`<li>${line}</li>`)}
      </ul>
    </article>`;
  }

  private renderNow(now: Now): TemplateResult {
    const action = now.action ?? "standby";
    const power =
      now.battery_w !== null && Math.abs(now.battery_w) >= 10
        ? ` · ${watts(now.battery_w, this.locale)}`
        : "";
    return html`<article class="card">
      <div class="label">
        <span class="dot" style="background:${actionFill(action)}"></span
        >${this.tr("now.title")}
      </div>
      <div class="big">
        ${now.action ? this.tr(`action.${action}`) + power : this.tr("now.waiting")}
      </div>
      ${now.reason ? html`<p class="text">${now.reason[this.uiLang]}</p>` : nothing}
      ${this.renderAirco(now)}
      <div class="foot">
        ${now.grid_w !== null ? html`<span>${this.tr("now.grid", { value: signedWatts(now.grid_w, this.locale) })}</span>` : nothing}
        ${now.live ? nothing : html`<span>${this.tr("now.shadow_note")}</span>`}
      </div>
    </article>`;
  }

  private renderAirco(now: Now): TemplateResult | typeof nothing {
    const line = aircoLine(now.excluded, this.uiLang, this.locale);
    if (!line) return nothing;
    const icon =
      line.icon === "heat"
        ? svg`<path d="M12 3c1 3 4 4.5 4 8.5a4 4 0 0 1-8 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-5 0-7.5Z"/>`
        : line.icon === "cool"
          ? svg`<path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9M9.5 4.5 12 7l2.5-2.5M9.5 19.5 12 17l2.5 2.5"/>`
          : nothing;
    return html`<p class=${line.allowed ? "airco allowed" : "airco"}>
      ${line.icon ? html`<svg viewBox="0 0 24 24" aria-hidden="true">${icon}</svg>` : nothing}
      <span
        >${line.text}${
          line.estimate
            ? html` <span
                class="estimate"
                tabindex="0"
                title=${line.estimate}
                aria-label=${`${this.tr("airco.estimate")}: ${line.estimate}`}
                >${this.tr("airco.estimate")}</span
              >`
            : nothing
        }</span
      >
    </p>`;
  }

  private renderBattery(now: Now): TemplateResult {
    if (now.soc === null) {
      return html`<article class="card">
        <div class="label">${this.tr("battery.title")}</div>
        <p class="text">${this.tr("battery.unknown")}</p>
      </article>`;
    }
    const soc = Math.max(0, Math.min(100, now.soc));
    const buffer = Math.max(0, now.buffer_pct);
    const sets =
      now.sets_total <= 1
        ? now.sets_online >= 1
          ? this.tr("battery.set")
          : this.tr("battery.set_offline")
        : this.tr("battery.sets", {
            online: now.sets_online,
            total: now.sets_total,
          });
    return html`<article class="card">
      <div class="label">${this.tr("battery.title")}</div>
      <div class="big-row">
        <span class="big">${percent(soc, this.locale)}</span>
        ${
          now.energy_kwh !== null && now.capacity_kwh !== null
            ? html`<span class="muted"
                >${this.tr("battery.of", { energy: kwh(now.energy_kwh, this.locale), capacity: kwh(now.capacity_kwh, this.locale) })}</span
              >`
            : nothing
        }
      </div>
      <div
        class="bar"
        role="meter"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow=${Math.round(soc)}
        aria-label=${this.tr("battery.title")}
      >
        <div class="fill" style="width:${soc}%"></div>
        ${
          buffer > 0
            ? html`<div
                class="buffer"
                style="left:${now.min_soc}%;width:${Math.min(buffer, 100 - now.min_soc)}%"
              ></div>`
            : nothing
        }
        <div class="mark" style="left:${now.min_soc}%"></div>
        <div class="mark" style="left:${now.max_soc}%"></div>
      </div>
      <div class="foot">
        <span
          >${this.tr("battery.limits", { min: Math.round(now.min_soc), max: Math.round(now.max_soc) })}${
            buffer > 0
              ? ` · ${this.tr("battery.buffer", { value: Math.round(buffer) })}`
              : ""
          }</span
        >
        <span>${sets}</span>
      </div>
    </article>`;
  }

  private renderNext(now: Now): TemplateResult {
    const plan = now.plan;
    const label = (extra = ""): TemplateResult =>
      html`<div class="label">
        <span
          class="dot"
          style="background:${actionFill(plan?.next?.action)}"
        ></span
        >${this.tr("next.title")}${extra}
      </div>`;
    if (!now.price_entity) {
      return html`<article class="card">
        ${label()}
        <p class="text">${this.tr("next.no_price_source")}</p>
      </article>`;
    }
    if (!plan) {
      return html`<article class="card">
        ${label()}
        <p class="text">${this.tr("status.loading")}</p>
      </article>`;
    }
    if (plan.state === "no_prices") {
      const since = plan.no_prices_since ?? plan.calculated_at;
      return html`<article class="card">
        ${label()}
        <p class="text warn">
          ${this.tr("next.no_prices", { time: since ? clock(since, this.locale, this.timeZone) : "–" })}
        </p>
      </article>`;
    }
    const next = plan.next;
    const priceNow = plan.price_now
      ? html`<div class="foot">
          <span
            >${this.tr("next.price_now", { price: euro(plan.price_now.import, this.locale) })}</span
          >
        </div>`
      : nothing;
    if (!next) {
      return html`<article class="card">
        ${label()}
        <p class="text">${this.tr("next.none")}</p>
        ${priceNow}
      </article>`;
    }
    const minutes = minutesUntil(next.start, this.clockMs);
    const until =
      minutes <= 0
        ? this.tr("next.now")
        : this.tr("next.in", {
            time:
              minutes >= 60
                ? this.tr("next.hours", {
                    h: Math.floor(minutes / 60),
                    m: minutes % 60,
                  })
                : this.tr("next.minutes", { m: minutes }),
          });
    const time = clock(next.start, this.locale, this.timeZone);
    const action = this.tr(`action.${next.action}`);
    const headline = sameDay(next.start, this.clockMs, this.timeZone)
      ? this.tr("next.at", { time, action })
      : this.tr("next.tomorrow", { time, action });
    return html`<article class="card">
      ${label(` · ${until}`)}
      <div class="big">${headline}</div>
      <p class="text">${this.detail(plan)}</p>
      ${next.indicative ? html`<p class="text muted">${this.tr("next.indicative")}</p>` : nothing}
      ${priceNow}
    </article>`;
  }

  private detail(plan: PlanNow): string {
    const next = plan.next;
    if (!next) return "";
    const params = {
      kwh: kwh(next.kwh, this.locale),
      price: euro(next.price, this.locale),
    };
    return this.tr(`next.${next.action}`, params);
  }

  static override styles = [
    theme,
    css`
      :host {
        display: block;
        min-height: 100%;
        background: var(--z-bg);
        color: var(--z-text);
        font-family: var(--z-font);
        -webkit-font-smoothing: antialiased;
      }
      .page {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
      }
      header {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 12px 28px;
        padding: 12px 32px;
        background: var(--z-card);
        border-bottom: 1px solid var(--z-border);
      }
      .brand {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: var(--z-font-head);
        font-weight: 700;
        font-size: 22px;
        letter-spacing: 0.12em;
      }
      .brand img {
        display: block;
        width: 32px;
        height: 32px;
      }
      nav {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        flex: 1 1 auto;
      }
      .tab {
        min-height: 44px;
        padding: 0 16px;
        border: 0;
        border-radius: 999px;
        background: transparent;
        color: var(--z-text);
        font: inherit;
        font-size: 14px;
        cursor: pointer;
      }
      .tab:hover {
        background: var(--z-track);
      }
      .tab.active {
        background: var(--z-text);
        color: var(--z-on-text);
        font-weight: 600;
      }
      .tab:focus-visible {
        outline: 2px solid var(--z-charge);
        outline-offset: 2px;
      }
      .meta {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px 12px;
        font-size: 14px;
        color: var(--z-muted);
      }
      .chip {
        padding: 6px 12px;
        border-radius: 999px;
        border: 1px solid var(--z-border);
        color: var(--z-text);
      }
      .chip.live {
        background: var(--z-text);
        color: var(--z-on-text);
        border-color: var(--z-text);
      }
      button.chip,
      select.chip {
        font: inherit;
        font-size: inherit;
        background: var(--z-card);
        min-height: 36px;
        cursor: pointer;
      }
      button.chip.live {
        background: var(--z-text);
      }
      select.chip {
        padding-right: 28px;
      }
      .sr {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
      }
      .livewrap {
        position: relative;
      }
      .popover {
        position: absolute;
        right: 0;
        top: calc(100% + 8px);
        z-index: 5;
        width: min(320px, 85vw);
        box-sizing: border-box;
        padding: 14px 16px;
        border-radius: 12px;
        background: var(--z-card);
        border: 1px solid var(--z-border);
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.18);
        font-size: 14px;
        line-height: 1.5;
        text-align: left;
      }
      .popover p {
        margin: 6px 0;
        color: var(--z-muted);
      }
      .popover ul {
        margin: 0 0 6px;
        padding-left: 18px;
        color: var(--z-warn-text);
      }
      .popover .row,
      .fast {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
      }
      .popover .row {
        justify-content: flex-end;
        margin-top: 8px;
      }
      .popover button,
      .fast button {
        min-height: 44px;
        padding: 0 16px;
        border-radius: 10px;
        font: inherit;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
      }
      .ghost {
        border: 1px solid var(--z-border);
        background: var(--z-card);
        color: var(--z-text);
      }
      .primary {
        border: 0;
        background: var(--z-text);
        color: var(--z-on-text);
      }
      .fastnote {
        font-size: 13px;
        color: var(--z-muted);
      }
      .banner .link {
        margin-left: 8px;
        border: 0;
        background: none;
        color: inherit;
        font: inherit;
        font-weight: 600;
        text-decoration: underline;
        cursor: pointer;
      }
      :disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      .time {
        font-variant-numeric: tabular-nums;
      }
      main {
        flex: 1;
        width: 100%;
        max-width: 1376px;
        margin: 0 auto;
        box-sizing: border-box;
        padding: 24px 32px 40px;
        display: flex;
        flex-direction: column;
        gap: 20px;
      }
      .banner {
        padding: 12px 16px;
        border-radius: 12px;
        background: var(--z-warn-bg);
        color: var(--z-warn-text);
        font-size: 14px;
        line-height: 1.5;
      }
      .banner.info {
        background: var(--z-info-bg);
        color: var(--z-text);
      }
      .cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
      }
      .cards.stale,
      .duo.stale,
      zephyr-prices-plan.stale,
      zephyr-sets.stale,
      zephyr-settings.stale {
        opacity: 0.6;
      }
      .duo {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
      }
      .duo > .card {
        flex: 1 1 420px;
      }
      h2 {
        margin: 0;
        font-family: var(--z-font-head);
        font-size: 20px;
      }
      .blocks,
      .why {
        margin: 0;
        padding: 0;
        list-style: none;
        font-size: 14px;
        line-height: 1.5;
      }
      .blocks li {
        display: grid;
        grid-template-columns: minmax(110px, auto) 4px 1fr auto;
        align-items: center;
        gap: 12px;
        padding: 10px 0;
        border-top: 1px solid var(--z-border);
      }
      .blocks .when {
        font-weight: 600;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
      }
      .blocks .swatch {
        width: 4px;
        height: 24px;
        border-radius: 2px;
      }
      @media (max-width: 700px) {
        .blocks li {
          grid-template-columns: 4px 1fr auto;
          grid-template-areas: "sw when when" "sw what detail";
          gap: 2px 12px;
        }
        .blocks .when {
          grid-area: when;
        }
        .blocks .swatch {
          grid-area: sw;
          height: 100%;
        }
        .blocks .what {
          grid-area: what;
        }
        .blocks .detail {
          grid-area: detail;
        }
      }
      .blocks .detail {
        color: var(--z-muted);
        font-variant-numeric: tabular-nums;
        text-align: right;
      }
      .blocks em {
        color: var(--z-muted);
        font-style: normal;
      }
      .why {
        display: flex;
        flex-direction: column;
        gap: 10px;
      }
      .why li {
        padding-left: 18px;
        position: relative;
      }
      .why li::before {
        content: "";
        position: absolute;
        left: 4px;
        top: 0.6em;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--z-muted);
      }
      .card {
        background: var(--z-card);
        border: 1px solid var(--z-border);
        border-radius: 16px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        min-width: 0;
      }
      .skeleton {
        min-height: 150px;
        background: linear-gradient(
          90deg,
          var(--z-card),
          var(--z-track),
          var(--z-card)
        );
        background-size: 200% 100%;
        animation: shimmer 1.4s linear infinite;
      }
      @keyframes shimmer {
        to {
          background-position: -200% 0;
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .skeleton {
          animation: none;
        }
      }
      .coming {
        color: var(--z-muted);
        font-size: 15px;
      }
      .label {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--z-muted);
      }
      .dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex: none;
      }
      .big {
        font-family: var(--z-font-head);
        font-size: 26px;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
      }
      .big-row {
        display: flex;
        flex-wrap: wrap;
        align-items: baseline;
        gap: 4px 10px;
      }
      .text {
        margin: 0;
        font-size: 14px;
        line-height: 1.5;
        color: var(--z-muted);
      }
      .airco {
        margin: 0;
        display: flex;
        align-items: flex-start;
        gap: 8px;
        line-height: 1.5;
        font-size: 14px;
        font-weight: 600;
        color: var(--z-text);
      }
      .airco.allowed {
        font-weight: 400;
        color: var(--z-muted);
      }
      .airco svg {
        width: 18px;
        height: 18px;
        fill: none;
        stroke: currentColor;
        stroke-width: 1.8;
        stroke-linecap: round;
        stroke-linejoin: round;
        flex: none;
        margin-top: 1px;
      }
      .estimate {
        white-space: nowrap;
        padding: 2px 8px;
        border-radius: 999px;
        background: var(--z-info-bg);
        font-size: 11px;
        font-weight: 600;
        cursor: help;
      }
      .text.warn {
        color: var(--z-warn-text);
        background: var(--z-warn-bg);
        padding: 10px 12px;
        border-radius: 10px;
      }
      .muted {
        font-size: 14px;
        color: var(--z-muted);
      }
      .foot {
        margin-top: auto;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 4px 12px;
        font-size: 13px;
        color: var(--z-muted);
        font-variant-numeric: tabular-nums;
      }
      .bar {
        position: relative;
        height: 12px;
        background: var(--z-track);
        border-radius: 6px;
        overflow: hidden;
      }
      .fill {
        height: 100%;
        background: var(--z-text);
        border-radius: 6px;
      }
      .buffer {
        position: absolute;
        top: 0;
        bottom: 0;
        background: repeating-linear-gradient(
          45deg,
          var(--z-hold-a) 0 3px,
          transparent 3px 6px
        );
        opacity: 0.8;
      }
      .mark {
        position: absolute;
        top: 0;
        bottom: 0;
        border-left: 2px solid var(--z-card);
      }
      @media (max-width: 700px) {
        header {
          padding: 10px 16px;
        }
        main {
          padding: 16px;
        }
      }
    `,
  ];
}

declare global {
  interface HTMLElementTagNameMap {
    "zephyr-panel": ZephyrPanel;
  }
}
