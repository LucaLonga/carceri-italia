"""Serie statistiche del Ministero oltre le capienze (scelte il 2026-11-28, inventario in data/storico/inventario_serie.csv).

Per ogni serie prende dall'inventario (data/storico/inventario_ministero.csv) tutte le voci, scarica le pagine,
salva il grezzo compresso in data/raw/serie/<serie>/ e scrive le tabelle in formato lungo:

  data/serie/<serie>.csv   una riga per cella: voce (data e titolo), tabella, riga, colonna, valore
  data/serie/indice.json   per ogni voce: url, tabelle lette, errori

La tabella si legge come griglia (rowspan e colspan rispettati). Le righe in cima senza numeri sono
l'intestazione: `colonna` le unisce con " | " (es. "Suicidi | per 10.000 presenza media"). `riga` è la prima
cella della riga, `riga_2` la seconda (es. l'istituto quando la prima è la regione). Il titolo della voce sta
nell'indice. Sopra 1 MB il file si divide per anno: data/serie/<serie>/<anno>.csv.
[VERIFICARE le intestazioni di ogni serie sul grezzo prima di usarle.]
Per le detenute madri per istituto c'è in più data/serie/detenute_madri_istituto.csv con il codice DAP.

Uso: python scripts/fetch_serie.py [--solo SERIE] [--aggiorna]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sys

from bs4 import BeautifulSoup

from common import DATA, LIMITE_GIT, get, norm_name, scrivi_gz, to_int

INVENTARIO = DATA / "storico" / "inventario_ministero.csv"
RAW = DATA / "raw" / "serie"
OUT = DATA / "serie"

# nell'ordine di priorità del 2026-11-28; espressione regolare sul titolo della voce
SERIE = [
    ("eventi_critici", r"^Eventi critici negli istituti penitenziari"),
    ("detenute_madri", r"^Detenute madri con figli al seguito"),
    ("pena_residua", r"^Detenuti condannati per pena residua"),
    ("pena_residua_anni", r"^Detenuti per durata della pena residua - Anni"),
    ("ingressi_liberta", r"^Ingressi in carcere dalla libert"),
    ("lavoranti", r"^Detenuti lavoranti(?! per datore| in lavorazioni)"),
    ("lavoranti_datore", r"^Detenuti lavoranti per datore di lavoro"),
    ("lavoranti_serie_storica", r"^Detenuti Lavoranti Serie Storica"),
    ("corsi_professionali", r"^Detenuti inseriti in corsi professionali"),
    ("percorsi_istruzione", r"^Attività trattamentali - Percorsi d'istruzione"),
    ("permessi_premio", r"^Permessi premio concessi ai detenuti"),
    ("usciti_legge_199", r"^Detenuti usciti dagli istituti penitenziari per effetto della legge 199"),
    ("classi_eta", r"^Detenuti per classi di et[àa](?! - Anni)"),
    ("classi_eta_anni", r"^Detenuti per classi di et[àa] - Anni"),
    ("posizione_giuridica_anni", r"^Detenuti presenti per posizione giuridica - Anni"),
    ("posizione_giuridica_regione", r"^Detenuti presenti - aggiornamento al"),  # solo la tabella con la posizione giuridica
    ("madri_asili_nido", r"^Detenute madri e asili nido"),
]
# serie che tengono solo alcune tabelle della pagina: parola che deve comparire nell'intestazione
SOLO_TABELLE = {"posizione_giuridica_regione": "attesa di primo giudizio"}
COLONNE = ["voce_data", "voce_id", "tabella", "riga_n", "riga", "riga_2", "colonna", "valore", "valore_num"]


def nome_file(v: dict) -> str:
    base = v["data"] or re.sub(r"[^a-z0-9]+", "-", v["titolo"].lower()).strip("-")[-60:]
    return f"{base}_{re.sub(r'[^A-Za-z0-9]', '', v['url'].split('contentId=')[-1])}"


def griglia(tb) -> list[list[str]]:
    """Tabella HTML come griglia piena: una cella con rowspan o colspan si ripete in tutte le posizioni che copre."""
    occupate: dict[tuple[int, int], str] = {}
    righe = tb.find_all("tr")
    for i, tr in enumerate(righe):
        j = 0
        for c in tr.find_all(["td", "th"]):
            while (i, j) in occupate:
                j += 1
            testo = " ".join(c.get_text().split())
            rs, cs = int(c.get("rowspan", 1) or 1), int(c.get("colspan", 1) or 1)
            for di in range(rs):
                for dj in range(cs):
                    occupate[(i + di, j + dj)] = testo
            j += cs
    if not occupate:
        return []
    n_r, n_c = max(k[0] for k in occupate) + 1, max(k[1] for k in occupate) + 1
    return [r for r in ([occupate.get((i, j), "") for j in range(n_c)] for i in range(n_r)) if any(r)]


def tabelle_lunghe(html: str, v: dict) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    righe = []
    for n, tb in enumerate(soup.find_all("table"), 1):
        g = griglia(tb)
        if not g:
            continue
        k = 0  # righe d'intestazione: in cima, senza numeri dopo la prima colonna
        while k < len(g) - 1 and not any(numero(x) != "" for x in g[k][1:]):
            k += 1
        k = max(k, 1)
        testa = [" | ".join(dict.fromkeys(x for x in col if x)) for col in zip(*g[:k])]
        for i, r in enumerate(g[k:], 1):
            for j, val in enumerate(r[1:], 1):
                if numero(val) == "" and j < len(r) - 1 and j == 1:
                    continue  # seconda colonna di testo (es. istituto): sta in riga_2
                righe.append({"voce_data": v["data"], "voce_id": v["id"], "tabella": n,
                              "riga_n": i, "riga": r[0], "riga_2": r[1] if len(r) > 2 and numero(r[1]) == "" else "",
                              "colonna": testa[j] if j < len(testa) else f"colonna {j + 1}",
                              "valore": val, "valore_num": numero(val)})
    return righe


def numero(s: str):
    s = (s or "").strip().replace("%", "").strip()
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})*", s):
        return to_int(s)
    if re.fullmatch(r"-?\d+,\d+", s):
        return float(s.replace(",", "."))
    return ""


TIPO_IN_CODA = re.compile(r'(?:(?<=["\s-])|^)(CCF/CRF|CCF|CRF|ICAM|CC|CR|CL|IP)$')
COLONNE_MADRI = ["data", "regione", "istituto", "codice_dap", "italiane_presenti", "italiane_figli",
                 "straniere_presenti", "straniere_figli", "totale_presenti", "totale_figli", "nota"]


def chiavi_nome(s: str) -> tuple[str, str, str]:
    """(nome completo, nome senza la dedica tra virgolette, tipo in coda): senza punteggiatura né spazi,
    tolti i "0" e "-" spuri delle tabelle."""
    s = norm_name(s).replace("“", '"').replace("”", '"')
    s = re.sub(r'(?<=[A-Z"])0\b', " ", s)  # zero spurio attaccato al nome ("FOGGIA0")
    s = " ".join(x for x in s.split() if x not in ("0", "-"))
    m = TIPO_IN_CODA.search(s.strip())
    tipo = m.group(1) if m else ""
    if m:
        s = s[: m.start()].strip(" -")
    def alnum(x: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", x)
    return alnum(s), alnum(re.sub(r'"[^"]*"', " ", s)), tipo


def madri_per_istituto(righe: list[dict]) -> list[dict]:
    """Detenute madri e figli al seguito per istituto, con il codice DAP dalla tabella di raccordo: nome
    completo, poi nome senza dedica; a parità di nome decide il tipo (Trani CC / CRF)."""
    ref = list(csv.DictReader((DATA / "reference" / "istituti.csv").open(encoding="utf-8")))
    pieni: dict[str, set] = {}
    corti: dict[str, set] = {}
    tipo_di = {r["codice_dap"]: r["tipo"] for r in ref}
    for r in ref:
        for nome in [r["nome_ministero"], *filter(None, r["alias_ministero"].split(";"))]:
            k1, k2, _ = chiavi_nome(nome)
            pieni.setdefault(k1, set()).add(r["codice_dap"])
            corti.setdefault(k2, set()).add(r["codice_dap"])
    out: dict[tuple, dict] = {}
    for r in righe:
        parti = [x.lower() for x in r["colonna"].split(" | ")]
        if len(parti) != 2 or parti[0] not in ("italiane", "straniere", "totale") or not r["riga_2"] \
                or r["riga_2"].lower() == "totale":
            continue
        col = f"{parti[0]}_{'figli' if 'figli' in parti[1] else 'presenti'}"
        k = (r["voce_data"], r["riga"], r["riga_2"])
        out.setdefault(k, {"data": r["voce_data"], "regione": r["riga"], "istituto": r["riga_2"]})[col] = r["valore_num"]
    risultato = []
    for (_, _, nome), x in sorted(out.items()):
        k1, k2, tipo = chiavi_nome(nome)
        codici = pieni.get(k1) or corti.get(k2) or set()
        if len(codici) > 1 and tipo:
            codici = {c for c in codici if tipo_di.get(c) == tipo} or codici
        x["codice_dap"] = next(iter(codici)) if len(codici) == 1 else ""
        x["nota"] = "" if len(codici) == 1 else ("nome ambiguo" if codici else "nome non abbinato [VERIFICARE]")
        risultato.append(x)
    return risultato


def scrivi_serie(sid: str, righe: list[dict]) -> None:
    """data/serie/<sid>.csv; se supera il limite di git, una cartella con un file per anno."""
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLONNE, lineterminator="\n")
    w.writeheader()
    w.writerows(righe)
    for vecchio in [OUT / f"{sid}.csv", *sorted((OUT / sid).glob("*.csv"))]:
        vecchio.unlink(missing_ok=True)
    if len(buf.getvalue().encode("utf-8")) <= LIMITE_GIT:
        (OUT / f"{sid}.csv").write_text(buf.getvalue(), encoding="utf-8")
        return
    (OUT / sid).mkdir(exist_ok=True)
    per_anno: dict[str, list[dict]] = {}
    for r in righe:
        per_anno.setdefault((r["voce_data"] or "senza-data")[:4], []).append(r)
    for anno, rr in per_anno.items():
        with (OUT / sid / f"{anno}.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLONNE, lineterminator="\n")
            w.writeheader()
            w.writerows(rr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo")
    ap.add_argument("--aggiorna", action="store_true", help="riscarica anche le pagine già salvate")
    a = ap.parse_args()
    voci = list(csv.DictReader(INVENTARIO.open(encoding="utf-8")))
    OUT.mkdir(parents=True, exist_ok=True)
    indice_p = OUT / "indice.json"
    indice = json.loads(indice_p.read_text(encoding="utf-8")) if indice_p.exists() else {}
    for sid, pat in SERIE:
        if a.solo and sid != a.solo:
            continue
        mie = sorted((v for v in voci if re.search(pat, v["titolo"], re.I)), key=lambda v: (v["data"], v["titolo"]))
        for v in mie:
            v["id"] = nome_file(v)
        tutte, info = [], []
        for v in mie:
            p = RAW / sid / f"{nome_file(v)}.html.gz"
            try:
                if p.exists() and not a.aggiorna:
                    html = gzip.decompress(p.read_bytes()).decode("utf-8")
                else:
                    html = get(v["url"], pause=1.5).text
                    p.parent.mkdir(parents=True, exist_ok=True)
                    scrivi_gz(p, html)
                righe = tabelle_lunghe(html, v)
                if sid in SOLO_TABELLE:
                    tenute = {r["tabella"] for r in righe if SOLO_TABELLE[sid] in r["colonna"].lower()}
                    righe = [r for r in righe if r["tabella"] in tenute]
                tutte += righe
                info.append({"voce_id": v["id"], "data": v["data"], "titolo": v["titolo"], "url": v["url"], "celle": len(righe),
                             "errori": [] if righe else ["nessuna tabella letta"]})
            except Exception as e:  # noqa: BLE001
                info.append({"data": v["data"], "titolo": v["titolo"], "url": v["url"], "errori": [str(e)]})
        scrivi_serie(sid, tutte)
        if sid == "detenute_madri":
            m = madri_per_istituto(tutte)
            with (OUT / "detenute_madri_istituto.csv").open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=COLONNE_MADRI)
                w.writeheader()
                w.writerows(m)
        indice[sid] = {"voci": len(mie), "celle": len(tutte), "voci_con_errori": sum(bool(i["errori"]) for i in info),
                       "dettaglio": info}
        print(f"{sid}: {len(mie)} voci, {len(tutte)} celle, errori in {indice[sid]['voci_con_errori']} voci", flush=True)
    indice_p.write_text(json.dumps(indice, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
