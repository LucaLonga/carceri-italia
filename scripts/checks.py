"""Controlli dopo ogni raccolta. Scrive data/checks/ultimo.md ed esce con errore se qualcosa non torna.

- tabella mensile del Ministero: somma delle righe = riga Totale (lo fa già fetch_ministero, qui si rilegge)
- nomenclatura: ogni istituto del Ministero ha un id in data/reference/istituti.csv (anche tramite alias)
- schede trasparenza: ogni codice DAP è nella tabella di raccordo; nessun codice nuovo o sparito
- coerenza interna delle schede: posti non disponibili <= posti regolamentari, stanze non disp. <= stanze
- struttura delle schede: sezioni o campi nuovi o spariti tra le ultime due copie di struttura/ (avviso, non errore:
  è un segnale da guardare, non un guasto)
"""
from __future__ import annotations

import csv
import json
import sys

from common import DATA, norm_name, today

REF = DATA / "reference" / "istituti.csv"


def _voci(schede: dict) -> dict[str, set]:
    """voce "gruppo › sezione › campo" -> codici delle schede che la hanno."""
    voci: dict[str, set] = {}
    for code, sezioni in schede.items():
        for s in sezioni:
            for campo in s["campi"] or [""]:
                voci.setdefault(f"{s['gruppo']} › {s['sezione']} › {campo}".rstrip(" ›"), set()).add(code)
    return voci


def confronta_strutture() -> list[str]:
    files = sorted((DATA / "raw" / "schede-trasparenza" / "struttura").glob("*.json"))
    if len(files) < 2:
        return ["\n## Struttura delle schede\n", f"- copie salvate: {len(files)}; niente da confrontare"]
    prima, dopo = (json.loads(f.read_text(encoding="utf-8"))["schede"] for f in files[-2:])
    vp, vd = _voci(prima), _voci(dopo)
    righe = ["\n## Struttura delle schede\n", f"- confronto {files[-2].stem} → {files[-1].stem}"]
    nuove, sparite = sorted(set(vd) - set(vp)), sorted(set(vp) - set(vd))
    righe.append(f"- voci nuove in tutte le schede: {len(nuove)}; voci sparite: {len(sparite)}")
    righe += [f"  - AVVISO nuova: {v} ({len(vd[v])} schede)" for v in nuove]
    righe += [f"  - AVVISO sparita: {v} (era in {len(vp[v])} schede)" for v in sparite]
    cambiate = sorted(v for v in set(vp) & set(vd) if vp[v] != vd[v])
    righe.append(f"- voci presenti in un numero diverso di schede: {len(cambiate)}")
    righe += [f"  - {v}: {len(vp[v])} → {len(vd[v])}" for v in cambiate[:30]]
    return righe


def main() -> int:
    ref = list(csv.DictReader(REF.open(encoding="utf-8")))
    chiavi = {}
    for r in ref:
        for nome in [r["nome_ministero"], *filter(None, r["alias_ministero"].split(";"))]:
            chiavi[(norm_name(nome), r["tipo"])] = r["id"]
    codici = {r["codice_dap"] for r in ref} | {c for r in ref for c in r["codici_dap_sezioni"].split(";") if c}

    report, errori = [f"# Controlli del {today()}\n"], 0

    indice_p = DATA / "raw" / "ministero" / "indice.json"
    if indice_p.exists():
        indice = json.loads(indice_p.read_text())
        ultimo = max(indice)
        info = indice[ultimo]
        report.append(f"## Ministero, tabella al {ultimo}\n")
        report.append(f"- righe: {info.get('righe')}; errori sui totali: {info.get('errori') or 'nessuno'}")
        errori += bool(info.get("errori"))
        csv_p = DATA / "raw" / "ministero" / f"{ultimo}_capienze-per-istituto.csv"
        if csv_p.exists():
            mancanti = [r["istituto"] for r in csv.DictReader(csv_p.open(encoding="utf-8"))
                        if (norm_name(r["istituto"]), r["tipo"]) not in chiavi]
            report.append(f"- istituti senza corrispondenza nella tabella di raccordo: {len(mancanti)}")
            report += [f"  - {m}" for m in mancanti]
            errori += bool(mancanti)

    sch_p = DATA / "raw" / "schede-trasparenza" / "latest.csv"
    if sch_p.exists():
        sch = list(csv.DictReader(sch_p.open(encoding="utf-8"), delimiter=";"))
        nuovi = sorted({r["code"] for r in sch} - codici)
        spariti = sorted(codici - {r["code"] for r in sch})
        report.append("\n## Schede trasparenza\n")
        report.append(f"- istituti: {len(sch)}; codici nuovi: {nuovi or 'nessuno'}; codici spariti: {spariti or 'nessuno'}")
        errori += bool(nuovi or spariti)
        incoerenti = []
        for r in sch:
            def n(k):
                return int(r[k]) if r[k] not in ("", None) else 0
            if n("posti_non_disp") > n("posti_reg") or n("stanze_non_disp") > n("stanze"):
                incoerenti.append(r["code"] + " " + r["titolo"])
        report.append(f"- righe incoerenti (non disponibili > totale): {incoerenti or 'nessuna'}")
        tot = {k: sum(int(r[k] or 0) for r in sch) for k in ["posti_reg", "posti_non_disp", "presenti", "stanze"]}
        report.append(f"- totali: {tot}")

    report += confronta_strutture()

    out = DATA / "checks"
    out.mkdir(parents=True, exist_ok=True)
    (out / "ultimo.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main())
