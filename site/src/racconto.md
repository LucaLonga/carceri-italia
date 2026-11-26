---
title: Il racconto
toc: false
---

```js
import {cartogramma, STATO_PIENO} from "./components/demers.js";
import {scrolly, strati} from "./components/scrolly.js";
import {cella, datiCella} from "./components/cella.js";
import {riquadri, numeriRiquadri, storia} from "./components/riquadri.js";
import {valutazione, classe} from "./components/metrica.js";
import {ARREDO_M2_PERSONA, VISITA_DATATA_MESI} from "./components/parametri.js";
import {legenda} from "./components/legenda.js";
import {data as dataIt, num, pct, m2} from "./components/formato.js";
import {pannelloDati, pannelloCodice} from "./components/pannelli.js";
```

```js
const dati = await FileAttachment("data/istituti.json").json();
const carto = await FileAttachment("data/cartogramma.json").json();
const st = await FileAttachment("data/storico.json").json();
const istituti = dati.istituti;
const val = new Map(istituti.map((i) => [i.codice, valutazione(i)]));
const presenti = d3.sum(istituti, (i) => i.scheda?.presenti);
const oltre = istituti.filter((i) => (i.scheda?.presenti ?? 0) > (i.scheda?.posti_reg ?? Infinity));
const piuGrande = d3.greatest(istituti, (i) => i.scheda?.presenti ?? 0);
const conta = d3.rollup(istituti, (v) => v.length, (i) => val.get(i.codice).classe);
const conAntigone = istituti.filter((i) => i.visite_antigone);
const daVisita = istituti.filter((i) => val.get(i.codice).fonte === "antigone");
const divergenti = istituti.filter((i) => val.get(i.codice).divergenze.length);
// Istituto esempio per la cella: il più affollato (meno m² lordi) tra quelli con almeno 300 presenti.
const esempio = d3.least(istituti.filter((i) => (i.scheda?.presenti ?? 0) >= 300 && i.calc.m2_lordi_persona), (i) => i.calc.m2_lordi_persona);
const dc = datiCella(esempio);
const nR = numeriRiquadri(istituti);
const dataDati = dataIt(dati.fonti.schede.data_max);
const sem = st.semestrali.filter((d) => d.data >= "2000");
```

# Quanto spazio ha una persona detenuta in Italia

<p class="domanda">Un racconto in dieci passi. Scorri: la mappa cambia a ogni passo. Dati al ${dataDati}.</p>

