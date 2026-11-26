// Cartogramma di Demers: un quadrato per istituto, disposto in fase di build (data/cartogramma.json.js).
//   area del quadrato pieno   = persone presenti
//   quadrato tratteggiato     = capienza (posti regolamentari o disponibili, a scelta)
//   colore                    = spazio per persona rispetto a 3 m² (classe della banda, o visita di Antigone se vale)
//   tacca nell'angolo         = la classe viene da una visita di Antigone non datata
// Sotto i quadrati, la sagoma dell'Italia (regioni ISTAT unite). Grana leggera con un filtro SVG.
// Il nodo restituito ha un metodo aggiorna(stato) per lo scrollytelling: nessun ridisegno, solo attributi.
import * as d3 from "npm:d3";
import {classe, motivi, valutazione} from "./metrica.js";
import {data as dataIt, m2, num} from "./formato.js";
import {corretto} from "./refusi.js";

export const STATO_PIENO = {sagoma: true, quadrati: true, tratteggi: true, colore: true, capienza: "reg", evidenzia: null, filtro: null};

export function cartogramma(carto, istituti, {larghezza = 640, base = ".", stato = STATO_PIENO, arredo, mesi, id = "c"} = {}) {
  const nome = larghezza < 560 ? "mobile" : "desktop";
  const D = carto.disposizioni[nome];
  const perCodice = new Map(istituti.map((i) => [i.codice, i]));
  const k = D.k;
  const punti = D.quadrati
    .filter((q) => perCodice.has(q.codice))
    .map((q) => {
      const i = perCodice.get(q.codice);
      return {q, i, v: valutazione(i, {arredo, mesi}), pres: i.scheda?.presenti ?? 0, reg: i.scheda?.posti_reg ?? 0, disp: i.calc?.posti_disp ?? 0};
    })
    .sort((a, b) => d3.descending(Math.max(a.pres, a.reg), Math.max(b.pres, b.reg)));
  const lato = (n) => k * Math.sqrt(Math.max(0, n));

  const radice = d3.create("div").attr("class", "demers").style("position", "relative");
  const svg = radice.append("svg")
    .attr("viewBox", `0 0 ${D.w} ${D.h}`)
    .attr("width", D.w).attr("height", D.h)
    .attr("style", "width:100%;height:auto;display:block;max-width:100%")
    .attr("role", "group");
  const conta = d3.rollup(punti, (v) => v.length, (p) => p.v.classe);
  svg.attr("aria-label",
    `Cartogramma dell'Italia: ${punti.length} istituti, ogni quadrato ha l'area proporzionale ai presenti. ` +
    `Sopra 3 m²: ${conta.get("sopra") ?? 0}; a cavallo di 3 m²: ${conta.get("attraversa") ?? 0}; sotto 3 m²: ${conta.get("sotto") ?? 0}; ` +
    `dato mancante: ${conta.get("mancante") ?? 0}. Lo stesso dato è nella tabella scaricabile.`);

  const defs = svg.append("defs");
  // Grana: rumore frattale che modula appena l'opacità del riempimento (niente immagini esterne).
  const f = defs.append("filter").attr("id", `${id}-grana`).attr("x", 0).attr("y", 0).attr("width", 1).attr("height", 1);
  f.append("feTurbulence").attr("type", "fractalNoise").attr("baseFrequency", 1.1).attr("numOctaves", 2).attr("seed", 7).attr("result", "rumore");
  f.append("feColorMatrix").attr("in", "rumore").attr("type", "matrix")
    .attr("values", "0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -0.55 1.05").attr("result", "alfa");
  f.append("feComposite").attr("in", "SourceGraphic").attr("in2", "alfa").attr("operator", "in");

  const sagoma = svg.append("path").attr("d", D.sagoma).attr("aria-hidden", "true")
    .attr("fill", "var(--theme-foreground-faintest)").attr("stroke", "none").attr("class", "demers-sagoma");

  const gPieni = svg.append("g").attr("filter", `url(#${id}-grana)`).attr("aria-hidden", "true");
  const gLink = svg.append("g");

  const pieni = gPieni.selectAll("rect").data(punti).join("rect").attr("class", "demers-pieno");
  const link = gLink.selectAll("a").data(punti).join("a")
    .attr("href", (p) => `${base}/istituto/${p.i.codice}`)
    .attr("class", "demers-link");
  const tratti = link.append("rect").attr("class", "demers-tratteggio").attr("fill", "none")
    .attr("stroke", "var(--theme-foreground)").attr("stroke-width", 1).attr("stroke-dasharray", "2.5 2").attr("vector-effect", "non-scaling-stroke");
  const tacche = link.append("path").attr("class", "demers-tacca").attr("fill", "var(--theme-foreground)");
  const bersagli = link.append("rect").attr("class", "demers-bersaglio").attr("fill", "transparent");

  // Tooltip
  const tip = radice.append("div").attr("class", "tooltip").attr("role", "status").style("display", "none");
  const testo = (p, cap) => {
    const {i, v} = p;
    const b = v.banda;
    const r = [`<strong>${i.nome}</strong>`, `${corretto(i.tipo_esteso)} (${i.tipo}) · ${i.provincia}`];
    r.push(`Presenti ${num(p.pres)} · ${cap === "disp" ? "posti disponibili" : "posti regolamentari"} ${num(cap === "disp" ? p.disp : p.reg)}`);
    if (b.alto == null) r.push(`Spazio per persona: dato mancante (${motivi(i).join("; ") || "nessun dato"})`);
    else r.push(`Stima: da ${m2(b.basso, 2)} a ${m2(b.alto, 2)} per persona <span class="etichetta">[ipotesi] [calcolato]</span>`);
    if (v.visita) r.push(`Visita Antigone del ${dataIt(v.visita.data)}: 3 m² in tutte le celle visitate: <b>${v.visita.tre_mq ?? "n.d."}</b>${v.datata ? " (visita datata)" : ""}`);
    r.push(`Vale: <b>${v.fonte === "antigone" ? "visita di Antigone" : "stima dal Ministero"}</b> · ${classe(v.classe).etichetta}`);
    if (v.divergenze.length) r.push(`Divergenza: ${v.divergenze[0].testo}`);
    r.push(`Scheda DAP del ${dataIt(i.scheda?.agg_capienza)}`);
    return r.join("<br>");
  };
  let statoCorrente = {...STATO_PIENO, ...stato};
  const mostra = (e, p) => {
    tip.html(testo(p, statoCorrente.capienza)).style("display", null);
    const box = radice.node().getBoundingClientRect(), s = box.width / D.w;
    const tw = tip.node().offsetWidth, th = tip.node().offsetHeight;
    let x = p.q.x * s + 14, y = p.q.y * s - th - 10;
    if (x + tw > box.width) x = p.q.x * s - tw - 14;
    if (x < 0) x = 4;
    if (y < 0) y = p.q.y * s + 16;
    tip.style("left", `${x}px`).style("top", `${y}px`);
  };
  link.on("pointerenter focus", mostra).on("pointerleave blur", () => tip.style("display", "none"));

  function aggiorna(nuovo = {}) {
    const s = (statoCorrente = {...statoCorrente, ...nuovo});
    sagoma.attr("opacity", s.sagoma ? 1 : 0);
    const visibile = (p) => !s.filtro || s.filtro(p.i, p.v);
    const evid = (p) => !s.evidenzia || s.evidenzia(p.i, p.v);
    pieni
      .attr("x", (p) => p.q.x - lato(p.pres) / 2).attr("y", (p) => p.q.y - lato(p.pres) / 2)
      .attr("width", (p) => lato(p.pres)).attr("height", (p) => lato(p.pres))
      .attr("fill", (p) => (s.colore ? (p.v.classe === "mancante" ? "none" : `var(--classe-${p.v.classe})`) : "var(--theme-foreground-muted)"))
      .attr("opacity", (p) => (!s.quadrati || !visibile(p) ? 0 : evid(p) ? 1 : 0.18));
    const capN = (p) => (s.capienza === "disp" ? p.disp : p.reg);
    tratti
      .attr("x", (p) => p.q.x - lato(capN(p)) / 2).attr("y", (p) => p.q.y - lato(capN(p)) / 2)
      .attr("width", (p) => lato(capN(p))).attr("height", (p) => lato(capN(p)))
      .attr("opacity", (p) => (!s.tratteggi || !visibile(p) ? 0 : evid(p) ? 0.9 : 0.15));
    const t = (p) => Math.max(3, Math.min(7, lato(p.pres) / 3));
    tacche
      .attr("d", (p) => {
        const L = lato(p.pres), x = p.q.x + L / 2, y = p.q.y - L / 2;
        return `M${x - t(p)},${y}H${x}V${y + t(p)}Z`;
      })
      .attr("opacity", (p) => (s.colore && s.quadrati && visibile(p) && p.v.fonte === "antigone" ? (evid(p) ? 1 : 0.2) : 0));
    bersagli
      .attr("x", (p) => p.q.x - Math.max(8, lato(Math.max(p.pres, capN(p)))) / 2)
      .attr("y", (p) => p.q.y - Math.max(8, lato(Math.max(p.pres, capN(p)))) / 2)
      .attr("width", (p) => Math.max(8, lato(Math.max(p.pres, capN(p)))))
      .attr("height", (p) => Math.max(8, lato(Math.max(p.pres, capN(p)))));
    link
      .attr("tabindex", (p) => (s.quadrati && visibile(p) ? null : -1))
      .attr("aria-hidden", (p) => (s.quadrati && visibile(p) ? null : "true"))
      .attr("aria-label", (p) =>
        `${p.i.nome}, ${corretto(p.i.tipo_esteso)}. Presenti ${num(p.pres)}, posti ${num(capN(p))}. ${classe(p.v.classe).etichetta}` +
        ` secondo ${p.v.fonte === "antigone" ? "la visita di Antigone" : "la stima dal Ministero"}.`);
  }
  aggiorna(statoCorrente);
  const nodo = radice.node();
  nodo.aggiorna = aggiorna;
  nodo.disposizione = nome;
  return nodo;
}

