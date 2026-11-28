"""Riconosce in un testo (articolo, comunicato, documento) gli istituti penitenziari citati e dice se il
testo parla di carcere.

- istituti: nomi da data/reference/nomi_nel_testo.csv (città, luoghi e soprannomi: Marassi, Poggioreale,
  San Vittore...). Il confronto rispetta le maiuscole ("Opera" sì, "opera" no). I nomi con
  richiede_contesto = si (tutte le città e i nomi comuni: Opera, Augusta, Trani, Isili, Fermo, Noto...)
  valgono solo se vicino c'è una parola del carcere ("carcere di", "casa circondariale", "detenuti"...).
  Una città con più istituti (Roma, Napoli, Milano...) o "Rebibbia" danno un risultato ambiguo:
  i codici sono tutti quelli possibili e non entrano tra i codici certi.
- pertinenza: il testo contiene almeno una delle PAROLE_CHIAVE.

Uso da riga di comando, per provare:  python scripts/istituti_nel_testo.py "testo da analizzare"
"""
from __future__ import annotations

import csv
import json
import re
import sys
from functools import lru_cache
from pathlib import Path

NOMI = Path(__file__).resolve().parents[1] / "data" / "reference" / "nomi_nel_testo.csv"

# parole del carcere che rendono valido un nome di città o un nome comune, se compaiono vicino
CONTESTO = re.compile(
    r"\b(carcer[ei]|carcerari[oae]|penitenziari[oae]?|casa circondariale|case circondariali|casa di reclusione|"
    r"casa di lavoro|istitut[oi] (?:penitenziari[oi]|di pena)|detenut[oiae]|reclus[oiae]|celle?|"
    r"polizia penitenziaria|agenti penitenziari|garante dei detenuti|direttore del carcere|"
    r"C\.?C\.?|C\.?R\.?|ICAM|evas[oiae]|evasione|sezione)\b",
    re.IGNORECASE,
)
PRIMA, DOPO = 80, 40  # caratteri in cui cercare il contesto, prima e dopo il nome

PAROLE_CHIAVE = [
    "carcere", "carceri", "carcerari", "penitenziari", "casa circondariale", "case circondariali",
    "casa di reclusione", "detenuti", "detenute", "detenuto", "detenzione", "polizia penitenziaria",
    "sovraffollamento", "suicidio in carcere", "suicidi in carcere", "DAP", "amministrazione penitenziaria",
    "Garante dei detenuti", "Garante nazionale dei diritti delle persone private della libertà",
    "edilizia penitenziaria", "REMS", "41 bis", "41-bis", "Torreggiani", "misure alternative",
]
_CHIAVE = re.compile(r"\b(" + "|".join(re.escape(p) for p in PAROLE_CHIAVE) + r")\b")
_CHIAVE_I = re.compile(r"\b(" + "|".join(re.escape(p) for p in PAROLE_CHIAVE if p != "DAP") + r")\b", re.IGNORECASE)


@lru_cache(maxsize=1)
def _nomi() -> tuple[list[dict], re.Pattern]:
    with NOMI.open(encoding="utf-8") as f:
        righe = list(csv.DictReader(f))
    for r in righe:
        r["codici"] = [c for c in r["codici_dap"].split(";") if c]
    righe.sort(key=lambda r: -len(r["testo"]))  # il nome più lungo vince: "Massa Marittima" prima di "Massa"
    alternative = "|".join(re.escape(r["testo"]) for r in righe)
    return righe, re.compile(r"(?<![\w'’])(" + alternative + r")(?![\w])")


def riconosci(testo: str) -> list[dict]:
    """Elenco dei nomi trovati: testo, posizione, codici DAP, certezza (alta | contesto | ambiguo)."""
    righe, pat = _nomi()
    per_testo = {r["testo"]: r for r in righe}
    trovati = []
    for m in pat.finditer(testo):
        r = per_testo[m.group(1)]
        if r["richiede_contesto"] == "si":
            vicino = testo[max(0, m.start() - PRIMA): m.start()] + " " + testo[m.end(): m.end() + DOPO]
            if not CONTESTO.search(vicino):
                continue
            certezza = "contesto"
        else:
            certezza = "alta"
        if len(r["codici"]) > 1:
            certezza = "ambiguo"
        trovati.append({"testo": m.group(1), "inizio": m.start(), "codici_dap": r["codici"], "certezza": certezza})
    return trovati


def codici_dap(testo: str) -> tuple[list[str], list[str]]:
    """(codici certi, codici possibili dai nomi ambigui), ordinati e senza ripetizioni."""
    certi, ambigui = set(), set()
    for t in riconosci(testo):
        (ambigui if t["certezza"] == "ambiguo" else certi).update(t["codici_dap"])
    return sorted(certi), sorted(ambigui - certi)


def pertinente(testo: str) -> bool:
    """Vero se il testo contiene almeno una parola chiave sul carcere ("DAP" solo in maiuscolo)."""
    return bool(_CHIAVE.search(testo) or _CHIAVE_I.search(testo))


if __name__ == "__main__":
    t = " ".join(sys.argv[1:]) or sys.stdin.read()
    certi, ambigui = codici_dap(t)
    print(json.dumps({"pertinente": pertinente(t), "codici_dap": certi, "codici_dap_ambigui": ambigui,
                      "trovati": riconosci(t)}, ensure_ascii=False, indent=1))
