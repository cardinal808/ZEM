// Changing settings from the panel (SPEC-ui §3.4, UI-7): pure helpers, tested in test/settings-edit.test.ts.

export interface EntityChoice {
  id: string;
  name: string;
}

export interface SetResult {
  ok: boolean;
  errors?: Record<string, string>;
  changed?: string[];
  reload?: boolean;
}

/** Number typed by the user: comma or point as decimal sign, spaces and thousands points ignored. null when not a number. */
export function parseNumber(text: string, locale: string): number | null {
  let s = text.trim().replace(/\s/g, "");
  if (!s) return null;
  const decimal = new Intl.NumberFormat(locale).format(1.5).includes(",") ? "," : ".";
  if (decimal === ",") s = s.replace(/\.(?=\d{3}(\D|$))/g, "").replace(",", ".");
  else s = s.replace(/,(?=\d{3}(\D|$))/g, "");
  if (!/^[-+]?\d*\.?\d+$/.test(s)) return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

/** Entities that fit a field: domain and, if given, device class; sorted by name. */
export function entityChoices(
  states: Record<string, { attributes?: Record<string, unknown> }> | undefined,
  domain: string,
  deviceClass: string | null,
): EntityChoice[] {
  if (!states) return [];
  return Object.entries(states)
    .filter(([id, st]) => id.startsWith(`${domain}.`) && (!deviceClass || st.attributes?.device_class === deviceClass))
    .map(([id, st]) => ({ id, name: String(st.attributes?.friendly_name ?? id) }))
    .sort((a, b) => a.name.localeCompare(b.name) || a.id.localeCompare(b.id));
}

/** The entity id behind what was typed or picked: an id, or a friendly name that is unique. */
export function resolveEntity(text: string, choices: EntityChoice[]): string | null {
  const s = text.trim();
  if (!s) return null;
  const byId = choices.find((c) => c.id === s);
  if (byId) return byId.id;
  const inLabel = /\(([a-z0-9_]+\.[a-z0-9_]+)\)$/.exec(s);
  if (inLabel && choices.some((c) => c.id === inLabel[1])) return inLabel[1];
  const byName = choices.filter((c) => c.name.toLowerCase() === s.toLowerCase());
  return byName.length === 1 ? byName[0].id : null;
}

/** Label in the picker list: name with the id, so two entities with the same name stay apart. */
export function choiceLabel(c: EntityChoice): string {
  return c.name === c.id ? c.id : `${c.name} (${c.id})`;
}

/** Same value (lists compared item by item). */
export function sameValue(a: unknown, b: unknown): boolean {
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((v, i) => v === b[i]);
  return (a ?? null) === (b ?? null);
}

/** A choice in a multi-select switched on or off, in the order of the options. */
export function toggleChoice(value: string[], option: string, options: string[]): string[] {
  const on = value.includes(option) ? value.filter((v) => v !== option) : [...value, option];
  return options.filter((o) => on.includes(o));
}

/** Seconds as "8,5 min" or "40 s". */
export function stepInterval(seconds: number, locale: string): string {
  if (seconds < 90) return `${Math.round(seconds)} s`;
  return `${new Intl.NumberFormat(locale, { maximumFractionDigits: 1 }).format(seconds / 60)} min`;
}
