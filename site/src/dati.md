---
title: Dati
---

```js
import {data as dataIt, num} from "./components/formato.js";
const dati = await FileAttachment("data/istituti.json").json();
const ambiente = await FileAttachment("data/ambiente.json").json();
const file = [
  {nome: "istituti.csv", f: FileAttachment("data/istituti.csv"), cosa: "Una riga per istituto: schede trasparenza, ultima tabella del Ministero, calcoli. Separatore virgola, UTF-8."},
  {nome: "istituti.json", f: FileAttachment("data/istituti.json"), cosa: "Gli stessi dati in forma annidata, con fonti, avvisi del caricamento ed esiti di Antigone. È il file usato dal sito."},
  {nome: "serie.csv", f: FileAttachment("data/serie.csv"), cosa: "Serie storica lunga: una riga per data, fonte e istituto."},
  {nome: "regioni.topojson", f: FileAttachment("data/regioni.topojson"), cosa: "Confini regionali semplificati per la mappa (ISTAT 1.1.2026 via openpolis, CC BY 4.0)."}
];
```

# Dati

Tutti i file usati dal sito. Sono generati a ogni pubblicazione dai file del repository (`data/`), senza modifiche a mano. Ultima generazione: ${dataIt(dati.generato)}.

```js
display(html`<table>
  <thead><tr><th scope="col">File</th><th scope="col">Contenuto</th><th scope="col">Peso</th></tr></thead>
  <tbody>${await Promise.all(file.map(async (d) => {
    const n = (await d.f.arrayBuffer()).byteLength;
    return html`<tr><td><a href="${d.f.href}" download="${d.nome}">${d.nome}</a></td><td>${d.cosa}</td><td style="white-space:nowrap">${num(n / 1024)} kB</td></tr>`;
  }))}</tbody></table>`);
```

```js
if (ambiente.repository) display(html`<p>I dati grezzi (copie delle schede, tabelle del Ministero, tabella di raccordo) sono nel <a href="${ambiente.repository}/tree/main/data">repository, cartella data/</a>, con la cronologia di ogni raccolta.</p>`);
```

## Licenze

- **Dati del Ministero della Giustizia (DAP)**: schede trasparenza e tabelle mensili. Condizioni d'uso di giustizia.it [VERIFICARE].
- **Esiti delle visite di Antigone**: aggregati copiati a mano dal report dell'Osservatorio [VERIFICARE le condizioni di riuso con Antigone].
- **Confini regionali**: ISTAT, CC BY 4.0, nella versione di openpolis/geojson-italy.
- **Tabella di raccordo, calcoli e serie**: elaborazioni di questo progetto, CC BY 4.0 [DA DECIDERE].
- **Codice**: MIT.

## Dizionario: istituti.csv

| Colonna | Contenuto | Etichetta |
|---|---|---|
| `codice_dap` | codice ufficiale DAP della scheda (chiave principale) | [verificata] |
| `codici_dap_sezioni` | codici sommati quando l'istituto ha più schede (San Vittore: BB01;BB32) | [verificata] |
| `id` | identificativo del progetto 2024 | [calcolato] |
| `nome`, `nome_ministero`, `nome_antigone` | nomi nelle tre nomenclature (scheda DAP, Ministero, Antigone) | [verificata] |
| `tipo`, `regione`, `provincia` | tipo di istituto (CC, CR, CCF, CRF, CL, ICAM, IP), regione, sigla di provincia | [verificata] |
| `lat_dap`, `lon_dap` | coordinate pubblicate dal DAP | [verificata] |
| `coord_da_verificare` | `si` se le coordinate DAP e quelle del 2024 distano più di 2 km | [calcolato] |
| `posti_reg` | posti regolamentari (9 m² per il primo posto, 5 m² per gli altri) | [verificata] |
| `posti_non_disp` | posti non disponibili | [verificata] |
| `presenti` | persone presenti | [verificata] |
| `stanze`, `stanze_non_disp` | stanze detentive e stanze non disponibili | [verificata] |
| `st_doccia`, `st_bidet`, `st_handicap`, `st_wc_porta`, `st_luce`, `st_prese` | stanze con doccia, bidet, per persone con disabilità, wc con porta, luce autonoma, prese elettriche | [verificata] |
| `pp_eff`, `pp_prev` | polizia penitenziaria effettiva e prevista [VERIFICARE] | [verificata] |
| `edu_eff`, `edu_prev` | educatori effettivi e previsti [VERIFICARE] | [verificata] |
| `agg_capienza`, `agg_spazi` | data di aggiornamento della scheda (capienza, spazi), AAAA-MM-GG | [verificata] |
| `posti_disp` | posti_reg − posti_non_disp | [calcolato] |
| `stanze_disp` | stanze − stanze_non_disp | [calcolato] |
| `superficie_lorda` | 9 · stanze_disp + 5 · (posti_disp − stanze_disp), in m² | [ipotesi] |
| `m2_lordi_persona` | superficie_lorda / presenti | [calcolato] |
| `persone_stanza` | presenti / stanze_disp | [calcolato] |
| `affollamento_reale` | presenti / posti_disp (1 = 100%) | [calcolato] |
| `casi` | casi limite: nessun presente, nessuna stanza disponibile, posti tutti non disponibili, dati incompleti | [calcolato] |
| `min_data` … `min_stranieri` | ultima tabella mensile del Ministero: data, capienza regolamentare, presenti, donne, stranieri | [verificata] |

Lo spazio "meno arredo" non è nei file: dipende da un parametro non ancora fissato (vedi [metodo](./metodo)) e si calcola nel sito.

## Dizionario: serie.csv

| Colonna | Contenuto |
|---|---|
| `data` | data del dato (AAAA-MM-GG) |
| `fonte` | `ministero` (tabella mensile) oppure `schede` (istantanea datata delle schede trasparenza) |
| `codice_dap` | istituto |
| `posti_reg`, `presenti` | posti regolamentari e presenti |
| `posti_non_disp`, `posti_disp`, `stanze_disp`, `superficie_lorda` | solo per `schede`: il Ministero non li pubblica |

## Avvisi del caricamento

```js
display(dati.avvisi.length
  ? html`<ul>${dati.avvisi.map((a) => html`<li>${a}</li>`)}</ul>`
  : html`<p>Nessun avviso: tutti i file presenti e tutti gli istituti collegati.</p>`);
```
