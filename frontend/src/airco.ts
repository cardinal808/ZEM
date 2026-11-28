// The air conditioner that may not run on the battery, in the card Now (SPEC-ui-airco §3.1, UI-A1).
import { t, type Lang } from "./i18n";

export interface Excluded {
  active: boolean;
  power_w: number;
  excluded_w: number;
  mode: string | null;
  action: string | null;
  blocked_modes: string[];
  has_climate: boolean;
  seconds_since_step: number | null;
  mean_step_interval_s: number | null;
  last_step_kwh: number;
  quality: "ok" | "fading" | "starting" | "no_climate";
}

export interface AircoLine {
  text: string;
  /** The line is about a load that may use the battery (shown grey). */
  allowed: boolean;
  /** Show the label "estimate" with its explanation. */
  estimate: string | null;
  icon: "heat" | "cool" | null;
}

const IDLE = new Set(["idle", "off"]);

function kw(watts: number, locale: string): string {
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }).format(watts / 1000);
}

/** The line for the card Now, or null when there is nothing to say (not set up, or the airco is off). */
export function aircoLine(
  ex: Excluded | null | undefined,
  lang: Lang,
  locale: string,
): AircoLine | null {
  if (!ex) return null;
  const icon = ex.mode === "heat" ? "heat" : ex.mode === "cool" ? "cool" : null;
  if (ex.active) {
    let text =
      ex.power_w > 0
        ? t(lang, "airco.blocked", { kw: kw(ex.power_w, locale) })
        : t(lang, "airco.blocked_unknown");
    if (ex.excluded_w > 0 && ex.excluded_w < ex.power_w - 50)
      text += ` ${t(lang, "airco.kept_off", { kw: kw(ex.excluded_w, locale) })}`;
    const estimate =
      ex.quality === "fading" || ex.quality === "starting"
        ? t(lang, "airco.estimate_more", {
            kwh: new Intl.NumberFormat(locale, {
              maximumFractionDigits: 2,
            }).format(ex.last_step_kwh || 0.25),
          })
        : null;
    return { text, allowed: false, estimate, icon };
  }
  if (
    ex.has_climate &&
    ex.mode &&
    ex.mode !== "off" &&
    ex.action &&
    !IDLE.has(ex.action)
  ) {
    return {
      text: t(lang, "airco.allowed", {
        mode: t(lang, `settings.options.${ex.mode}`).toLowerCase(),
      }),
      allowed: true,
      estimate: null,
      icon,
    };
  }
  return null;
}
