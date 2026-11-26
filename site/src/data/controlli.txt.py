"""Data loader: testo dei controlli dell'ultima raccolta (data/checks/ultimo.md), per la pagina di metodo."""
import sys

from _unione import CHECKS, rel

if CHECKS.exists():
    sys.stdout.write(CHECKS.read_text(encoding="utf-8"))
else:
    print(f"[controlli.txt] manca {rel(CHECKS)}", file=sys.stderr)
    sys.stdout.write(f"Esito dei controlli non disponibile: manca {rel(CHECKS)}.\n")
