#!/usr/bin/env bash
# Servizio settimanale di ArchiveBox (launchd): tutto sul disco interno, mai il repository di lavoro.
#
#   ~/Library/Application Support/carceri-italia/
#     archivebox_servizio.sh      questo script (copiato qui all'installazione)
#     carceri-italia/             clone del repository pubblico (solo lettura: fetch + reset, mai commit né push)
#     carceri-italia-redazione/   clone del privato, per gli URL della rassegna stampa
#     venv/                       Python con pyyaml, per l'elenco degli URL
#   ~/ArchiveBoxData              archivio ArchiveBox
#
# A ogni giro: se un clone manca lo crea; poi git fetch + git reset --hard origin/main; poi
# carceri-italia/scripts/archivebox_local.sh. Niente sul volume esterno: niente permessi speciali.
# Con --prova aggiorna i cloni e stampa solo il numero di URL, senza archiviare.
set -euo pipefail

BASE="$HOME/Library/Application Support/carceri-italia"
export ARCHIVEBOX_DATA="$HOME/ArchiveBoxData"
export PATH="$BASE/venv/bin:$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/Library/Frameworks/Python.framework/Versions/Current/bin:/usr/bin:/bin"
mkdir -p "$BASE"
echo "=== $(date '+%Y-%m-%d %H:%M:%S') servizio ArchiveBox"

aggiorna() {  # $1 = nome del repository su GitHub, $2 = cartella del clone
  if [ ! -d "$2/.git" ]; then
    git clone --quiet "https://github.com/LucaLonga/$1.git" "$2"
  fi
  git -C "$2" fetch --quiet origin main
  git -C "$2" reset --quiet --hard origin/main
  echo "$1: $(git -C "$2" log -1 --format='%h %cd' --date=short)"
}
aggiorna carceri-italia "$BASE/carceri-italia"
# il privato serve solo per l'elenco degli URL: se non si riesce ad aggiornarlo si va avanti senza
aggiorna carceri-italia-redazione "$BASE/carceri-italia-redazione" || echo "privato non aggiornato: proseguo senza"

if [ ! -x "$BASE/venv/bin/python" ]; then
  python3 -m venv "$BASE/venv"
  "$BASE/venv/bin/pip" install --quiet pyyaml
fi

command -v archivebox >/dev/null || { echo "archivebox non trovato nel PATH" >&2; exit 1; }
"$BASE/carceri-italia/scripts/archivebox_local.sh" "${1:-}" | { [ "${1:-}" = "--prova" ] && tail -0 || cat; }
echo "=== $(date '+%Y-%m-%d %H:%M:%S') fine"
