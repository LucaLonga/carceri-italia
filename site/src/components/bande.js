// Le bande di tutti gli istituti, ordinate dallo spazio lordo più basso, con la soglia di 3 m².
// L'asse verticale si ferma a Y_MAX m²: i pochi istituti oltre sono tagliati e contati nella nota.
// Ogni segmento va dal limite basso (lordo meno arredo, [ipotesi]) al limite alto (lordo, [calcolato]).
import * as Plot from "npm:@observablehq/plot";
import * as d3 from "npm:d3";
import {banda, classe} from "./metrica.js";
import {SOGLIA_M2} from "./parametri.js";
import {m2, num} from "./formato.js";

export const Y_MAX = 12;

export function righeBande(istituti, arredo) {
  const r = istituti.map((i) => ({codice: i.codice, nome: i.nome, presenti: i.scheda?.presenti ?? null, ...banda(i, arredo)}))
    .filter((d) => d.alto != null);
  return d3.sort(r, (d) => d.alto).map((d, k) => ({...d, rango: k + 1}));
}

export function graficoBande(righe, {larghezza = 640, arredo} = {}) {
  const conta = d3.rollup(righe, (v) => v.length, (d) => d.classe);
  const oltre = righe.filter((d) => d.alto > Y_MAX).length;
  return Plot.plot({
    width: Math.max(300, larghezza),
    height: 360,
    marginLeft: 44,
    x: {label: "istituti, dal meno spazioso →", ticks: [], axis: "bottom"},
    y: {label: "m² per persona", domain: [0, Y_MAX], grid: true, tickFormat: (d) => num(d)},
    clip: true,
    caption: oltre ? `${oltre} istituti hanno più di ${Y_MAX} m² lordi per persona: il segmento è tagliato in alto.` : null,
    ariaLabel: "Bande dello spazio per persona di tutti gli istituti",
    ariaDescription: `${righe.length} istituti ordinati per spazio lordo per persona. Con ${m2(arredo, 1)} di arredo per persona: ` +
      `${conta.get("sopra") ?? 0} con la banda tutta sopra 3 m², ${conta.get("attraversa") ?? 0} con la banda che attraversa 3 m², ` +
      `${conta.get("sotto") ?? 0} con la banda tutta sotto.`,
    marks: [
      Plot.ruleX(righe, {x: "rango", y1: "basso", y2: "alto", stroke: (d) => `var(--classe-${d.classe})`, strokeWidth: Math.max(1.5, Math.min(3, larghezza / righe.length - 1))}),
      Plot.ruleY([SOGLIA_M2], {stroke: "var(--soglia)", strokeWidth: 1.5}),
      Plot.text([SOGLIA_M2], {y: (d) => d, x: 1, text: () => "soglia 3 m² (Torreggiani)", textAnchor: "start", dy: 12, fill: "currentColor", stroke: "var(--theme-background)", strokeWidth: 4, fontSize: 12}),
      Plot.ruleY([0]),
      Plot.tip(righe, Plot.pointerX({
        x: "rango", y: "alto",
        title: (d) => `${d.nome}\nda ${m2(d.basso, 2)} [ipotesi] a ${m2(d.alto, 2)} [calcolato]\n${classe(d.classe).etichetta}`
      }))
    ]
  });
}
