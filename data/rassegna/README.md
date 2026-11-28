# data/rassegna

Rassegna dei **documenti ufficiali**: circolari, risposte alle interrogazioni, relazioni, audizioni, norme,
sentenze, rapporti di autorità pubbliche. Una riga per documento.

**Gli articoli di stampa non sono qui**, nemmeno come riga anonima: stanno interamente nel repository
privato del progetto fino alla pubblicazione dell'inchiesta (scelta del 2026-11-28, per i diritti delle
testate e per i nomi delle persone che gli articoli contengono). Lo stesso vale per i rapporti non
ufficiali (associazioni, università).

| Colonna | Contenuto |
|---|---|
| `id` | `doc-NNNN`, stabile |
| `data` | data del documento (AAAA-MM-GG, o AAAA-MM, o AAAA se non è certa) |
| `ente_o_testata` | chi ha prodotto il documento |
| `tipo` | circolare, risposta interrogazione, relazione, audizione, norma, sentenza, rapporto, comunicato |
| `titolo` | come scritto nel documento o nell'elenco ufficiale che lo pubblica (verificato il 2026-11-28) |
| `url` | indirizzo ufficiale |
| `wayback`, `archivebox`, `file_privato` | copie: si compilano dopo l'archiviazione (`archive/manifest.csv` per Wayback e copia locale) |
| `codici_dap` | istituti citati (`;`) |
| `temi` | temi del documento; quelli marcati `[proposta]` sono una proposta da confermare |
| `affermazioni` | che cosa il documento sostiene con numeri, una per riga |
| `verifica_dati` | dove e come si controlla con i nostri dati, oppure "non verificabile" |
| `stato_giudiziario` | per sentenze e atti giudiziari |
| `nota` | |

`temi`, `affermazioni`, `verifica_dati` sono `[DA COMPILARE: Luca]`: si scrivono leggendo il documento.
Gli script compilano solo i campi tecnici.

I documenti nuovi degli elenchi ufficiali (`archive/elenchi_ufficiali.yml`: risposte alle interrogazioni,
circolari DAP, Commissario, Garante) entrano da soli ogni giorno con `scripts/documenti_ufficiali.py`
(workflow `documenti`), se sono pertinenti: almeno 3 parole chiave sul carcere nel testo. Ogni documento visto, pertinente o no, è in `archive/documenti_visti.csv`. La prima lettura
del 2026-11-28 ha preso come base gli elenchi e analizzato i 12 documenti più recenti di ciascuno.
Sono documenti dello Stato (art. 5 L. 633/1941): si conservano interi negli allegati della release
mensile `documenti-AAAA-MM` (`release_url` in `archive/manifest.csv`), con il testo in `archive/text/`.

Ogni URL è anche in `archive/extra_urls.txt` (copia locale e Wayback con `scripts/archive_sources.py`) e
ArchiveBox lo legge da qui. I documenti nuovi trovati dalla sorveglianza arrivano come candidati nel
repository privato (`rassegna/ufficiali_candidati.csv`) e si aggiungono qui a mano, dopo la lettura.
