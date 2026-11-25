#!/usr/bin/env bash
# Terza copia delle fonti, in locale, con ArchiveBox (https://archivebox.io).
# Da lanciare sul proprio computer, non su GitHub Actions.
#
#   ARCHIVEBOX_DATA=~/ArchiveBoxData ./scripts/archivebox_local.sh
#
# Legge archive/urls.txt (prodotto da archive_sources.py) e archive/extra_urls.txt,
# e li aggiunge all'archivio ArchiveBox indicato. Con --depth=0 salva solo la pagina,
# non i link che contiene.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="${ARCHIVEBOX_DATA:-$HOME/ArchiveBoxData}"

if ! command -v archivebox >/dev/null 2>&1; then
  echo "archivebox non trovato. Installazione: pip install archivebox (oppure Docker)." >&2
  exit 1
fi

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT
python3 - "$REPO" > "$TMP" <<'PY'
import sys, yaml, pathlib
repo = pathlib.Path(sys.argv[1])
urls = [f["url"] for f in yaml.safe_load((repo / "sources.yml").read_text())["fonti"] if f.get("archivia")]
extra = repo / "archive" / "extra_urls.txt"
if extra.exists():
    urls += [l.split("#")[0].split()[0] for l in extra.read_text().splitlines() if l.split("#")[0].strip()]
print("\n".join(dict.fromkeys(urls)))
PY

echo "Aggiungo $(wc -l < "$TMP" | tr -d ' ') URL ad ArchiveBox in $DATA_DIR"
cd "$DATA_DIR"
archivebox add --depth=0 --tag=carceri-italia < "$TMP"
