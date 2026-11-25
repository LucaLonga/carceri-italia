# Ricognizione delle fonti (25.11.2026)

Domanda: oltre a Ministero e Antigone, chi pubblica dati sul carcere in Italia? Dove si completano,
dove si ripetono, dove si contraddicono? Il registro operativo delle fonti è `sources.yml`.

## Quadro

Quasi tutti i numeri sul carcere in Italia hanno **un'unica origine: il DAP** (Dipartimento
dell'amministrazione penitenziaria). ISTAT, Garante, Antigone e Consiglio d'Europa li riprendono,
li tagliano in modo diverso o li datano in modo diverso. Le uniche fonti **indipendenti** sono le
visite: Osservatorio di Antigone, Garanti (nazionale e territoriali), CPT del Consiglio d'Europa.

| Fonte | Ruolo nel progetto | Granularità | Frequenza | Origine dei dati |
|---|---|---|---|---|
| Ministero, tabella "capienze per istituto" | **serie storica ufficiale** | istituto | mensile, archivio dal 2018 circa | DAP |
| DAP, schede trasparenza | **fonte principale nuova**: posti non disponibili, stanze, dotazioni, personale | istituto (190 schede) | giornaliera (capienza), variabile (spazi) | DAP |
| Ministero, detenuti per regione di residenza / di nascita | parte del "vuoto" sulla provenienza | regione | semestrale, serie 2005-2025 | DAP |
| Antigone, Osservatorio (visite) | **verifica sul campo** della soglia 3 m² calpestabili | istituto visitato (69/anno) | continua | indipendente |
| Antigone, rapporto annuale | contesto, numeri nazionali | nazionale | annuale | DAP + analisi |
| Garante nazionale, report analitici | controllo incrociato, decessi | nazionale/istituto [VERIFICARE] | irregolare | DAP |
| ISTAT (Annuario, IstatData) | serie lunghe, definizioni | nazionale/regionale | annuale | DAP |
| Consiglio d'Europa, SPACE I | confronto europeo | paese | annuale | DAP |
| CPT, rapporti di visita sull'Italia | misure delle celle visitate, standard 6+4 m² | istituto visitato | ogni 4-5 anni | indipendente [DA CERCARE] |
| Garanti regionali (es. Lazio) | dati locali, posti disponibili | istituto | annuale | DAP + visite |
| OpenStreetMap `amenity=prison` | terza fonte per le coordinate | punto/poligono | continua | indipendente [DA PROVARE] |

## Dove i numeri non coincidono (e perché)

1. **Posti regolamentari vs posti disponibili.** ISTAT e SPACE I calcolano l'affollamento sui posti
   regolamentari (ISTAT: 109,5 per 100 posti a fine 2022). Antigone e il Garante sui posti disponibili
   (Antigone: 139,1% a fine aprile 2026). Le schede di oggi danno 142%. Non è una contraddizione nei
   dati, ma una scelta di denominatore: va dichiarata ogni volta.
2. **Date diverse.** Ministero al 31.10.2026: 51.283 posti regolamentari, 66.285 presenti. Schede al
   24.11.2026: 51.289 e 66.171. Garante al 7.4.2026: 46.331 posti disponibili; Antigone al 30.4.2026:
   46.318; schede al 24.11.2026: 46.480. Sono coerenti tra loro; vanno sempre datati.
3. **Stesso istituto, capienza diversa.** Ravenna: 49 posti nella tabella mensile di ottobre, 55 nella
   scheda di novembre. Le capienze cambiano (lavori, nuovi reparti): la serie storica lo mostra.
4. **Aggregati di terzi incompleti.** Il report Data Studio di Antigone al 25.11.2026 somma 50.170 posti
   regolamentari perché il Piemonte risulta "null" (collegamento ai dati interrotto). Prendere sempre
   il dato dalla fonte DAP, non dalle rielaborazioni.
5. **Unità diverse.** Il Ministero dà una riga per Milano San Vittore; le schede due (maschile e femminile).
6. **Decessi e suicidi.** Ministero, Garante e il dossier di Ristretti Orizzonti non coincidono;
   Antigone li incrocia. Fuori dal perimetro di questo progetto, ma da citare se si parla di eventi critici.

## Che cosa resta nel vuoto

- **Superficie reale delle celle**: nessuna fonte pubblica la pubblica per istituto. Le schede danno il
  numero di stanze, non i metri quadri. La relazione al Parlamento del 2014 parlava di un progetto per
  "rilevare gli spazi detentivi con l'esatta metratura delle camere" [VERIFICARE se esiste un esito].
  Possibile richiesta di accesso civico generalizzato (FOIA) al DAP.
- **Motivi dei posti non disponibili**: non spiegati nelle schede.
- **Provenienza dei detenuti per istituto**: non pubblica; solo per regione di residenza e di nascita.

## Fonti da aggiungere più avanti

- Piano di edilizia penitenziaria (luglio 2025) e Commissario straordinario: posti in costruzione per
  istituto, per la parte "come cambia nel tempo" [DA CERCARE].
- Relazione annuale del Ministero sull'amministrazione della giustizia: obiettivo della "soglia
  fisiologica del 5%" di posti non disponibili.
- Corte EDU, *Torreggiani c. Italia* (2013) e *Sulejmanovic c. Italia* (2009), su HUDOC: per la pagina di metodo.
