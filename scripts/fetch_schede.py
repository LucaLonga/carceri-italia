"""Scarica le schede trasparenza dei 190 istituti penitenziari (DAP).

1. legge la pagina con la mappa: per ogni istituto codice DAP, codice MII, nome, tipo, coordinate, indirizzo;
2. per ogni istituto apre la scheda all'indirizzo diretto (GET dettaglio_scheda_istituto_penitenziario?s=<mii>;
   POST come ripiego se manca il MII) e legge tutte le sezioni "campoComplesso": tabelle, sottocampi
   (nome: valore) e campi semplici ("dati aggiornati al ...");
3. salva:
   - data/raw/schede-trasparenza/latest.csv          campi numerici principali (una riga per istituto)
   - data/raw/schede-trasparenza/AAAA-MM-GG_schede.csv  copia datata, solo se i numeri sono cambiati
   - data/raw/schede-trasparenza/json/AAAA-MM-GG.json.gz tutto il contenuto di tutte le schede, solo se è cambiato
   - data/raw/schede-trasparenza/struttura/AAAA-MM-GG.json gruppi, sezioni e campi di ogni scheda, solo se è cambiata
   - data/reference/istituti_dap.csv                 anagrafica ufficiale (codice, MII, indirizzo della scheda, coordinate)

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

from common import DATA, get, scrivi_gz, to_int, today

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
ANAG = ["code", "mii", "url_scheda", "titolo", "nome", "tipo", "lat", "lon", "indirizzo", "regione", "provveditorato"]


def url_scheda(mii: str) -> str:
    return f"{SCHEDA}?s={mii}" if mii else ""


def _js_str(block: str, key: str) -> str:
    m = re.search(r"marker\." + key + r""" = ("(?:[^"\\]|\\.)*"|'[^']*'|[-\d.]+)""", block)
    if not m:
        return ""
    v = m.group(1)
    if v.startswith('"'):
        v = json.loads(v)
    elif v.startswith("'"):
        v = v[1:-1]
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
            "mii": _js_str(b, "mii"),
            "url_scheda": url_scheda(_js_str(b, "mii")),
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


def _txt(el) -> str:
    return " ".join(el.get_text().split())


def leggi_scheda(ist: dict) -> tuple[dict, list[dict]]:
    """Contenuto della scheda e la sua struttura (gruppi, sezioni, campi, nell'ordine della pagina)."""
    if ist.get("mii"):
        r = get(ist["url_scheda"], pause=0.7)
    else:
        r = get(SCHEDA, method="POST", data={
            "codiceIstituto": ist["code"], "imgUrl": "", "titolo": ist["titolo"],
            "nome": ist["nome"], "tipo": ist["tipo"]}, pause=0.7)
    soup = BeautifulSoup(r.text, "lxml")
    tabelle, sottocampi, semplici, struttura = {}, [], {}, []
    gruppo = ""
    # gruppi (h1 di sezione), sezioni (campoComplesso) e campi semplici, nell'ordine della pagina
    for el in soup.select("h1.custom-col-11, .campoComplesso, .listaContenutiComplessi > h2"):
        if el.name == "h1":
            gruppo = _txt(el)
            continue
        if el.name == "h2":  # campo semplice: "dati aggiornati al" + valore
            val = el.find_next_sibling(class_="valoreCampoSemplice")
            nome = _txt(el)
            semplici[f"{gruppo}|{nome}"] = _txt(val) if val else ""
            struttura.append({"gruppo": gruppo, "sezione": nome, "tipo": "semplice", "campi": []})
            continue
        h2 = el.find("h2")
        if not h2:
            continue
        titolo = _txt(h2)
        tb = el.find("table")
        if tb:
            th = [_txt(x) for x in tb.select("thead th")]
            rows = [[_txt(td) for td in tr.find_all("td")] for tr in tb.select("tbody tr")]
            tabelle[titolo] = [dict(zip(th, row)) for row in rows if row]
            struttura.append({"gruppo": gruppo, "sezione": titolo, "tipo": "tabella", "campi": th})
        else:
            campi = [(_txt(s.select_one(".nomeSottocampo")), _txt(s.select_one(".valoreSottocampo")))
                     for s in el.select(".sottocampo") if s.select_one(".nomeSottocampo")]
            sottocampi.append({"sezione": titolo, "campi": campi})
            struttura.append({"gruppo": gruppo, "sezione": titolo, "tipo": "campi", "campi": [c[0] for c in campi]})
    testo = " ".join(soup.get_text(" ").split())
    m1 = re.search(r"Capienza e presenze.*?dati aggiornati al (\d\d/\d\d/\d{4})", testo)
    m2 = re.search(r"data di aggiornamento spazi detentivi (\d\d/\d\d/\d{4})", testo)
    scheda = {"code": ist["code"], "tabelle": tabelle, "sottocampi": sottocampi, "semplici": semplici,
              "agg_capienza": m1.group(1) if m1 else "", "agg_spazi": m2.group(1) if m2 else ""}
    return scheda, struttura


