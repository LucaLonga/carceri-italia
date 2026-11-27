---
title: Metodo
---

```js
import {banda, CLASSI, classe, valutazione} from "./components/metrica.js";
import {ARREDO_M2_PERSONA, SOGLIA_M2, VISITA_DATATA_MESI} from "./components/parametri.js";
import {data as dataIt, m2, num, pct} from "./components/formato.js";
import {legenda} from "./components/legenda.js";
import {righeBande, graficoBande} from "./components/bande.js";
import {pannelloDati, pannelloCodice} from "./components/pannelli.js";
```

```js
const dati = await FileAttachment("data/istituti.json").json();
const ambiente = await FileAttachment("data/ambiente.json").json();
const controlli = await FileAttachment("data/controlli.txt").text();
const st = await FileAttachment("data/storico.json").json();
const istituti = dati.istituti;
const f = dati.fonti;
```

# Metodo

## La domanda e le fonti

Quanto spazio ha una persona detenuta, istituto per istituto? Nessuna fonte pubblica la superficie delle celle. Il sito la **stima** da due fonti del Ministero della Giustizia (DAP):

- le **schede trasparenza** dei ${num(istituti.length)} istituti (${istituti.reduce((n, i) => n + i.codici_sezioni.length, 0)} schede): posti regolamentari, posti non disponibili, presenti, stanze, stanze non disponibili, dotazioni, personale. Dati al ${dataIt(f.schede.data_max)}. Si raccolgono ogni lunedì.
- la **tabella mensile** "capienze per istituto": posti regolamentari e presenti, senza i posti non disponibili. Ultima tabella: ${dataIt(f.ministero.data)}. È la serie lunga.

La nota del Ministero alla tabella dice come si contano i posti:

> ${f.ministero.nota_capienza ?? "[nota non disponibile]"}

Quindi i posti regolamentari sono già una superficie, convertita in persone. Il sito fa il percorso inverso.

**Licenze.** Dati del Ministero: condizioni d'uso di giustizia.it [VERIFICARE]. Dati delle visite di Antigone: [VERIFICARE] con Antigone. Confini regionali: ISTAT, CC BY 4.0. Codice: MIT. Elaborazioni di questo progetto: CC BY 4.0 [DA DECIDERE].

## La formula

```
posti_disp         = posti_reg − posti_non_disp
stanze_disp        = stanze − stanze_non_disp
superficie_lorda   ≈ 9 · stanze_disp + 5 · (posti_disp − stanze_disp)   [ipotesi]
m2_lordi_persona   = superficie_lorda / presenti                        [calcolato]
persone_stanza     = presenti / stanze_disp                             [calcolato]
affollamento_reale = presenti / posti_disp                              [calcolato]
```

L'ipotesi è che ogni stanza disponibile misuri esattamente la sua capienza: 9 m² per il primo posto, 5 m² per ogni altro. Le persone per stanza e l'affollamento non hanno ipotesi: sono rapporti tra numeri pubblicati.

Casi limite: se un istituto non ha presenti, stanze disponibili o posti disponibili (oggi Pozzuoli, chiuso), lo spazio per persona non si calcola e l'istituto è "dato mancante".

## Lordo e calpestabile: la banda

La soglia di **${num(SOGLIA_M2)} m²** viene dalla Corte europea dei diritti dell'uomo (*Torreggiani c. Italia*, 2013). La giurisprudenza italiana la misura sullo spazio **calpestabile**, senza gli arredi fissi (Cassazione, Sezioni Unite, 2021 [VERIFICARE estremi]). I 9 + 5 m² sono invece superfici **lorde**.

Per questo il sito non dice "sopra" o "sotto" 3 m². Mostra una **banda**:

- limite alto: lo spazio lordo per persona [calcolato];
- limite basso: lo spazio lordo meno una superficie di arredo per persona [ipotesi].

La superficie di arredo per persona non è ancora fissata con una fonte. Il valore provvisorio è **${m2(ARREDO_M2_PERSONA)}**. Prova a cambiarlo:

```js
const arredo = view(Inputs.range([0, 4], {value: ARREDO_M2_PERSONA, step: 0.1, label: "Arredo per persona (m²)"}));
```

```js
const righe = righeBande(istituti, arredo);
const conta = Object.fromEntries(d3.rollup(istituti.map((i) => banda(i, arredo)), (v) => v.length, (b) => b.classe));
const critici = (conta.attraversa ?? 0) + (conta.sotto ?? 0);
```

<p>Con <b>${m2(arredo, 1)}</b> di arredo per persona, in <b>${num(critici)}</b> istituti su ${num(istituti.length)} la banda tocca o scende sotto 3 m².</p>

${legenda(conta)}

```js
display(resize((w) => graficoBande(righe, {larghezza: w, arredo})));
```

