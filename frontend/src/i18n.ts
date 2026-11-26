// NL and EN texts of the panel (SPEC-ui §2). Dutch for "nl*", English otherwise.
import en from "./locales/en.json";
import nl from "./locales/nl.json";

type Texts = typeof en;
const TEXTS: Record<"nl" | "en", Texts> = { nl, en };

export type Lang = "nl" | "en";

export function language(code: string | undefined): Lang {
  return code?.toLowerCase().startsWith("nl") ? "nl" : "en";
}

/** Text by dotted key, with {name} placeholders. Falls back to English, then to the key. */
export function t(lang: Lang, key: string, params: Record<string, string | number> = {}): string {
  const find = (texts: unknown): string | undefined => {
    let node: unknown = texts;
    for (const part of key.split(".")) {
      if (node === null || typeof node !== "object") return undefined;
      node = (node as Record<string, unknown>)[part];
    }
    return typeof node === "string" ? node : undefined;
  };
  const template = find(TEXTS[lang]) ?? find(TEXTS.en) ?? key;
  return template.replace(/\{(\w+)\}/g, (match, name: string) => (name in params ? String(params[name]) : match));
}
