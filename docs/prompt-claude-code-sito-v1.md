# Prompt per Claude Code: prima versione del sito "carceri-italia"

Copia tutto il testo sotto la riga in Claude Code, aperto nella cartella del repository `carceri-italia`.

---

Stai lavorando nel repository `carceri-italia` (leggi prima `README.md`, `sources.yml`,
`docs/metodo-bozza.md`, `docs/nomenclatura.md`, `docs/fonti.md`, `data/reference/README.md`).
Il repository raccoglie già i dati in automatico (GitHub Actions, cartella `scripts/`). Il tuo compito
è costruire la **prima versione del sito pubblico**, dentro questo stesso repository, senza toccare
gli script di raccolta né i dati in `data/raw/`.

## Obiettivo

Un sito statico, in italiano, ospitato su GitHub Pages e linkato dalla sezione "greenhouse" di
https://lucalonga.com, che risponde a una domanda: **quanto spazio ha davvero una persona detenuta in
Italia, istituto per istituto, e come cambia nel tempo?** L'unità visiva è la cella.

Pubblico: Antigone e chi lavora sul carcere, redazioni, studi di data visualization che guardano il
metodo. Tono sobrio: niente immagini di celle o persone, niente drammatizzazione visiva, niente rosso
allarme. Il rigore del metodo è parte del prodotto.

## Strumento

- **Observable Framework** (open source, `@observablehq/framework`), progetto in `site/`
  (`site/src/` per le pagine, `site/observablehq.config.js`). Hosting su GitHub Pages, non su
  Observable Cloud.
- Grafici con **D3** per le forme proprie (la cella in scala, la mappa) e **Observable Plot** per i
  grafici standard (serie storiche).
- **Data loader in Python** (`site/src/data/*.py`) che leggono i file del repository e producono i
  file usati dalle pagine. Nessun dato inventato o copiato a mano nelle pagine: ogni numero mostrato
  viene da un file in `data/`.
- Font open source (per esempio IBM Plex Sans/Mono o Atkinson Hyperlegible, ospitati nel sito).
  Nessun tracciamento, nessun cookie, nessuna risorsa da CDN di terzi a runtime se si può evitare.
- Prima di iniziare verifica nella documentazione attuale di Framework le funzioni che userai
  (data loader, route parametriche `[codice].md`, `FileAttachment`, deploy su GitHub Pages).
  Se una funzione non c'è nella versione installata, dimmelo e proponi un'alternativa.

## Dati di ingresso (contratto)

