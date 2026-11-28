"""Conserva le fonti in tre modi.

Per ogni URL con `archivia: true` in sources.yml e per ogni riga di archive/extra_urls.txt:
  1. scarica la pagina o il file e ne salva una copia in archive/files/<id>/ (solo se è cambiata). La cartella è
     fuori da git: la copia va come allegato della release mensile documenti-AAAA-MM (release_url nel
     manifest); un file con la stessa sha256 già caricato non si ricarica;
  2. salva un estratto leggibile in Markdown (archive/text/<id>.md): testo delle pagine HTML e dei PDF;
  3. chiede alla Wayback Machine di salvarla (Save Page Now) e annota l'indirizzo dello snapshot.
Tutto finisce in archive/manifest.csv (data, id, url, sha256, file locale, wayback, esito).
Le fonti con `copia_locale: false` (testi protetti dal diritto d'autore) non si copiano: solo Wayback.
Se un file è invariato ma non ha ancora uno snapshot Wayback riuscito, lo snapshot si richiede.

La terza copia, in locale con ArchiveBox, si fa con scripts/archivebox_local.sh
(la lista degli URL la produce questo script: archive/urls.txt).

Wayback: senza chiavi usa l'endpoint pubblico (limitato). Con le chiavi S3 di archive.org nelle
variabili IA_ACCESS_KEY e IA_SECRET_KEY usa l'API SPN2, più affidabile.

Con --schede chiede invece uno snapshot Wayback di ognuna delle 190 schede trasparenza (indirizzo diretto
?s=<MII> da data/reference/istituti_dap.csv), con una pausa tra le richieste; la copia locale delle schede è
già il json di fetch_schede.py. Esito in archive/wayback_schede.csv. Non fallisce mai.

Uso:  python scripts/archive_sources.py [--no-wayback] [--solo ID]
      python scripts/archive_sources.py --schede [--pausa 20] [--limite N] [--solo-falliti]
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import io
import logging

import yaml
from bs4 import BeautifulSoup
from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)  # avvisi sui font, non errori

from common import ARCHIVE, ROOT, pubblica_in_release, release_gia_caricata, scrivi_testo, session, sha256, today

MANIFEST = ARCHIVE / "manifest.csv"
WAYBACK_SCHEDE = ARCHIVE / "wayback_schede.csv"
CAMPI = ["data", "id", "url", "sha256", "dimensione", "file", "release_url", "wayback", "esito"]
NON_SCARICABILI = {"looker"}  # pagine che si leggono solo in un browser: solo Wayback e ArchiveBox


def carica_fonti() -> list[dict]:
    fonti = yaml.safe_load((ROOT / "sources.yml").read_text(encoding="utf-8"))["fonti"]
    out = [f for f in fonti if f.get("archivia")]
    extra = ARCHIVE / "extra_urls.txt"
    if extra.exists():
        for riga in extra.read_text(encoding="utf-8").splitlines():
            riga = riga.split("#")[0].strip()
            if not riga:
                continue
            parti = riga.split(maxsplit=1)
            url = parti[0]
            fid = parti[1].strip() if len(parti) > 1 else re.sub(r"[^a-z0-9]+", "-", urlparse(url).netloc + urlparse(url).path.lower()).strip("-")[:80]
            out.append({"id": fid, "url": url, "tipo": "pdf" if url.lower().endswith(".pdf") else "html"})
    # documenti della rassegna pubblica: si conservano tutti; l'id è quello già usato nel manifest, se c'è
    rassegna = ROOT / "data" / "rassegna" / "documenti.csv"
    if rassegna.exists():
        gia = {r["url"]: r["id"] for r in csv.DictReader(MANIFEST.open(encoding="utf-8"))} if MANIFEST.exists() else {}
        for r in csv.DictReader(rassegna.open(encoding="utf-8")):
            if r["url"].startswith("http"):
                fid = gia.get(r["url"]) or re.sub(r"[^a-z0-9]+", "-", urlparse(r["url"]).netloc + urlparse(r["url"]).path.lower()).strip("-")[:80]
                out.append({"id": fid, "url": r["url"], "tipo": "pdf" if r["url"].lower().endswith(".pdf") else "html"})
    visti, unici = set(), []
    for f in out:  # lo stesso URL una volta sola
        if f["url"] not in visti:
            visti.add(f["url"])
            unici.append(f)
    return unici


def pdf_a_markdown(dati: bytes, url: str) -> str:
    """Testo di un PDF, pagina per pagina. Un PDF di sole immagini dà un testo vuoto (servirebbe l'OCR)."""
    try:
        pagine = [(p.extract_text() or "").strip() for p in PdfReader(io.BytesIO(dati)).pages]
    except Exception as e:  # noqa: BLE001
        pagine, nota = [], f"testo non estratto: {e}"
    else:
        nota = "" if any(pagine) else "nessun testo estraibile (PDF di immagini?)"
    corpo = "\n\n".join(f"<!-- pagina {i} -->\n\n{p}" for i, p in enumerate(pagine, 1) if p)
    return f"---\nurl: {url}\nscaricato: {today()}\npagine: {len(pagine)}\nnota: {nota}\n---\n\n{corpo}\n"


def wayback_riuscito(fid: str) -> bool:
    if not MANIFEST.exists():
        return False
    return any(r["id"] == fid and r["wayback"].startswith("https://web.archive.org/web/")
               for r in csv.DictReader(MANIFEST.open(encoding="utf-8")))


def ultimo_hash(fid: str) -> str | None:
    if not MANIFEST.exists():
        return None
    righe = [r for r in csv.DictReader(MANIFEST.open(encoding="utf-8")) if r["id"] == fid and r["sha256"]]
    return righe[-1]["sha256"] if righe else None


def html_a_markdown(html: str, url: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        t.decompose()
    titolo = soup.title.get_text(strip=True) if soup.title else url
    corpo = soup.find("main") or soup.find("article") or soup.body or soup
    righe = []
    for el in corpo.find_all(["h1", "h2", "h3", "h4", "p", "li", "tr"]):
        if el.name == "tr":
            celle = [" ".join(c.get_text().split()) for c in el.find_all(["td", "th"])]
            if any(celle):
                righe.append("| " + " | ".join(celle) + " |")
            continue
        t = " ".join(el.get_text().split())
        if not t:
            continue
        if el.name in {"h1", "h2", "h3", "h4"}:
            righe.append("\n" + "#" * int(el.name[1]) + " " + t + "\n")
        elif el.name == "li":
            righe.append("- " + t)
        else:
            righe.append(t + "\n")
    return f"---\nurl: {url}\nscaricato: {today()}\n---\n\n# {titolo}\n\n" + "\n".join(righe) + "\n"


def wayback(url: str) -> str:
    """Chiede uno snapshot alla Wayback Machine. Restituisce l'URL dello snapshot o un messaggio."""
    k, s = os.environ.get("IA_ACCESS_KEY"), os.environ.get("IA_SECRET_KEY")
    try:
        if k and s:
            r = session.post("https://web.archive.org/save",
                             headers={"Authorization": f"LOW {k}:{s}", "Accept": "application/json"},
                             data={"url": url, "capture_all": "1", "skip_first_archive": "1"}, timeout=120)
            j = r.json()
            job = j.get("job_id")
            if not job:
                return f"errore: {j.get('message', r.status_code)}"
            for _ in range(20):
                time.sleep(6)
                st = session.get(f"https://web.archive.org/save/status/{job}",
                                 headers={"Authorization": f"LOW {k}:{s}"}, timeout=60).json()
                if st.get("status") == "success":
                    return f"https://web.archive.org/web/{st['timestamp']}/{st['original_url']}"
                if st.get("status") == "error":
                    return f"errore: {st.get('message')}"
            return "in coda"
        r = session.get("https://web.archive.org/save/" + url, timeout=180, allow_redirects=True)
        loc = r.headers.get("Content-Location") or ""
        if loc.startswith("/web/"):
            return "https://web.archive.org" + loc
        return r.url if "/web/" in r.url else f"risposta {r.status_code}"
    except Exception as e:  # noqa: BLE001
        return f"errore: {e}"


def wayback_schede(pausa: float, limite: int, solo_falliti: bool = False) -> int:
    """Uno snapshot Wayback per scheda. Annota l'esito; non fallisce mai (la Wayback a volte rifiuta)."""
    ref = ROOT / "data" / "reference" / "istituti_dap.csv"
    schede = [r for r in csv.DictReader(ref.open(encoding="utf-8")) if r.get("url_scheda")]
    if solo_falliti:  # solo le schede senza nessuno snapshot riuscito in archive/wayback_schede.csv
        riuscite = {r["code"] for r in csv.DictReader(WAYBACK_SCHEDE.open(encoding="utf-8"))
                    if r["wayback"].startswith("https://web.archive.org/web/")} if WAYBACK_SCHEDE.exists() else set()
        schede = [r for r in schede if r["code"] not in riuscite]
        print(f"schede senza snapshot riuscito: {len(schede)}")
    if limite:
        schede = schede[:limite]
    nuovo = not WAYBACK_SCHEDE.exists()
    ok = 0
    with WAYBACK_SCHEDE.open("a", newline="", encoding="utf-8") as fw:
        w = csv.DictWriter(fw, fieldnames=["data", "code", "url", "wayback"])
        if nuovo:
            w.writeheader()
        for i, r in enumerate(schede):
            if i:
                time.sleep(pausa)
            snap = wayback(r["url_scheda"])
            ok += snap.startswith("https://web.archive.org/web/")
            w.writerow({"data": today(), "code": r["code"], "url": r["url_scheda"], "wayback": snap})
            fw.flush()
            print(r["code"], snap, flush=True)
    print(f"snapshot riusciti: {ok}/{len(schede)}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-wayback", action="store_true")
    ap.add_argument("--solo")
    ap.add_argument("--schede", action="store_true", help="snapshot Wayback delle 190 schede trasparenza")
    ap.add_argument("--pausa", type=float, default=20, help="secondi tra una scheda e l'altra (con --schede)")
    ap.add_argument("--limite", type=int, default=0, help="solo le prime N schede (prove)")
    ap.add_argument("--solo-falliti", action="store_true", help="con --schede: solo le schede senza snapshot riuscito")
    a = ap.parse_args()
    if a.schede:
        return wayback_schede(a.pausa, a.limite, a.solo_falliti)
    fonti = carica_fonti()
    if a.solo:
        fonti = [f for f in fonti if f["id"] == a.solo]
    (ARCHIVE / "files").mkdir(parents=True, exist_ok=True)
    (ARCHIVE / "text").mkdir(parents=True, exist_ok=True)
    nuovo = not MANIFEST.exists()
    with MANIFEST.open("a", newline="", encoding="utf-8") as fm:
        w = csv.DictWriter(fm, fieldnames=CAMPI)
        if nuovo:
            w.writeheader()
        for f in fonti:
            riga = {"data": today(), "id": f["id"], "url": f["url"], "sha256": "", "file": "", "wayback": "", "esito": ""}
            if f.get("tipo") not in NON_SCARICABILI and f.get("copia_locale", True):
                try:
                    r = session.get(f["url"], timeout=120)
                    r.raise_for_status()
                    h = sha256(r.content)
                    riga["sha256"] = h
                    if h == ultimo_hash(f["id"]):
                        riga["esito"] = "invariato"
                    else:
                        ext = ".pdf" if "pdf" in r.headers.get("Content-Type", "") or f.get("tipo") == "pdf" else ".html"
                        dest = ARCHIVE / "files" / f["id"] / f"{today()}{ext}"
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_bytes(r.content)
                        riga["file"] = str(dest.relative_to(ROOT))
                        riga["dimensione"] = len(r.content)
                        riga["release_url"] = (release_gia_caricata(h, MANIFEST)
                                               or pubblica_in_release(dest, f"{f['id']}_{dest.name}"))
                        md = html_a_markdown(r.text, f["url"]) if ext == ".html" else pdf_a_markdown(r.content, f["url"])
                        scrivi_testo(f["id"], md)
                        riga["esito"] = "salvato"
                except Exception as e:  # noqa: BLE001
                    riga["esito"] = f"download fallito: {e}"
            else:
                riga["esito"] = "solo archivio web"
            if not a.no_wayback and (riga["esito"] != "invariato" or not wayback_riuscito(f["id"])):
                riga["wayback"] = wayback(f["url"])
            w.writerow(riga)
            print(f["id"], riga["esito"], riga["wayback"])
    (ARCHIVE / "urls.txt").write_text("\n".join(f["url"] for f in fonti) + "\n", encoding="utf-8")
    completa_wayback_rassegna()
    return 0


def completa_wayback_rassegna() -> None:
    """Scrive nella rassegna pubblica lo snapshot Wayback riuscito più recente, dove manca."""
    rassegna = ROOT / "data" / "rassegna" / "documenti.csv"
    if not (rassegna.exists() and MANIFEST.exists()):
        return
    snap = {}
    for r in csv.DictReader(MANIFEST.open(encoding="utf-8")):
        if r["wayback"].startswith("https://web.archive.org/web/"):
            snap[r["url"]] = r["wayback"]
    righe = list(csv.DictReader(rassegna.open(encoding="utf-8")))
    if not righe:
        return
    n = 0
    for r in righe:
        if not r["wayback"] and r["url"] in snap:
            r["wayback"], n = snap[r["url"]], n + 1
    if n:
        with rassegna.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(righe[0]))
            w.writeheader()
            w.writerows(righe)
        print(f"rassegna: {n} snapshot Wayback aggiunti")


if __name__ == "__main__":
    sys.exit(main())
