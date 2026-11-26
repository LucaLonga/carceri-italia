---
title: Scheda istituto
---

```js
import {banda, classe, motivi} from "../components/metrica.js";
import {ARREDO_M2_PERSONA, SOGLIA_M2} from "../components/parametri.js";
import {data as dataIt, m2, num, pct, regione} from "../components/formato.js";
import {simbolo} from "../components/legenda.js";
import {cella, datiCella, PX_M} from "../components/cella.js";
import {grafico, righeSerie, salti, SERIE, etichettaMisura} from "../components/serie.js";
import {pannelloDati, pannelloCodice} from "../components/pannelli.js";
```

```js
const codice = observable.params.codice;
const dati = await FileAttachment("../data/istituti.json").json();
const serieCsv = await FileAttachment("../data/serie.csv").csv({typed: false});
const ist = dati.istituti.find((i) => i.codice === codice || i.codici_sezioni.includes(codice));
if (!ist) throw new Error(`Codice DAP ${codice} non trovato in istituti.json`);
const b = banda(ist);
const s = ist.scheda ?? {};
const c = ist.calc;
const dc = datiCella(ist);
document.title = `${ist.nome} · Quanto spazio`;
```

<p class="nota"><a href="../">← Mappa e istituti</a></p>

# ${ist.nome}

<p class="domanda">${ist.tipo_esteso} · ${regione(ist.regione)} (${ist.provincia}) · codice DAP ${ist.codice}</p>

```js
const note = [];
if (ist.coord_da_verificare) note.push(html`<li><b>Posizione da verificare.</b> Le coordinate pubblicate dal DAP e quelle geocodificate nel 2024 distano ${num(ist.distanza_coord_km, 1)} km. Sulla mappa si usano quelle del DAP.</li>`);
if (ist.note_qualita) note.push(html`<li><b>Nota sui dati.</b> ${ist.note_qualita}</li>`);
if (ist.codici_sezioni.length > 1) note.push(html`<li><b>Più schede.</b> I numeri sono la somma delle schede ${ist.codici_sezioni.join(" e ")}.</li>`);
for (const m of motivi(ist)) note.push(html`<li><b>Caso limite.</b> ${m}.</li>`);
if (note.length) display(html`<ul class="avviso">${note}</ul>`);
```

<div class="numeri">
  <div class="numero">
    <div class="valore">${b.alto == null ? "–" : `${num(b.basso, 1)}–${num(b.alto, 1)} m²`}</div>
    <div class="spiega">spazio per persona: da lordo meno arredo [ipotesi] a lordo [calcolato]</div>
    <div class="badge">${simbolo(b.classe)} ${classe(b.classe).etichetta}</div>
  </div>
  <div class="numero">
    <div class="valore">${num(c.persone_stanza, 1)}</div>
    <div class="spiega">persone per stanza disponibile [calcolato]</div>
  </div>
  <div class="numero">
    <div class="valore">${pct(c.affollamento_reale)}</div>
    <div class="spiega">presenti su posti disponibili [calcolato]</div>
  </div>
</div>

## La cella in scala

```js
if (dc) display(html`<p>La stanza media di questo istituto misura circa <b>${m2(dc.area, 1)} lordi</b> [calcolato][ipotesi] e ospita in media <b>${num(dc.persone, 1)} persone</b> [calcolato]. Ogni quadrato è <b>3 m²</b>, lo spazio minimo per una persona. Il tratteggio è la parte occupata dagli arredi (${m2(ARREDO_M2_PERSONA)} a persona [ipotesi]). Dove due punti stanno nello stesso quadrato, una persona ha meno di 3 m².</p>`);
```

<div class="cella-scorrevole">

```js
display(cella(ist, {larghezza: width}));
```

</div>

<p class="nota">Scala reale: 1 m = ${PX_M} px. La forma è astratta: le fonti non pubblicano le misure delle stanze, solo il numero di posti e di stanze. Il punto vuoto è la frazione di persona (media).</p>

```js
display(pannelloDati(dc ? [
  {voce: "superficie lorda stimata dell'istituto [ipotesi]", valore: c.superficie_lorda, unita: "m²"},
  {voce: "stanze disponibili", valore: c.stanze_disp, unita: ""},
  {voce: "stanza media, superficie lorda [calcolato]", valore: dc.area, unita: "m²"},
  {voce: "persone per stanza [calcolato]", valore: dc.persone, unita: ""},
  {voce: "arredo per persona [ipotesi]", valore: ARREDO_M2_PERSONA, unita: "m²"},
  {voce: "stanza media, meno arredo [ipotesi]", valore: dc.areaLibera, unita: "m²"},
  {voce: "m² lordi per persona [calcolato]", valore: b.alto, unita: "m²"},
  {voce: "m² meno arredo per persona [ipotesi]", valore: b.basso, unita: "m²"},
  {voce: "soglia", valore: SOGLIA_M2, unita: "m²"}
] : [], [{chiave: "voce", etichetta: "Voce"}, {chiave: "valore", etichetta: "Valore", formato: (v) => num(v, 2)}, {chiave: "unita", etichetta: "Unità"}],
  `cella-${codice}.csv`, {nota: "superficie lorda = 9 × stanze disponibili + 5 × (posti disponibili − stanze disponibili)"}));
display(pannelloCodice(await FileAttachment("../components/cella.js").text(), "components/cella.js"));
```

## Nel tempo

```js
const righe = righeSerie(serieCsv, codice);
const cambi = salti(righe);
const nDate = new Set(righe.map((d) => d.giorno)).size;
```