- `data/reference/istituti.csv`: tabella di raccordo. Chiave principale **`codice_dap`**;
  `id` è l'identificativo del 2024. Milano San Vittore ha due codici (`codici_dap_sezioni` = BB01;BB32):
  nelle schede vanno sommati. Usa `lat_dap`/`lon_dap` per la mappa e segnala gli istituti con
  `coord_da_verificare = si` (per esempio con un'annotazione nella scheda istituto).
- `data/raw/schede-trasparenza/latest.csv` (separatore `;`): stato attuale per codice DAP. Colonne:
  `posti_reg, posti_non_disp, presenti, stanze, stanze_non_disp, st_doccia, st_bidet, st_handicap,
  st_wc_porta, st_luce, st_prese, pp_eff, pp_prev, edu_eff, edu_prev, agg_capienza, agg_spazi`.
- `data/raw/schede-trasparenza/AAAA-MM-GG_schede.csv`: istantanee datate (stessa struttura) → serie storica
  delle schede. Oggi ce n'è una sola: la serie deve funzionare con 1 punto e crescere da sola.
- `data/raw/ministero/AAAA-MM-GG_capienze-per-istituto.csv` + `indice.json`: tabelle mensili del Ministero
  (`regione, istituto, tipo, capienza_regolamentare, presenti, donne, stranieri`). Si collegano a
  `istituti.csv` con **nome normalizzato + tipo** (vedi `norm_name` in `scripts/common.py`; usa anche
  `alias_ministero`). È la serie storica lunga (posti regolamentari e presenti, senza posti non disponibili).
- `data/manual/antigone/osservatorio_2026-11-25.md`: esiti aggregati delle visite di Antigone.
- `data/checks/ultimo.md`: esito dei controlli dell'ultima raccolta (mostralo nella pagina di metodo).

Scrivi un data loader `site/src/data/istituti.json.py` che unisce tutto in un unico file per istituto, e
uno `site/src/data/serie.csv.py` per la serie lunga. Se un file manca o un istituto non si collega,
il loader non deve fallire in silenzio: scrive l'elenco dei problemi in un campo `avvisi` e lo stampa.

## Metrica (da `docs/metodo-bozza.md`, da implementare esattamente così)

```
posti_disp     = posti_reg − posti_non_disp
stanze_disp    = stanze − stanze_non_disp
superficie_lorda ≈ 9 · stanze_disp + 5 · (posti_disp − stanze_disp)      [ipotesi]
m2_lordi_persona = superficie_lorda / presenti                           [calcolato]
persone_stanza   = presenti / stanze_disp                                [calcolato]
affollamento_reale = presenti / posti_disp
```

- La soglia **3 m²** (CEDU, *Torreggiani c. Italia*, 2013) è una linea fissa in ogni vista dove compare
  lo spazio per persona.
- Lo spazio stimato è **lordo**; la soglia è sullo spazio **calpestabile**. Mostra una **banda**: limite
  alto = stima lorda; limite basso = lorda − `arredo_m2_persona`, un parametro **non ancora deciso**.
  Mettilo in un solo punto (`site/src/components/parametri.js`, valore provvisorio 1,5 m² con il commento
  `// [ipotesi] DA FISSARE con una fonte`) e mostralo nella pagina di metodo con un controllo (slider)
  che permette al lettore di vedere come cambia la classificazione.
- Classificazione per colore (palette sequenziale sobria, accessibile ai daltonici, contrasto verificato):
  "banda tutta sopra 3 m²", "la banda attraversa 3 m²", "banda tutta sotto 3 m²", "dato mancante".
  Mai un binario sopra/sotto presentato come certo.
- Ogni numero calcolato porta l'etichetta [calcolato] o [ipotesi] nel tooltip o nella didascalia.
- Gestisci i casi limite: presenti = 0 (Pozzuoli, chiuso), stanze_disp = 0, posti tutti non disponibili.

## Pagine

Struttura dal piano di progetto (sez. 7):

1. **Home** (`index.md`)
   - Titolo e una riga: la domanda.
   - **Vista principale**: mappa d'Italia (confini regionali da un file open data incluso nel repo,
     proiezione adatta all'Italia, es. Transverse Mercator), un simbolo per istituto, colore = classe
     della banda, dimensione = presenti. Al passaggio: nome, m² per persona (banda), persone per stanza,
     data del dato. Al clic: scheda istituto.
   - **Tre numeri chiave**: istituti in cui la banda tocca o scende sotto 3 m²; persone detenute in quegli
     istituti; data dei dati. Calcolati, non scritti a mano.
   - **"Che cosa non sappiamo"**, visibile senza scorrere fino in fondo (subito dopo i numeri chiave):
     superficie reale delle celle non pubblica; motivi dei posti non disponibili non spiegati; provenienza
     per istituto non pubblica; coordinate in disaccordo tra fonti. Il vuoto va **disegnato**, non solo
     scritto: per esempio i posti non disponibili come celle tratteggiate nella vista della cella.
   - Elenco ordinabile e filtrabile degli istituti (regione, tipo, classe), utile anche come alternativa
     accessibile alla mappa.
2. **Scheda istituto** (`istituto/[codice].md`, route parametrica, una pagina per codice DAP)
   - Deve funzionare **da sola su mobile**, senza la mappa (link diretto condivisibile).
   - **La cella in scala**: un quadrato di 3 m² ripetuto; dentro, le persone come punti; la superficie
     disponibile per persona confrontata con la soglia. Disegno geometrico, astratto, in scala reale
     (1 m = N px dichiarato), niente arredi illustrati.
   - Serie storica: presenti, posti regolamentari, posti disponibili (dove esistono le istantanee), con la
     soglia; spiega i salti (cambi di capienza).
   - Numeri: posti regolamentari e disponibili, stanze e stanze non disponibili, dotazioni delle stanze
     (quota con doccia, wc con porta), personale effettivo/previsto.
   - Nomi dell'istituto nelle tre nomenclature (Ministero, DAP, Antigone) e note di qualità.
   - Fonti con data di aggiornamento della scheda (`agg_capienza`, `agg_spazi`).
3. **Metodo** (`metodo.md`, 300-400 parole più i pannelli): fonti, licenze, formula, ipotesi, banda,
   slider del parametro d'arredo, confronto con le visite di Antigone, quadro what/why/how di Munzner
   in tre righe (lascia un segnaposto `[DA SCRIVERE: Luca]` per le tre righe), data dell'ultima raccolta
   automatica, esito dei controlli, link al repository e al poster del 2024
   (https://lucalonga.com/projects/dv-24-01).
4. **Dati** (`dati.md`): tutti i file scaricabili (CSV/JSON) con dizionario delle colonne e licenza.

## Codice e dati visibili (pannelli espandibili)

Sotto ogni grafico, due pannelli `<details>` chiusi per default:
- **"Dati"**: tabella dei dati esatti usati dal grafico + link per scaricarli (CSV).
- **"Codice"**: il codice del grafico, mostrato con evidenziazione della sintassi. Il codice mostrato deve
  essere **lo stesso che gira** (non una copia che può divergere): usa i blocchi di codice di Framework
  con `echo`, oppure importa il sorgente del componente come testo.
Facoltativo, solo se semplice: un link "apri in un notebook Observable" per la cella in scala. Gli
embed da observablehq.com non sono necessari: tutto deve funzionare anche senza servizi esterni.

## Deploy

- Workflow `.github/workflows/sito.yml`: build del sito (Node LTS + Python per i data loader) e deploy su
  GitHub Pages; si avvia a ogni push su `main` che tocca `data/` o `site/`, quindi anche dopo ogni
  raccolta automatica, e a mano (`workflow_dispatch`).
- Configura `base` per l'indirizzo `https://<utente>.github.io/carceri-italia/` (lascia il nome utente
  in una variabile; non indovinarlo).
- Il workflow di raccolta esistente (`raccolta.yml`) non va modificato, salvo aggiungere, se serve, un
  `workflow_run` che avvia il deploy.

## Qualità

- Accessibilità: testo alternativo per ogni grafico (frase generata dai dati), navigazione da tastiera
  della mappa o alternativa equivalente (l'elenco), contrasti AA, `prefers-reduced-motion`.
- Mobile: prova a 375 px di larghezza; la scheda istituto deve restare leggibile senza scorrimento
  orizzontale.
- Prestazioni: il JSON della home sotto i 300 kB; niente librerie pesanti oltre a D3 e Plot.
- Lingua: italiano, frasi brevi, numeri in formato italiano (virgola decimale, punto per le migliaia),
  date in formato "24 novembre 2026".

## Modo di lavorare

1. Prima di scrivere codice, mostrami un piano breve: file che creerai, struttura delle pagine,
   eventuali dubbi sul contratto dei dati. Aspetta il mio via.
2. Costruisci per passi: data loader → home con elenco → mappa → scheda istituto → cella in scala →
   metodo → dati → deploy. Dopo ogni passo esegui `npm run build` (nella cartella `site/`) e correggi gli
   errori.
3. Alla fine: controlla 5 istituti a caso confrontando i numeri mostrati con `latest.csv`, e verifica che
   la somma dei presenti sulla home coincida con la somma del file. Riportami l'esito.
4. Non inventare dati, fonti, citazioni o testi di metodo: dove manca un contenuto, lascia
   `[DA SCRIVERE: Luca]` o `[VERIFICARE]`.
5. Commit piccoli con messaggi in italiano. Non fare push senza chiedermelo.
