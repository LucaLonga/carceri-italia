// Il vuoto disegnato: i posti regolamentari come 100 quadrati (1 quadrato = 1% dei posti).
// Pieni = posti disponibili; tratteggiati = posti non disponibili, di cui le fonti non danno il motivo.
import * as d3 from "npm:d3";
import {num, pct} from "./formato.js";

export function vuotoPosti({posti_reg, posti_non_disp, larghezza = 420, titolo = "Posti regolamentari in Italia"}) {
  const quota = posti_reg > 0 ? posti_non_disp / posti_reg : 0;
  const nVuoti = Math.round(quota * 100);
  const col = 20, lato = Math.max(10, Math.floor((larghezza - 2) / col) - 2), passo = lato + 2;
  const righe = 5, alt = righe * passo + 44;
  const svg = d3.create("svg")
    .attr("width", col * passo + 2).attr("height", alt)
    .attr("viewBox", `0 0 ${col * passo + 2} ${alt}`)
    .attr("class", "vuoto-griglia")
    .attr("role", "img")
    .attr("aria-label", `${titolo}: ${num(posti_reg)}. Di questi ${num(posti_non_disp)} (${pct(quota, 1)}) sono non disponibili, per motivi non spiegati dalle fonti. Ogni quadrato vale l'1% dei posti.`);
  // I quadrati vuoti stanno in fondo, così si leggono come la parte che manca.
  const celle = d3.range(100).map((k) => ({k, vuoto: k >= 100 - nVuoti}));
  svg.append("g").attr("transform", "translate(1,1)")
    .selectAll("rect").data(celle).join("rect")
    .attr("x", (d) => (d.k % col) * passo).attr("y", (d) => Math.floor(d.k / col) * passo)
    .attr("width", lato).attr("height", lato).attr("rx", 1)
    .attr("fill", (d) => (d.vuoto ? "none" : "var(--classe-attraversa)"))
    .attr("stroke", (d) => (d.vuoto ? "var(--tratteggio)" : "none"))
    .attr("stroke-width", 1.2)
    .attr("stroke-dasharray", (d) => (d.vuoto ? "3 2" : null));
  const t = svg.append("text").attr("y", righe * passo + 18).attr("fill", "currentColor").style("font-size", "13px");
  t.append("tspan").attr("x", 1).text(`■ disponibili ${num(posti_reg - posti_non_disp)}`);
  t.append("tspan").attr("x", 1).attr("dy", 18).text(`⬚ non disponibili ${num(posti_non_disp)} (${pct(quota, 1)}): motivo non pubblicato`);
  return svg.node();
}
