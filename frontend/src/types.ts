// Shapes of Home Assistant objects the panel uses, and of the zephyr/* messages (SPEC-ui §3).

export interface HassConnection {
  subscribeMessage<T>(
    callback: (message: T) => void,
    message: Record<string, unknown>,
  ): Promise<() => Promise<void>>;
  addEventListener(event: "ready" | "disconnected", listener: () => void): void;
  removeEventListener(
    event: "ready" | "disconnected",
    listener: () => void,
  ): void;
}

export interface HomeAssistant {
  connection: HassConnection;
  callWS<T>(message: Record<string, unknown>): Promise<T>;
  states?: Record<string, { attributes?: Record<string, unknown> }>;
  language: string;
  locale?: { language: string };
  themes?: { darkMode?: boolean };
  user?: { is_admin: boolean };
  config: { time_zone: string };
}

export interface PanelInfo {
  config?: { static?: string; version?: string };
}

export interface Localized {
  nl: string;
  en: string;
}

export interface NextBlock {
  action: PlanAction;
  start: string;
  end: string;
  kwh: number;
  price: number;
  indicative: boolean;
}

export type PlanAction = "charge" | "hold" | "deliver" | "export";

export interface PlanNow {
  state: string;
  action: PlanAction;
  reason: Localized;
  calculated_at: string | null;
  no_prices_since: string | null;
  price_now: { import: number; export: number } | null;
  next: NextBlock | null;
}

export interface Now {
  updated_at: string;
  mode: string;
  modes: string[];
  previous_mode: string;
  entities: { mode: string | null; live: string | null };
  live: boolean;
  blockers: string[];
  action: string | null;
  reason: Localized | null;
  reason_code: string | null;
  setpoint_w: number | null;
  grid_w: number | null;
  /** Shadow mode: the real meter; grid_w is then what the meter would show if ZEPHYR controlled. */
  grid_measured_w?: number | null;
  battery_w: number | null;
  solar_w: number | null;
  /** Part from inverters the sets do not see; estimated = from the solar energy counter. */
  solar_external_w?: number | null;
  /** PV on the sets themselves. */
  solar_sets_w?: number | null;
  solar_estimated?: boolean;
  soc: number | null;
  energy_kwh: number | null;
  capacity_kwh: number | null;
  min_soc: number;
  max_soc: number;
  buffer_pct: number;
  sets_online: number;
  sets_total: number;
  price_entity: boolean;
  plan: PlanNow | null;
  excluded?: import("./airco").Excluded | null;
  /** Goes up when appliances or their planned runs change (B36): fetch zephyr/appliances again. */
  appliances_revision?: number | null;
  /** Curtailing at a negative export price now (B45); null without a curtail manager. */
  curtail?: {
    mode: string;
    negative: boolean;
    active: boolean;
    percent: number | null;
    switch_on: boolean | null;
    export_blocked: boolean;
  } | null;
}

export type SubscribeEvent = { type: "now"; data: Now } | { type: "unloaded" };
