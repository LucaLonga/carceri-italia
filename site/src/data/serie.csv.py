"""Data loader: serie storica lunga per istituto, formato lungo (una riga per data, fonte e istituto).

fonte = ministero  -> tabelle mensili (posti regolamentari, presenti; niente posti non disponibili)
fonte = schede     -> istantanee datate delle schede trasparenza (AAAA-MM-GG_schede.csv)
La serie cresce da sola: ogni nuovo file datato aggiunge una data."""
import csv
import sys

from _unione import (SCHEDE_DIR, codici, file_datati, leggi_ministero, leggi_riferimento, leggi_schede,
                     metrica, stampa_avvisi, somma_schede)

avvisi = []
ref = leggi_riferimento(avvisi)
mesi, _ = leggi_ministero(ref, avvisi)
w = csv.writer(sys.stdout, lineterminator="\n")
w.writerow(["data", "fonte", "codice_dap", "posti_reg", "posti_non_disp", "posti_disp", "presenti"])
for data in sorted(mesi):
    for cod, m in sorted(mesi[data].items()):
        w.writerow([data, "ministero", cod, m["capienza_regolamentare"], "", "", m["presenti"]])
istantanee = file_datati(SCHEDE_DIR, "_schede.csv")
if not istantanee:
    avvisi.append("nessuna istantanea datata delle schede: la serie usa solo il Ministero")
for data, p in istantanee:
    schede = leggi_schede(p, avvisi)
    for r in ref:
        righe = [schede[c] for c in codici(r) if c in schede]
        if len(righe) != len(codici(r)):
            avvisi.append(f"schede {data}: manca {r['codice_dap']}")
            continue
        s = somma_schede(righe)
        c = metrica(s)
        w.writerow([data, "schede", r["codice_dap"], s["posti_reg"], s["posti_non_disp"], c["posti_disp"], s["presenti"]])
stampa_avvisi(avvisi, "serie.csv")
