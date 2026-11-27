// Schizzi statici per scegliere la forma del passo 7 del racconto ("cosa è cambiato dal 2019").
// Uso: node scripts/schizzi-passo7.js <cartogramma.json> <istituti.json> <serie.csv> <storico.json> <cartella>
// Produce variante-A.svg (flussi sulla mappa principale) e variante-B.svg (schema a parte, non geografico).
import {readFileSync, writeFileSync} from "node:fs";
const [carto, ist, serieCsv, storico, out] = process.argv.slice(2);
const C = JSON.parse(readFileSync(carto, "utf8")).disposizioni.desktop;
const I = new Map(JSON.parse(readFileSync(ist, "utf8")).istituti.map((i) => [i.codice, i]));
const S = JSON.parse(readFileSync(storico, "utf8"));
const righe = readFileSync(serieCsv, "utf8").trim().split("\n").slice(1).map((l) => l.split(","));
const primo = {};
for (const [data, fonte, cod, , , , pres] of righe) if (fonte === "ministero" && pres && !(cod in primo)) primo[cod] = {data, pres: +pres};
const font = `font-family="IBM Plex Sans, sans-serif"`;
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");

// Variante A: sulla mappa principale. Pieno = presenti oggi; contorno sottile = presenti a gennaio 2019.
{
  const w = C.w, h = C.h + 70;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" ${font}><rect width="100%" height="100%" fill="#fcfcfb"/>`;
  s += `<text x="16" y="28" font-size="20" font-weight="600" fill="#0b0b0b">Variante A · sulla mappa principale</text>`;
  s += `<text x="16" y="50" font-size="13" fill="#52514e">Pieno: presenti oggi. Contorno: presenti a gennaio 2019. Blu se oggi sono di più, grigio se di meno.</text>`;
  s += `<g transform="translate(0,60)"><path d="${C.sagoma}" fill="#ecebe7"/>`;
  for (const q of C.quadrati) {
    const i = I.get(q.codice), p = primo[q.codice];
    if (!i) continue;
    const L = C.k * Math.sqrt(i.scheda?.presenti ?? 0), L0 = p ? C.k * Math.sqrt(p.pres) : 0;
    const cresce = p && (i.scheda?.presenti ?? 0) > p.pres;
    s += `<rect x="${q.x - L / 2}" y="${q.y - L / 2}" width="${L}" height="${L}" fill="${cresce ? "#2a78d6" : "#b8b6ae"}"/>`;
    if (L0) s += `<rect x="${q.x - L0 / 2}" y="${q.y - L0 / 2}" width="${L0}" height="${L0}" fill="none" stroke="#0b0b0b" stroke-width="0.8"/>`;
  }
  s += `</g><text x="16" y="${h - 10}" font-size="12" fill="#52514e">Pro: un'unica vista, si vede dove. Contro: gli eventi nazionali non hanno posto; con molti anni diventa illeggibile.</text></svg>`;
  writeFileSync(`${out}/variante-A.svg`, s);
}

