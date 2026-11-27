"""Data loader: un unico JSON con tutti gli istituti (schede + Ministero + raccordo + Antigone).
Gli avvisi (file mancanti, istituti non collegati) finiscono nel campo `avvisi` e su stderr."""
import json
import sys

from _unione import stampa_avvisi, unisci

dati = unisci()
# Per stare sotto i 300 kB: delle visite di Antigone qui restano solo i campi che servono alla mappa e
# alla regola di affidabilità. Il dettaglio completo è in antigone.json (caricato solo dalla scheda).
CAMPI = ("data", "tre_mq", "presenti", "capienza", "celle")
for i in dati["istituti"]:
    va = i.get("visite_antigone")
    if va:
        i["visite_antigone"] = {"scheda_id": va["scheda_id"], "url_scheda": va["url_scheda"],
                                "visite": [{k: v[k] for k in CAMPI if v.get(k) is not None} for v in va["visite"]]}
stampa_avvisi(dati["avvisi"], "istituti.json")
json.dump(dati, sys.stdout, ensure_ascii=False, separators=(",", ":"))
