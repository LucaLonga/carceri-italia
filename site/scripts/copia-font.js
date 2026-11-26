// Prepara i font (IBM Plex, licenza OFL 1.1) per il sito: npm run font
// Il bundler CSS di Framework non accetta file .woff2, quindi i font entrano in
// src/assets/fonts/plex.css come data URI. Il file resta nel repository: il sito non chiama CDN.
import {copyFileSync, mkdirSync, readFileSync, writeFileSync} from "node:fs";
const dest = "src/assets/fonts";
mkdirSync(dest, {recursive: true});
const facce = [
  ["IBM Plex Sans", 400, "ibm-plex-sans", "ibm-plex-sans-latin-400-normal.woff2"],
  ["IBM Plex Sans", 600, "ibm-plex-sans", "ibm-plex-sans-latin-600-normal.woff2"],
  ["IBM Plex Mono", 400, "ibm-plex-mono", "ibm-plex-mono-latin-400-normal.woff2"]
];
let css = "/* Generato da site/scripts/copia-font.js. IBM Plex, SIL Open Font License 1.1 (LICENSE-OFL.txt). */\n";
for (const [famiglia, peso, pkg, f] of facce) {
  const b64 = readFileSync(`node_modules/@fontsource/${pkg}/files/${f}`).toString("base64");
  css += `@font-face{font-family:"${famiglia}";font-weight:${peso};font-style:normal;font-display:swap;src:url(data:font/woff2;base64,${b64}) format("woff2");}\n`;
}
writeFileSync(`${dest}/plex.css`, css);
copyFileSync("node_modules/@fontsource/ibm-plex-sans/LICENSE", `${dest}/LICENSE-OFL.txt`);
console.log("font scritti in", `${dest}/plex.css`, Math.round(css.length / 1024), "kB");
