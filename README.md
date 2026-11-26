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
  manual/                   dati ottenuti a mano (Antigone, report non scaricabili)
  checks/ultimo.md          esito dei controlli dell'ultima raccolta
archive/
  manifest.csv              ogni copia conservata: data, sha256, file locale, snapshot Wayback
  files/ text/              copie delle pagine e dei PDF, estratti in Markdown
  extra_urls.txt            articoli e documenti da conservare oltre alle fonti
scripts/                    raccolta, archivio, controlli
site/                       sito pubblico (Observable Framework)
docs/                       ricognizione delle fonti, nomenclatura, metodo
```

## Sito

Il sito pubblico è in `site/` ([Observable Framework](https://observablehq.com/framework/), D3, Plot).
I data loader Python in `site/src/data/` leggono i file di `data/` e producono i file del sito;
la metrica è descritta in `docs/metodo-bozza.md` e il parametro d'arredo sta in `site/src/components/parametri.js`.
Pubblicazione su GitHub Pages con `.github/workflows/sito.yml` (a ogni push su `data/` o `site/` e dopo ogni raccolta).

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

## Licenze

Codice: MIT (`LICENSE`). Dati: restano con la licenza della fonte (vedi `sources.yml`); le elaborazioni
originali di questo repository: CC BY 4.0 [DA DECIDERE].
