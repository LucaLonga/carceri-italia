"""Scarica le tabelle mensili "Detenuti italiani e stranieri presenti e capienze per istituto".

1. scorre l'elenco delle statistiche del Ministero della Giustizia (area carcere);
2. trova tutte le voci "capienze per istituto" (anche quelle vecchie: recupero della serie storica);
3. per ogni mese non ancora salvato scarica la pagina, salva l'HTML grezzo (gzip) e un CSV pulito;
4. controlla che la somma delle righe coincida con la riga "Totale" dichiarata dal Ministero.

Uso:  python scripts/fetch_ministero.py [--max-pagine 40] [--solo-ultimo]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from common import DATA, data_da_titolo, get, scrivi_gz, to_int, today

ELENCO = "https://www.giustizia.it/giustizia/page/it/statistiche?selectedNode=0_2&page={n}"
OUT = DATA / "raw" / "ministero"
COLONNE = ["regione", "istituto", "tipo", "capienza_regolamentare", "presenti", "donne", "stranieri"]
PATTERN = re.compile(r"capienze per istituto", re.I)


def trova_voci(max_pagine: int) -> dict[str, str]:
    """Restituisce {data_iso: url} per tutte le voci "capienze per istituto" trovate."""
    voci: dict[str, str] = {}
    for n in range(1, max_pagine + 1):
        html = get(ELENCO.format(n=n)).text
        soup = BeautifulSoup(html, "lxml")
        links = [a for a in soup.select("a[href]") if "contentId=SST" in a["href"]]
        if not links:
            break
        for a in links:
            titolo = " ".join(a.get_text().split())
            if PATTERN.search(titolo):
                d = data_da_titolo(titolo)
                if d:
                    voci.setdefault(d, urljoin("https://www.giustizia.it", a["href"]))
    return voci


def leggi_tabella(html: str) -> tuple[list[dict], dict, str]:
    """Estrae righe, riga Totale e la nota (*) sul criterio di capienza."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if table is None:
        raise ValueError("nessuna tabella nella pagina")
    righe, totale = [], {}
    for tr in table.find_all("tr"):
        celle = [" ".join(td.get_text().split()) for td in tr.find_all(["td", "th"])]
        if not celle:
            continue
        if celle[0].lower().startswith("totale"):
            nums = [to_int(c) for c in celle[1:]]
            nums = [x for x in nums if x is not None]
            totale = dict(zip(COLONNE[3:], nums[-4:]))
            continue
        # fino a settembre 2025 c'è una colonna in più, "Sigla Provincia", in seconda posizione
        sigla = ""
        if len(celle) == 8 and re.fullmatch(r"[A-Z]{2}", celle[1]):
            sigla = celle.pop(1)
        if len(celle) < 7 or to_int(celle[3]) is None and celle[3] != "":
            continue  # intestazioni
        if celle[0].lower().startswith("regione"):
            continue
        r = dict(zip(COLONNE, celle[:7]))
        r["sigla_provincia"] = sigla
        r["istituto"] = re.sub(r"\s*-\s*$", "", r["istituto"])
        for k in COLONNE[3:]:
            r[k] = to_int(r[k])
        righe.append(r)
    nota = ""
    for p in soup.find_all("p"):
        t = " ".join(p.get_text().split())
        if "mq" in t and "(*)" in t:
            nota = t
            break
    return righe, totale, nota


def controlla(righe: list[dict], totale: dict) -> list[str]:
    errori = []
    for k, v in totale.items():
        s = sum(r[k] or 0 for r in righe)
        if s != v:
            errori.append(f"{k}: somma righe {s} ≠ totale dichiarato {v}")
    return errori


def salva(data_iso: str, url: str) -> dict:
    r = get(url)
    html = r.text
    (OUT / "html").mkdir(parents=True, exist_ok=True)
    scrivi_gz(OUT / "html" / f"{data_iso}.html.gz", html)
    righe, totale, nota = leggi_tabella(html)
    with open(OUT / f"{data_iso}_capienze-per-istituto.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[*COLONNE, "sigla_provincia"])
        w.writeheader()
        w.writerows(righe)
    errori = controlla(righe, totale)
    if not righe:
        errori.append("nessuna riga letta: struttura della tabella cambiata?")
    return {"data": data_iso, "url": url, "scaricato": today(), "righe": len(righe),
            "totale_dichiarato": totale, "errori": errori, "nota_capienza": nota}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pagine", type=int, default=40)
    ap.add_argument("--solo-ultimo", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    indice_path = OUT / "indice.json"
    indice = json.loads(indice_path.read_text()) if indice_path.exists() else {}

    voci = trova_voci(1 if a.solo_ultimo else a.max_pagine)
    if not voci:
        print("ERRORE: nessuna voce trovata nell'elenco: il sito potrebbe essere cambiato", file=sys.stderr)
        return 1
    nuovi, problemi = 0, 0
    for d, url in sorted(voci.items()):
        if d in indice and not indice[d].get("errori"):
            continue
        try:
            info = salva(d, url)
        except Exception as e:  # noqa: BLE001 - registriamo e proseguiamo
            info = {"data": d, "url": url, "scaricato": today(), "errori": [f"lettura fallita: {e}"]}
        indice[d] = info
        nuovi += 1
        problemi += bool(info.get("errori"))
        print(d, info.get("righe"), info.get("errori") or "ok")
    indice_path.write_text(json.dumps(dict(sorted(indice.items())), ensure_ascii=False, indent=2))
    print(f"mesi nuovi o riletti: {nuovi}; con problemi: {problemi}")
    # fallisce solo se l'ultimo mese disponibile ha problemi: i mesi vecchi con formati diversi
    # restano segnalati in indice.json senza bloccare la raccolta
    ultimo = max(indice)
    return 1 if indice[ultimo].get("errori") else 0


if __name__ == "__main__":
    sys.exit(main())
