// Mappa degli istituti: un cerchio per istituto, colore = classe della banda, area = presenti.
// Ogni cerchio è un link alla scheda (raggiungibile da tastiera con Tab; il fuoco mostra il tooltip).
import * as d3 from "npm:d3";
import * as topojson from "npm:topojson-client";
import {banda, classe, motivi} from "./metrica.js";
import {data as dataIt, m2, num} from "./formato.js";

export function mappa(istituti, regioni, {larghezza = 640, arredo, base = "."} = {}) {
  const confini = topojson.feature(regioni, regioni.objects.regioni);
  const w = Math.max(300, larghezza);
  const h = Math.round(w * 1.12);
  // Proiezione trasversa di Mercatore centrata sull'Italia (meridiano 12,5° E).
  const proiezione = d3.geoTransverseMercator().rotate([-12.5, -42]).fitExtent([[8, 8], [w - 8, h - 8]], confini);
  const percorso = d3.geoPath(proiezione);
  const rMax = Math.max(9, Math.min(20, w / 32));
  const r = d3.scaleSqrt().domain([0, d3.max(istituti, (i) => i.scheda?.presenti ?? 0)]).range([0, rMax]);

  const punti = istituti
    .filter((i) => i.lat != null && i.lon != null)
    .map((i) => {
      const b = banda(i, arredo);
      const [x, y] = proiezione([i.lon, i.lat]);
      return {i, b, x, y, r: b.classe === "mancante" ? 4 : Math.max(2.5, r(i.scheda?.presenti ?? 0))};
    })
    .sort((a, b) => d3.descending(a.r, b.r)); // i grandi sotto, i piccoli sopra

  const conta = d3.rollup(punti, (v) => v.length, (p) => p.b.classe);
  const contenitore = d3.create("div").attr("class", "mappa");
  const svg = contenitore.append("svg")
    .attr("width", w).attr("height", h).attr("viewBox", `0 0 ${w} ${h}`)
    .attr("style", "max-width:100%;height:auto;display:block")
    .attr("role", "group")
    .attr("aria-label",
      `Mappa d'Italia con ${punti.length} istituti. Banda tutta sopra 3 m²: ${conta.get("sopra") ?? 0}; ` +
      `la banda attraversa 3 m²: ${conta.get("attraversa") ?? 0}; banda tutta sotto 3 m²: ${conta.get("sotto") ?? 0}; ` +
      `dato mancante: ${conta.get("mancante") ?? 0}. La dimensione del cerchio è il numero di presenti. ` +
      `Gli stessi dati sono nell'elenco sotto la mappa.`);

  svg.append("g").attr("aria-hidden", "true")
    .selectAll("path").data(confini.features).join("path")
    .attr("d", percorso)
    .attr("fill", "var(--theme-foreground-faintest)")
    .attr("stroke", "var(--superficie)").attr("stroke-width", 1);

  const tooltip = contenitore.append("div").attr("class", "tooltip").attr("role", "status").style("display", "none");
  const testo = ({i, b}) => {
    const righe = [`<strong>${i.nome}</strong>`, `${i.tipo_esteso} · ${i.provincia}`];
    if (b.classe === "mancante") righe.push(`Spazio per persona: dato mancante (${motivi(i).join("; ") || "nessun dato"})`);
    else righe.push(`Spazio per persona: da ${m2(b.basso, 2)} a ${m2(b.alto, 2)} <span class="etichetta">[ipotesi] [calcolato]</span>`);
    righe.push(`Persone per stanza: ${num(i.calc.persone_stanza, 1)} <span class="etichetta">[calcolato]</span>`);
    righe.push(`Presenti: ${num(i.scheda?.presenti)} · ${classe(b.classe).etichetta}`);
    righe.push(`Dato del ${dataIt(i.scheda?.agg_capienza)}`);
    if (i.coord_da_verificare) righe.push(`Posizione da verificare (le fonti distano ${num(i.distanza_coord_km, 1)} km)`);
    return righe.join("<br>");
  };
  const mostra = (p) => {
    tooltip.html(testo(p)).style("display", null);
    const box = contenitore.node().getBoundingClientRect();
    const scala = box.width / w;
    const tw = tooltip.node().offsetWidth, th = tooltip.node().offsetHeight;
    let x = p.x * scala + 12, y = p.y * scala - th - 8;
    if (x + tw > box.width) x = p.x * scala - tw - 12;
    if (x < 0) x = 4;
    if (y < 0) y = p.y * scala + 14;
    tooltip.style("left", `${x}px`).style("top", `${y}px`);
  };
  const nascondi = () => tooltip.style("display", "none");

  const link = svg.append("g").selectAll("a").data(punti).join("a")
    .attr("href", (p) => `${base}/istituto/${p.i.codice}`)
    .attr("aria-label", (p) =>
      `${p.i.nome}, ${p.i.tipo_esteso}. ${classe(p.b.classe).etichetta}` +
      (p.b.alto != null ? `: da ${m2(p.b.basso, 1)} a ${m2(p.b.alto, 1)} per persona` : "") +
      `. Presenti ${num(p.i.scheda?.presenti)}.`)
    .on("pointerenter focus", (e, p) => mostra(p))
    .on("pointerleave blur", nascondi);

  // Area di contatto più grande del segno (almeno 8 px di raggio).
  link.append("circle").attr("cx", (p) => p.x).attr("cy", (p) => p.y).attr("r", (p) => Math.max(8, p.r)).attr("fill", "transparent");
  link.append("circle")
    .attr("cx", (p) => p.x).attr("cy", (p) => p.y).attr("r", (p) => p.r)
    .attr("fill", (p) => (p.b.classe === "mancante" ? "none" : `var(--classe-${p.b.classe})`))
    .attr("stroke", (p) => (p.b.classe === "mancante" ? "var(--classe-mancante)" : "var(--superficie)"))
    .attr("stroke-width", (p) => (p.b.classe === "mancante" ? 1.5 : 1))
    .attr("stroke-dasharray", (p) => (p.b.classe === "mancante" ? "2 2" : null));

  // Legenda delle dimensioni: cerchi affiancati, in basso a destra.
  const esempi = [100, 500, 1500].filter((v) => v <= r.domain()[1]);
  const xs = [];
  let cx = 0;
  for (const v of esempi) { const m = Math.max(r(v), 16); cx += m; xs.push(cx); cx += m + 6; }
  const lg = svg.append("g").attr("transform", `translate(${w - 8 - cx},${h - 22})`).attr("aria-hidden", "true");
  lg.append("text").attr("x", 0).attr("y", -2 * rMax - 8).attr("fill", "currentColor").style("font-size", "12px").text("Presenti");
  esempi.forEach((v, k) => {
    lg.append("circle").attr("cx", xs[k]).attr("cy", -r(v)).attr("r", r(v)).attr("fill", "none").attr("stroke", "currentColor").attr("stroke-opacity", 0.6);
    lg.append("text").attr("x", xs[k]).attr("y", 14).attr("text-anchor", "middle").attr("fill", "currentColor").style("font-size", "11px").text(num(v));
  });
  return contenitore.node();
}
