/**
 * Own picture for the screen Stroom (Instellingen → Apparaten): upload, then per item a tap for
 * its box and a tap for the spot its line goes to. Positions are fractions of the picture, so a
 * picture of any size works; the picture itself stays in the user's Home Assistant.
 */
import { LitElement, css, html, nothing, svg, type TemplateResult } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import { COLORS, ITEM_KEYS, OWN_BOX_W, ownLine, type ItemKey } from "./house";
import { t, type Lang } from "./i18n";
import type { HousePicture } from "./stroom";

type Place = { box?: [number, number]; point?: [number, number] };
type Call = (msg: Record<string, unknown>) => Promise<unknown>;

const MAX_W = 1800;

const COLOR: Record<ItemKey, string> = {
  roof: COLORS.sun,
  shed_solar: COLORS.sun,
  battery: COLORS.batt,
  grid: COLORS.grid,
  ev: COLORS.batt,
  attic: COLORS.house,
  first: COLORS.house,
  ground: COLORS.house,
  shed: COLORS.batt,
};

/** Scale an image file down to at most MAX_W wide; WebP where the browser can, else JPEG. */
export async function shrink(file: Blob): Promise<{ data: string; width: number; height: number }> {
  const bitmap = await createImageBitmap(file);
  const scale = Math.min(1, MAX_W / bitmap.width);
  const width = Math.round(bitmap.width * scale);
  const height = Math.round(bitmap.height * scale);
  const canvas = document.createElement("canvas");
  canvas.width = width;
  canvas.height = height;
  canvas.getContext("2d")?.drawImage(bitmap, 0, 0, width, height);
  const blob = await new Promise<Blob>((ok, fail) =>
    canvas.toBlob((b) => (b ? ok(b) : fail(new Error("canvas"))), "image/webp", 0.85),
  );
  const bytes = new Uint8Array(await blob.arrayBuffer());
  let bin = "";
  for (let i = 0; i < bytes.length; i += 0x8000) bin += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return { data: btoa(bin), width, height };
}

/** The next item without a box, after `from`; null when all are placed or hidden. */
export function nextUnplaced(
  items: Partial<Record<string, Place>>,
  hidden: string[],
  from: ItemKey | null,
): ItemKey | null {
  const start = from ? ITEM_KEYS.indexOf(from) + 1 : 0;
  for (let i = 0; i < ITEM_KEYS.length; i++) {
    const k = ITEM_KEYS[(start + i) % ITEM_KEYS.length];
    if (!hidden.includes(k) && !items[k]?.point) return k;
  }
  return null;
}

@customElement("zephyr-house-editor")
export class ZephyrHouseEditor extends LitElement {
  @property({ attribute: false }) picture: HousePicture | null = null;
  @property({ attribute: false }) canEdit = false;
  @property({ attribute: false }) uiLang: Lang = "en";
  @property({ attribute: false }) call?: Call;
  @property({ attribute: false }) sign?: (path: string) => Promise<string>;
  /** Asks the panel to load the settings (and so this picture) again. */
  @property({ attribute: false }) changed?: () => Promise<void>;

  @state() private draft: { custom: boolean; items: Partial<Record<string, Place>>; hidden: string[] } | null = null;
  @state() private selected: ItemKey | null = null;
  @state() private busy = false;
  @state() private error: string | null = null;
  @state() private url: string | null = null;
  private signed = -1;

  private tr(key: string, params: Record<string, string | number> = {}): string {
    return t(this.uiLang, key, params);
  }

  private label(k: ItemKey): string {
    return ["attic", "first", "ground", "shed"].includes(k)
      ? this.tr(`settings.floors.${k}`)
      : this.tr(`house.${k}`);
  }

  private get current() {
    const p = this.picture;
    return this.draft ?? { custom: !!p?.custom, items: p?.items ?? {}, hidden: p?.hidden ?? [] };
  }

  protected override willUpdate(): void {
    const p = this.picture;
    if (!p?.has_image || !this.sign || p.version === this.signed) return;
    this.signed = p.version;
    void this.sign(`/api/zephyr/house_picture?v=${p.version}`).then(
      (u) => (this.url = u),
      () => (this.signed = -1),
    );
  }

