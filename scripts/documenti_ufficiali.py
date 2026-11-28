"""Documenti ufficiali nuovi dagli elenchi di archive/elenchi_ufficiali.yml (risposte alle interrogazioni,
circolari, relazioni del Commissario e del Garante).

Per ogni documento nuovo di un elenco:
  1. lo scarica e ne estrae il testo (PDF o pagina HTML);
  2. misura la pertinenza: parole chiave sul carcere (almeno SOGLIA_DOCUMENTI, o una nell'oggetto) e istituti citati;
  3. se è pertinente: copia intera in archive/files/<id>/, testo in archive/text/<id>.md, snapshot Wayback
     (si riusa uno snapshot recente se c'è già), riga in archive/manifest.csv e in data/rassegna/documenti.csv
     con temi, affermazioni e verifica [DA COMPILARE: Luca].
Ogni documento visto finisce in archive/documenti_visti.csv, pertinente o no.
La prima lettura di un elenco fa da base: i documenti già presenti si annotano come "base", senza scaricarli
(con --arretrati N si analizzano anche gli N più recenti della base).

La stessa analisi (funzione `analizza`) la usa la sorveglianza del repository privato per le sue issue.

Uso:  python scripts/documenti_ufficiali.py [--solo ID] [--arretrati N] [--no-wayback]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup

from archive_sources import CAMPI as CAMPI_MANIFEST, MANIFEST, html_a_markdown, pdf_a_markdown, wayback
from common import ARCHIVE, DATA, ROOT, get, session, sha256, today
from istituti_nel_testo import SOGLIA_DOCUMENTI, codici_dap, pertinente, punteggio, riconosci

ELENCHI = ARCHIVE / "elenchi_ufficiali.yml"
VISTI = ARCHIVE / "documenti_visti.csv"
RASSEGNA = DATA / "rassegna" / "documenti.csv"
COL_VISTI = ["url", "elenco", "primo_visto", "titolo", "esito", "punteggio", "codici_dap", "id_rassegna"]
DA_COMPILARE = "[DA COMPILARE: Luca]"
MESI = {m: i for i, m in enumerate(["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"], 1)}


def carica_elenchi() -> list[dict]:
    return yaml.safe_load(ELENCHI.read_text(encoding="utf-8"))["elenchi"]


def documenti_dell_elenco(html: str, el: dict) -> dict[str, str]:
    """url -> titolo dei link che sono documenti, nell'ordine della pagina."""
    soup = BeautifulSoup(html, "lxml")
    pat = re.compile(el["link"], re.I)
    sito = urlparse(el["url"]).netloc
    out = {}
    for a in soup.find_all("a", href=True):
        url = urljoin(el["url"], a["href"].strip()).split("#")[0]
        titolo = " ".join(a.get_text().split())
        if urlparse(url).netloc == sito and pat.search(url) and url not in out and titolo:
            out[url] = titolo
    return out


def analizza(url: str, pausa: float = 1.0) -> dict:
    """Scarica un documento e dice se riguarda il carcere. Restituisce contenuto, testo, pertinenza, istituti."""
    r = get(url, pause=pausa)
    pdf = "pdf" in r.headers.get("Content-Type", "") or url.lower().endswith(".pdf")
    url_file, contenuto = url, r.content
    if pdf:
        md = pdf_a_markdown(r.content, url)
    else:
        # pagina di presentazione con il documento allegato (Garante, alcune circolari): il documento è il PDF
        allegato = pdf_allegato(r.text, url)
        if allegato:
            ra = get(allegato, pause=pausa)
            url_file, contenuto, pdf = allegato, ra.content, True
            md = html_a_markdown(r.text, url) + "\n\n# Allegato\n\n" + pdf_a_markdown(ra.content, allegato)
        else:
            md = html_a_markdown(r.text, url)
    certi, ambigui = codici_dap(md)
    nomi = sorted({t["testo"] for t in riconosci(md)})
    p = punteggio(md)
    # pertinente: abbastanza parole chiave, oppure (solo per i PDF) il carcere è già nell'oggetto, all'inizio
    oggetto = md.split("---", 2)[-1][:1500]
    return {"url": url, "url_file": url_file, "contenuto": contenuto, "estensione": ".pdf" if pdf else ".html",
            "testo": md, "punteggio": p,
            "pertinente": p >= SOGLIA_DOCUMENTI or (pdf and p >= 1 and pertinente(oggetto)), "codici_dap": certi, "codici_dap_ambigui": ambigui,
            "istituti_citati": nomi}


