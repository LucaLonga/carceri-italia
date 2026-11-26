// Serie storica di un istituto: presenti, posti regolamentari, posti disponibili, e la soglia
// espressa in persone: quante persone ci starebbero con 3 m² a testa.
//   alto  = superficie lorda / 3                      [calcolato][ipotesi]
//   basso = superficie lorda / (3 + arredo per persona) [ipotesi]
// Fonti diverse hanno simboli diversi: cerchio = schede trasparenza, quadrato = tabella mensile del Ministero.
import * as Plot from "npm:@observablehq/plot";
import * as d3 from "npm:d3";
import {ARREDO_M2_PERSONA, SOGLIA_M2} from "./parametri.js";
import {data as dataIt, num} from "./formato.js";

export const SERIE = [
  {id: "presenti", etichetta: "presenti", colore: "var(--serie-1)"},
  {id: "posti_reg", etichetta: "posti regolamentari", colore: "var(--serie-2)"},
  {id: "posti_disp", etichetta: "posti disponibili", colore: "var(--serie-3)"}
];
const FONTI = {ministero: "Ministero, tabella mensile", schede: "DAP, scheda trasparenza"};

// Righe lunghe (data, fonte, misura, valore) per il grafico e per il pannello "Dati".
export function righeSerie(righeCsv, codice, arredo = ARREDO_M2_PERSONA) {
  const out = [];
  for (const r of righeCsv.filter((r) => r.codice_dap === codice)) {
    const data = new Date(`${r.data}T00:00:00Z`);
    for (const s of SERIE) {
      const v = r[s.id];
      if (v != null && v !== "" && Number.isFinite(+v)) out.push({data, giorno: r.data, fonte: r.fonte, misura: s.id, valore: +v});
    }
    if (r.fonte === "schede" && r.superficie_lorda != null && r.superficie_lorda !== "") {
      out.push({data, giorno: r.data, fonte: r.fonte, misura: "soglia_alto", valore: +r.superficie_lorda / SOGLIA_M2});
      out.push({data, giorno: r.data, fonte: r.fonte, misura: "soglia_basso", valore: +r.superficie_lorda / (SOGLIA_M2 + arredo)});
    }
  }
  return d3.sort(out, (d) => d.data);
}

// Cambi di capienza tra due date consecutive della stessa fonte: spiegano i salti.
export function salti(righe) {
  const out = [];
  for (const [chiave, v] of d3.group(righe.filter((d) => d.misura === "posti_reg" || d.misura === "posti_disp"), (d) => `${d.fonte}|${d.misura}`)) {
    const [fonte, misura] = chiave.split("|");
    for (let k = 1; k < v.length; k++) {
      if (v[k].valore !== v[k - 1].valore) out.push({fonte, misura, da: v[k - 1], a: v[k]});
    }
  }
  return out;
}

export function grafico(righe, {larghezza = 640, nome = ""} = {}) {
  const linee = righe.filter((d) => SERIE.some((s) => s.id === d.misura));
  const soglia = d3.rollups(righe.filter((d) => d.misura.startsWith("soglia")), (v) => ({
    data: v[0].data, giorno: v[0].giorno,
    alto: v.find((d) => d.misura === "soglia_alto")?.valore,
    basso: v.find((d) => d.misura === "soglia_basso")?.valore
  }), (d) => d.giorno).map(([, v]) => v);
  const date = d3.extent(righe, (d) => d.data);
  const unaData = +date[0] === +date[1];
  const giorno = 864e5;
  const x0 = new Date(+date[0] - (unaData ? 20 : 5) * giorno), x1 = new Date(+date[1] + (unaData ? 20 : 5) * giorno);
  const dateUniche = [...new Set(righe.map((d) => d.giorno))].map((g) => new Date(`${g}T00:00:00Z`));
  const nDate = dateUniche.length;
  const colore = (m) => SERIE.find((s) => s.id === m)?.colore;
  const ultimi = d3.rollups(linee, (v) => v.at(-1), (d) => d.misura).map(([, v]) => v);

  return Plot.plot({
    width: Math.max(300, larghezza),
    height: 300,
    marginRight: 130,
    marginLeft: 50,
    x: {domain: [x0, x1], label: null, ticks: nDate <= 4 ? dateUniche : 5, tickFormat: (d) => dataIt(d.toISOString())},
    y: {grid: true, label: "persone / posti", zero: true, tickFormat: (d) => num(d)},
    ariaLabel: `Serie storica di ${nome}`,
    ariaDescription: testoAlternativo(righe, nome),
    marks: [
      // Soglia in persone: banda tra 3 m² lordi (alto) e 3 m² calpestabili stimati (basso).
      soglia.length > 1
        ? Plot.areaY(soglia, {x: "data", y1: "basso", y2: "alto", fill: "var(--theme-foreground-faint)", fillOpacity: 0.35})
        : Plot.ruleX(soglia, {x: "data", y1: "basso", y2: "alto", stroke: "var(--theme-foreground-muted)", strokeWidth: 14, strokeOpacity: 0.35}),
      Plot.text(soglia.slice(-1), {x: "data", y: "alto", text: () => "soglia 3 m²", dx: 12, dy: -4, textAnchor: "start", fill: "var(--theme-foreground-muted)", fontSize: 11}),
      Plot.ruleY([0]),
      Plot.line(linee, {x: "data", y: "valore", z: "misura", stroke: (d) => colore(d.misura), strokeWidth: 2}),
      Plot.dot(linee.filter((d) => d.fonte === "schede"), {x: "data", y: "valore", fill: (d) => colore(d.misura), r: 5, stroke: "var(--superficie)", strokeWidth: 2, symbol: "circle"}),
      Plot.dot(linee.filter((d) => d.fonte === "ministero"), {x: "data", y: "valore", fill: (d) => colore(d.misura), r: 5, stroke: "var(--superficie)", strokeWidth: 2, symbol: "square"}),
      Plot.text(ultimi, {x: "data", y: "valore", text: (d) => SERIE.find((s) => s.id === d.misura).etichetta, dx: 10, textAnchor: "start", fill: "currentColor", fontSize: 11}),
      Plot.tip(righe, Plot.pointer({
        x: "data", y: "valore",
        title: (d) => `${dataIt(d.giorno)} · ${FONTI[d.fonte]}\n${etichettaMisura(d.misura)}: ${num(d.valore)}`
      }))
    ]
  });
}

export function etichettaMisura(m) {
  if (m === "soglia_alto") return "persone a 3 m² lordi [calcolato][ipotesi]";
  if (m === "soglia_basso") return "persone a 3 m² meno arredo [ipotesi]";
  return SERIE.find((s) => s.id === m)?.etichetta ?? m;
}

function testoAlternativo(righe, nome) {
  if (!righe.length) return `Nessun dato storico per ${nome}.`;
  const date = [...new Set(righe.map((d) => d.giorno))];
  const ultimo = (m) => righe.filter((d) => d.misura === m).at(-1);
  const p = ultimo("presenti"), r = ultimo("posti_reg"), dsp = ultimo("posti_disp"), sa = ultimo("soglia_alto");
  return `${date.length} date, dal ${dataIt(date[0])} al ${dataIt(date.at(-1))}. ` +
    (p ? `Ultimo dato: ${num(p.valore)} presenti` : "") +
    (r ? `, ${num(r.valore)} posti regolamentari` : "") +
    (dsp ? `, ${num(dsp.valore)} posti disponibili` : "") +
    (sa ? `; con 3 m² lordi a testa ci starebbero ${num(sa.valore)} persone.` : ".");
}