// Legenda delle aree (100, 400, 1.600 presenti, come nel poster del 2024) nella stessa scala del cartogramma.
export function legendaAree(carto, larghezza) {
  const D = carto.disposizioni[larghezza < 560 ? "mobile" : "desktop"];
  const s = Math.min(1, larghezza / D.w);
  const valori = [100, 400, 1600];
  const lati = valori.map((v) => D.k * Math.sqrt(v) * s);
  const w = d3.sum(lati) + 40 * valori.length + 60, h = Math.max(...lati) + 22;
  const svg = d3.create("svg").attr("width", w).attr("height", h).attr("role", "img")
    .attr("aria-label", "Legenda: quadrati per 100, 400 e 1.600 presenti; il quadrato tratteggiato è la capienza.");
  let x = 0;
  valori.forEach((v, j) => {
    svg.append("rect").attr("x", x).attr("y", h - 18 - lati[j]).attr("width", lati[j]).attr("height", lati[j])
      .attr("fill", "var(--theme-foreground-faint)");
    svg.append("text").attr("x", x + lati[j] + 4).attr("y", h - 18).attr("fill", "currentColor").style("font-size", "12px").text(num(v));
    x += lati[j] + 40;
  });
  svg.append("rect").attr("x", x + 4).attr("y", h - 18 - 14).attr("width", 14).attr("height", 14).attr("fill", "none")
    .attr("stroke", "currentColor").attr("stroke-dasharray", "2.5 2");
  svg.append("text").attr("x", x + 22).attr("y", h - 20).attr("fill", "currentColor").style("font-size", "12px").text("capienza");
  return svg.node();
}
