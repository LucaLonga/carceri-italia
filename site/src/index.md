---
title: Quanto spazio
---

```js
import {banda, CLASSI, classe} from "./components/metrica.js";
import {ARREDO_M2_PERSONA, SOGLIA_M2} from "./components/parametri.js";
import {data as dataIt, num, pct, m2} from "./components/formato.js";
import {righeElenco, tabellaElenco} from "./components/elenco.js";
import {legenda} from "./components/legenda.js";
import {pannelloDati, pannelloCodice} from "./components/pannelli.js";
import {vuotoPosti} from "./components/vuoto.js";
import {mappa} from "./components/mappa.js";
```

```js
const dati = await FileAttachment("data/istituti.json").json();
const regioni = await FileAttachment("data/regioni.topojson").json();
const istituti = dati.istituti;
const conBanda = istituti.map((i) => ({...i, b: banda(i)}));
const critici = conBanda.filter((i) => i.b.classe === "attraversa" || i.b.classe === "sotto");
const presentiCritici = d3.sum(critici, (i) => i.scheda?.presenti);
const presentiTotali = d3.sum(istituti, (i) => i.scheda?.presenti);
const conteggi = d3.rollup(conBanda, (v) => v.length, (i) => i.b.classe);
const fonteSchede = dati.fonti.schede;
const dataDati = fonteSchede.data_min === fonteSchede.data_max
  ? dataIt(fonteSchede.data_max)
  : `${dataIt(fonteSchede.data_min)} – ${dataIt(fonteSchede.data_max)}`;
```

# Quanto spazio ha davvero una persona detenuta in Italia?

<p class="domanda">Istituto per istituto, e come cambia nel tempo. L'unità di misura è la cella.</p>

<div class="grid grid-cols-2 apertura" style="grid-auto-rows:auto">
<div>

```js
const laMappa = resize((w) => mappa(istituti, regioni, {larghezza: w}));
display(laMappa);
```

${legenda(Object.fromEntries(conteggi))}
<p class="nota">Area del cerchio = persone presenti. Passa sopra un cerchio (o usa Tab) per i numeri; clic per la scheda.</p>

```js
display(pannelloDati(conBanda.map((i) => ({codice: i.codice, nome: i.nome, lat: i.lat, lon: i.lon, presenti: i.scheda?.presenti, m2_lordi: i.b.alto, m2_meno_arredo: i.b.basso, classe: i.b.classe, data: i.scheda?.agg_capienza, coord_da_verificare: i.coord_da_verificare ? "sì" : ""})),
  ["codice", "nome", "lat", "lon", "presenti", "m2_lordi", "m2_meno_arredo", "classe", "data", "coord_da_verificare"].map((chiave) => ({chiave, formato: chiave.startsWith("m2") ? (v) => num(v, 2) : undefined})),
  "mappa-istituti.csv", {nota: "Coordinate pubblicate dal DAP (lat_dap, lon_dap). m2_lordi [calcolato], m2_meno_arredo [ipotesi]."}));
display(pannelloCodice(await FileAttachment("components/mappa.js").text(), "components/mappa.js"));
```

</div>
<div>

<div class="numeri" role="group" aria-label="Tre numeri chiave">
  <div class="numero">
    <div class="valore">${num(critici.length)} <span class="etichetta">su ${num(istituti.length)}</span></div>
    <div class="spiega">istituti in cui la banda dello spazio per persona tocca o scende sotto 3 m² <span class="etichetta">[calcolato] [ipotesi]</span></div>
  </div>
  <div class="numero">
    <div class="valore">${num(presentiCritici)}</div>
    <div class="spiega">persone detenute in quegli istituti, su ${num(presentiTotali)} <span class="etichetta">[calcolato]</span></div>
  </div>
  <div class="numero">
    <div class="valore" style="font-size:1.5rem">${dataDati}</div>
    <div class="spiega">data delle schede trasparenza del DAP usate qui</div>
  </div>
</div>

<p class="nota">La banda va dallo spazio lordo per persona (stima dai posti regolamentari) allo spazio lordo meno ${m2(ARREDO_M2_PERSONA)} di arredo per persona, un valore ancora da fissare con una fonte. Come si calcola: <a href="./metodo">metodo</a>.</p>

## Che cosa non sappiamo

