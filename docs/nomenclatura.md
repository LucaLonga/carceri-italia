# Verifica della nomenclatura (25.11.2026)

Domanda: la tabella di raccordo del 2024 (nomi del Ministero ↔ nomi di Antigone) funziona ancora?

## Esito

**Sì, con tre aggiornamenti.** Confronto tra il foglio MASTER del 2024 (189 istituti) e la tabella del
Ministero al 31.10.2026 (189 istituti), sulla coppia *nome normalizzato + tipo di istituto*:

- 186 istituti corrispondono senza modifiche;
- 3 hanno cambiato nome nella tabella del Ministero:

| id | Nome 2024 | Nome 2026 |
|---|---|---|
| 066 | VELLETRI | VELLETRI "A. CAROTENUTO" |
| 106 | CUNEO | CUNEO "IGNAZIO DE FLORIO" |
| 130 | ONANI "MAMONE" | ONANI' "MAMONE" |

- nessun istituto nuovo, nessuno sparito; i tipi (CC, CR, CRF…) coincidono tutti.
- I due istituti di Trani (CC maschile e CRF femminile) hanno lo stesso nome: si distinguono solo con il tipo.
  Per questo la chiave di confronto è sempre **nome + tipo**.

I nomi vecchi restano nella colonna `alias_ministero` di `data/reference/istituti.csv`, così i dati storici
si ricollegano allo stesso `id`.

## Una terza nomenclatura: le schede trasparenza del DAP

Le schede trasparenza (fonte dei posti non disponibili e delle stanze) usano **nomi propri e un codice
ufficiale DAP** (es. `BB17` = Como). Ora ogni riga della tabella di raccordo ha il suo `codice_dap`.

- 190 schede contro 189 righe del Ministero: **Milano San Vittore** ha due schede (maschile `BB01`,
  femminile `BB32`) che il Ministero somma in una riga. Colonna `codici_dap_sezioni`.
- Il codice DAP è l'identificativo più stabile disponibile: conviene usarlo come chiave principale
  da qui in avanti, tenendo l'`id` del 2024 per continuità.

## Problemi trovati nel dataset del 2024

1. **Numeri letti come orari** nel file Excel (10 istituti, i più grandi): vedi `data/raw/dv-24-01/README.md`.
2. **Coordinate**: confrontando le coordinate geocodificate nel 2024 con quelle pubblicate dal DAP,
   47 istituti differiscono di più di 2 km circa (colonna `coord_da_verificare`). Gli errori sono da
   entrambe le parti:
   - Cuneo nel 2024 è geocodificato ad Alba (errore nostro);
   - Alessandria San Michele ha un indirizzo testuale di Voghera (errore nostro, coordinate plausibili);
   - il DAP dà le stesse coordinate a più istituti dello stesso complesso (Rebibbia, Catania, Alessandria)
     e per Como indica un punto a nord della città (il carcere è al Bassone, Albate).
   Proposta: terza fonte indipendente da OpenStreetMap (`amenity=prison`) e verifica a mano dei casi in disaccordo.
3. **Sigle di provincia** vecchie (FO, PS, CA, MI per Monza): aggiunta la colonna `sigla_prov_attuale`.
