/**
 * Register a custom element only once.
 *
 * Home Assistant can load the panel module a second time (a new version with another cache
 * key while the old one is still registered). Lit's `@customElement` then throws "the name …
 * has already been used with this registry" for the first element of the bundle, and the rest
 * of the module stops. The first registration stays; the second load just reuses it.
 */
export function element(name: string) {
  return <T extends CustomElementConstructor>(target: T): T => {
    if (!customElements.get(name)) customElements.define(name, target);
    return target;
  };
}