def pdf_allegato(html: str, url: str) -> str:
    """Primo PDF dello stesso sito nel corpo della pagina (non nei menu), o ''."""
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["nav", "header", "footer"]):
        t.decompose()
    sito = urlparse(url).netloc
    for a in (soup.find("main") or soup.body or soup).find_all("a", href=True):
        u = urljoin(url, a["href"].strip()).split("#")[0]
        if u.lower().endswith(".pdf") and urlparse(u).netloc == sito:
            return u
    return ""


def data_dal_documento(url: str, titolo: str) -> str:
    """'…_risposta_25nov2026.pdf' -> 2026-11-25; 'Circolare 6 maggio 2026 - …' -> 2026-05-06; altrimenti ''."""
    m = re.search(r"(\d{1,2})(gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)[a-z]*(\d{4})", unquote(url).lower())
    if m:
        return f"{m.group(3)}-{MESI[m.group(2)]:02d}-{int(m.group(1)):02d}"
    m = re.search(r"(\d{1,2})\s+(gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)[a-z]*\s+(\d{4})", titolo.lower())
    return f"{m.group(3)}-{MESI[m.group(2)]:02d}-{int(m.group(1)):02d}" if m else ""


def id_documento(url: str, elenco: str) -> str:
    q = re.search(r"contentId=([A-Za-z0-9]+)", url)
    base = q.group(1).lower() if q else Path(urlparse(url).path).stem.lower()
    return re.sub(r"[^a-z0-9]+", "-", f"{elenco}-{base}").strip("-")[:90]


def wayback_recente(url: str) -> str:
    """Snapshot già presente (ultimi 7 giorni), per non chiederne un secondo; altrimenti se ne chiede uno."""
    try:
        j = session.get("https://archive.org/wayback/available", params={"url": url}, timeout=60).json()
        snap = j.get("archived_snapshots", {}).get("closest", {})
        if snap.get("available") and snap.get("timestamp", "") >= time.strftime("%Y%m%d", time.gmtime(time.time() - 7 * 86400)):
            return snap["url"].replace("http://", "https://", 1)
    except Exception:  # noqa: BLE001
        pass
    return wayback(url)


def prossimo_id_rassegna() -> str:
    righe = list(csv.DictReader(RASSEGNA.open(encoding="utf-8"))) if RASSEGNA.exists() else []
    n = max((int(r["id"].split("-")[1]) for r in righe if r["id"].startswith("doc-")), default=0)
    return f"doc-{n + 1:04d}"