```js
display(pannelloDati(righe, [
  {chiave: "rango"}, {chiave: "codice", etichetta: "codice DAP"}, {chiave: "nome", etichetta: "istituto"}, {chiave: "presenti", formato: num},
  {chiave: "basso", etichetta: "m2_meno_arredo", formato: (v) => num(v, 2)}, {chiave: "alto", etichetta: "m2_lordi", formato: (v) => num(v, 2)},
  {chiave: "classe", formato: (v) => classe(v).etichetta}
], "bande-istituti.csv", {nota: `Arredo per persona: ${num(arredo, 1)} m² [ipotesi].`}));
display(pannelloCodice(await FileAttachment("components/bande.js").text(), "components/bande.js"));
display(pannelloCodice(await FileAttachment("components/metrica.js").text(), "components/metrica.js"));
display(pannelloCodice(await FileAttachment("components/parametri.js").text(), "components/parametri.js"));
```

## Il confronto con le visite di Antigone

```js
const ant = dati.antigone;
const domanda = ant?.domande.find((d) => /3 mq calpestabili/i.test(d.domanda));
```

```js
if (ant && domanda) {
  const tot = domanda.si + domanda.no + domanda.nd;
  display(html`<p>L'Osservatorio di Antigone ha visitato <b>${num(ant.visite)}</b> istituti (${ant.meta.periodo ?? "[periodo]"}). Alla domanda "${domanda.domanda}" la risposta è stata <b>no in ${num(domanda.no)}</b> istituti (${pct(domanda.no / tot)}), sì in ${num(domanda.si)}, non disponibile in ${num(domanda.nd)}.</p>
  <p>Con la banda di questo sito, gli istituti in cui la banda tocca o scende sotto 3 m² sono ${num(critici)} su ${num(istituti.length)} (${pct(critici / istituti.length)}).</p>
  <p class="avviso">I due numeri <b>non sono confrontabili</b> uno a uno: Antigone ha visitato un sottoinsieme di istituti, e "no" vuol dire che almeno una cella visitata non garantiva 3 m², non che l'istituto in media sta sotto. Il report non dice quali istituti hanno risposto no. Per calibrare la banda servono le risposte istituto per istituto [DA FARE].</p>`);
  display(pannelloDati(ant.domande, [{chiave: "domanda"}, {chiave: "si"}, {chiave: "no"}, {chiave: "nd"}], "antigone-osservatorio.csv",
    {nota: `Fonte: ${ant.meta.fonte ?? "Antigone"}, letto il ${dataIt(ant.meta["letto il"])}; ${ant.meta.metodo ?? ""}. File: ${ant.file}.`}));
} else display(html`<p class="avviso">Dati delle visite di Antigone non disponibili.</p>`);
```

## Quale fonte vale: la regola di affidabilità

Il Ministero conta i posti e le persone, ma non vede le celle una per una e può contare spazi non agibili. L'Osservatorio di Antigone fa sopralluoghi. Per questo, per la classe di ogni istituto:

- se c'è una visita di Antigone **non datata** con una risposta sì o no alla domanda sui 3 m² calpestabili, vale la visita: "no" porta l'istituto in "sotto 3 m²", "sì" in "sopra 3 m²";
- altrimenti vale la banda stimata dalle schede del Ministero.

Una visita è **datata** se è più vecchia di **${num(VISITA_DATATA_MESI)} mesi** rispetto alla data della scheda del DAP. Il valore è provvisorio: [DA DECIDERE: Luca]. Sulla mappa una tacca nell'angolo del quadrato indica gli istituti in cui vale la visita; nella scheda di ogni istituto ci sono la fonte, la data e le divergenze tra le due fonti.

```js
const vals = istituti.map((i) => ({i, v: valutazione(i)}));
const conVisita = vals.filter((x) => x.i.visite_antigone);
const datate = conVisita.filter((x) => x.v.datata);
const valgono = vals.filter((x) => x.v.fonte === "antigone");
const div = vals.filter((x) => x.v.divergenze.length);
display(html`<ul>
  <li>Istituti con almeno una visita abbinata: <b>${num(conVisita.length)}</b> su ${num(istituti.length)} (${pct(conVisita.length / istituti.length, 1)}) [calcolato]</li>
  <li>Istituti con l'ultima visita datata: <b>${num(datate.length)}</b></li>
  <li>Istituti in cui vale la visita: <b>${num(valgono.length)}</b></li>
  <li>Istituti con divergenze tra le fonti: <b>${num(div.length)}</b></li>
</ul>`);
display(pannelloDati(conVisita.map(({i, v}) => ({codice: i.codice, nome: i.nome, visita: v.visita?.data, eta_mesi: v.eta_mesi, datata: v.datata ? "sì" : "", tre_mq: v.visita?.tre_mq, classe_stima: v.banda.classe, classe_finale: v.classe, fonte: v.fonte, divergenze: v.divergenze.map((d) => d.testo).join("; ")})),
  ["codice", "nome", "visita", "eta_mesi", "datata", "tre_mq", "classe_stima", "classe_finale", "fonte", "divergenze"].map((chiave) => ({chiave})),
  "fonte-per-istituto.csv", {nota: `Soglia della visita datata: ${VISITA_DATATA_MESI} mesi [DA DECIDERE: Luca].`}));
