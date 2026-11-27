"""Abbina le schede dell'Osservatorio di Antigone agli istituti della tabella di raccordo (codice DAP).

Ordine dei tentativi (il primo che riesce vale):
1. eccezioni scritte a mano in data/reference/eccezioni_antigone.csv (scheda_id -> codice_dap, oppure
   "nessuno" per le schede senza istituto corrispondente, con una nota);
2. nome identico: titolo della scheda = colonna nome_antigone di istituti.csv (dopo norm_name);
3. nome simile nella stessa regione e con tipo compatibile: somiglianza ≥ 0,85 e distacco di
   almeno 0,10 dal secondo candidato (altrimenti è ambiguo e resta da correggere a mano).
Le schede non abbinate finiscono in data/antigone/non_abbinati.csv, da risolvere nelle eccezioni.

Uscite: data/antigone/abbinamento.csv, data/antigone/non_abbinati.csv
Uso: python abbina_antigone.py
"""
from __future__ import annotations

import csv
import re
import sys
from difflib import SequenceMatcher

from common import DATA, norm_name

REF = DATA / "reference" / "istituti.csv"
ECC = DATA / "reference" / "eccezioni_antigone.csv"
ANT = DATA / "antigone"

PAROLE_VUOTE = {"CASA", "CIRCONDARIALE", "DI", "DE", "DEL", "DELLA", "RECLUSIONE", "FEMMINILE", "ISTITUTO",
                "PENITENZIARIO", "PENALE", "CC", "CR", "NC", "N", "C", "NUOVO", "COMPLESSO", "A", "CUSTODIA",
                "ATTENUATA", "LAVORO", "CIRCONDARIALI", "SEZIONE", "E", "IL", "LA", "LE", "LO", "PER"}


def chiave(nome: str) -> str:
    s = norm_name(nome)
    s = re.sub(r"\([A-Z]{2}\)", " ", s)              # sigla di provincia tra parentesi
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return " ".join(w for w in s.split() if w not in PAROLE_VUOTE)


def tipo_da_nome(nome: str) -> set[str]:
    n = norm_name(nome)
    t = set()
    if "ICAM" in n or "MADRI" in n:
        t.add("ICAM")
    if "LAVORO" in n:
        t.add("CL")
    if "RECLUSIONE" in n:
        t.add("CRF" if "FEMMINIL" in n else "CR")
    if "CIRCONDARIALE" in n:
        t.add("CCF" if "FEMMINIL" in n else "CC")
    if "PENALE" in n or "ISTITUTI DI PENA" in n:
        t.add("IP")
    return t


def regione_slug(r: str) -> str:
    s = norm_name(r).lower().replace("'", " ")
    s = re.sub(r"[^a-z]+", "-", s).strip("-")
    return {"valle-d-aosta": "val-d-aosta", "emilia-romagna": "emilia-romagna"}.get(s, s)


def main() -> None:
    ref = list(csv.DictReader(REF.open(encoding="utf-8")))
    schede = list(csv.DictReader((ANT / "schede.csv").open(encoding="utf-8")))
    ecc = {}
    if ECC.exists():
        ecc = {r["scheda_id"]: r for r in csv.DictReader(ECC.open(encoding="utf-8"))}
    per_nome = {}
    for r in ref:
        per_nome.setdefault(norm_name(r["nome_antigone"]), []).append(r)

    abbinate, non = [], []
    for s in schede:
        sid, nome = s["scheda_id"], s["nome_antigone"]
        riga = {"scheda_id": sid, "nome_antigone": nome, "regione_slug": s["regione_slug"], "url": s["url"]}
        if sid in ecc:
            cod = ecc[sid]["codice_dap"].strip()
            abbinate.append({**riga, "codice_dap": "" if cod == "nessuno" else cod, "metodo": "eccezione", "somiglianza": "", "nota": ecc[sid].get("nota", "")})
            continue
        esatti = per_nome.get(norm_name(nome), [])
        if len(esatti) == 1:
            abbinate.append({**riga, "codice_dap": esatti[0]["codice_dap"], "metodo": "nome identico", "somiglianza": "1.00", "nota": ""})
            continue
        tipi = tipo_da_nome(nome)
        cand = [r for r in ref if regione_slug(r["regione"]) == s["regione_slug"] and (not tipi or r["tipo"] in tipi or
                                                                                        (r["tipo"] in {"CC", "CR"} and tipi & {"CC", "CR"}))]
        k = chiave(nome)
        punti = sorted(((max(SequenceMatcher(None, k, chiave(r[c])).ratio() for c in ("nome_antigone", "nome_ministero", "nome_scheda_dap")), r)
                        for r in cand), key=lambda x: -x[0])
        if punti and punti[0][0] >= 0.85 and (len(punti) == 1 or punti[0][0] - punti[1][0] >= 0.10):
            abbinate.append({**riga, "codice_dap": punti[0][1]["codice_dap"], "metodo": "nome simile", "somiglianza": f"{punti[0][0]:.2f}", "nota": ""})
        else:
            prop = "; ".join(f"{r['codice_dap']} {r['nome_ministero']} ({p:.2f})" for p, r in punti[:3])
            non.append({**riga, "candidati": prop})

    cols = ["scheda_id", "codice_dap", "metodo", "somiglianza", "nome_antigone", "regione_slug", "url", "nota"]
    with (ANT / "abbinamento.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(sorted(abbinate, key=lambda r: int(r["scheda_id"])))
    with (ANT / "non_abbinati.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["scheda_id", "nome_antigone", "regione_slug", "url", "candidati"], lineterminator="\n")
        w.writeheader()
        w.writerows(non)
    doppi = {}
    for r in abbinate:
        if r["codice_dap"]:
            doppi.setdefault(r["codice_dap"], []).append(r["scheda_id"])
    doppi = {k: v for k, v in doppi.items() if len(v) > 1}
    coperti = {r["codice_dap"] for r in abbinate if r["codice_dap"]}
    print(f"schede {len(schede)}: abbinate {sum(1 for r in abbinate if r['codice_dap'])}, "
          f"senza istituto (eccezioni) {sum(1 for r in abbinate if not r['codice_dap'])}, non abbinate {len(non)}; "
          f"istituti coperti {len(coperti)} su {len(ref)} ({100 * len(coperti) / len(ref):.1f}%)", file=sys.stderr)
    if doppi:
        print(f"codici con più schede: {doppi}", file=sys.stderr)


if __name__ == "__main__":
    main()