```js
const larghezzaFigura = Math.min(width, 900) * (width >= 900 ? 0.58 : 1);
const mappa = cartogramma(carto, istituti, {larghezza: larghezzaFigura, id: "racconto", stato: {...STATO_PIENO, quadrati: false, tratteggi: false, colore: false}});
const figura = strati({
  mappa,
  cella: (() => { const d = document.createElement("div"); d.className = "figura-cella"; d.append(cella(esempio, {larghezza: Math.min(larghezzaFigura, 420)})); return d; })(),
  storia: storia(st, {larghezza: Math.max(320, larghezzaFigura), altezza: width < 640 ? 300 : 440}),
  riquadri: riquadri(carto, nR, {larghezza: larghezzaFigura})
});

const P = (titolo, ...corpo) => html`<div><h2>${titolo}</h2>${corpo}</div>`;
const passi = [
  {figura: "mappa", stato: {sagoma: true, quadrati: true, tratteggi: false, colore: false, evidenzia: null},
   contenuto: P("1. L'Italia delle carceri",
     html`<p>Ogni quadrato è un istituto penitenziario per adulti: ${num(istituti.length)} in tutto. Sta vicino a dove si trova davvero, spostato quanto basta per non coprire gli altri.</p>`)},
  {figura: "mappa", stato: {evidenzia: (i) => (i.scheda?.presenti ?? 0) >= 1000},
   contenuto: P("2. La grandezza è fatta di persone",
     html`<p>L'area di ogni quadrato è il numero di persone presenti: ${num(presenti)} in tutto il ${dataDati}.</p>`,
     html`<p>In evidenza gli istituti con almeno 1.000 persone. Il più grande è ${piuGrande.nome}, con ${num(piuGrande.scheda.presenti)}.</p>`)},
  {figura: "mappa", stato: {tratteggi: true, capienza: "reg", evidenzia: (i) => (i.scheda?.presenti ?? 0) > (i.scheda?.posti_reg ?? Infinity)},
   contenuto: P("3. La capienza",
     html`<p>Il quadrato tratteggiato è la capienza: i posti regolamentari, calcolati con 9 m² per il primo posto della stanza e 5 m² per ogni altro.</p>`,
     html`<p>Dove il quadrato pieno esce dal tratteggio, le persone sono più dei posti. Succede in <b>${num(oltre.length)}</b> istituti su ${num(istituti.length)}.</p>`)},
  {figura: "mappa", stato: {colore: true, evidenzia: null},
   contenuto: P("4. Lo spazio per persona",
     html`<p>Nel 2013 la Corte europea dei diritti dell'uomo, nella sentenza Torreggiani, ha indicato 3 m² calpestabili a persona come soglia minima.</p>`,
     html`<p>Il colore dice dove sta ogni istituto rispetto a quella soglia. Lo spazio è stimato dai posti, quindi è un intervallo: tra lo spazio lordo e lo spazio meno ${m2(ARREDO_M2_PERSONA)} di arredo a persona [ipotesi].</p>`,
     legenda(Object.fromEntries(conta), {visita: true}))},
  {figura: "cella", stato: null,
   contenuto: P(`5. Dentro una cella di ${esempio.nome}`,
     html`<p>La stanza media di ${esempio.nome} misura circa ${m2(dc.area, 1)} lordi e ospita in media ${num(dc.persone, 1)} persone [calcolato].</p>`,
     html`<p>Ogni quadrato è 3 m², in scala reale. Il tratteggio è l'arredo. Dove due punti stanno nello stesso quadrato, una persona ha meno di 3 m².</p>`,
     html`<p><a href="./istituto/${esempio.codice}">La scheda di ${esempio.nome}</a></p>`)},
  {figura: "mappa", stato: {colore: true, evidenzia: (i, v) => v.fonte === "antigone" || v.divergenze.length > 0},
   contenuto: P("6. Ministero e Antigone",
     html`<p>Il Ministero conta i posti. L'Osservatorio di Antigone entra negli istituti e guarda le celle. Quando una visita è recente (meno di ${num(VISITA_DATATA_MESI)} mesi), vale la visita: la tacca nell'angolo lo segnala.</p>`,
     html`<p>${num(conAntigone.length)} istituti hanno almeno una visita; per ${num(daVisita.length)} la visita è abbastanza recente da valere. In ${num(divergenti.length)} le due fonti non dicono la stessa cosa.</p>`)},
  {figura: "storia", stato: null,
   contenuto: P("7. Che cosa è cambiato dal 2000",
     html`<p>Le persone detenute erano ${num(sem[0]?.presenti)} a metà 2000 e ${num(sem.at(-1)?.presenti)} il ${dataIt(sem.at(-1)?.data)}.</p>`,
     html`<p>La capienza nazionale è nell'archivio online del Ministero solo dal 2019: prima c'è un buco, segnato in grigio.</p>`,
     html`<p class="nota">Schema provvisorio. [DA DECIDERE: Luca] la forma definitiva: sulla mappa o in uno schema a parte.</p>`)},
  {figura: "riquadri", stato: null,
   contenuto: P("8. Tre numeri, nella scala della mappa",
     html`<p><b>${num(nR.mancanti)}</b> posti mancanti: le persone oltre i posti regolamentari, sommate istituto per istituto [calcolato].</p>`,
     html`<p><b>${num(nR.nonDisponibili)}</b> posti che esistono ma non si usano. Le schede non dicono perché.</p>`,
     html`<p><b>${num(nR.sotto)}</b> persone in istituti sotto 3 m² (${pct(nR.sotto / nR.presenti, 1)}) [calcolato].</p>`)},
  {figura: "mappa", stato: {colore: true, tratteggi: true, evidenzia: (i, v) => v.classe === "mancante" || i.coord_da_verificare},
   contenuto: P("9. Che cosa non sappiamo",
     html`<ul><li>La superficie reale delle celle: non è pubblica. Qui è una stima.</li>
       <li>Perché ci sono posti non disponibili.</li>
       <li>Da dove vengono le persone, istituto per istituto.</li>
       <li>Dove sono esattamente ${num(istituti.filter((i) => i.coord_da_verificare).length)} istituti: le fonti non concordano (in evidenza).</li></ul>`)},
  {figura: "mappa", stato: {...STATO_PIENO},
   contenuto: P("10. Metodo e fonti",
     html`<p>Schede trasparenza del DAP, tabelle mensili del Ministero, visite dell'Osservatorio di Antigone. Ogni numero calcolato ha la sua etichetta. Il metodo, le ipotesi e i file sono nelle pagine <a href="./metodo">metodo</a> e <a href="./dati">dati</a>.</p>`,
     html`<p>Ora la mappa è tua: passa sopra un quadrato o usa Tab, clic per la scheda.</p>`)}
];

