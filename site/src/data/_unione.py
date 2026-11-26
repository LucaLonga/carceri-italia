"""Unione dei dati per istituto: modulo comune ai data loader del sito.

Legge solo file del repository (data/). Non inventa valori: dove manca un dato scrive None
e aggiunge una riga all'elenco `avvisi`, che i loader stampano su stderr.

Metrica (docs/metodo-bozza.md):
    posti_disp       = posti_reg - posti_non_disp
    stanze_disp      = stanze - stanze_non_disp
    superficie_lorda = 9 * stanze_disp + 5 * (posti_disp - stanze_disp)   [ipotesi]
    m2_lordi_persona = superficie_lorda / presenti                        [calcolato]
    persone_stanza   = presenti / stanze_disp                             [calcolato]
    affollamento_reale = presenti / posti_disp                            [calcolato]
Il limite basso della banda (meno l'arredo) si calcola nel browser: site/src/components/metrica.js.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]          # radice del repository
DATA = ROOT / "data"


def _carica_norm_name():
    """Prende norm_name da scripts/common.py senza importare il modulo (che richiede `requests`):
    una sola definizione, la stessa usata dalla raccolta."""
    import ast
    import unicodedata
    src = (ROOT / "scripts" / "common.py").read_text(encoding="utf-8")
    nodo = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "norm_name")
    spazio = {"re": re, "unicodedata": unicodedata}
    exec(compile(ast.Module(body=[nodo], type_ignores=[]), "scripts/common.py", "exec"), spazio)
    return spazio["norm_name"]


norm_name = _carica_norm_name()

SCHEDE_DIR = DATA / "raw" / "schede-trasparenza"
MIN_DIR = DATA / "raw" / "ministero"
REF = DATA / "reference" / "istituti.csv"
ANTIGONE = DATA / "manual" / "antigone"
CHECKS = DATA / "checks" / "ultimo.md"
ANT_DIR = DATA / "antigone"

NUM_SCHEDE = ["posti_reg", "posti_non_disp", "presenti", "stanze", "stanze_non_disp",
              "st_doccia", "st_bidet", "st_handicap", "st_wc_porta", "st_luce", "st_prese",
              "pp_eff", "pp_prev", "edu_eff", "edu_prev"]
NUM_MIN = ["capienza_regolamentare", "presenti", "donne", "stranieri"]
RE_DATA = re.compile(r"^(\d{4}-\d{2}-\d{2})_")


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def to_int(v) -> int | None:
    v = (v or "").strip().replace(".", "")
    if v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None


def data_it_a_iso(v: str) -> str | None:
    """'24/11/2026' -> '2026-11-24'."""
    try:
        return datetime.strptime(v.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return None


def leggi_riferimento(avvisi: list[str]) -> list[dict]:
    if not REF.exists():
        avvisi.append(f"manca {rel(REF)}: nessun istituto")
        return []
    with REF.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def codici(r: dict) -> list[str]:
    return [c for c in (r["codici_dap_sezioni"] or r["codice_dap"]).split(";") if c]


def leggi_schede(path: Path, avvisi: list[str]) -> dict[str, dict]:
    if not path.exists():
        avvisi.append(f"manca {rel(path)}")
        return {}
    with path.open(encoding="utf-8") as f:
        return {r["code"]: r for r in csv.DictReader(f, delimiter=";")}


def somma_schede(righe: list[dict]) -> dict:
    """Somma le schede di più sezioni (San Vittore). Un campo vuoto in una sezione rende vuoto il totale."""
    out = {}
    for k in NUM_SCHEDE:
        vals = [to_int(r.get(k)) for r in righe]
        out[k] = None if any(v is None for v in vals) else sum(vals)
    for k in ("agg_capienza", "agg_spazi"):
        date = sorted(d for d in (data_it_a_iso(r.get(k, "")) for r in righe) if d)
        out[k] = date[0] if date else None          # la più vecchia: il dato è aggiornato almeno a quella data
    return out


def metrica(s: dict) -> dict:
    """Calcoli dello spazio. Restituisce anche `casi`: i casi limite incontrati."""
    pr, pn, p, st, sn = (s.get(k) for k in ("posti_reg", "posti_non_disp", "presenti", "stanze", "stanze_non_disp"))
    casi = []
    if None in (pr, pn, p, st, sn):
        return {"posti_disp": None, "stanze_disp": None, "superficie_lorda": None,
                "m2_lordi_persona": None, "persone_stanza": None, "affollamento_reale": None,
                "casi": ["dati_incompleti"]}
    posti_disp = pr - pn
    stanze_disp = st - sn
    if posti_disp <= 0:
        casi.append("posti_tutti_non_disponibili")
    if stanze_disp <= 0:
        casi.append("nessuna_stanza_disponibile")
    if p == 0:
        casi.append("nessun_presente")
    if 0 < posti_disp < stanze_disp:
        casi.append("piu_stanze_che_posti")       # la formula darebbe meno di 9 m² per stanza
    sup = 9 * stanze_disp + 5 * (posti_disp - stanze_disp) if posti_disp > 0 and stanze_disp > 0 else None
    return {
        "posti_disp": posti_disp,
        "stanze_disp": stanze_disp,
        "superficie_lorda": sup,
        "m2_lordi_persona": round(sup / p, 4) if sup is not None and p > 0 else None,
        "persone_stanza": round(p / stanze_disp, 4) if stanze_disp > 0 and p > 0 else (0 if p == 0 and stanze_disp > 0 else None),
        "affollamento_reale": round(p / posti_disp, 4) if posti_disp > 0 else None,
        "casi": casi,
    }


def file_datati(cartella: Path, suffisso: str) -> list[tuple[str, Path]]:
    out = []
    for p in sorted(cartella.glob(f"*{suffisso}")):
        m = RE_DATA.match(p.name)
        if m:
            out.append((m.group(1), p))
    return out


def chiavi_ministero(r: dict) -> list[tuple[str, str]]:
    nomi = [r["nome_ministero"]] + [a for a in (r["alias_ministero"] or "").split(";") if a]
    return [(norm_name(n), r["tipo"].strip().upper()) for n in nomi]


def leggi_ministero(ref: list[dict], avvisi: list[str]) -> tuple[dict, dict]:
    """Restituisce ({data: {codice_dap: riga}}, indice.json)."""
    indice = {}
    ip = MIN_DIR / "indice.json"
    if ip.exists():
        indice = json.loads(ip.read_text(encoding="utf-8"))
    else:
        avvisi.append(f"manca {rel(ip)}")
    mappa = {}
    for r in ref:
        for k in chiavi_ministero(r):
            if k in mappa and mappa[k] != r["codice_dap"]:
                avvisi.append(f"chiave Ministero ambigua {k}: {mappa[k]} e {r['codice_dap']}")
            mappa[k] = r["codice_dap"]
    # Secondo tentativo per i nomi storici: stesso nome senza la dedica tra virgolette, stesso tipo,
    # solo se l'abbinamento è unico (es. 'POTENZA "ANTONIO SANTORO"' -> 'POTENZA').
    def senza_dedica(n: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r'"[^"]*"|“[^”]*”', " ", n)).strip()
    base: dict[tuple[str, str], set[str]] = {}
    for r in ref:
        for n, t in chiavi_ministero(r):
            base.setdefault((senza_dedica(n), t), set()).add(r["codice_dap"])
    non_collegati: dict[tuple[str, str], list[str]] = {}
    # Alias storici scritti a mano (data/reference/alias_ministero_storici.csv): nomi o tipi cambiati
    # nel tempo; "nessuno" = istituto non presente nella tabella di raccordo (righe ignorate di proposito).
    ignorati = set()
    pa = DATA / "reference" / "alias_ministero_storici.csv"
    if pa.exists():
        for r in csv.DictReader(pa.open(encoding="utf-8")):
            k = (norm_name(r["nome_ministero"]), r["tipo"].strip().upper())
            if r["codice_dap"].strip() == "nessuno":
                ignorati.add(k)
            else:
                mappa[k] = r["codice_dap"].strip()
    mesi = {}
    # Tabelle mensili: quelle della raccolta (data/raw/ministero) e quelle rilette dallo storico
    # (data/storico/per_istituto_mensile.csv, dal 2019). A parità di data vale la raccolta.
    sorgenti: dict[str, list[dict]] = {}
    storico = DATA / "storico" / "per_istituto_mensile.csv"
    if storico.exists():
        with storico.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                sorgenti.setdefault(row["data"], []).append(row)
    vuote = []
    for data, p in file_datati(MIN_DIR, "_capienze-per-istituto.csv"):
        with p.open(encoding="utf-8") as f:
            righe_file = list(csv.DictReader(f))
        if righe_file:
            sorgenti[data] = righe_file
        else:
            vuote.append(data)
    if vuote:
        avvisi.append(f"Ministero: {len(vuote)} tabelle mensili vuote in {rel(MIN_DIR)} (ignorate; vedi fetch_storico.py)")
    if not sorgenti:
        avvisi.append(f"nessuna tabella mensile in {rel(MIN_DIR)}")
    for data in sorted(sorgenti):
        righe = {}
        if True:
            for row in sorgenti[data]:
                k = (norm_name(row["istituto"]), row["tipo"].strip().upper())
                cod = mappa.get(k)
                if cod is None:
                    cand = base.get((senza_dedica(k[0]), k[1]), set())
                    cod = next(iter(cand)) if len(cand) == 1 else None
                if cod is None and k in ignorati:
                    continue
                if cod is None:
                    non_collegati.setdefault((row["istituto"], row["tipo"]), []).append(data)
                    continue
                righe[cod] = {k2: to_int(row.get(k2)) for k2 in NUM_MIN}
        mancanti = [r["codice_dap"] for r in ref if r["codice_dap"] not in righe]
        if mancanti and data == max(sorgenti):
            avvisi.append(f"Ministero {data}: {len(mancanti)} istituti senza riga ({', '.join(mancanti[:10])})")
        mesi[data] = righe
    for (nome, tipo), date in sorted(non_collegati.items()):
        avvisi.append(f"Ministero: '{nome}' ({tipo}) non collegato a istituti.csv in {len(date)} tabelle (dal {date[0]} al {date[-1]})")
    return mesi, indice


def leggi_antigone(avvisi: list[str]) -> dict | None:
    """Esiti aggregati delle visite: legge la prima tabella e l'intestazione del file più recente."""
    files = sorted(ANTIGONE.glob("osservatorio_*.md"))
    if not files:
        avvisi.append(f"nessun file osservatorio_*.md in {rel(ANTIGONE)}")
        return None
    p = files[-1]
    testo = p.read_text(encoding="utf-8")
    meta = {}
    m = re.match(r"^---\n(.*?)\n---", testo, re.S)
    if m:
        for riga in m.group(1).splitlines():
            if ":" in riga:
                k, v = riga.split(":", 1)
                meta[k.strip()] = v.strip()
    visite = re.search(r"Visite dell'Osservatorio negli ultimi 12 mesi:\s*(\d+)", testo)
    domande = []
    for riga in testo.splitlines():
        c = [x.strip() for x in riga.strip().strip("|").split("|")]
        if len(c) == 4 and c[0] not in ("Domanda",) and not set(c[0]) <= set("-: "):
            domande.append({"domanda": c[0], "si": to_int(c[1]), "no": to_int(c[2]), "nd": to_int(c[3])})
    return {"file": rel(p), "visite": int(visite.group(1)) if visite else None, "meta": meta, "domande": domande}


