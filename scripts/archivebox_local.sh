#!/usr/bin/env bash
# Terza copia delle fonti, in locale, con ArchiveBox (https://archivebox.io).
# Da lanciare sul proprio computer, non su GitHub Actions. Ogni settimana con launchd: scripts/launchd/.
#
#   ARCHIVEBOX_DATA=~/ArchiveBoxData ./scripts/archivebox_local.sh [--prova]
#
# Raccoglie gli URL da:
#   - sources.yml (archivia: true)                    pagine che cambiano: una copia nuova a ogni lancio
#   - data/reference/istituti_dap.csv (url_scheda)    le 190 schede trasparenza: una copia nuova a ogni lancio
#   - archive/extra_urls.txt                          documenti e articoli: una copia sola
#   - data/rassegna/documenti.csv (url), se esiste    documenti ufficiali della rassegna: una copia sola
#   - ../carceri-italia-redazione/rassegna/*.csv (url), se il repository privato è accanto: rassegna stampa
# e li aggiunge all'archivio ArchiveBox indicato, con --depth=0 (solo la pagina, non i link che contiene).
#
# ArchiveBox non riarchivia un URL già presente: per avere una copia datata delle pagine che cambiano
# si aggiunge all'indirizzo un frammento con la data (#AAAA-MM-GG), che il server non riceve.
# Con --prova stampa solo l'elenco e non archivia niente.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="${ARCHIVEBOX_DATA:-$HOME/ArchiveBoxData}"
PROVA="${1:-}"

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
python3 - "$REPO" > "$TMP" <<'PY'
import csv, datetime, pathlib, sys
import yaml

repo = pathlib.Path(sys.argv[1])
oggi = datetime.date.today().isoformat()
datati, una_volta = [], []

datati += [f["url"] for f in yaml.safe_load((repo / "sources.yml").read_text())["fonti"] if f.get("archivia")]
ref = repo / "data" / "reference" / "istituti_dap.csv"
if ref.exists():
    datati += [r["url_scheda"] for r in csv.DictReader(ref.open(encoding="utf-8")) if r.get("url_scheda")]

extra = repo / "archive" / "extra_urls.txt"
if extra.exists():
    una_volta += [l.split("#")[0].split()[0] for l in extra.read_text().splitlines() if l.split("#")[0].strip()]
rassegne = [repo / "data" / "rassegna" / "documenti.csv"]
rassegne += sorted((repo.parent / "carceri-italia-redazione" / "rassegna").glob("*.csv"))
for p in rassegne:
    if p.exists():
        una_volta += [r["url"] for r in csv.DictReader(p.open(encoding="utf-8")) if r.get("url", "").startswith("http")]

urls = [f"{u}#{oggi}" for u in dict.fromkeys(datati)] + [u for u in dict.fromkeys(una_volta) if u not in datati]
print("\n".join(urls))
PY

N="$(wc -l < "$TMP" | tr -d ' ')"
if [ "$PROVA" = "--prova" ]; then
  cat "$TMP"
  echo "--- $N URL (prova: niente archiviato)" >&2
  exit 0
fi

if ! command -v archivebox >/dev/null 2>&1; then
  echo "archivebox non trovato. Installazione: pip install archivebox (oppure Docker)." >&2
  exit 1
fi
echo "Aggiungo $N URL ad ArchiveBox in $DATA_DIR"
cd "$DATA_DIR"
archivebox add --depth=0 --tag=carceri-italia < "$TMP"
