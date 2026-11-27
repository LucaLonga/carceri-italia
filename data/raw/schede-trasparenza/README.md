# data/raw/schede-trasparenza

Schede trasparenza dei 190 istituti (Ministero della Giustizia, DAP). Raccolta: `scripts/fetch_schede.py`
ogni lunedì (workflow `raccolta`), poi `scripts/estrai_attivita.py`. Indirizzo di ogni scheda:
`url_scheda` in `data/reference/istituti_dap.csv`.

Il Ministero aggiorna le schede ogni giorno e sovrascrive il dato precedente: la serie esiste solo qui
(cronologia dei commit e copie datate), sulla Wayback Machine e in ArchiveBox.

| File | Contenuto | Quando cambia | Etichetta |
|---|---|---|---|
| `latest.csv` | campi numerici principali, una riga per istituto (`;`) | a ogni raccolta | [verificata] |
| `AAAA-MM-GG_schede.csv` | copia datata di `latest.csv` | solo se cambiano i numeri | [verificata] |
| `json/AAAA-MM-GG.json.gz` | tutto il contenuto di tutte le schede: tabelle, sottocampi (nome: valore), campi semplici ("dati aggiornati al") | solo se cambia il contenuto (le date di aggiornamento non contano) | [verificata] |
| `struttura/AAAA-MM-GG.json` | per ogni scheda, nell'ordine della pagina: gruppo, sezione, tipo (tabella, campi, semplice) e nomi dei campi; una riga per scheda | solo se cambia la struttura | [verificata] |
| `attivita/*.csv` | tabelle estratte dalla copia json più recente (vedi sotto) | a ogni raccolta | [verificata] |

`data/checks/ultimo.md` confronta le ultime due copie di `struttura/` e segnala come **AVVISO** le voci
(gruppo › sezione › campo) nuove o sparite: un campo che compare o scompare è un segnale da guardare.

## attivita/

Una riga per istituto (`personale`, `spazi`) o per voce (le altre), sempre con `data` (giorno della copia)
e `code` (codice DAP). I nomi delle colonne sono quelli della scheda, normalizzati
(`polizia penitenziaria - effettivi` → `polizia_penitenziaria_effettivi`).

| File | Sezioni della scheda |
|---|---|
| `personale.csv` | Personale: polizia penitenziaria, amministrativi, educatori (effettivi, previsti) e date di aggiornamento |
| `spazi.csv` | Spazi comuni e impianti; Spazi d'incontro con i visitatori (prefisso `incontro_`) |
| `corsi_formazione.csv` | Formazione lavoro › Corsi |
| `corsi_istruzione.csv` | Attività scolastiche › Corsi istruzione |
| `lavoro.csv` | Attività gestite da terzi (`gestione = terzi`), Lavorazioni gestite dall'amministrazione |
| `attivita.csv` | Attività teatrali, sportive, culturali, religiose (`tipo`); "a cura di" → `organizzata_da` |

Limiti: i dati sono quelli che ogni direzione inserisce, con date di aggiornamento diverse da istituto a
istituto; una tabella vuota può voler dire "nessuna attività" o "dato non inserito" [VERIFICARE caso per caso].
