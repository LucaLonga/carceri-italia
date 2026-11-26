"""Data loader: la stessa unione di istituti.json in forma piatta, per lo scaricamento."""
import csv
import sys

from _unione import NUM_SCHEDE, stampa_avvisi, unisci

dati = unisci()
stampa_avvisi(dati["avvisi"], "istituti.csv")
CALC = ["posti_disp", "stanze_disp", "superficie_lorda", "m2_lordi_persona", "persone_stanza", "affollamento_reale"]
cols = (["codice_dap", "codici_dap_sezioni", "id", "nome", "nome_ministero", "nome_antigone", "tipo", "regione",
         "provincia", "lat_dap", "lon_dap", "coord_da_verificare"]
        + NUM_SCHEDE + ["agg_capienza", "agg_spazi"] + CALC + ["casi",
        "min_data", "min_capienza_regolamentare", "min_presenti", "min_donne", "min_stranieri"])
w = csv.writer(sys.stdout, lineterminator="\n")
w.writerow(cols)
for i in dati["istituti"]:
    s = i["scheda"] or {}
    m = i["ministero"] or {}
    c = i["calc"]
    w.writerow([i["codice"], ";".join(i["codici_sezioni"]), i["id"], i["nome"], i["nomi"]["ministero"],
                i["nomi"]["antigone"], i["tipo"], i["regione"], i["provincia"], i["lat"], i["lon"],
                "si" if i["coord_da_verificare"] else ""]
               + [s.get(k) for k in NUM_SCHEDE] + [s.get("agg_capienza"), s.get("agg_spazi")]
               + [c[k] for k in CALC] + [";".join(c["casi"]),
               m.get("data"), m.get("capienza_regolamentare"), m.get("presenti"), m.get("donne"), m.get("stranieri")])
