// Shapes of Home Assistant objects the panel uses, and of the zephyr/* messages (SPEC-ui §3).

export interface HassConnection {
  subscribeMessage<T>(callback: (message: T) => void, message: Record<string, unknown>): Promise<() => Promise<void>>;
  addEventListener(event: "ready" | "disconnected", listener: () => void): void;
  removeEventListener(event: "ready" | "disconnected", listener: () => void): void;
}

export interface HomeAssistant {
  connection: HassConnection;
  callWS<T>(message: Record<string, unknown>): Promise<T>;
  language: string;
  locale?: { language: string };
  themes?: { darkMode?: boolean };
  user?: { is_admin: boolean };
  config: { time_zone: string };
}

export interface PanelInfo {
  config?: { static?: string };
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
  live: boolean;
  blockers: string[];
  action: string | null;
  reason: Localized | null;
  reason_code: string | null;
  setpoint_w: number | null;
  grid_w: number | null;
  battery_w: number | null;
  solar_w: number | null;
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
}

export type SubscribeEvent = { type: "now"; data: Now } | { type: "unloaded" };
