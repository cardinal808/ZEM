// Copies the used font files (SIL OFL 1.1) and the logo next to the built panel.
import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";

const out = "../custom_components/zephyr/frontend/fonts";
const files = [
  ["@fontsource/inter", "inter-latin-400-normal.woff2"],
  ["@fontsource/inter", "inter-latin-600-normal.woff2"],
  ["@fontsource/inter", "inter-latin-700-normal.woff2"],
  ["@fontsource/space-grotesk", "space-grotesk-latin-700-normal.woff2"],
];
mkdirSync(out, { recursive: true });
for (const [pkg, file] of files) copyFileSync(`node_modules/${pkg}/files/${file}`, `${out}/${file}`);
const licence = (pkg) => readFileSync(`node_modules/${pkg}/LICENSE`, "utf8");
writeFileSync(
  `${out}/LICENSE.txt`,
  `Inter\n=====\n${licence("@fontsource/inter")}\n\nSpace Grotesk\n=============\n${licence("@fontsource/space-grotesk")}\n`,
);
copyFileSync("../custom_components/zephyr/brand/icon.png", "../custom_components/zephyr/frontend/logo.png");
console.log(`assets: ${files.length} fonts and the logo`);