  protected override render(): TemplateResult {
    const p = this.picture;
    const cur = this.current;
    const edit = this.canEdit && !this.busy;
    return html`<h3>${this.tr("picture.title")}</h3>
      <div class="choice" role="radiogroup">
        <button
          type="button"
          role="radio"
          aria-checked=${!cur.custom}
          class=${cur.custom ? "" : "on"}
          ?disabled=${!edit}
          @click=${() => this.patch({ custom: false })}
        >
          ${this.tr("picture.default")}
        </button>
        <button
          type="button"
          role="radio"
          aria-checked=${cur.custom}
          class=${cur.custom ? "on" : ""}
          ?disabled=${!edit}
          @click=${() => (p?.has_image ? this.patch({ custom: true }) : this.pickFile())}
        >
          ${this.tr("picture.own")}
        </button>
      </div>
      <p class="muted">${this.tr("picture.note")}</p>
      ${this.busy ? html`<p class="muted" role="status">${this.tr("picture.uploading")}</p>` : nothing}
      ${this.error ? html`<p class="err" role="alert">${this.tr("picture.error", { msg: this.error })}</p>` : nothing}
      <input type="file" accept="image/jpeg,image/png,image/webp" hidden @change=${this.onFile} />
      ${cur.custom && p?.has_image ? this.renderPlacing(p, cur, edit) : nothing}
      ${this.draft && this.canEdit
        ? html`<div class="row">
            <button type="button" class="primary" ?disabled=${this.busy} @click=${() => void this.save()}>
              ${this.tr("settings.save")}
            </button>
            <button type="button" class="ghost" @click=${() => ((this.draft = null), (this.selected = null))}>
              ${this.tr("settings.discard")}
            </button>
          </div>`
        : nothing}`;
  }

  private renderPlacing(
    p: HousePicture,
    cur: { items: Partial<Record<string, Place>>; hidden: string[] },
    edit: boolean,
  ): TemplateResult {
    const w = p.width || 1600;
    const h = p.height || 1200;
    const sel = this.selected;
    const step = sel && cur.items[sel]?.box && !cur.items[sel]?.point ? "point" : "box";
    const shown = ITEM_KEYS.filter((k) => !cur.hidden.includes(k) && cur.items[k]?.box);
    return html`<p class="hint">
        ${sel ? this.tr(`picture.step_${step}`, { item: this.label(sel) }) : this.tr("picture.pick")}
      </p>
      <div
        class=${edit && sel ? "stage active" : "stage"}
        style=${`aspect-ratio:${w}/${h}`}
        @click=${(e: MouseEvent) => edit && this.tap(e)}
      >
        ${this.url ? html`<img src=${this.url} alt="" draggable="false" />` : nothing}
        <svg viewBox="0 0 ${w} ${h}" aria-hidden="true">
          ${shown.map((k) => {
            const place = cur.items[k];
            if (!place?.box || !place.point) return nothing;
            const pts = ownLine(place.box, place.point, w, h);
            const end = pts[pts.length - 1];
            return svg`<path d=${`M${pts.map((q) => q.join(" ")).join(" L")}`} stroke=${COLOR[k]} stroke-width=${w / 300} fill="none"></path>
              <circle cx=${end[0]} cy=${end[1]} r=${w / 150} fill=${COLOR[k]}></circle>`;
          })}
        </svg>
        ${shown.map((k) => {
          const [x, y] = cur.items[k]?.box ?? [0, 0];
          return html`<span
            class=${k === sel ? "tag sel" : "tag"}
            style=${`left:${Math.min(x, 1 - OWN_BOX_W) * 100}%;top:${y * 100}%;width:${OWN_BOX_W * 100}%;--c:${COLOR[k]}`}
            >${this.label(k)}</span
          >`;
        })}
      </div>
      <div class="chips">
        ${ITEM_KEYS.map((k) => {
          const hidden = cur.hidden.includes(k);
          const done = !!cur.items[k]?.point;
          return html`<button
            type="button"
            class=${["chip", k === sel ? "sel" : "", done ? "done" : "", hidden ? "hid" : ""].join(" ")}
            ?disabled=${!edit}
            title=${hidden ? this.tr("picture.hidden") : done ? "" : this.tr("picture.unplaced")}
            @click=${() => (this.selected = k === sel ? null : k)}
          >
            ${done && !hidden ? "✓ " : ""}${this.label(k)}
          </button>`;
        })}
      </div>
      <div class="row">
        ${sel
          ? html`<button type="button" ?disabled=${!edit} @click=${() => this.toggleHidden(sel)}>
                ${cur.hidden.includes(sel) ? this.tr("picture.show") : this.tr("picture.hide")}
              </button>
              <button type="button" ?disabled=${!edit} @click=${() => this.place(sel, {})}>
                ${this.tr("picture.reset")}
              </button>`
          : nothing}
        <button type="button" class="ghost" ?disabled=${!edit} @click=${() => this.pickFile()}>
          ${this.tr("picture.replace")}
        </button>
        <button type="button" class="ghost" ?disabled=${!edit} @click=${() => void this.removePicture()}>
          ${this.tr("picture.delete")}
        </button>
      </div>`;
  }

