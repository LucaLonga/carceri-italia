#!/usr/bin/env bash
# Raccolta sul Mac: alternativa a .github/workflows/raccolta.yml se i server di GitHub non raggiungono
# giustizia.it. Stessi script, stesso messaggio di commit, poi push su main.
#
#   ./scripts/raccolta_locale.sh [tutto|schede|ministero|archivio|auto]
#
# "auto" (quello che usa launchd) fa come il calendario del workflow:
#   lunedì → schede trasparenza;  giorno 12 → tabelle mensili e archivio delle fonti.
# Serve il virtualenv del repository: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PY="$REPO/.venv/bin/python"
COSA="${1:-auto}"
cd "$REPO"

if [ "$COSA" = "auto" ]; then
  COSA=""
  [ "$(date +%u)" = "1" ] && COSA="schede"
  [ "$(date +%d)" = "12" ] && COSA="${COSA:+$COSA,}ministero,archivio"
  if [ -z "$COSA" ]; then echo "oggi niente da raccogliere"; exit 0; fi
fi
fa() { [ "$COSA" = "tutto" ] || [[ ",$COSA," == *",$1,"* ]]; }

git checkout main
git pull --ff-only

cd scripts
errori=0
fa schede    && { "$PY" fetch_schede.py && "$PY" estrai_attivita.py || errori=1; }
fa ministero && { "$PY" fetch_ministero.py || errori=1; }
fa archivio  && { "$PY" archive_sources.py || true; }   # la Wayback non deve bloccare i dati
"$PY" checks.py || errori=1
cd "$REPO"

git add data archive
if git diff --cached --quiet; then
  echo "Nessun cambiamento."
else
  git commit -m "dati: raccolta del $(date -u +%Y-%m-%d)"
  git push
fi
exit $errori
