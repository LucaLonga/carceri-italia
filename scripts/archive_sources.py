"""Conserva le fonti in tre modi.

Per ogni URL con `archivia: true` in sources.yml e per ogni riga di archive/extra_urls.txt:
  1. scarica la pagina o il file e ne salva una copia in archive/files/<id>/ (solo se è cambiata);
  2. salva un estratto leggibile: testo in Markdown per le pagine HTML (archive/text/<id>.md);
  3. chiede alla Wayback Machine di salvarla (Save Page Now) e annota l'indirizzo dello snapshot.
Tutto finisce in archive/manifest.csv (data, id, url, sha256, file locale, wayback, esito).

La terza copia, in locale con ArchiveBox, si fa con scripts/archivebox_local.sh
(la lista degli URL la produce questo script: archive/urls.txt).

Wayback: senza chiavi usa l'endpoint pubblico (limitato). Con le chiavi S3 di archive.org nelle
variabili IA_ACCESS_KEY e IA_SECRET_KEY usa l'API SPN2, più affidabile.

Uso:  python scripts/archive_sources.py [--no-wayback] [--solo ID]
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

import yaml
from bs4 import BeautifulSoup

from common import ARCHIVE, ROOT, session, sha256, today

MANIFEST = ARCHIVE / "manifest.csv"
CAMPI = ["data", "id", "url", "sha256", "file", "wayback", "esito"]
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
    visti, unici = set(), []
    for f in out:  # lo stesso URL una volta sola
        if f["url"] not in visti:
            visti.add(f["url"])
            unici.append(f)
    return unici


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-wayback", action="store_true")
    ap.add_argument("--solo")
    a = ap.parse_args()
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
            if f.get("tipo") not in NON_SCARICABILI:
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
                        if ext == ".html":
                            (ARCHIVE / "text" / f"{f['id']}.md").write_text(html_a_markdown(r.text, f["url"]), encoding="utf-8")
                        riga["esito"] = "salvato"
                except Exception as e:  # noqa: BLE001
                    riga["esito"] = f"download fallito: {e}"
            else:
                riga["esito"] = "solo archivio web"
            if not a.no_wayback and riga["esito"] != "invariato":
                riga["wayback"] = wayback(f["url"])
            w.writerow(riga)
            print(f["id"], riga["esito"], riga["wayback"])
    (ARCHIVE / "urls.txt").write_text("\n".join(f["url"] for f in fonti) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
