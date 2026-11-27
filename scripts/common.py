"""Funzioni comuni agli script di raccolta di carceri-italia."""
from __future__ import annotations

import gzip
import hashlib
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ARCHIVE = ROOT / "archive"

UA = (
    "carceri-italia/0.1 (+https://lucalonga.com; "
    "raccolta di dati pubblici per ricerca e giornalismo)"
)

session = requests.Session()
session.headers.update({"User-Agent": UA, "Accept-Language": "it-IT,it;q=0.9"})


def get(url: str, *, method: str = "GET", data: dict | None = None, retries: int = 3, pause: float = 1.0) -> requests.Response:
    """Richiesta con pause e tentativi ripetuti. Solleva l'errore all'ultimo tentativo."""
    for attempt in range(1, retries + 1):
        try:
            r = session.request(method, url, data=data, timeout=60)
            r.raise_for_status()
            time.sleep(pause)
            return r
        except requests.RequestException:
            if attempt == retries:
                raise
            time.sleep(pause * 2 * attempt)
    raise RuntimeError("non raggiungibile")


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def scrivi_gz(path: Path, testo: str) -> None:
    """Scrive testo compresso senza data nell'intestazione gzip: stesso contenuto, stesso file (niente commit inutili)."""
    path.write_bytes(gzip.compress(testo.encode("utf-8"), mtime=0))


def norm_name(s: str) -> str:
    """Normalizza un nome di istituto per i confronti (maiuscolo, senza accenti, senza ' -' finale)."""
    s = str(s).upper().strip().replace("’", "'")
    s = re.sub(r"\s*-\s*$", "", s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s)


def to_int(s: str) -> int | None:
    """'1.616' -> 1616 ; '' -> None (formato numerico italiano)."""
    s = (s or "").strip().replace(".", "").replace("\xa0", "")
    if s in {"", "-", "n.d.", "nd"}:
        return None
    try:
        return int(s)
    except ValueError:
        return None


MESI = {m: i for i, m in enumerate(
    ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
     "agosto", "settembre", "ottobre", "novembre", "dicembre"], start=1)}


def data_da_titolo(t: str) -> str | None:
    """'... aggiornamento al 31 ottobre 2026' -> '2026-10-31'."""
    m = re.search(r"(\d{1,2})\s+([a-zà]+)\s+(\d{4})", t.lower())
    if not m or m.group(2) not in MESI:
        return None
    return f"{m.group(3)}-{MESI[m.group(2)]:02d}-{int(m.group(1)):02d}"
