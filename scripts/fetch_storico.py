"""Serie storica dal 2000 a oggi: che cosa pubblica il Ministero, anno per anno, e con quali buchi.

Fonti (Ministero della Giustizia, DAP, Sezione statistica; pagine "statistiche", area carcere):
1. "Detenuti presenti italiani e stranieri - Anni 1991-..." (una pagina): presenti al 30 giugno e
   al 31 dicembre di ogni anno, con donne e stranieri. Nessuna capienza.
2. "Detenuti presenti - aggiornamento al <data>" (una pagina al mese, nell'archivio online dal 2019):
   per regione, numero di istituti, capienza regolamentare, presenti, donne, stranieri.
3. Per istituto: le tabelle "capienze per istituto" (archivio online dal gennaio 2019). Le pagine
   grezze le salva scripts/fetch_ministero.py in data/raw/ministero/html/; qui si rileggono tutte,
   perché fino a settembre 2025 la tabella ha 8 colonne (c'è anche la sigla di provincia) e il
   lettore di fetch_ministero.py ne aspetta 7. Se una pagina manca, si scarica in data/raw/storico/.
Prima del 2019 l'archivio online del Ministero non ha capienze: il buco è dichiarato in copertura.csv
[DA CERCARE: copie della Wayback Machine, Annuario ISTAT, rapporti Antigone].

Uscite (data/storico/):
  inventario_ministero.csv   tutte le voci dell'elenco statistiche (titolo, data, url)
  presenti_semestrali.csv    serie 1991-oggi
  nazionale_mensile.csv      totali nazionali mensili dal 2019 (dalla riga "Totale")
  regionale_mensile.csv      stesse tabelle per regione
  per_istituto_mensile.csv   capienze per istituto dal 2019 (formato lungo), con controllo sui totali
  copertura.csv              per ogni anno dal 2000: che cosa esiste, da dove viene, che cosa manca
Il grezzo (HTML compresso) va in data/raw/storico/.

Uso: python fetch_storico.py [--max-pagine 60] [--solo-copertura]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import html as htmlmod
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "storico"
RAW = DATA / "raw" / "storico"
ELENCO = "https://www.giustizia.it/giustizia/page/it/statistiche?selectedNode=0_2&page={n}"
BASE = "https://www.giustizia.it"
UA = "carceri-italia/0.2 (+https://github.com/LucaLonga/carceri-italia; ricerca e giornalismo sui dati pubblici)"
MESI = {m: i for i, m in enumerate(["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
                                    "agosto", "settembre", "ottobre", "novembre", "dicembre"], start=1)}

s = requests.Session()
s.headers.update({"User-Agent": UA, "Accept-Language": "it-IT,it;q=0.9"})


def get(url: str, pausa: float = 1.0) -> str:
    for k in range(3):
        try:
            r = s.get(url, timeout=90)
            r.raise_for_status()
            time.sleep(pausa)
            return r.text
        except requests.RequestException:
            if k == 2:
                raise
            time.sleep(3 * (k + 1))
    raise RuntimeError


def pulisci(x: str) -> str:
    return re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", "", x))).strip()


def intero(x: str) -> int | None:
    x = x.replace(".", "").replace("\xa0", "").strip()
    return int(x) if re.fullmatch(r"\d+", x) else None


def data_titolo(t: str) -> str | None:
    m = re.search(r"(\d{1,2})\s+(" + "|".join(MESI) + r")\s+(\d{4})", t, re.I)
    if not m:
        return None
    return date(int(m.group(3)), MESI[m.group(2).lower()], int(m.group(1))).isoformat()


def tabelle(pagina: str) -> list[list[list[str]]]:
    out = []
    for t in re.findall(r"<table.*?</table>", pagina, re.S):
        out.append([[pulisci(c) for c in re.findall(r"<t[dh][^>]*>.*?</t[dh]>", tr, re.S)] for tr in re.findall(r"<tr.*?</tr>", t, re.S)])
    return out


def salva_grezzo(nome: str, pagina: str) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    # mtime=0: stesso contenuto, stesso file (niente commit inutili)
    (RAW / f"{nome}.html.gz").write_bytes(gzip.compress(pagina.encode("utf-8"), mtime=0))


def scrivi(p: Path, righe: list[dict], cols: list[str] | None = None) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    cols = cols or (list(righe[0].keys()) if righe else [])
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(righe)


def inventario(max_pagine: int) -> list[dict]:
    voci = []
    for n in range(1, max_pagine + 1):
        pag = get(ELENCO.format(n=n), 0.8)
        trovate = re.findall(r'<a[^>]+href="([^"]*contentId=SST\d+[^"]*)"[^>]*>(.*?)</a>', pag, re.S)
        if not trovate:
            break
        for u, t in trovate:
            t = pulisci(t)
            if t:
                voci.append({"titolo": t, "data": data_titolo(t) or "", "url": u if u.startswith("http") else BASE + u, "pagina_elenco": n})
    # togli i doppioni (stessa voce in più pagine)
    visti, out = set(), []
    for v in voci:
        if v["url"] not in visti:
            visti.add(v["url"])
            out.append(v)
    return out


def presenti_semestrali(voci: list[dict], errori: list[str]) -> list[dict]:
    v = next((x for x in voci if re.match(r"Detenuti presenti italiani e stranieri - Anni 1991", x["titolo"])), None)
    if not v:
        errori.append("serie 1991-oggi non trovata nell'elenco")
        return []
    pag = get(v["url"])
    salva_grezzo("presenti_italiani_stranieri_1991_oggi", pag)
    righe = []
    for r in tabelle(pag)[0]:
        if len(r) >= 9 and re.fullmatch(r"\d{2}/\d{2}/\d{4}", r[0]):
            righe.append({"data": datetime.strptime(r[0], "%d/%m/%Y").date().isoformat(),
                          "imputati": intero(r[1]), "condannati": intero(r[2]), "internati": intero(r[3]),
                          "presenti": intero(r[4]), "donne": intero(r[5]), "stranieri": intero(r[7]),
                          "fonte": v["url"]})
    return righe


def mensili(voci: list[dict], errori: list[str]) -> tuple[list[dict], list[dict]]:
    naz, reg = [], []
    for v in sorted((x for x in voci if x["titolo"].startswith("Detenuti presenti - aggiornamento al") and x["data"]), key=lambda x: x["data"]):
        try:
            pag = get(v["url"])
        except Exception as ex:  # noqa: BLE001
            errori.append(f"{v['data']}: {ex}")
            continue
        salva_grezzo(f"presenti_regione_{v['data']}", pag)
        t = tabelle(pag)
        if not t:
            errori.append(f"{v['data']}: nessuna tabella")
            continue
        somma = {"istituti": 0, "capienza_regolamentare": 0, "presenti": 0}
        totale = None
        for r in t[0]:
            if len(r) < 6:
                continue
            nums = [intero(c) for c in r[1:6]]
            if r[0].lower().startswith("totale"):
                totale = nums
            elif None not in nums[:3]:
                reg.append({"data": v["data"], "regione": r[0], "istituti": nums[0], "capienza_regolamentare": nums[1],
                            "presenti": nums[2], "donne": nums[3], "stranieri": nums[4]})
                for k, n in zip(somma, nums[:3]):
                    somma[k] += n
        if totale is None:
            errori.append(f"{v['data']}: riga Totale mancante")
            continue
        if [somma["istituti"], somma["capienza_regolamentare"], somma["presenti"]] != totale[:3]:
            errori.append(f"{v['data']}: somma delle regioni diversa dal totale dichiarato")
        naz.append({"data": v["data"], "istituti": totale[0], "capienza_regolamentare": totale[1], "presenti": totale[2],
                    "donne": totale[3], "stranieri": totale[4], "fonte": v["url"]})
    return naz, reg


def per_istituto(voci: list[dict], errori: list[str]) -> list[dict]:
    """Tabelle "capienze per istituto": legge entrambe le impaginazioni (7 o 8 colonne)."""
    out = []
    for v in sorted((x for x in voci if "capienze per istituto" in x["titolo"] and x["data"]), key=lambda x: x["data"]):
        p_min = DATA / "raw" / "ministero" / "html" / f"{v['data']}.html.gz"
        p_sto = RAW / f"capienze_{v['data']}.html.gz"
        if p_min.exists():
            pag = gzip.open(p_min, "rt", encoding="utf-8").read()
        elif p_sto.exists():
            pag = gzip.open(p_sto, "rt", encoding="utf-8").read()
        else:
            try:
                pag = get(v["url"])
            except Exception as ex:  # noqa: BLE001
                errori.append(f"capienze {v['data']}: {ex}")
                continue
            salva_grezzo(f"capienze_{v['data']}", pag)
        t = tabelle(pag)
        if not t:
            errori.append(f"capienze {v['data']}: nessuna tabella")
            continue
        righe, totale = [], None
        for r in t[0]:
            if not r or r[0].lower().startswith("regione"):
                continue
            if r[0].lower().startswith("totale"):
                totale = [n for n in (intero(c) for c in r[1:]) if n is not None]
                continue
            if len(r) >= 8 and re.fullmatch(r"[A-Z]{2}", r[1] or ""):       # 8 colonne: con la sigla di provincia
                reg, prov, ist, tipo, cap, pres, donne, stran = r[:8]
            elif len(r) >= 7:                                                 # 7 colonne
                reg, ist, tipo, cap, pres, donne, stran = r[:7]
                prov = ""
            else:
                continue
            if intero(cap) is None and intero(pres) is None:
                continue
            righe.append({"data": v["data"], "regione": reg, "provincia": prov, "istituto": re.sub(r"\s*-\s*$", "", ist),
                          "tipo": tipo, "capienza_regolamentare": intero(cap), "presenti": intero(pres),
                          "donne": intero(donne), "stranieri": intero(stran)})
        if totale and len(totale) >= 2:
            sc = sum(r["capienza_regolamentare"] or 0 for r in righe)
            sp = sum(r["presenti"] or 0 for r in righe)
            if [sc, sp] != totale[-4:-2]:
                errori.append(f"capienze {v['data']}: somma righe {sc}/{sp} diversa dal totale dichiarato {totale[-4:-2]}")
        else:
            errori.append(f"capienze {v['data']}: riga Totale mancante")
        out += righe
    return out


def copertura() -> list[dict]:
    """Per ogni anno dal 2000: che cosa esiste nel repository e da dove viene."""
    def leggi(p: Path) -> list[dict]:
        return list(csv.DictReader(p.open(encoding="utf-8"))) if p.exists() else []
    sem = leggi(OUT / "presenti_semestrali.csv")
    naz = leggi(OUT / "nazionale_mensile.csv")
    per_ist = sorted({r["data"] for r in leggi(OUT / "per_istituto_mensile.csv")})
    schede = sorted(p.name[:10] for p in (DATA / "raw" / "schede-trasparenza").glob("*_schede.csv"))
    ant = leggi(DATA / "antigone" / "visite.csv")
    out = []
    for anno in range(2000, date.today().year + 1):
        a = str(anno)
        s_ = [r["data"] for r in sem if r["data"].startswith(a)]
        n_ = [r["data"] for r in naz if r["data"].startswith(a)]
        i_ = [d for d in per_ist if d.startswith(a)]
        sc = [d for d in schede if d.startswith(a)]
        av = [r for r in ant if (r.get("data_visita") or "").startswith(a)]
        buchi = []
        if not n_:
            buchi.append("capienza nazionale")
        if not i_ and not sc:
            buchi.append("dati per istituto")
        if not s_:
            buchi.append("presenti")
        out.append({
            "anno": anno,
            "presenti_nazionali": f"{len(s_)} rilevazioni (DAP, serie 1991-oggi)" if s_ else "",
            "capienza_nazionale": f"{len(n_)} mesi (DAP, tabelle per regione)" if n_ else "",
            "per_istituto_ministero": f"{len(i_)} mesi (capienze per istituto)" if i_ else "",
            "per_istituto_schede": f"{len(sc)} istantanee (schede trasparenza)" if sc else "",
            "visite_antigone": len(av),
            "buchi": "; ".join(buchi) + (" [DA CERCARE]" if buchi else ""),
        })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pagine", type=int, default=60)
    ap.add_argument("--solo-copertura", action="store_true")
    a = ap.parse_args()
    errori: list[str] = []
    if not a.solo_copertura:
        voci = inventario(a.max_pagine)
        scrivi(OUT / "inventario_ministero.csv", voci, ["data", "titolo", "url", "pagina_elenco"])
        sem = presenti_semestrali(voci, errori)
        scrivi(OUT / "presenti_semestrali.csv", sem, ["data", "imputati", "condannati", "internati", "presenti", "donne", "stranieri", "fonte"])
        naz, reg = mensili(voci, errori)
        scrivi(OUT / "nazionale_mensile.csv", naz, ["data", "istituti", "capienza_regolamentare", "presenti", "donne", "stranieri", "fonte"])
        scrivi(OUT / "regionale_mensile.csv", reg, ["data", "regione", "istituti", "capienza_regolamentare", "presenti", "donne", "stranieri"])
        pi = per_istituto(voci, errori)
        scrivi(OUT / "per_istituto_mensile.csv", pi, ["data", "regione", "provincia", "istituto", "tipo", "capienza_regolamentare", "presenti", "donne", "stranieri"])
    if a.solo_copertura and (OUT / "indice.json").exists():
        errori = json.loads((OUT / "indice.json").read_text(encoding="utf-8")).get("errori", [])  # dell'ultima raccolta completa
    cop = copertura()
    scrivi(OUT / "copertura.csv", cop)
    (OUT / "indice.json").write_text(json.dumps({
        "raccolta": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "user_agent": UA,
        "anni_con_presenti": [c["anno"] for c in cop if c["presenti_nazionali"]],
        "anni_con_capienza": [c["anno"] for c in cop if c["capienza_nazionale"]],
        "anni_per_istituto": [c["anno"] for c in cop if c["per_istituto_ministero"] or c["per_istituto_schede"]],
        "errori": errori,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"errori: {len(errori)}", *errori, sep="\n", file=sys.stderr)


if __name__ == "__main__":
    main()
