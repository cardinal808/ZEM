import { defineConfig } from "vite";

// One ES module for Home Assistant's panel_custom; HACS only ships custom_components/.
export default defineConfig({
  build: {
    outDir: "../custom_components/zephyr/frontend",
    emptyOutDir: false,
    target: "es2022",
    minify: true,
    sourcemap: false,
    lib: {
      entry: "src/zephyr-panel.ts",
      formats: ["es"],
      fileName: () => "zephyr-panel.js",
    },
  },
});
