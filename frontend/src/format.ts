// Number, money and time formatting in the user's notation (SPEC-ui §2: € 0,27 / €0.27).

const MINUS = "−";

// Creating an Intl formatter is slow (the 48-hour chart formats hundreds of dates per render):
// keep one per locale and options.
const dateFormats = new Map<string, Intl.DateTimeFormat>();
const numberFormats = new Map<string, Intl.NumberFormat>();

/** A cached ``Intl.DateTimeFormat``. */
export function dateFormat(
  locale: string,
  options: Intl.DateTimeFormatOptions,
): Intl.DateTimeFormat {
  const key = `${locale}|${JSON.stringify(options)}`;
  let f = dateFormats.get(key);
  if (!f) {
    f = new Intl.DateTimeFormat(locale, options);
    dateFormats.set(key, f);
  }
  return f;
}

/** A cached ``Intl.NumberFormat``. */
export function numberFormat(
  locale: string,
  options: Intl.NumberFormatOptions,
): Intl.NumberFormat {
  const key = `${locale}|${JSON.stringify(options)}`;
  let f = numberFormats.get(key);
  if (!f) {
    f = new Intl.NumberFormat(locale, options);
    numberFormats.set(key, f);
  }
  return f;
}

export function number(value: number, locale: string, digits: number): string {
  return numberFormat(locale, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

/** Price per kWh: two decimals, true minus sign. */
export function euro(value: number, locale: string): string {
  const text = numberFormat(locale, {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(value));
  return value < 0 ? MINUS + text : text;
}

/** Power without sign (the action tells the direction). Rounded to 10 W below 1 kW. */
export function watts(value: number, locale: string): string {
  const abs = Math.abs(value);
  if (abs >= 1000) return `${number(abs / 1000, locale, 2)} kW`;
  return `${number(Math.round(abs / 10) * 10, locale, 0)} W`;
}

/** Power with sign: + import/charging, − export/delivering. */
export function signedWatts(value: number, locale: string): string {
  const sign = value > 0 ? "+" : value < 0 ? MINUS : "";
  return sign + watts(value, locale);
}

export function kwh(value: number, locale: string, digits = 1): string {
  return `${number(value, locale, digits)} kWh`;
}

export function percent(value: number, locale: string): string {
  return `${number(Math.round(value), locale, 0)} %`;
}

/** Clock time hh:mm in the Home Assistant time zone. */
export function clock(iso: string, locale: string, timeZone: string): string {
  return dateFormat(locale, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone,
  }).format(new Date(iso));
}

/** "vr 20 nov" / "Fri 20 Nov". */
export function day(iso: string, locale: string, timeZone: string): string {
  return dateFormat(locale, {
    weekday: "short",
    day: "numeric",
    month: "short",
    timeZone,
  }).format(new Date(iso));
}

/** Minutes until ``iso`` from ``nowMs``, never negative. */
export function minutesUntil(iso: string, nowMs: number): number {
  return Math.max(0, Math.round((new Date(iso).getTime() - nowMs) / 60000));
}

/** Two dates on the same calendar day in ``timeZone``. */
export function sameDay(
  a: string | number,
  b: string | number,
  timeZone: string,
): boolean {
  const f = dateFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone,
  });
  return f.format(new Date(a)) === f.format(new Date(b));
}