```js
const totPostiReg = d3.sum(istituti, (i) => i.scheda?.posti_reg);
const totNonDisp = d3.sum(istituti, (i) => i.scheda?.posti_non_disp);
const nCoord = istituti.filter((i) => i.coord_da_verificare).length;
```

<div>
<div>

- **La superficie reale delle celle** non è pubblica. Le schede danno il numero di stanze, non i metri quadri: qui la superficie è una stima.
- **Perché ${num(totNonDisp)} posti sono "non disponibili"** (${pct(totNonDisp / totPostiReg, 1)} dei posti regolamentari): le schede non lo spiegano.
- **Da dove vengono le persone detenute**, istituto per istituto: non è pubblico. Ci sono solo dati per regione di residenza.
- **Dove sono esattamente gli istituti**: per ${num(nCoord)} istituti le coordinate del DAP e quelle del 2024 distano più di 2 km. Sono segnalati nelle schede.

</div>
<div>

```js
const vuoto = vuotoPosti({posti_reg: totPostiReg, posti_non_disp: totNonDisp, larghezza: Math.min(width, 420)});
display(vuoto);
```

</div>
</div>

```js
display(pannelloDati(
  [{voce: "posti regolamentari", valore: totPostiReg}, {voce: "posti non disponibili", valore: totNonDisp}, {voce: "posti disponibili", valore: totPostiReg - totNonDisp}],
  [{chiave: "voce", etichetta: "Voce"}, {chiave: "valore", etichetta: "Posti", formato: num}],
  "posti-non-disponibili.csv",
  {nota: `Somma delle schede trasparenza (${dataDati}).`}
));
display(pannelloCodice(await FileAttachment("components/vuoto.js").text(), "components/vuoto.js"));
```

</div>
</div>

## Gli istituti

```js
const righe0 = righeElenco(istituti);
```

```js
const fRegione = view(Inputs.select(["tutte", ...d3.sort(new Set(righe0.map((r) => r.regione)))], {label: "Regione"}));
const fTipo = view(Inputs.select(["tutti", ...d3.sort(new Set(righe0.map((r) => r.tipo)))], {label: "Tipo"}));
const fClasse = view(Inputs.select(["tutte", ...CLASSI.map((c) => c.id)], {label: "Banda", format: (d) => d === "tutte" ? d : classe(d).etichetta}));
const fCerca = view(Inputs.search(righe0, {placeholder: "Cerca un istituto…", columns: ["nome"], format: (n) => `${n} istituti`}));
```

```js
const righe = fCerca.filter((r) =>
  (fRegione === "tutte" || r.regione === fRegione) &&
  (fTipo === "tutti" || r.tipo === fTipo) &&
  (fClasse === "tutte" || r.classe === fClasse));
```

${legenda(Object.fromEntries(conteggi))}

```js
display(tabellaElenco(righe));
```

<p class="nota">${num(righe.length)} istituti mostrati. Clic sul nome per la scheda; clic sull'intestazione per ordinare. <b>m² lordi</b>: spazio lordo stimato per persona [calcolato]. <b>meno arredo</b>: lo stesso meno ${m2(ARREDO_M2_PERSONA)} [ipotesi]. <b>pers./stanza</b>: presenti per stanza disponibile [calcolato]. <b>affoll.</b>: presenti su posti disponibili [calcolato].</p>

```js
display(pannelloDati(righe, [
  {chiave: "codice", etichetta: "Codice DAP"}, {chiave: "nome", etichetta: "Istituto"}, {chiave: "regione"}, {chiave: "tipo"},
  {chiave: "presenti"}, {chiave: "posti_disp"}, {chiave: "m2_alto", etichetta: "m2_lordi_persona"}, {chiave: "m2_basso", etichetta: "m2_meno_arredo"},
  {chiave: "persone_stanza"}, {chiave: "affollamento_reale"}, {chiave: "classe"}, {chiave: "coord_da_verificare"}
], "istituti-elenco.csv"));
display(pannelloCodice(await FileAttachment("components/elenco.js").text(), "components/elenco.js"));
```

```js
if (dati.avvisi.length) display(html`<details class="pannello"><summary>Avvisi del caricamento dati (${dati.avvisi.length})</summary><ul>${dati.avvisi.map((a) => html`<li>${a}</li>`)}</ul></details>`);
```