```

Le visite si leggono dai fogli pubblicati in fondo alle schede dell'Osservatorio (2017-2025). Antigone non dichiara una licenza di riuso: il sito usa solo dati fattuali, con il link alla scheda e al foglio di ogni visita. Gli eventi critici registrati nelle visite non sono mostrati: serviranno a una parte che verrà progettata a parte.

## La serie storica: che cosa esiste

```js
display(html`<div class="tabella-scorrevole"><table><thead><tr><th scope="col">Anno</th><th scope="col">Presenti (nazionali)</th><th scope="col">Capienza (nazionale)</th><th scope="col">Per istituto</th><th scope="col">Visite Antigone</th><th scope="col">Buchi</th></tr></thead>
<tbody>${st.copertura.map((c) => html`<tr><td>${c.anno}</td><td>${c.presenti_nazionali}</td><td>${c.capienza_nazionale}</td><td>${[c.per_istituto_ministero, c.per_istituto_schede].filter(Boolean).join("; ")}</td><td>${c.visite_antigone}</td><td>${c.buchi}</td></tr>`)}</tbody></table></div>`);
```

<p class="nota">Fonti: Ministero della Giustizia, DAP, Sezione statistica (serie dei presenti dal 1991; tabelle mensili per regione e per istituto, nell'archivio online dal 2019). Eventi in data/manual/eventi.yml, ognuno con la sua fonte e la sua etichetta.</p>

## Perché questa forma

<p>Cartogramma di Demers: ogni istituto è un quadrato con l'area proporzionale ai presenti, spostato quanto basta per non sovrapporsi (disposizione calcolata una volta in fase di build). Il quadrato tratteggiato è la capienza; il colore è lo spazio per persona rispetto a 3 m². La tipologia dell'istituto è nel filtro, nel tooltip e nella scheda, non nel colore: sette tipi non si distinguono bene a colori, e il colore serve alla domanda del progetto.</p>
<p class="avviso">[DA SCRIVERE: Luca] Il quadro what / why / how di Munzner, in tre righe.<br>What: …<br>Why: …<br>How: …</p>

## Raccolta automatica e controlli

I dati si raccolgono da soli con GitHub Actions: le schede ogni lunedì, la tabella del Ministero il 12 di ogni mese. Ultima raccolta con controlli: **${dataIt(f.ultima_raccolta)}**. Il sito si ricostruisce dopo ogni raccolta.

```js
// Il file è Markdown semplice: titoli "## " ed elenchi "- ". Lo si mostra riga per riga, senza interpretarlo oltre.
const righeControlli = controlli.split("\n").filter((r) => r.trim() && !r.startsWith("# "));
display(html`<details class="pannello" open><summary>Esito dei controlli (data/checks/ultimo.md)</summary>${righeControlli.map((r) =>
  r.startsWith("## ") ? html`<h3>${r.slice(3)}</h3>` : r.startsWith("- ") ? html`<p style="margin:.15rem 0">· ${r.slice(2)}</p>` : html`<p>${r}</p>`)}</details>`);
```

```js
const tot = f.ministero.totale_dichiarato;
const somma = (k) => d3.sum(istituti, (i) => i.ministero?.[k]);
if (tot) display(html`<p>Totali della tabella del Ministero al ${dataIt(f.ministero.data)}: dichiarati ${num(tot.capienza_regolamentare)} posti e ${num(tot.presenti)} presenti; somma delle righe collegate ${num(somma("capienza_regolamentare"))} e ${num(somma("presenti"))}.</p>`);
display(dati.avvisi.length
  ? html`<details class="pannello"><summary>Avvisi del caricamento dati (${dati.avvisi.length})</summary><ul>${dati.avvisi.map((a) => html`<li>${a}</li>`)}</ul></details>`
  : html`<p class="nota">Caricamento dei dati senza avvisi: tutti gli istituti collegati.</p>`);
```

## Link

```js
display(html`<ul>
  ${ambiente.repository ? html`<li><a href="${ambiente.repository}">Repository del progetto</a> (dati, script di raccolta, codice del sito)</li>` : html`<li>Repository del progetto [link aggiunto alla pubblicazione]</li>`}
  <li><a href="${ambiente.poster_2024}">Il poster del 2024 (DV-24.01)</a></li>
  <li><a href="./dati">Tutti i file dei dati</a></li>
</ul>`);
```
