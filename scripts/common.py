"""Funzioni comuni agli script di raccolta di carceri-italia."""
from __future__ import annotations

import csv
import gzip
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
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


# --- file grandi: fuori da git ------------------------------------------------------------------

LIMITE_GIT = 1_000_000  # byte: in git nessun file sopra 1 MB (checks.py e .githooks/pre-commit lo controllano)


def scrivi_testo(fid: str, md: str) -> list[Path]:
    """Scrive archive/text/<fid>.md; sopra il limite divide in parti (<fid>.parte2.md, ...) ai confini di pagina."""
    cartella = ARCHIVE / "text"
    cartella.mkdir(parents=True, exist_ok=True)
    for vecchia in cartella.glob(f"{fid}.parte*.md"):
        vecchia.unlink()
    parti, cur = [], ""
    for pezzo in re.split(r"(?=<!-- pagina \d+ -->)", md):
        if cur and len((cur + pezzo).encode("utf-8")) > 0.9 * LIMITE_GIT:
            parti.append(cur)
            cur = ""
        cur += pezzo
    parti.append(cur)
    scritti = []
    for i, c in enumerate(parti, 1):
        q = cartella / (f"{fid}.md" if i == 1 else f"{fid}.parte{i}.md")
        testa = f"<!-- parte {i} di {len(parti)} -->\n" if i > 1 else ""
        coda = f"\n<!-- continua in {fid}.parte{i + 1}.md -->\n" if i < len(parti) else ""
        q.write_text(testa + c + coda, encoding="utf-8")
        scritti.append(q)
    return scritti


def release_gia_caricata(sha: str, manifest: Path) -> str:
    """release_url di un file con la stessa sha256 già caricato, o ''."""
    if not manifest.exists():
        return ""
    with manifest.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("sha256") == sha and (r.get("release_url") or "").startswith("https://"):
                return r["release_url"]
    return ""


def pubblica_in_release(path: Path, nome: str) -> str:
    """Carica un file come allegato della release mensile documenti-AAAA-MM del repository pubblico
    (creata se manca come pre-release: GitHub non la segna mai "latest"). Restituisce l'URL di scaricamento o un messaggio d'errore: non solleva mai."""
    if not shutil.which("gh"):
        return "errore: gh non trovato"
    tag = f"documenti-{today()[:7]}"
    try:
        repo = os.environ.get("GITHUB_REPOSITORY") or subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()
        if subprocess.run(["gh", "release", "view", tag, "-R", repo], capture_output=True).returncode != 0:
            subprocess.run(["gh", "release", "create", tag, "-R", repo, "--latest=false", "--prerelease",
                            "--title", f"Documenti {tag[-7:]}",
                            "--notes", "Copie integrali dei documenti ufficiali e delle pagine conservate nel mese "
                                       "(archive/manifest.csv: sha256, dimensione, URL originale, snapshot Wayback). "
                                       "Nessun codice: gli archivi \"Source code\" li aggiunge GitHub da sé."],
                           check=True, capture_output=True, text=True)
        with tempfile.TemporaryDirectory() as tmp:
            copia = Path(tmp) / nome
            shutil.copyfile(path, copia)
            subprocess.run(["gh", "release", "upload", tag, str(copia), "--clobber", "-R", repo],
                           check=True, capture_output=True, text=True)
        return f"https://github.com/{repo}/releases/download/{tag}/{nome}"
    except subprocess.CalledProcessError as e:
        return f"errore: {(e.stderr or str(e)).strip()[:200]}"