def riga_numerica(ist: dict, sch: dict) -> dict:
    out = {k: ist[k] for k in ["code", "titolo", "nome", "tipo", "lat", "lon"]}
    for col, chiave in CAMPI.items():
        sezione, campo = chiave.split("|")
        righe = sch["tabelle"].get(sezione) or [{}]
        out[col] = to_int(righe[0].get(campo, ""))
    out["agg_capienza"] = sch["agg_capienza"]
    out["agg_spazi"] = sch["agg_spazi"]
    return out


def ultimo_file(cartella, motivo: str):
    files = sorted(cartella.glob(motivo)) if cartella.exists() else []
    return files[-1] if files else None


def gzip_leggi(p) -> str:
    return gzip.decompress(p.read_bytes()).decode("utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limite", type=int, default=0, help="solo i primi N istituti (prove)")
    a = ap.parse_args()
    (OUT / "json").mkdir(parents=True, exist_ok=True)

    istituti = leggi_mappa()
    if a.limite:
        istituti = istituti[: a.limite]
    schede, righe, errori, strutture = [], [], [], {}
    for ist in istituti:
        try:
            s, strutture[ist["code"]] = leggi_scheda(ist)
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
    if a.limite:  # prova: si legge e si stampa, non si scrive niente
        for ist, s in zip(istituti, schede):
            print(f"  {ist['code']} {ist['mii']} {ist['titolo']}: {len(strutture[ist['code']])} sezioni, "
                  f"{len(s['tabelle'])} tabelle, posti non disp. {riga_numerica(ist, s)['posti_non_disp']}")
        return 0

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
        print("numeri cambiati: salvata copia datata")
    else:
        print("nessun cambiamento nei numeri")

    # contenuto completo e struttura: una copia datata solo se cambiano rispetto all'ultima salvata
    # (non si confrontano i campi "aggiornato al", che cambiano ogni giorno)
    def senza_agg(schede_):
        return [{k: v for k, v in s.items() if k not in ("agg_capienza", "agg_spazi", "semplici")} for s in schede_]

    ultimo_json = ultimo_file(OUT / "json", "*.json.gz")
    precedente = json.loads(gzip_leggi(ultimo_json))["schede"] if ultimo_json else None
    if precedente is None or senza_agg(precedente) != senza_agg(schede):
        scrivi_gz(OUT / "json" / f"{today()}.json.gz",
                  json.dumps({"scaricato": today(), "istituti": istituti, "schede": schede}, ensure_ascii=False))
        print("contenuto delle schede cambiato: salvato json")
    (OUT / "struttura").mkdir(exist_ok=True)
    ultima_str = ultimo_file(OUT / "struttura", "*.json")
    strutture = dict(sorted(strutture.items()))
    if (ultima_str is None or json.loads(ultima_str.read_text())["schede"] != strutture):
        # una riga per scheda: file leggibile e differenze piccole tra una copia e l'altra
        righe_str = ",\n".join(f"  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in strutture.items())
        (OUT / "struttura" / f"{today()}.json").write_text(
            f'{{"scaricato": "{today()}", "schede": {{\n{righe_str}\n}}}}\n', encoding="utf-8")
        print("struttura delle schede cambiata: salvata copia datata")

    ref = DATA / "reference" / "istituti_dap.csv"
    ref.parent.mkdir(parents=True, exist_ok=True)
    with open(ref, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ANAG)
        w.writeheader()
        w.writerows(sorted(istituti, key=lambda r: r["code"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
