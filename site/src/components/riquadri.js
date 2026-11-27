// I tre riquadri del poster del 2024, rifatti nella stessa scala del cartogramma: un quadrato di lato
// k · √persone, con lo stesso k della disposizione usata dalla mappa. Così si confrontano a occhio
// con i quadrati degli istituti.
//   posti mancanti     = somma, istituto per istituto, delle persone oltre i posti regolamentari [calcolato]
//   posti non disponibili = somma dei posti non disponibili delle schede [verificata]
//   persone sotto 3 m² = presenti negli istituti in classe "sotto 3 m²" (visita di Antigone o banda) [calcolato]
import * as d3 from "npm:d3";
import {valutazione} from "./metrica.js";
import {num, pct} from "./formato.js";

export function numeriRiquadri(istituti, opzioni) {
  const v = istituti.map((i) => ({i, v: valutazione(i, opzioni)}));
  const presenti = d3.sum(istituti, (i) => i.scheda?.presenti);
  return {
    mancanti: d3.sum(istituti, (i) => Math.max(0, (i.scheda?.presenti ?? 0) - (i.scheda?.posti_reg ?? 0))),
    nonDisponibili: d3.sum(istituti, (i) => i.scheda?.posti_non_disp),
    sotto: d3.sum(v.filter((x) => x.v.classe === "sotto"), (x) => x.i.scheda?.presenti),
    aCavallo: d3.sum(v.filter((x) => x.v.classe === "attraversa"), (x) => x.i.scheda?.presenti),
    presenti
  };
}

export function riquadri(carto, n, {larghezza = 640} = {}) {
  const D = carto.disposizioni[larghezza < 560 ? "mobile" : "desktop"];
  const voci = [
    {nome: "posti mancanti", valore: n.mancanti, nota: "persone oltre i posti regolamentari, istituto per istituto [calcolato]", tratteggio: false, colore: "var(--theme-foreground-muted)"},
    {nome: "posti non disponibili", valore: n.nonDisponibili, nota: "posti che esistono ma non si usano; motivo non pubblicato", tratteggio: true, colore: "none"},
    {nome: "persone sotto 3 m²", valore: n.sotto, nota: `${pct(n.sotto / n.presenti, 1)} dei presenti; altre ${num(n.aCavallo)} in istituti a cavallo della soglia [calcolato]`, tratteggio: false, colore: "var(--classe-sotto)"}
  ];
  // Stessa scala della mappa: il viewBox ha la larghezza della disposizione, quindi a parità di larghezza
  // sullo schermo un quadrato qui e un quadrato sulla mappa con lo stesso numero di persone coincidono.
  const lati = voci.map((v) => D.k * Math.sqrt(v.valore));
  const gap = 24, tot = d3.sum(lati) + gap * (voci.length - 1);
  const s = Math.min(1, (D.w - 16) / tot);
  const alt = Math.max(...lati) * s + 8;
  const box = d3.create("div").attr("class", "riquadri");
  const svg = box.append("svg").attr("viewBox", `0 0 ${D.w} ${alt}`).attr("width", D.w).attr("height", alt)
    .attr("style", "width:100%;height:auto;display:block").attr("role", "img")
    .attr("aria-label", voci.map((v) => `${v.nome}: ${num(v.valore)}`).join("; ") + ". Quadrati nella stessa scala della mappa.");
  let x = (D.w - tot * s) / 2;
  voci.forEach((v, k) => {
    const L = lati[k] * s;
    svg.append("rect").attr("x", x).attr("y", alt - 4 - L).attr("width", L).attr("height", L)
      .attr("fill", v.colore).attr("stroke", v.tratteggio ? "currentColor" : "none")
      .attr("stroke-dasharray", v.tratteggio ? "4 3" : null).attr("stroke-width", 1.5).attr("vector-effect", "non-scaling-stroke");
    x += L + gap * s;
  });
  const ul = box.append("ul").attr("class", "riquadri-voci");
  for (const v of voci) {
    const li = ul.append("li");
    li.append("b").text(num(v.valore));
    li.append("span").text(` ${v.nome}`);
    li.append("small").text(v.nota);
  }
  if (s < 1) box.append("p").attr("class", "nota").text(`Quadrati ridotti al ${num(s * 100)}% della scala della mappa per farli stare nel riquadro.`);
  return box.node();
}
