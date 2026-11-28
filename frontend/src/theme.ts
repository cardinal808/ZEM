// Colour tokens in one place (UI-ontwerpbrief §8: provisional colours), light and dark.
import { css } from "lit";

export const theme = css`
  :host {
    --z-bg: #f4f5f2;
    --z-card: #ffffff;
    --z-border: #e1e4de;
    --z-text: #1a1e1c;
    --z-muted: #565d59;
    --z-track: #e8ebe6;
    --z-on-text: #ffffff;
    --z-charge: #1f5fc4;
    --z-deliver: #f0a04b;
    --z-hold-a: #aeb8c8;
    --z-hold-b: #eef1f6;
    --z-export: #16917a;
    --z-import: #c62828;
    --z-solar: #f2c230;
    --z-warn-bg: #fdebd5;
    --z-warn-text: #5c3300;
    --z-info-bg: #eef3fb;
    --z-bar: #8c9792;
    --z-good-bg: #ddf2ec;
    --z-good-text: #0b5a4b;
    --z-bad-bg: #fbdcdc;
    --z-bad-text: #7a1414;
    --z-font: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
    --z-font-head: "Space Grotesk", Inter, system-ui, sans-serif;
  }
  :host([dark]) {
    --z-bg: #0f1211;
    --z-card: #191d1b;
    --z-border: #2b312e;
    --z-text: #ecefec;
    --z-muted: #a4aca7;
    --z-track: #2b312e;
    --z-on-text: #0f1211;
    --z-charge: #3d7be6;
    --z-deliver: #f2a65a;
    --z-hold-a: #56607a;
    --z-hold-b: #232833;
    --z-export: #3cc4a8;
    --z-import: #ff7a7a;
    --z-solar: #e8c547;
    --z-warn-bg: #3a2a14;
    --z-warn-text: #f7d4a8;
    --z-info-bg: #1b2433;
    --z-bar: #6f7a75;
    --z-good-bg: #163b33;
    --z-good-text: #9fe3cf;
    --z-bad-bg: #3d1a1a;
    --z-bad-text: #f5b4b4;
  }
`;

/** Fill of an action swatch (hold is striped, so colour is never the only cue). */
export function actionFill(action: string | null | undefined): string {
  switch (action) {
    case "charge":
      return "var(--z-charge)";
    case "deliver":
      return "var(--z-deliver)";
    case "export":
      return "var(--z-export)";
    case "hold":
      return "repeating-linear-gradient(45deg, var(--z-hold-a) 0 3px, var(--z-hold-b) 3px 6px)";
    default:
      return "var(--z-muted)";
  }
}