def leggi_visite_antigone(avvisi: list[str]) -> dict[str, dict]:
    """Visite dell'Osservatorio per codice DAP (abbinamento in data/antigone/abbinamento.csv).
    Solo campi fattuali; gli eventi critici non entrano nel sito."""
    va, ab = ANT_DIR / "visite.csv", ANT_DIR / "abbinamento.csv"
    if not va.exists() or not ab.exists():
        avvisi.append(f"mancano {rel(va)} o {rel(ab)}: nessun dato Antigone per istituto")
        return {}
    cod = {r["scheda_id"]: r["codice_dap"] for r in csv.DictReader(ab.open(encoding="utf-8")) if r["codice_dap"]}
    out: dict[str, dict] = {}
    for v in csv.DictReader(va.open(encoding="utf-8")):
        c = cod.get(v["scheda_id"])
        if not c or not v["data_visita"]:
            continue
        o = out.setdefault(c, {"scheda_id": v["scheda_id"], "url_scheda": v["url_scheda"], "visite": []})
        o["visite"].append({
            "data": v["data_visita"], "url": v["url_foglio"],
            "presenti": to_int(v["presenti_visita"]), "capienza": to_int(v["capienza_visita"]),
            "tre_mq": v["tre_mq_calpestabili"] or None, "riscaldamento": v["riscaldamento"] or None,
            "acqua_calda": v["acqua_calda"] or None, "wc_separato": v["wc_separato"] or None,
            "doccia": v["doccia_in_cella"] or None, "costruzione": v["anno_costruzione"] or None,
            "pp": [to_int(v["pp_prevista"]), to_int(v["pp_presente"])],
            "celle": [to_int(v["celle_posti_previsti"]), to_int(v["celle_persone"])] if v["celle_persone"] else None,
        })
    for o in out.values():
        o["visite"].sort(key=lambda x: x["data"])
    non = ANT_DIR / "non_abbinati.csv"
    if non.exists():
        n = sum(1 for _ in csv.DictReader(non.open(encoding="utf-8")))
        if n:
            avvisi.append(f"Antigone: {n} schede non abbinate (data/antigone/non_abbinati.csv)")
    return out


