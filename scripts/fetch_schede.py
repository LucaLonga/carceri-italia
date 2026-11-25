"""Scarica le schede trasparenza dei 190 istituti penitenziari (DAP).

1. legge la pagina con la mappa: per ogni istituto codice DAP, nome, tipo, coordinate, indirizzo;
2. per ogni istituto chiede la scheda (POST) e legge tutte le tabelle "campoComplesso";
3. salva:
   - data/raw/schede-trasparenza/latest.csv          campi numerici principali (una riga per istituto)
   - data/raw/schede-trasparenza/AAAA-MM-GG_schede.csv  copia datata, solo se i numeri sono cambiati
   - data/raw/schede-trasparenza/json/AAAA-MM-GG.json.gz tutte le tabelle di tutte le schede
   - data/reference/istituti_dap.csv                 anagrafica ufficiale (codice, nome, coordinate, indirizzo)

La cronologia dei commit di latest.csv è la serie storica.
Uso:  python scripts/fetch_schede.py [--limite N]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import html as htmllib
import json
import re
import sys

from bs4 import BeautifulSoup

from common import DATA, get, to_int, today

MAPPA = "https://www.giustizia.it/giustizia/page/it/istituti_penitenziari"
SCHEDA = "https://www.giustizia.it/giustizia/page/it/dettaglio_scheda_istituto_penitenziario"
OUT = DATA / "raw" / "schede-trasparenza"

CAMPI = {
    "posti_reg": "Capienza e presenze|posti regolamentari",
    "posti_non_disp": "Capienza e presenze|posti non disponibili",
    "presenti": "Capienza e presenze|totale detenuti",
    "stanze": "Stanze di detenzione|numero complessivo",
    "stanze_non_disp": "Stanze di detenzione|numero non disponibili",
    "st_doccia": "Stanze di detenzione|doccia",
    "st_bidet": "Stanze di detenzione|bidet",
    "st_handicap": "Stanze di detenzione|portatori di handicap",
    "st_wc_porta": "Stanze di detenzione|servizi igienici con porta",
    "st_luce": "Stanze di detenzione|accensione luce autonoma",
    "st_prese": "Stanze di detenzione|prese elettriche",
    "pp_eff": "Personale|polizia penitenziaria - effettivi",
    "pp_prev": "Personale|polizia penitenziaria - previsti",
    "edu_eff": "Personale|educatori - effettivi",
    "edu_prev": "Personale|educatori - previsti",
}
ANAG = ["code", "titolo", "nome", "tipo", "lat", "lon", "indirizzo", "regione", "provveditorato"]


def _js_str(block: str, key: str) -> str:
    m = re.search(r"marker\." + key + r' = ("(?:[^"\\]|\\.)*"|[-\d.]+)', block)
    if not m:
        return ""
    v = m.group(1)
    v = json.loads(v) if v.startswith('"') else v
    return htmllib.unescape(v).strip()


def leggi_mappa() -> list[dict]:
    page = get(MAPPA).text
    script = next((s for s in re.findall(r"<script[^>]*>(.*?)</script>", page, re.S) if "markerByRegioni" in s), None)
    if script is None:
        raise RuntimeError("script della mappa non trovato: la pagina è cambiata")
    out = []
    for b in script.split("marker = {};")[1:]:
        reg = re.search(r'marker\.regione = \{code: "([^"]*)", desc: "([^"]*)"', b)
        prov = re.search(r'marker\.provv = \{id: \d+, name: "([^"]*)"', b)
        out.append({
            "code": _js_str(b, "codiceIstituto"),
            "titolo": _js_str(b, "title"),
            "nome": _js_str(b, "nome"),
            "tipo": re.sub(r"\s*-\s*$", "", _js_str(b, "tipo")),
            "lat": _js_str(b, "lat"),
            "lon": _js_str(b, "lon"),
            "indirizzo": _js_str(b, "indirizzo"),
            "regione": htmllib.unescape(reg.group(2)) if reg else "",
            "provveditorato": htmllib.unescape(prov.group(1)) if prov else "",
        })
    if len(out) < 150:
        raise RuntimeError(f"trovati solo {len(out)} istituti: la pagina è cambiata?")
    return out


def leggi_scheda(ist: dict) -> dict:
    r = get(SCHEDA, method="POST", data={
        "codiceIstituto": ist["code"], "imgUrl": "", "titolo": ist["titolo"],
        "nome": ist["nome"], "tipo": ist["tipo"]}, pause=0.7)
    soup = BeautifulSoup(r.text, "lxml")
    tabelle = {}
    for cc in soup.select(".campoComplesso"):
        h2, tb = cc.find("h2"), cc.find("table")
        if not h2 or not tb:
            continue
        titolo = " ".join(h2.get_text().split())
        th = [" ".join(x.get_text().split()) for x in tb.select("thead th")]
        rows = [[" ".join(td.get_text().split()) for td in tr.find_all("td")] for tr in tb.select("tbody tr")]
        tabelle[titolo] = [dict(zip(th, row)) for row in rows if row]
    testo = " ".join(soup.get_text(" ").split())
    m1 = re.search(r"Capienza e presenze.*?dati aggiornati al (\d\d/\d\d/\d{4})", testo)
    m2 = re.search(r"data di aggiornamento spazi detentivi (\d\d/\d\d/\d{4})", testo)
    return {"code": ist["code"], "tabelle": tabelle,
            "agg_capienza": m1.group(1) if m1 else "", "agg_spazi": m2.group(1) if m2 else ""}


def riga_numerica(ist: dict, sch: dict) -> dict:
    out = {k: ist[k] for k in ["code", "titolo", "nome", "tipo", "lat", "lon"]}
    for col, chiave in CAMPI.items():
        sezione, campo = chiave.split("|")
        righe = sch["tabelle"].get(sezione) or [{}]
        out[col] = to_int(righe[0].get(campo, ""))
    out["agg_capienza"] = sch["agg_capienza"]
    out["agg_spazi"] = sch["agg_spazi"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=0, help="solo i primi N istituti (prove)")
    a = ap.parse_args()
    (OUT / "json").mkdir(parents=True, exist_ok=True)

    istituti = leggi_mappa()
    if a.limite:
        istituti = istituti[: a.limite]
    schede, righe, errori = [], [], []
    for ist in istituti:
        try:
            s = leggi_scheda(ist)
            schede.append(s)
            righe.append(riga_numerica(ist, s))
        except Exception as e:  # noqa: BLE001
            errori.append(f"{ist['code']}: {e}")
    print(f"schede lette: {len(righe)}/{len(istituti)}; errori: {len(errori)}")
    for e in errori:
        print("  ", e)
    if len(righe) < 0.95 * len(istituti):
        print("ERRORE: troppe schede non lette", file=sys.stderr)
        return 1

    cols = ["code", "titolo", "nome", "tipo", "lat", "lon", *CAMPI.keys(), "agg_capienza", "agg_spazi"]
    righe.sort(key=lambda r: r["code"])

    def scrivi(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols, delimiter=";")
            w.writeheader()
            w.writerows(righe)

    latest = OUT / "latest.csv"
    prima = latest.read_text(encoding="utf-8") if latest.exists() else ""
    scrivi(latest)
    # una copia datata solo se cambiano i numeri (le date di aggiornamento cambiano ogni giorno)
    def senza_date(t):
        return "\n".join(";".join(r.split(";")[:-2]) for r in t.splitlines())
    if senza_date(prima) != senza_date(latest.read_text(encoding="utf-8")):
        scrivi(OUT / f"{today()}_schede.csv")
        with gzip.open(OUT / "json" / f"{today()}.json.gz", "wt", encoding="utf-8") as f:
            json.dump({"scaricato": today(), "istituti": istituti, "schede": schede}, f, ensure_ascii=False)
        print("numeri cambiati: salvata copia datata")
    else:
        print("nessun cambiamento nei numeri")

    ref = DATA / "reference" / "istituti_dap.csv"
    ref.parent.mkdir(parents=True, exist_ok=True)
    with open(ref, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ANAG)
        w.writeheader()
        w.writerows(sorted(istituti, key=lambda r: r["code"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