<ul class="legenda-serie" aria-label="Legenda della serie">
  ${SERIE.map((x) => html`<li><i style="background:${x.colore}"></i>${x.etichetta}</li>`)}
  <li><i style="background:var(--theme-foreground-faint);height:10px"></i>persone che ci starebbero con 3 m² a testa (da lordo a meno arredo)</li>
  <li>● scheda DAP · ■ tabella mensile del Ministero</li>
</ul>

```js
display(resize((w) => grafico(righe, {larghezza: w, nome: ist.nome})));
```

```js
display(html`<p class="nota">${nDate < 3 ? `Per ora ci sono ${nDate} date: la serie cresce da sola a ogni raccolta (schede ogni lunedì, Ministero ogni mese). ` : ""}Le due fonti contano in modo diverso: la tabella del Ministero non dà i posti non disponibili, e le date non coincidono.</p>`);
display(cambi.length
  ? html`<p><b>Cambi di capienza.</b></p><ul>${cambi.map((k) => html`<li>${etichettaMisura(k.misura)} (${k.fonte === "schede" ? "scheda DAP" : "Ministero"}): da ${num(k.da.valore)} il ${dataIt(k.da.giorno)} a ${num(k.a.valore)} il ${dataIt(k.a.giorno)}.</li>`)}</ul>`
  : html`<p class="nota">Nessun cambio di capienza nelle date disponibili.</p>`);
```

```js
display(pannelloDati(righe, [
  {chiave: "giorno", etichetta: "data"}, {chiave: "fonte"}, {chiave: "misura", formato: etichettaMisura}, {chiave: "valore", formato: (v) => num(v, 1)}
], `serie-${codice}.csv`, {nota: "Da serie.csv. Le righe soglia_* sono calcolate dalla superficie lorda stimata."}));
display(pannelloCodice(await FileAttachment("../components/serie.js").text(), "components/serie.js"));
```

## I numeri della scheda

<div class="grid grid-cols-2" style="grid-auto-rows:auto">
<div>

### Posti e stanze

<dl class="dl-numeri">
  <dt>Posti regolamentari</dt><dd>${num(s.posti_reg)}</dd>
  <dt>Posti non disponibili</dt><dd>${num(s.posti_non_disp)}</dd>
  <dt>Posti disponibili [calcolato]</dt><dd>${num(c.posti_disp)}</dd>
  <dt>Presenti</dt><dd>${num(s.presenti)}</dd>
  <dt>Stanze</dt><dd>${num(s.stanze)}</dd>
  <dt>Stanze non disponibili</dt><dd>${num(s.stanze_non_disp)}</dd>
  <dt>Stanze disponibili [calcolato]</dt><dd>${num(c.stanze_disp)}</dd>
</dl>

</div>
<div>

### Dotazioni delle stanze

<dl class="dl-numeri">
  <dt>con doccia</dt><dd>${num(s.st_doccia)} (${pct(s.st_doccia / s.stanze)})</dd>
  <dt>wc con porta</dt><dd>${num(s.st_wc_porta)} (${pct(s.st_wc_porta / s.stanze)})</dd>
  <dt>con bidet</dt><dd>${num(s.st_bidet)} (${pct(s.st_bidet / s.stanze)})</dd>
  <dt>luce autonoma</dt><dd>${num(s.st_luce)} (${pct(s.st_luce / s.stanze)})</dd>
  <dt>prese elettriche</dt><dd>${num(s.st_prese)} (${pct(s.st_prese / s.stanze)})</dd>
  <dt>per persone con disabilità</dt><dd>${num(s.st_handicap)}</dd>
</dl>
<p class="nota">Quote sul totale delle stanze [calcolato].</p>

### Personale (effettivo / previsto)

<dl class="dl-numeri">
  <dt>Polizia penitenziaria [VERIFICARE]</dt><dd>${num(s.pp_eff)} / ${num(s.pp_prev)}</dd>
  <dt>Educatori [VERIFICARE]</dt><dd>${num(s.edu_eff)} / ${num(s.edu_prev)}</dd>
</dl>

</div>
</div>

## Nomi e fonti

<dl class="dl-numeri">
  <dt>Ministero (tabella mensile)</dt><dd>${ist.nomi.ministero}</dd>
  ${ist.nomi.alias_ministero.length ? html`<dt>Nomi precedenti (Ministero)</dt><dd>${ist.nomi.alias_ministero.join("; ")}</dd>` : ""}
  <dt>DAP (scheda trasparenza)</dt><dd>${ist.nomi.dap}</dd>
  <dt>Antigone</dt><dd>${ist.nomi.antigone}</dd>
  <dt>Codice DAP · id 2024</dt><dd>${ist.codici_sezioni.join(", ")} · ${ist.id}</dd>
</dl>

- **Scheda trasparenza del DAP**: capienza aggiornata al ${dataIt(s.agg_capienza)}, spazi al ${dataIt(s.agg_spazi)}. [giustizia.it, istituti penitenziari](https://www.giustizia.it/giustizia/page/it/istituti_penitenziari).
- **Tabella mensile del Ministero**: ${ist.ministero ? `dati al ${dataIt(ist.ministero.data)}: ${num(ist.ministero.capienza_regolamentare)} posti regolamentari, ${num(ist.ministero.presenti)} presenti, di cui ${num(ist.ministero.donne)} donne e ${num(ist.ministero.stranieri)} stranieri` : "istituto non presente nell'ultima tabella"}.
- Metodo e ipotesi: [pagina di metodo](../metodo). Tutti i file: [dati](../dati).
