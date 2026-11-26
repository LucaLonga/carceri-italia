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
import {cartogramma, legendaAree} from "./components/demers.js";
import {valutazione} from "./components/metrica.js";
```

```js
const dati = await FileAttachment("data/istituti.json").json();
const carto = await FileAttachment("data/cartogramma.json").json();
const istituti = dati.istituti;
const conBanda = istituti.map((i) => ({...i, b: banda(i), v: valutazione(i)}));
const critici = conBanda.filter((i) => i.v.classe === "attraversa" || i.v.classe === "sotto");
const presentiCritici = d3.sum(critici, (i) => i.scheda?.presenti);
const presentiTotali = d3.sum(istituti, (i) => i.scheda?.presenti);
const conteggi = d3.rollup(conBanda, (v) => v.length, (i) => i.v.classe);
const fonteSchede = dati.fonti.schede;
const dataDati = fonteSchede.data_min === fonteSchede.data_max
  ? dataIt(fonteSchede.data_max)
  : `dal ${dataIt(fonteSchede.data_min)} al ${dataIt(fonteSchede.data_max)}`;
```

# Quanto spazio ha davvero una persona detenuta in Italia?

<p class="domanda">Istituto per istituto, e come cambia nel tempo. L'unità di misura è la cella. <a href="./racconto">Leggi il racconto in dieci passi</a>.</p>

<div class="grid grid-cols-2 apertura" style="grid-auto-rows:auto">
<div>

<div class="controlli">

```js
const capienza = view(Inputs.radio(new Map([["regolamentare", "reg"], ["disponibile", "disp"]]), {label: "Capienza", value: "reg"}));
const tipoMappa = view(Inputs.select(["tutti", ...d3.sort(new Set(istituti.map((i) => i.tipo)))], {label: "Tipo"}));
const cercaMappa = view(Inputs.text({label: "Cerca", placeholder: "nome dell'istituto", autocomplete: "off"}));
```

</div>

```js
const laMappa = resize((w) => cartogramma(carto, istituti, {larghezza: w, id: "home"}));
display(laMappa);
```

```js
{
  const q = cercaMappa.trim().toLowerCase();
  laMappa.aggiorna?.({
    capienza,
    filtro: tipoMappa === "tutti" ? null : (i) => i.tipo === tipoMappa,
    evidenzia: q ? (i) => i.nome.toLowerCase().includes(q) || i.nomi.ministero.toLowerCase().includes(q) : null
  });
}
```

${legenda(Object.fromEntries(conteggi), {visita: true})}
${resize((w) => legendaAree(carto, w))}
<p class="nota">Ogni quadrato è un istituto, con l'area proporzionale alle persone presenti. I quadrati sono spostati quanto basta per non sovrapporsi: la posizione è indicativa. Passa sopra un quadrato (o usa Tab) per i numeri; clic per la scheda.</p>

```js
display(pannelloDati(conBanda.map((i) => ({codice: i.codice, nome: i.nome, tipo: i.tipo, presenti: i.scheda?.presenti, posti_reg: i.scheda?.posti_reg, posti_disp: i.calc.posti_disp, m2_lordi: i.b.alto, m2_meno_arredo: i.b.basso, classe: i.v.classe, fonte: i.v.fonte, visita: i.v.visita?.data ?? "", data_scheda: i.scheda?.agg_capienza})),
  ["codice", "nome", "tipo", "presenti", "posti_reg", "posti_disp", "m2_lordi", "m2_meno_arredo", "classe", "fonte", "visita", "data_scheda"].map((chiave) => ({chiave, formato: chiave.startsWith("m2") ? (v) => num(v, 2) : undefined})),
  "cartogramma-istituti.csv", {nota: "Posizioni del cartogramma in data/cartogramma.json. m2_lordi [calcolato], m2_meno_arredo [ipotesi]; fonte = quale dato vale per la classe."}));
display(pannelloCodice(await FileAttachment("components/demers.js").text(), "components/demers.js"));
display(pannelloCodice(await FileAttachment("data/cartogramma.json.js").text(), "data/cartogramma.json.js"));
```

</div>
<div>

<div class="numeri" role="group" aria-label="Tre numeri chiave">
  <div class="numero">
    <div class="valore">${num(critici.length)} <span class="etichetta">su ${num(istituti.length)}</span></div>
    <div class="spiega">istituti sotto 3 m² o a cavallo della soglia, secondo la stima o una visita recente di Antigone <span class="etichetta">[calcolato] [ipotesi]</span></div>
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
