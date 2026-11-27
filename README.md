# carceri-italia

Quanto spazio ha davvero una persona detenuta in Italia, istituto per istituto, e come cambia nel tempo.

Seconda versione del progetto [DV-24.01](https://lucalonga.com/projects/dv-24-01): il poster del 2024
era la fotografia di un giorno; qui i dati si raccolgono da soli ogni settimana e ogni mese, e la
cronologia dei commit diventa la serie storica.

## Che cosa c'è

```
sources.yml                 registro delle fonti (cosa, dove, come si raccoglie, licenza)
data/
  reference/istituti.csv    tabella di raccordo: id, codice DAP, nomi Ministero / DAP / Antigone, coordinate
  raw/ministero/            tabelle mensili "capienze per istituto" (CSV + HTML grezzo) e indice.json
  raw/schede-trasparenza/   schede DAP: latest.csv (serie nei commit) + copie datate + JSON completo
  raw/dv-24-01/             dati del progetto 2024
  manual/                   dati ottenuti a mano (Antigone, report non scaricabili, eventi.yml)
  antigone/                 visite dell'Osservatorio per istituto (campi estratti) e abbinamento
  storico/                  serie storica dal Ministero (1991-oggi) e copertura anno per anno
  raw-locale/               grezzo senza licenza di riuso dichiarata: cache locale fuori da git (copia conservata nel repository privato)
  checks/ultimo.md          esito dei controlli dell'ultima raccolta
archive/
  manifest.csv              ogni copia conservata: data, sha256, file locale, snapshot Wayback
  files/ text/              copie delle pagine e dei PDF, estratti in Markdown
  extra_urls.txt            articoli e documenti da conservare oltre alle fonti
scripts/                    raccolta, archivio, controlli
site/                       prototipo del sito (Observable Framework), banco di lavoro, non pubblicato
docs/                       ricognizione delle fonti, nomenclatura, metodo
```

## Sito

Il prototipo del sito è in `site/` ([Observable Framework](https://observablehq.com/framework/), D3, Plot).
I data loader Python in `site/src/data/` leggono i file di `data/` e producono i file del sito;
la metrica è descritta in `docs/metodo-bozza.md` e il parametro d'arredo sta in `site/src/components/parametri.js`.
Il sito è un banco di lavoro per i dati e **non si pubblica**: `.github/workflows/sito.yml` parte solo a mano,
fa il build e pubblica su GitHub Pages soltanto con `pubblica: si` (Pages oggi è spento).

```bash
cd site
npm ci
npm run dev        # anteprima su http://127.0.0.1:3000
npm run build      # sito statico in site/dist
npm run pulisci    # svuota la cache dei data loader (si rieseguono solo se cambia il loader)
```

## Raccolta automatica

GitHub Actions (`.github/workflows/raccolta.yml`):
- ogni lunedì: schede trasparenza dei 190 istituti;
- il 12 di ogni mese: tabelle mensili del Ministero (con recupero dei mesi passati) e archivio delle fonti;
- dopo ogni raccolta: controlli; commit solo se i dati sono cambiati. Se uno script fallisce, GitHub manda una notifica.
- ogni tre mesi e a mano (`antigone.yml`): schede dell'Osservatorio di Antigone e abbinamento;
- solo a mano (`storico.yml`): serie storica dal Ministero.

In locale:

```bash
pip install -r requirements.txt
cd scripts
python fetch_schede.py --limite 3     # prova veloce
python fetch_ministero.py --solo-ultimo
python archive_sources.py --no-wayback
python checks.py
ARCHIVEBOX_DATA=~/ArchiveBoxData ./archivebox_local.sh   # terza copia, solo in locale
```

Per la Wayback Machine con l'API autenticata: chiavi S3 di archive.org nei secrets del repository
`IA_ACCESS_KEY` e `IA_SECRET_KEY` (facoltative).

## Conservazione delle fonti

Ogni fonte importante si conserva in tre modi: copia dei dati e della pagina nel repository
(CSV, Markdown, JSON, PDF), snapshot sulla Wayback Machine, copia locale con ArchiveBox.
Le schede trasparenza si aprono con una richiesta POST e la Wayback Machine non le può salvare:
per quelle fa fede la copia JSON nel repository.

## Scheda di provenienza

| Colonna / dato | Fonte | Estrazione | Metodo | Licenza | Etichetta |
|---|---|---|---|---|---|
| capienza regolamentare, presenti, donne, stranieri (mensili) | Ministero della Giustizia, DAP | mensile | scraping HTML | [VERIFICARE] | [verificata] |
| posti non disponibili, stanze, dotazioni, personale | DAP, schede trasparenza | settimanale | scraping HTML (POST) | [VERIFICARE] | [verificata] |
| codice DAP, coordinate ufficiali | DAP, mappa delle schede | settimanale | scraping script della pagina | [VERIFICARE] | [verificata] |
| nomi Antigone, geocodifica 2024 | lavoro DV-24.01 | 2024 | manuale + geocodifica | CC BY 4.0 [DA DECIDERE] | [calcolato] |
| visite dell'Osservatorio | Antigone | manuale | copia dal report | [VERIFICARE] | [verificata] |
| superficie e spazio per persona | elaborazione | a ogni raccolta | vedi docs/metodo-bozza.md | | [calcolato] / [ipotesi] |
| visite dell'Osservatorio per istituto: data, presenze e capienza alla visita, 3 m² calpestabili, docce, wc, riscaldamento, acqua calda, costruzione, personale | Antigone, schede e fogli Google | ogni tre mesi | scraping dei fogli in CSV, lettura per etichetta | nessuna dichiarata: solo campi fattuali, grezzo fuori da git | [verificata] |
| celle visitate: posti e persone per cella | Antigone, testo libero delle visite | ogni tre mesi | estrazione da frasi non ambigue | come sopra | [calcolato] dal testo [VERIFICARE] |
| eventi critici (autolesionismo, suicidi, isolamento) | Antigone | ogni tre mesi | come sopra | come sopra | [verificata], non mostrati nel sito |
| abbinamento Antigone ↔ codice DAP | elaborazione + eccezioni a mano | a ogni raccolta | nome identico o simile, stessa regione e tipo | CC BY 4.0 [DA DECIDERE] | [calcolato] |
| presenti nazionali dal 1991 | Ministero, DAP | semestrale | scraping HTML | [VERIFICARE] | [verificata] |
| capienza e presenti nazionali e regionali mensili | Ministero, DAP | dal 2019, mensile | scraping HTML | [VERIFICARE] | [verificata] |
| capienze per istituto dal 2019 | Ministero, DAP | mensile | rilettura delle pagine grezze (7 o 8 colonne) | [VERIFICARE] | [verificata] |
| eventi (leggi, sentenze, piani) | fonti primarie, a mano | quando serve | data/manual/eventi.yml | | [verificata] / [VERIFICARE] per voce |
| cartogramma (posizioni dei quadrati) | elaborazione | a ogni pubblicazione | simulazione di forze con collisione tra quadrati | MIT (codice) | [calcolato] |

## Licenze

Codice: MIT (`LICENSE`). Dati: restano con la licenza della fonte (vedi `sources.yml`); le elaborazioni
originali di questo repository: CC BY 4.0 [DA DECIDERE].