// Variante B: schema a parte. In alto la linea del tempo nazionale con gli eventi; sotto gli istituti
// come quadrati in righe per tipo, ordinati per variazione dei presenti dal 2019.
{
  const w = 900, h = 760, x0 = 60, x1 = w - 30;
  const anni = [1991, 2027];
  const X = (d) => x0 + ((new Date(d).getFullYear() + new Date(d).getMonth() / 12 - anni[0]) / (anni[1] - anni[0])) * (x1 - x0);
  const ymax = 70000, Y = (v) => 330 - (v / ymax) * 230;
  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" ${font}><rect width="100%" height="100%" fill="#fcfcfb"/>`;
  s += `<text x="16" y="28" font-size="20" font-weight="600" fill="#0b0b0b">Variante B · schema a parte, non geografico</text>`;
  s += `<text x="16" y="50" font-size="13" fill="#52514e">In alto: presenti (DAP, 1991-oggi) e capienza (dal 2019; prima: buco dichiarato). Tacche: eventi di eventi.yml.</text>`;
  for (const v of [0, 20000, 40000, 60000]) s += `<line x1="${x0}" x2="${x1}" y1="${Y(v)}" y2="${Y(v)}" stroke="#e3e2dd"/><text x="${x0 - 6}" y="${Y(v) + 4}" font-size="11" text-anchor="end" fill="#52514e">${v / 1000}k</text>`;
  for (let a = 1995; a <= 2025; a += 5) s += `<text x="${X(`${a}-01-01`)}" y="348" font-size="11" text-anchor="middle" fill="#52514e">${a}</text>`;
  s += `<rect x="${X("2000-01-01")}" y="${Y(ymax)}" width="${X("2019-01-01") - X("2000-01-01")}" height="${Y(0) - Y(ymax)}" fill="url(#b)" opacity=".5"/>`;
  s += `<defs><pattern id="b" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line y2="6" stroke="#b8b6ae"/></pattern></defs>`;
  s += `<polyline fill="none" stroke="#2a78d6" stroke-width="2" points="${S.semestrali.map((r) => `${X(r.data)},${Y(r.presenti)}`).join(" ")}"/>`;
  s += `<polyline fill="none" stroke="#eb6834" stroke-width="2" points="${S.mensili.map((r) => `${X(r.data)},${Y(r.capienza)}`).join(" ")}"/>`;
  s += `<text x="${X("2003-01-01")}" y="${Y(64000)}" font-size="12" fill="#52514e">capienza 2000-2018: non nell'archivio online [DA CERCARE]</text>`;
  for (const e of S.eventi.filter((e) => /^\d{4}/.test(e.data))) {
    const x = X(e.data.length === 7 ? `${e.data}-01` : e.data);
    s += `<line x1="${x}" x2="${x}" y1="${Y(ymax)}" y2="${Y(0)}" stroke="#0b0b0b" stroke-width=".7" stroke-dasharray="2 3"/>`;
    s += `<text transform="translate(${x + 3},${Y(ymax) + 4}) rotate(90)" font-size="9.5" fill="#0b0b0b">${esc(e.titolo.slice(0, 48))}</text>`;
  }
  s += `<text x="16" y="392" font-size="14" font-weight="600" fill="#0b0b0b">Istituti per tipo, ordinati per variazione dei presenti da gennaio 2019 (sinistra: calo, destra: aumento)</text>`;
  const tipi = ["CC", "CR", "CCF", "CRF", "CL", "ICAM", "IP"];
  let y = 410;
  for (const t of tipi) {
    const lista = [...I.values()].filter((i) => i.tipo === t && primo[i.codice])
      .map((i) => ({i, d: (i.scheda?.presenti ?? 0) - primo[i.codice].pres})).sort((a, b) => a.d - b.d);
    if (!lista.length) continue;
    s += `<text x="16" y="${y + 12}" font-size="12" fill="#52514e">${t}</text>`;
    let x = 60, rigaMax = 0;
    for (const {i, d} of lista) {
      const L = Math.max(2, 0.45 * Math.sqrt(i.scheda?.presenti ?? 0));
      if (x + L > w - 20) { x = 60; y += rigaMax + 3; rigaMax = 0; }
      s += `<rect x="${x}" y="${y}" width="${L}" height="${L}" fill="${d > 0 ? "#2a78d6" : "#b8b6ae"}"/>`;
      x += L + 2; rigaMax = Math.max(rigaMax, L);
    }
    y += rigaMax + 14;
  }
  s += `<text x="16" y="${h - 10}" font-size="12" fill="#52514e">Pro: c'è posto per il tempo lungo, gli eventi e i buchi. Contro: si perde la geografia, serve una transizione dalla mappa.</text></svg>`;
  writeFileSync(`${out}/variante-B.svg`, s);
}
console.log("schizzi scritti in", out);
