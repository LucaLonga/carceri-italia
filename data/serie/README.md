# data/serie

Serie statistiche del Ministero della Giustizia (DAP, Sezione statistica) oltre le capienze, scelte il
2026-11-28 (proposta e livello di ogni serie in `data/storico/inventario_serie.csv`). Raccolta:
`scripts/fetch_serie.py` (workflow `storico`, a mano, dopo l'aggiornamento dell'inventario). Grezzo
compresso in `data/raw/serie/<serie>/`. Licenza: note legali di giustizia.it (riuso non commerciale con
citazione della fonte). Etichetta: [verificata] i valori, [VERIFICARE] la lettura delle intestazioni.

## Formato

Una riga per cella (formato lungo), perché le intestazioni cambiano da un anno all'altro:

| Colonna | Contenuto |
|---|---|
| `voce_data` | data della voce nell'elenco del Ministero (vuota per le serie "Anno …" e "Anni …") |
| `voce_id` | identificativo della voce: titolo, URL ed esito in `indice.json` |
| `tabella` | numero della tabella nella pagina |
| `riga_n`, `riga`, `riga_2` | posizione della riga, prima cella (regione, anno, classe) e seconda cella di testo (istituto) |
| `colonna` | intestazione: le righe d'intestazione unite con " \| " (es. "Suicidi \| valore assoluto") |
| `valore`, `valore_num` | come scritto nella pagina, e come numero |

Una serie che supera 1 MB sta in una cartella con un file per anno (`<serie>/<anno>.csv`).

## Serie

| File | Contenuto | Livello | Dal | Domande §3 |
|---|---|---|---|---|
| `eventi_critici.csv` | presenza media, detenuti in custodia nell'anno, suicidi e decessi per cause naturali (valore assoluto e ogni 10.000) | nazionale, annuale | 1992 | C9 C11 |
| `detenute_madri.csv`, `detenute_madri_istituto.csv` | madri presenti e figli al seguito, italiane e straniere; il secondo con `codice_dap` (692 righe, tutte abbinate, 38 istituti) | **istituto**, mensile | 2016 | D13 |
| `pena_residua.csv`, `pena_residua_anni.csv` | condannati per classi di pena residua | regione semestrale; nazionale annuale | 2019; 2005 | D13 E15 |
| `ingressi_liberta.csv` | ingressi dalla libertà, uomini e donne | regione, semestrale e annuale | 2019 | C9 B7 |
| `lavoranti.csv`, `lavoranti_datore.csv`, `lavoranti_serie_storica.csv` | lavoranti alle dipendenze e non; per datore; serie dal 1991 | regione semestrale; nazionale | 2019; 1991 | E14 |
| `corsi_professionali.csv`, `percorsi_istruzione.csv` | corsi professionali attivati e terminati; corsi, iscritti e promossi | regione; nazionale | 2019 | E14 |
| `permessi_premio.csv` | permessi premio concessi | regione | 2019 | E15 |
| `usciti_legge_199.csv` | usciti per esecuzione domiciliare delle pene brevi (L. 199/2010) | regione, mensile | 2019 | E15 |
| `classi_eta.csv`, `classi_eta_anni.csv` | classi di età | regione semestrale; nazionale annuale | 2019; 2005 | D13 |
| `posizione_giuridica_regione/<anno>.csv`, `posizione_giuridica_anni.csv` | in attesa di primo giudizio, condannati non definitivi (appellanti, ricorrenti, misti), definitivi, internati | regione mensile; nazionale annuale | 2019; 2008 | D13 |
| `madri_asili_nido.csv` | asili nido, ICAM, madri, bambini, detenute in gravidanza | regione | 2019 | D13 |

**Eventi critici**: la serie pubblicata ha solo suicidi e decessi per cause naturali, a livello nazionale.
Autolesionismi, tentati suicidi, aggressioni e il dettaglio per istituto non ci sono [DA CERCARE: Garante,
Antigone, risposte alle interrogazioni].
