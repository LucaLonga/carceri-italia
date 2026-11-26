"""Data loader: indirizzi che dipendono dal nome utente GitHub, senza scriverlo nel codice.
In GitHub Actions il nome arriva da GITHUB_REPOSITORY_OWNER; in locale da SITO_UTENTE (facoltativo)."""
import json
import os
import sys

utente = os.environ.get("SITO_UTENTE") or os.environ.get("GITHUB_REPOSITORY_OWNER") or ""
json.dump({
    "utente": utente or None,
    "repository": f"https://github.com/{utente}/carceri-italia" if utente else None,
    "sito": f"https://{utente.lower()}.github.io/carceri-italia/" if utente else None,
    "poster_2024": "https://lucalonga.com/projects/dv-24-01",
}, sys.stdout, ensure_ascii=False)
if not utente:
    print("[ambiente.json] nome utente non impostato: link al repository omessi", file=sys.stderr)
