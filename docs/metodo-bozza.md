# Metodo: bozza per lo spazio per persona

Stato: bozza del 25.11.2026, da discutere. Ogni valore calcolato è etichettato [calcolato]; ogni
assunzione [ipotesi].

## La norma di riferimento (prima era [VERIFICARE])

La nota (*) della tabella mensile del Ministero dichiara il criterio della capienza regolamentare:

> 9 m² per detenuto singolo + 5 m² per ogni altro, lo stesso criterio dell'abitabilità delle abitazioni
> (D.M. Sanità 5 luglio 1975 [VERIFICARE il rimando]), più favorevole dei 6 m² + 4 del CPT, servizi sanitari esclusi.

Quindi i posti regolamentari sono già una misura di superficie, convertita in persone.

## Che cosa danno le schede trasparenza (novità rispetto al 2024)

Per ogni istituto: posti regolamentari, **posti non disponibili**, presenti, **numero di stanze** e
**stanze non disponibili**, dotazioni delle stanze (doccia, bidet, wc con porta, luce autonoma, prese).

## Stima proposta

```
posti_disp   = posti_reg − posti_non_disp
stanze_disp  = stanze − stanze_non_disp
superficie   ≈ 9 · stanze_disp + 5 · (posti_disp − stanze_disp)        [ipotesi: ogni stanza misura
                                                                        esattamente la sua capienza]
m²_persona   = superficie / presenti                                   [calcolato]
persone_stanza = presenti / stanze_disp                                [calcolato, nessuna ipotesi]
```

Prima prova sui dati del 24.11.2026 (190 schede):

- posti disponibili 46.480, presenti 66.171: affollamento sui posti disponibili 142%;
- superficie stimata 347.728 m², cioè **5,25 m² lordi per persona** a livello nazionale;
- valori più bassi: Foggia 3,25 m², Grosseto 3,36, Milano San Vittore 3,42, Trieste 3,47,
  Brescia Canton Mombello 3,56; 22 istituti sotto i 4 m² lordi.

## Il problema: lordo contro calpestabile

**Nessun istituto risulta sotto i 3 m² con questa stima**, perché 9 + 5 m² sono superfici **lorde**
della stanza. La soglia Torreggiani, secondo la giurisprudenza italiana (Cassazione, Sezioni Unite,
2021 [VERIFICARE estremi]), si misura sullo spazio **calpestabile**, togliendo gli arredi fissi
(letti compresi i letti a castello, armadi fissi).

Le visite di Antigone dicono che nell'ultimo anno, in 38 istituti su 69 visitati, non tutte le celle
garantivano 3 m² calpestabili (`data/manual/antigone/osservatorio_2026-11-25.md`).

Proposta per la banda di incertezza:
- **limite alto** [calcolato]: la stima lorda qui sopra;
- **limite basso** [ipotesi]: lorda meno una superficie di arredo per persona (letto, armadietto, sgabello),
  da fissare con una fonte (CPT, perizie, sentenze) [DA FARE];
- **calibrazione**: per gli istituti visitati da Antigone, confrontare la banda con la risposta
  "3 m² calpestabili SI/NO".

Conseguenza per la forma: la mappa non può dire "sopra/sotto 3 m²" come se fosse un dato. Può mostrare
la banda e dove la banda attraversa la soglia.

## Altre misure senza ipotesi

- persone per stanza (presenti / stanze disponibili): Vallo della Lucania 6,7, Trieste 5,1, Matera 4,8,
  Napoli Poggioreale 4,8;
- quota di stanze con doccia (14.708 su 31.898 stanze, il 46%);
- posti non disponibili: 4.809 (9,4% della capienza), con casi estremi (Arezzo 86 su 108, Nuoro 104 su 378,
  Pozzuoli 98 su 98, chiuso).
