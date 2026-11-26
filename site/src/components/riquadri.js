// I tre riquadri del poster del 2024, rifatti nella stessa scala del cartogramma: un quadrato di lato
// k · √persone, con lo stesso k della disposizione usata dalla mappa. Così si confrontano a occhio
// con i quadrati degli istituti.
//   posti mancanti     = somma, istituto per istituto, delle persone oltre i posti regolamentari [calcolato]
//   posti non disponibili = somma dei posti non disponibili delle schede [verificata]
//   persone sotto 3 m² = presenti negli istituti in classe "sotto 3 m²" (visita di Antigone o banda) [calcolato]
import * as d3 from "npm:d3";
import * as Plot from "npm:@observablehq/plot";
import {valutazione} from "./metrica.js";
import {data as dataIt, num, pct} from "./formato.js";

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

// Passo 7, versione provvisoria (variante B ridotta): serie nazionale e eventi di eventi.yml.
// [DA DECIDERE: Luca] variante A (sulla mappa) o B (schema a parte): vedi docs/schizzi/.
export function storia(st, {larghezza = 640, altezza = 420} = {}) {
  const sem = st.semestrali.filter((d) => d.data >= "2000").map((d) => ({...d, t: new Date(d.data)}));
  const men = st.mensili.map((d) => ({...d, t: new Date(d.data)}));
  const ev = st.eventi.filter((e) => /^\d{4}-\d{2}/.test(e.data)).map((e) => ({...e, t: new Date(e.data.length === 7 ? `${e.data}-01` : e.data)}));
  const fine = new Date(Math.max(+sem.at(-1)?.t || 0, +men.at(-1)?.t || 0));
  return Plot.plot({
    width: larghezza, height: altezza, marginLeft: 48, marginTop: 24,
    x: {domain: [new Date("2000-01-01"), fine], label: null},
    y: {domain: [0, 70000], grid: true, label: "persone / posti", tickFormat: (d) => num(d)},
    ariaLabel: "Presenti e capienza in Italia dal 2000",
    ariaDescription: `Presenti dal ${dataIt(sem[0]?.data)} al ${dataIt(sem.at(-1)?.data)}: da ${num(sem[0]?.presenti)} a ${num(sem.at(-1)?.presenti)}. ` +
      `Capienza regolamentare pubblicata solo dal ${dataIt(men[0]?.data)}. ${ev.length} eventi segnati.`,
    marks: [
      Plot.rectY([{a: new Date("2000-01-01"), b: men[0]?.t ?? fine}], {x1: "a", x2: "b", y1: 0, y2: 70000, fill: "var(--theme-foreground-faintest)"}),
      Plot.text([{t: new Date("2001-01-01")}], {x: "t", y: 66000, text: () => "capienza prima del 2019: non nell'archivio online", textAnchor: "start", fill: "var(--theme-foreground-muted)", fontSize: 11}),
      Plot.ruleX(ev, {x: "t", stroke: "var(--theme-foreground-muted)", strokeDasharray: "2 3"}),
      Plot.dot(ev, {x: "t", y: 70000, r: 3, fill: "currentColor"}),
      Plot.ruleY([0]),
      Plot.line(sem, {x: "t", y: "presenti", stroke: "var(--serie-1)", strokeWidth: 2}),
      Plot.line(men, {x: "t", y: "capienza", stroke: "var(--serie-2)", strokeWidth: 2}),
      Plot.text(sem.slice(-1), {x: "t", y: "presenti", text: () => "presenti", dy: -10, textAnchor: "end", fill: "currentColor", fontSize: 12}),
      Plot.text(men.slice(-1), {x: "t", y: "capienza", text: () => "capienza", dy: 14, textAnchor: "end", fill: "currentColor", fontSize: 12}),
      Plot.tip(ev, Plot.pointerX({x: "t", y: 70000, title: (e) => `${e.titolo}\n${e.data} · ${e.etichetta}`}))
    ]
  });
}
