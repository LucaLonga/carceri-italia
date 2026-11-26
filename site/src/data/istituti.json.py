"""Data loader: un unico JSON con tutti gli istituti (schede + Ministero + raccordo + Antigone).
Gli avvisi (file mancanti, istituti non collegati) finiscono nel campo `avvisi` e su stderr."""
import json
import sys

from _unione import stampa_avvisi, unisci

dati = unisci()
stampa_avvisi(dati["avvisi"], "istituti.json")
json.dump(dati, sys.stdout, ensure_ascii=False, separators=(",", ":"))
