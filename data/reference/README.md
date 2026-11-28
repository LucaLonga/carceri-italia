# data/reference

## istituti.csv: tabella di raccordo degli istituti

Una riga per istituto come lo conta il Ministero nella tabella mensile (189 al 31.10.2026).

| Colonna | Contenuto | Etichetta |
|---|---|---|
| `id` | identificativo del progetto 2024 (stabile) | [calcolato] |
| `codice_dap` | codice ufficiale DAP della scheda trasparenza (es. BB17) | [verificata] |
| `codici_dap_sezioni` | se l'istituto ha più schede (San Vittore: BB01;BB32) | [verificata] |
| `nome_ministero` | nome nella tabella mensile del Ministero al 31.10.2026 | [verificata] |
| `alias_ministero` | nomi precedenti usati dal Ministero (separati da `;`) | [verificata] |
| `nome_scheda_dap` | nome nella scheda trasparenza | [verificata] |
| `nome_antigone` | nome completo usato da Antigone (lavoro 2024) | [calcolato] |
| `tipo`, `tipo_esteso` | CC casa circondariale, CR casa di reclusione, CCF/CRF femminili, CL casa lavoro, ICAM, IP istituti di pena | [verificata] |
| `regione`, `provincia` | come nel 2024 | [verificata] |
| `sigla_prov_attuale` | sigla aggiornata (FC, PU, SU, MB…) | [calcolato] |
| `lat_dap`, `lon_dap` | coordinate pubblicate dal DAP | [verificata] (ma con errori, vedi sotto) |
| `lat_geocod`, `lon_geocod`, `indirizzo` | geocodifica del 2024 | [calcolato] |
| `distanza_coord_km` | distanza approssimata tra le due coordinate | [calcolato] |
| `coord_da_verificare` | `si` se le due coordinate distano più di circa 2 km | [calcolato] |
| `note_qualita` | problemi noti | |

Chiave per collegare la tabella mensile: **nome normalizzato + tipo** (Trani ha due istituti con lo stesso nome).
Per collegare le schede: `codice_dap`.

## istituti_dap.csv

Prodotto da `scripts/fetch_schede.py` a ogni raccolta: anagrafica ufficiale delle 190 schede (codice,
nome, tipo, coordinate, indirizzo, regione, provveditorato).

## nomi_nel_testo.csv

Nomi con cui gli istituti compaiono nei testi (stampa, comunicati, documenti), usati da
`scripts/istituti_nel_testo.py` per dare a ogni testo i `codici_dap` citati. Prima versione generata
dalla tabella di raccordo e corretta a mano il 2026-11-28; si corregge a mano.

| Colonna | Contenuto |
|---|---|
| `codici_dap` | uno o più codici (`;`): più codici = nome ambiguo (Roma, Napoli, Milano, Rebibbia, Trani…) |
| `testo` | il nome come si scrive, con le maiuscole (il confronto le rispetta: "Opera" sì, "opera" no) |
| `tipo` | `citta` oppure `luogo_o_soprannome` (Marassi, Poggioreale, San Vittore, Bancali…) |
| `richiede_contesto` | `si`: il nome vale solo se vicino c'è una parola del carcere ("carcere di", "casa circondariale", "detenuti"…). Vale per tutte le città e per i nomi comuni o di altri luoghi (Opera, Bicocca, Santa Maria Maggiore, Gorgona, Uta…) |
| `nota` | perché |

Limiti noti [VERIFICARE con l'uso]: soprannomi mancanti; città citate per il tribunale e non per il carcere
("tribunale di Santa Maria Capua Vetere"), se accanto c'è anche la parola "detenuti"; nomi a inizio frase.
Prove in `tests/test_istituti_nel_testo.py` (`python -m unittest discover -s tests`).
