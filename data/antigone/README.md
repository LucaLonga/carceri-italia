# data/antigone

Visite dell'Osservatorio di Antigone sulle condizioni di detenzione, istituto per istituto.
Fonte: https://www.antigone.it/osservatorio_detenzione/regioni (schede) e i fogli Google pubblicati
collegati in fondo a ogni scheda, uno per visita. Raccolta: `scripts/fetch_antigone.py`; abbinamento:
`scripts/abbina_antigone.py`.

**Licenza**: antigone.it non dichiara una licenza di riuso (controllato il 2026-11-26). Qui ci sono
solo campi fattuali estratti, con il link alla scheda e al foglio di ogni visita. Il grezzo (pagine e
fogli) resta in `data/raw-locale/antigone/`, fuori da git. Permesso da chiedere ad Antigone [DA FARE].

## visite.csv (una riga per visita)

| Colonna | Contenuto | Etichetta |
|---|---|---|
| `scheda_id`, `url_scheda` | identificativo e link della scheda sul sito di Antigone | [verificata] |
| `anno_etichetta`, `url_foglio` | anno indicato nel link ("visita svolta nel …") e link al foglio | [verificata] |
| `nome_foglio`, `tipologia` | nome e tipo dell'istituto scritti nel foglio | [verificata] |
| `data_visita` | data della visita (AAAA-MM-GG) | [verificata] |
| `presenti_visita`, `capienza_visita` | persone al momento della visita e capienza regolamentare indicata | [verificata] |
| `tre_mq_calpestabili` | "In tutte le celle visitate sono garantiti 3 mq calpestabili per ogni persona?" si/no/nd | [verificata] |
| `riscaldamento`, `acqua_calda`, `wc_separato`, `doccia_in_cella`, `spazi_non_in_uso` | risposte si/no/nd | [verificata] |
| `anno_costruzione`, `anno_apertura` | come scritti nel foglio (anche fasce: "Dal 1950 al 1980") | [verificata] |
| `pp_prevista`, `pp_presente`, `edu_previsti`, `edu_presenti` | polizia penitenziaria ed educatori | [verificata] |
| `celle_posti_previsti`, `celle_persone`, `celle_frase` | posti e persone per cella, estratti dal testo libero solo da frasi non ambigue | [calcolato] [VERIFICARE] |

Campi vuoti: il foglio non riporta il dato, o l'etichetta è diversa negli anni (i fogli 2017-2019 hanno
una struttura un po' diversa).

## eventi_critici.csv

Autolesionismo, suicidi, tentati suicidi, morti per altre cause, isolamento disciplinare, nell'anno
precedente la visita. Raccolti per una parte futura, da progettare a parte. **Il sito non li mostra.**

## abbinamento.csv, non_abbinati.csv

`codice_dap` della tabella di raccordo per ogni scheda, con il metodo (eccezione, nome identico, nome
simile) e la somiglianza. Le schede non abbinate vanno risolte a mano in
`data/reference/eccezioni_antigone.csv` (`scheda_id,codice_dap,nota`; `codice_dap = nessuno` per le
schede senza istituto corrispondente, per esempio istituti chiusi o non per adulti).