const racconto = scrolly(passi, {
  figura,
  etichetta: "Racconto in dieci passi",
  attiva: (k) => {
    const p = passi[k];
    figura.mostra(p.figura);
    if (p.figura === "mappa" && p.stato) mappa.aggiorna(p.stato);
  }
});
invalidation.then(() => racconto.ferma());
display(racconto);
```

## Esplora

```js
const cercaR = view(Inputs.text({label: "Cerca un istituto", placeholder: "nome", autocomplete: "off"}));
const capR = view(Inputs.radio(new Map([["regolamentare", "reg"], ["disponibile", "disp"]]), {label: "Capienza", value: "reg"}));
```

```js
// Agisce solo quando il lettore usa i controlli: al caricamento il racconto parte dal passo 1.
const qR = cercaR.trim().toLowerCase();
if (qR || capR !== "reg") {
  mappa.aggiorna({...STATO_PIENO, capienza: capR, evidenzia: qR ? (i) => i.nome.toLowerCase().includes(qR) : null});
  figura.mostra("mappa");
}
```

<p class="nota">La ricerca e la capienza agiscono sulla mappa qui sopra. Elenco completo, filtri e tabella scaricabile: <a href="./">mappa e istituti</a>.</p>

```js
display(pannelloDati(istituti.map((i) => {
  const v = val.get(i.codice);
  return {codice: i.codice, nome: i.nome, tipo: i.tipo, presenti: i.scheda?.presenti, posti_reg: i.scheda?.posti_reg, posti_non_disp: i.scheda?.posti_non_disp,
    classe: v.classe, fonte: v.fonte, visita: v.visita?.data ?? "", visita_datata: v.datata ? "sì" : "", divergenze: v.divergenze.map((d) => d.testo).join("; ")};
}), ["codice", "nome", "tipo", "presenti", "posti_reg", "posti_non_disp", "classe", "fonte", "visita", "visita_datata", "divergenze"].map((chiave) => ({chiave})),
  "racconto-istituti.csv", {nota: `Riquadri: posti mancanti ${num(nR.mancanti)}, non disponibili ${num(nR.nonDisponibili)}, persone sotto 3 m² ${num(nR.sotto)}.`}));
display(pannelloCodice(await FileAttachment("components/scrolly.js").text(), "components/scrolly.js"));
display(pannelloCodice(await FileAttachment("components/riquadri.js").text(), "components/riquadri.js"));
```
