"""Dalle copie complete delle schede trasparenza (json/*.json.gz) estrae le tabelle su personale, spazi,
corsi, lavoro e attività, una riga per istituto (o per voce) con la data della copia.

Scrive in data/raw/schede-trasparenza/attivita/:
  personale.csv          polizia penitenziaria, amministrativi, educatori (effettivi e previsti) + date di aggiornamento
  spazi.csv              spazi comuni e impianti, spazi d'incontro con i visitatori (una riga per istituto)
  corsi_formazione.csv   "Formazione lavoro › Corsi"
  corsi_istruzione.csv   "Attività scolastiche › Corsi istruzione"
  lavoro.csv             lavorazioni gestite da terzi e dall'amministrazione
  attivita.csv           attività teatrali, sportive, culturali, religiose

Legge per default la copia più recente; la serie storica è nella cronologia dei commit (come latest.csv).
Uso:  python scripts/estrai_attivita.py [--json data/raw/schede-trasparenza/json/AAAA-MM-GG.json.gz]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sys
from pathlib import Path

from common import DATA, norm_name

SCHEDE = DATA / "raw" / "schede-trasparenza"
OUT = SCHEDE / "attivita"


def colonna(s: str) -> str:
    """'polizia penitenziaria - effettivi' -> 'polizia_penitenziaria_effettivi'."""
    return re.sub(r"[^a-z0-9]+", "_", norm_name(s).lower()).strip("_")


def scrivi(nome: str, righe: list[dict], prime: list[str]) -> None:
    cols = list(prime)
    for r in righe:
        cols += [k for k in r if k not in cols]
    with open(OUT / nome, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
        w.writeheader()
        w.writerows(righe)
    print(f"{nome}: {len(righe)} righe")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path, help="copia da leggere (default: la più recente)")
    a = ap.parse_args()
    src = a.json or max((SCHEDE / "json").glob("*.json.gz"), default=None)
    if src is None:
        print("ERRORE: nessuna copia in json/: lanciare prima fetch_schede.py", file=sys.stderr)
        return 1
    dati = json.loads(gzip.decompress(src.read_bytes()))
    data = dati["scaricato"]
    OUT.mkdir(parents=True, exist_ok=True)

    personale, spazi, formazione, istruzione, lavoro, attivita = [], [], [], [], [], []
    for s in sorted(dati["schede"], key=lambda s: s["code"]):
        tab, semplici = s["tabelle"], s.get("semplici", {})
        base = {"data": data, "code": s["code"]}

        p = dict(base)
        for k, v in (tab.get("Personale") or [{}])[0].items():
            p[colonna(k)] = v
        for k, v in semplici.items():
            if k.startswith("Personale|"):
                p[colonna(k.split("|", 1)[1])] = v
        personale.append(p)

        sp = dict(base)
        for sezione, pref in [("Spazi comuni e impianti", ""), ("Spazi d'incontro con i visitatori", "incontro_")]:
            for k, v in (tab.get(sezione) or [{}])[0].items():
                sp[pref + colonna(k)] = v
        spazi.append(sp)

        formazione += [{**base, **{colonna(k): v for k, v in r.items()}} for r in tab.get("Corsi", [])]
        istruzione += [{**base, **{colonna(k): v for k, v in r.items()}} for r in tab.get("Corsi istruzione", [])]
        for sezione, gestione in [("Attività gestite da terzi", "terzi"),
                                  ("Lavorazioni gestite dall'amministrazione", "amministrazione")]:
            lavoro += [{**base, "gestione": gestione, **{colonna(k): v for k, v in r.items()}}
                       for r in tab.get(sezione, [])]
        for sezione in ["Attività teatrali", "Attività sportive", "Attività culturali", "Attività religiose"]:
            for r in tab.get(sezione, []):
                riga = {**base, "tipo": sezione.split()[1]}
                for k, v in r.items():
                    riga["organizzata_da" if k in ("organizzata da", "a cura di") else colonna(k)] = v
                attivita.append(riga)

    scrivi("personale.csv", personale, ["data", "code"])
    scrivi("spazi.csv", spazi, ["data", "code"])
    scrivi("corsi_formazione.csv", formazione, ["data", "code"])
    scrivi("corsi_istruzione.csv", istruzione, ["data", "code"])
    scrivi("lavoro.csv", lavoro, ["data", "code", "gestione"])
    scrivi("attivita.csv", attivita, ["data", "code", "tipo"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