  private patch(p: Partial<{ custom: boolean; items: Partial<Record<string, Place>>; hidden: string[] }>): void {
    this.draft = { ...this.current, ...p };
  }

  private place(k: ItemKey, place: Place): void {
    this.patch({ items: { ...this.current.items, [k]: place } });
  }

  private toggleHidden(k: ItemKey): void {
    const hidden = this.current.hidden;
    this.patch({ hidden: hidden.includes(k) ? hidden.filter((x) => x !== k) : [...hidden, k] });
  }

  private tap(e: MouseEvent): void {
    const k = this.selected;
    if (!k) return;
    const r = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const at: [number, number] = [
      Math.round(((e.clientX - r.left) / r.width) * 1000) / 1000,
      Math.round(((e.clientY - r.top) / r.height) * 1000) / 1000,
    ];
    const old = this.current.items[k] ?? {};
    if (!old.box || old.point) {
      this.place(k, { box: at });
    } else {
      this.place(k, { box: old.box, point: at });
      this.selected = nextUnplaced(this.current.items, this.current.hidden, k);
    }
  }

  private pickFile(): void {
    this.renderRoot.querySelector<HTMLInputElement>("input[type=file]")?.click();
  }

  private onFile = async (e: Event): Promise<void> => {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = "";
    if (!file || !this.call) return;
    this.busy = true;
    this.error = null;
    try {
      const img = await shrink(file);
      await this.call({ type: "zephyr/house/picture/upload", ...img });
      this.draft = null;
      this.selected = nextUnplaced(this.picture?.items ?? {}, this.picture?.hidden ?? [], null);
      await this.changed?.();
    } catch (err) {
      this.error = (err as { message?: string })?.message ?? String(err);
    } finally {
      this.busy = false;
    }
  };

  private async save(): Promise<void> {
    const d = this.draft;
    if (!d || !this.call) return;
    this.busy = true;
    try {
      await this.call({ type: "zephyr/house/picture", custom: d.custom, items: d.items, hidden: d.hidden });
      this.draft = null;
      this.selected = null;
      await this.changed?.();
    } catch (err) {
      this.error = (err as { message?: string })?.message ?? String(err);
    } finally {
      this.busy = false;
    }
  }

  private async removePicture(): Promise<void> {
    if (!this.call) return;
    this.busy = true;
    try {
      await this.call({ type: "zephyr/house/picture/delete" });
      this.draft = null;
      this.selected = null;
      this.url = null;
      await this.changed?.();
    } finally {
      this.busy = false;
    }
  }

  static override styles = css`
    :host {
      display: block;
      margin: 8px 0 20px;
    }
    h3 {
      font-size: 15px;
      font-weight: 600;
      margin: 0 0 8px;
    }
    .muted,
    .hint {
      color: var(--z-muted);
      font-size: 13px;
      margin: 8px 0;
    }
    .hint {
      color: var(--z-text);
    }
    .err {
      color: var(--z-danger, #c62828);
      font-size: 13px;
    }
    .choice,
    .row,
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .row {
      margin-top: 12px;
    }
    button {
      font: inherit;
      font-size: 13px;
      padding: 7px 12px;
      border-radius: 10px;
      border: 1px solid var(--z-border);
      background: var(--z-card);
      color: var(--z-text);
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    button.on,
    button.primary {
      background: var(--z-text);
      color: var(--z-card);
      border-color: var(--z-text);
    }
    button.ghost {
      border-color: transparent;
      text-decoration: underline;
    }
    .chip {
      padding: 4px 10px;
      border-radius: 999px;
    }
    .chip.done {
      border-color: #2e9e6a;
    }
    .chip.sel {
      outline: 2px solid #3b82f6;
    }
    .chip.hid {
      text-decoration: line-through;
      opacity: 0.6;
    }
    .stage {
      position: relative;
      width: 100%;
      max-width: 760px;
      border-radius: 12px;
      overflow: hidden;
      background: #0f1d27;
      margin: 8px 0 12px;
      user-select: none;
    }
    .stage.active {
      cursor: crosshair;
    }
    .stage img {
      display: block;
      width: 100%;
      height: 100%;
    }
    .stage svg {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    }
    .tag {
      position: absolute;
      box-sizing: border-box;
      padding: 4px 8px;
      font-size: 12px;
      color: #fff;
      background: rgba(12, 26, 36, 0.9);
      border: 2px solid var(--c);
      border-radius: 8px;
      pointer-events: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .tag.sel {
      box-shadow: 0 0 0 2px #3b82f6;
    }
  `;
}
