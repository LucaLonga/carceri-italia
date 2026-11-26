"""Data loader: serie nazionale per il passo 7 del racconto e per la pagina dati.

- presenti al 30/6 e 31/12 dal 1991 (DAP, data/storico/presenti_semestrali.csv) [verificata]
- capienza regolamentare e presenti mensili dal 2019 (DAP, data/storico/nazionale_mensile.csv) [verificata]
- copertura anno per anno e buchi (data/storico/copertura.csv)
- eventi scritti a mano con fonte ed etichetta (data/manual/eventi.yml)
Usa PyYAML se c'è; altrimenti un lettore minimo per il formato semplice di eventi.yml
(un elenco di voci con valori su una riga), così il loader resta solo libreria standard."""
import csv
import json
import re
import sys

try:
    import yaml
except ImportError:  # lettore minimo
    yaml = None


def leggi_eventi_semplice(testo):
    voci, voce = [], None
    for riga in testo.splitlines():
        r = re.sub(r"\s+#.*$", "", riga).rstrip()
        if not r.strip() or r.lstrip().startswith("#") or r.strip() == "eventi:":
            continue
        m = re.match(r"^\s*(-\s+)?([a-z_]+):\s*(.*)$", r)
        if not m:
            continue
        if m.group(1):
            voce = {}
            voci.append(voce)
        v = m.group(3).strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            v = v[1:-1]
        if voce is not None:
            voce[m.group(2)] = v or None
    return {"eventi": voci}

from _unione import DATA, rel

avvisi = []


def leggi(p):
    if not p.exists():
        avvisi.append(f"manca {rel(p)}")
        return []
    return list(csv.DictReader(p.open(encoding="utf-8")))


def n(v):
    return int(v) if v not in (None, "") else None


sem = [{"data": r["data"], "presenti": n(r["presenti"]), "donne": n(r["donne"]), "stranieri": n(r["stranieri"])}
       for r in leggi(DATA / "storico" / "presenti_semestrali.csv")]
mens = [{"data": r["data"], "capienza": n(r["capienza_regolamentare"]), "presenti": n(r["presenti"]), "istituti": n(r["istituti"])}
        for r in leggi(DATA / "storico" / "nazionale_mensile.csv")]
cop = leggi(DATA / "storico" / "copertura.csv")
pe = DATA / "manual" / "eventi.yml"
eventi = []
if pe.exists():
    testo = pe.read_text(encoding="utf-8")
    for e in (yaml.safe_load(testo) if yaml else leggi_eventi_semplice(testo)).get("eventi", []):
        eventi.append({k: (str(v) if v is not None else None) for k, v in e.items()})
else:
    avvisi.append(f"manca {rel(pe)}")
for a in avvisi:
    print("[storico.json]", a, file=sys.stderr)
json.dump({"semestrali": sem, "mensili": mens, "copertura": cop, "eventi": eventi, "avvisi": avvisi}, sys.stdout, ensure_ascii=False, separators=(",", ":"))