def ultima_raccolta() -> str | None:
    if not CHECKS.exists():
        return None
    m = re.search(r"Controlli del (\d{4}-\d{2}-\d{2})", CHECKS.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def unisci() -> dict:
    avvisi: list[str] = []
    ref = leggi_riferimento(avvisi)
    latest_path = SCHEDE_DIR / "latest.csv"
    schede = leggi_schede(latest_path, avvisi)
    mesi, indice = leggi_ministero(ref, avvisi)
    ultimo_mese = max(mesi) if mesi else None
    antigone_ist = leggi_visite_antigone(avvisi)

    usati = set()
    istituti = []
    for r in ref:
        cods = codici(r)
        righe = []
        for c in cods:
            if c in schede:
                righe.append(schede[c])
                usati.add(c)
            else:
                avvisi.append(f"{r['codice_dap']} ({r['nome_scheda_dap']}): manca la scheda {c} in latest.csv")
        s = somma_schede(righe) if righe and len(righe) == len(cods) else None
        calc = metrica(s) if s else metrica({})
        m = mesi.get(ultimo_mese, {}).get(r["codice_dap"]) if ultimo_mese else None
        lat, lon = to_float(r["lat_dap"]), to_float(r["lon_dap"])
        if lat is None or lon is None:
            avvisi.append(f"{r['codice_dap']}: coordinate DAP mancanti")
        istituti.append({
            "codice": r["codice_dap"],
            "codici_sezioni": cods,
            "id": r["id"],
            "nome": r["nome_scheda_dap"] or r["nome_ministero"],
            "nomi": {
                "ministero": r["nome_ministero"],
                "alias_ministero": [a for a in (r["alias_ministero"] or "").split(";") if a],
                "dap": r["nome_scheda_dap"],
                "antigone": r["nome_antigone"],
            },
            "tipo": r["tipo"],
            "tipo_esteso": r["tipo_esteso"],
            "regione": r["regione"],
            "provincia": r["sigla_prov_attuale"] or r["provincia"],
            "lat": lat,
            "lon": lon,
            "coord_da_verificare": r["coord_da_verificare"].strip().lower() == "si",
            "distanza_coord_km": to_float(r["distanza_coord_km"]),
            "note_qualita": r["note_qualita"] or None,
            "scheda": s,
            "ministero": ({"data": ultimo_mese, **m} if m else None),
            "calc": calc,
            "visite_antigone": antigone_ist.get(r["codice_dap"]),
        })
    for c in sorted(set(schede) - usati):
        avvisi.append(f"scheda {c} ({schede[c].get('titolo')}) in latest.csv ma non in istituti.csv")
    for i in istituti:
        if "piu_stanze_che_posti" in i["calc"]["casi"]:
            avvisi.append(f"{i['codice']}: più stanze disponibili che posti disponibili")

    date_schede = sorted({i["scheda"]["agg_capienza"] for i in istituti if i["scheda"] and i["scheda"]["agg_capienza"]})
    return {
        "generato": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fonti": {
            "schede": {"file": rel(latest_path), "data_min": date_schede[0] if date_schede else None,
                       "data_max": date_schede[-1] if date_schede else None},
            "ministero": {"data": ultimo_mese,
                          "file": rel(MIN_DIR / f"{ultimo_mese}_capienze-per-istituto.csv") if ultimo_mese else None,
                          "url": (indice.get(ultimo_mese) or {}).get("url"),
                          "scaricato": (indice.get(ultimo_mese) or {}).get("scaricato"),
                          "totale_dichiarato": (indice.get(ultimo_mese) or {}).get("totale_dichiarato"),
                          "nota_capienza": (indice.get(ultimo_mese) or {}).get("nota_capienza")},
            "riferimento": rel(REF),
            "ultima_raccolta": ultima_raccolta(),
        },
        "antigone": leggi_antigone(avvisi),
        "avvisi": avvisi,
        "istituti": istituti,
    }


def to_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def stampa_avvisi(avvisi: list[str], nome: str) -> None:
    if avvisi:
        print(f"[{nome}] {len(avvisi)} avvisi:", file=sys.stderr)
        for a in avvisi:
            print("  -", a, file=sys.stderr)
    else:
        print(f"[{nome}] nessun avviso", file=sys.stderr)
