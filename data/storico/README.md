# data/storico

Serie storica dal Ministero della Giustizia (DAP, Sezione statistica). Raccolta: `scripts/fetch_storico.py`
(solo a mano, workflow `storico.yml`). Grezzo in `data/raw/storico/` e `data/raw/ministero/html/`.

| File | Contenuto | Copertura | Etichetta |
|---|---|---|---|
| `presenti_semestrali.csv` | presenti al 30/6 e al 31/12, imputati, condannati, internati, donne, stranieri | 1991-oggi | [verificata] |
| `nazionale_mensile.csv` | istituti, capienza regolamentare, presenti, donne, stranieri (riga "Totale") | dal gennaio 2019 | [verificata] |
| `regionale_mensile.csv` | stesse colonne per regione | dal gennaio 2019 | [verificata] |
| `per_istituto_mensile.csv` | capienza regolamentare, presenti, donne, stranieri per istituto | dal gennaio 2019 | [verificata] |
| `inventario_ministero.csv` | tutte le voci dell'elenco statistiche (titolo, data, link) | archivio online | [verificata] |
| `copertura.csv` | per ogni anno dal 2000: che cosa esiste, da dove viene, buchi | 2000-oggi | [calcolato] |

**Buchi dichiarati**: la capienza (nazionale e per istituto) prima del 2019 non è nell'archivio online del
Ministero [DA CERCARE: copie della Wayback Machine, Annuario ISTAT, rapporti Antigone]. I presenti ci sono
dal 1991 ogni sei mesi. Alcuni mesi mancano anche dopo il 2019 (vedi `copertura.csv`).

**Controlli**: la somma delle righe si confronta con la riga "Totale" dichiarata; le differenze finiscono in
`indice.json` (oggi: la tabella per regione del 28 febbraio 2026).