def conserva(doc: dict, el: dict, titolo: str, usa_wayback: bool) -> str:
    """Copia, testo, Wayback, manifest e riga di rassegna di un documento pertinente. Restituisce l'id di rassegna."""
    fid = id_documento(doc["url"], el["id"])
    dest = ARCHIVE / "files" / fid / f"{today()}{doc['estensione']}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(doc["contenuto"])
    (ARCHIVE / "text").mkdir(exist_ok=True)
    (ARCHIVE / "text" / f"{fid}.md").write_text(doc["testo"], encoding="utf-8")
    snap = wayback_recente(doc["url"]) if usa_wayback else ""
    with MANIFEST.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CAMPI_MANIFEST).writerow({
            "data": today(), "id": fid, "url": doc["url"], "sha256": sha256(doc["contenuto"]),
            "file": str(dest.relative_to(ROOT)), "wayback": snap, "esito": "salvato (documenti_ufficiali)"})
    rid = prossimo_id_rassegna()
    with RASSEGNA.open(encoding="utf-8") as f:
        cols = next(csv.reader(f))
    with RASSEGNA.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=cols).writerow({
            "id": rid, "data": data_dal_documento(doc["url"], titolo), "ente_o_testata": el["ente"], "tipo": el["tipo"],
            "titolo": titolo, "url": doc["url"], "wayback": snap if snap.startswith("https://web.archive.org/web/") else "",
            "archivebox": "", "file_privato": "", "codici_dap": ";".join(doc["codici_dap"]),
            "temi": DA_COMPILARE, "affermazioni": DA_COMPILARE, "verifica_dati": DA_COMPILARE, "stato_giudiziario": "",
            "nota": f"aggiunto da documenti_ufficiali.py ({el['id']}, {today()}); punteggio {doc['punteggio']}"
                    + (f"; nomi ambigui: {';'.join(doc['codici_dap_ambigui'])}" if doc["codici_dap_ambigui"] else "")})
    return rid


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", help="solo l'elenco con questo id")
    ap.add_argument("--arretrati", type=int, default=0, help="analizza anche gli N documenti più recenti già in base")
    ap.add_argument("--no-wayback", action="store_true")
    a = ap.parse_args()
    visti = {r["url"]: r for r in csv.DictReader(VISTI.open(encoding="utf-8"))} if VISTI.exists() else {}
    nuovi_visti, errori = [], []
    for el in carica_elenchi():
        if a.solo and el["id"] != a.solo:
            continue
        try:
            docs = documenti_dell_elenco(get(el["url"], pause=2).text, el)
        except Exception as e:  # noqa: BLE001
            errori.append(f"{el['id']}: elenco non letto: {e}")
            continue
        base = not any(v["elenco"] == el["id"] for v in visti.values())
        da_fare = [u for u in docs if u not in visti]
        if base:
            arretrati = set(da_fare[: a.arretrati])
            for u in da_fare:
                if u not in arretrati:
                    nuovi_visti.append({"url": u, "elenco": el["id"], "primo_visto": today(), "titolo": docs[u], "esito": "base"})
            da_fare = [u for u in da_fare if u in arretrati]
        print(f"{el['id']}: {len(docs)} documenti, {len(da_fare)} da analizzare" + (" (prima lettura: base)" if base else ""))
        in_rassegna = {r["url"]: r["id"] for r in csv.DictReader(RASSEGNA.open(encoding="utf-8"))}
        for u in da_fare:
            if u in in_rassegna:  # già entrato da un'altra strada (a mano o da un altro elenco)
                nuovi_visti.append({"url": u, "elenco": el["id"], "primo_visto": today(), "titolo": docs[u],
                                    "esito": "già in rassegna", "id_rassegna": in_rassegna[u]})
                continue
            try:
                doc = analizza(u)
            except Exception as e:  # noqa: BLE001
                errori.append(f"{u}: {e}")
                continue
            riga = {"url": u, "elenco": el["id"], "primo_visto": today(), "titolo": docs[u],
                    "punteggio": doc["punteggio"], "codici_dap": ";".join(doc["codici_dap"])}
            if doc["pertinente"]:
                riga["esito"] = "pertinente"
                riga["id_rassegna"] = conserva(doc, el, docs[u], not a.no_wayback)
            else:
                riga["esito"] = "non pertinente"
            nuovi_visti.append(riga)
            print(f"  {riga['esito']:15} {doc['punteggio']:4d} {docs[u][:80]}")
    if nuovi_visti:
        nuovo = not VISTI.exists()
        with VISTI.open("a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COL_VISTI)
            if nuovo:
                w.writeheader()
            w.writerows(nuovi_visti)
    print(f"documenti annotati: {len(nuovi_visti)}; errori: {len(errori)}")
    for e in errori:
        print("  ", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
