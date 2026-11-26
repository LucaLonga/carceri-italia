// La cella in scala. Disegno geometrico e astratto della "stanza media" di un istituto.
//
// - La superficie lorda della stanza media (superficie stimata / stanze disponibili) è disegnata
//   come una fila di quadrati da 3 m² (lato √3 ≈ 1,73 m): ogni quadrato è lo spazio minimo per
//   una persona secondo la soglia. L'ultimo quadrato può essere parziale.
// - La parte occupata dagli arredi (arredo per persona × persone) è tratteggiata, dalla fine.
// - Le persone sono punti. Ogni persona occupa un quadrato libero (almeno per metà); quando le persone
//   sono più dei quadrati liberi, i punti si raddoppiano nello stesso quadrato.
// - La scala è reale e fissa: 1 m = PX_M px (non cambia con lo schermo). La forma non è quella vera:
//   le fonti non pubblicano le misure delle stanze.
import * as d3 from "npm:d3";
import {ARREDO_M2_PERSONA, SOGLIA_M2} from "./parametri.js";
import {m2, num} from "./formato.js";

export const PX_M = 40; // 1 metro = 40 pixel
const LATO = Math.sqrt(SOGLIA_M2) * PX_M; // lato del quadrato da 3 m², in pixel

export function datiCella(ist, arredo = ARREDO_M2_PERSONA) {
  const c = ist.calc;
  if (!c || c.superficie_lorda == null || !c.stanze_disp || !ist.scheda?.presenti) return null;
  const area = c.superficie_lorda / c.stanze_disp;          // m² lordi della stanza media [calcolato][ipotesi]
  const persone = ist.scheda.presenti / c.stanze_disp;      // persone per stanza [calcolato]
  const areaArredo = Math.min(area, arredo * persone);      // [ipotesi]
  return {area, persone, areaArredo, areaLibera: area - areaArredo, quadrati: area / SOGLIA_M2, quadratiLiberi: (area - areaArredo) / SOGLIA_M2};
}

export function cella(ist, {larghezza = 640, arredo = ARREDO_M2_PERSONA} = {}) {
  const d = datiCella(ist, arredo);
  if (!d) {
    const p = document.createElement("p");
    p.className = "avviso";
    p.textContent = "Cella in scala non disponibile: mancano stanze disponibili o persone presenti.";
    return p;
  }
  const gap = 4;
  const perRiga = Math.max(1, Math.floor((Math.min(larghezza, 680) - 2 + gap) / (LATO + gap)));
  const nQ = Math.ceil(d.quadrati - 1e-9);
  const righe = Math.ceil(nQ / perRiga);
  const margSup = 4, scalaH = 40;
  const w = perRiga * (LATO + gap) - gap + 2;
  const h = margSup + righe * (LATO + gap) + scalaH;
  const pos = (k) => ({x: 1 + (k % perRiga) * (LATO + gap), y: margSup + Math.floor(k / perRiga) * (LATO + gap)});

  const svg = d3.create("svg")
    .attr("width", w).attr("height", h).attr("viewBox", `0 0 ${w} ${h}`)
    .attr("style", `max-width:none;display:block`)
    .attr("role", "img")
    .attr("aria-label",
      `Stanza media di ${ist.nome}, in scala (1 metro = ${PX_M} pixel): ${m2(d.area, 1)} lordi divisi in quadrati da 3 m², ` +
      `cioè spazio per ${num(d.quadrati, 1)} persone alla soglia. Ci stanno in media ${num(d.persone, 1)} persone. ` +
      `Togliendo ${m2(arredo, 1)} di arredo per persona restano ${m2(d.areaLibera, 1)} liberi, cioè ${m2(d.areaLibera / d.persone, 2)} per persona.`);

  const defs = svg.append("defs");
  const idTr = `tratteggio-${ist.codice}`;
  defs.append("pattern").attr("id", idTr).attr("width", 6).attr("height", 6).attr("patternUnits", "userSpaceOnUse").attr("patternTransform", "rotate(45)")
    .append("line").attr("x1", 0).attr("y1", 0).attr("x2", 0).attr("y2", 6).attr("stroke", "var(--tratteggio)").attr("stroke-width", 1.2);

  const g = svg.append("g");
  // Quadrati da 3 m²: parte lorda (riempimento chiaro), parte d'arredo tratteggiata.
  for (let k = 0; k < nQ; k++) {
    const {x, y} = pos(k);
    const frazione = Math.min(1, d.quadrati - k);            // l'ultimo può essere parziale
    const inizioArredo = d.quadratiLiberi - k;               // da dove comincia l'arredo in questo quadrato
    g.append("rect").attr("x", x).attr("y", y).attr("width", LATO).attr("height", LATO)
      .attr("fill", "none").attr("stroke", "var(--theme-foreground-faint)").attr("stroke-dasharray", frazione < 1 ? "3 3" : null);
    g.append("rect").attr("x", x).attr("y", y).attr("width", LATO * frazione).attr("height", LATO)
      .attr("fill", "var(--theme-foreground-faintest)");
    if (inizioArredo < frazione) {
      const da = Math.max(0, inizioArredo);
      g.append("rect").attr("x", x + LATO * da).attr("y", y).attr("width", LATO * (frazione - da)).attr("height", LATO)
        .attr("fill", `url(#${idTr})`);
    }
  }
  // Persone: punti nei quadrati liberi almeno per metà, a giro.
  const liberi = Math.max(1, Math.round(d.quadratiLiberi));
  const intere = Math.floor(d.persone), resto = d.persone - intere;
  const nPunti = intere + (resto > 0.05 ? 1 : 0);
  const perQuadrato = d3.range(liberi).map(() => 0);
  const punti = d3.range(nPunti).map((p) => {
    const q = p % liberi, n = perQuadrato[q]++;
    return {q, n, parziale: p === intere};
  });
  const posPunto = [[0.5, 0.5], [0.25, 0.25], [0.75, 0.75], [0.75, 0.25], [0.25, 0.75]];
  for (const p of punti) {
    const {x, y} = pos(p.q);
    const larghezzaLibera = Math.max(0.5, Math.min(1, d.quadratiLiberi - p.q));
    const tot = perQuadrato[p.q];
    const [fx, fy] = tot === 1 ? posPunto[0] : posPunto[1 + (p.n % 4)];
    g.append("circle").attr("cx", x + LATO * fx * larghezzaLibera).attr("cy", y + LATO * fy).attr("r", 6)
      .attr("fill", p.parziale ? "none" : "var(--classe-attraversa)")
      .attr("stroke", p.parziale ? "var(--classe-attraversa)" : "var(--superficie)").attr("stroke-width", p.parziale ? 2 : 1.5);
  }
  // Barra di scala: 1 m.
  const yS = margSup + righe * (LATO + gap) + 14;
  const sc = svg.append("g").attr("transform", `translate(1,${yS})`).attr("aria-hidden", "true");
  sc.append("path").attr("d", `M0,0V6H${PX_M}V0`).attr("fill", "none").attr("stroke", "currentColor");
  sc.append("text").attr("x", PX_M + 8).attr("y", 8).attr("fill", "currentColor").style("font-size", "12px").text(`1 m (scala 1 m = ${PX_M} px)`);
  return svg.node();
}
