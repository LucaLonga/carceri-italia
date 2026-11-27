"""Data loader: visite dell'Osservatorio di Antigone per codice DAP, con tutti i campi fattuali estratti
(link ai fogli, riscaldamento, acqua calda, doccia, wc, costruzione, personale). Usato dalla scheda istituto.
Gli eventi critici non ci sono: restano in data/antigone/eventi_critici.csv e il sito non li mostra."""
import json
import sys

from _unione import leggi_visite_antigone, stampa_avvisi

avvisi = []
dati = leggi_visite_antigone(avvisi)
stampa_avvisi(avvisi, "antigone.json")
json.dump(dati, sys.stdout, ensure_ascii=False, separators=(",", ":"))
