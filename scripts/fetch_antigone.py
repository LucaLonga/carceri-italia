"""Schede dell'Osservatorio di Antigone sulle condizioni di detenzione, istituto per istituto.

Fonte principale: i fogli Google pubblicati ("pubhtml") collegati in fondo a ogni scheda, uno per
visita (2017-2025). Si scaricano in CSV e si leggono per etichetta. Il parsing dell'HTML della scheda
serve solo a trovare i fogli e il nome dell'istituto (ripiego: se una scheda non ha fogli resta
senza visite e finisce negli avvisi).

Regole:
- robots.txt di antigone.it non vieta /osservatorio_detenzione/ (controllato a ogni avvio);
- user agent con il link al repository, pausa tra le richieste (--pausa, default 1,5 s);
- il grezzo si salva sempre, in data/raw-locale/antigone/ (fuori da git: antigone.it non dichiara
  una licenza di riuso; nel repository vanno solo i campi fattuali estratti, con il link alla fonte);
- i testi liberi delle schede (descrizioni, condizioni) non si copiano nei file pubblici.

Uscite (data/antigone/):
  schede.csv          una riga per scheda: id, nome, regione, url, numero di fogli trovati
  visite.csv          una riga per visita: data, presenze e capienza, 3 m², docce, wc, riscaldamento,
                      acqua calda, anno di costruzione, personale, celle (numeri estratti dal testo)
  eventi_critici.csv  autolesionismo, suicidi, tentati suicidi, morti, isolamento: raccolti per una
                      parte futura, NON mostrati nel sito
  indice.json         data, conteggi, errori della raccolta

Uso:
  python fetch_antigone.py                 # tutto (usa i fogli già scaricati se ci sono)
  python fetch_antigone.py --aggiorna      # riscarica anche i fogli già presenti
  python fetch_antigone.py --limite 3      # prova veloce: prime 3 schede
  python fetch_antigone.py --solo-parsing  # rilegge solo il grezzo locale, senza rete
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html as htmlmod
import io
import json
import re
import sys
import time
import unicodedata
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "antigone"
RAW = ROOT / "data" / "raw-locale" / "antigone"
BASE = "https://www.antigone.it"
INDICE = f"{BASE}/osservatorio_detenzione/regioni"
UA = "carceri-italia/0.2 (+https://github.com/LucaLonga/carceri-italia; ricerca e giornalismo sui dati pubblici)"

sessione = requests.Session()
sessione.headers.update({"User-Agent": UA, "Accept-Language": "it-IT,it;q=0.9"})
PAUSA = 1.5


def oggi() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def scarica(url: str, tentativi: int = 3) -> requests.Response:
    for k in range(1, tentativi + 1):
        try:
            r = sessione.get(url, timeout=60)
            r.raise_for_status()
            time.sleep(PAUSA)
            return r
        except requests.RequestException:
            if k == tentativi:
                raise
            time.sleep(PAUSA * 2 * k)
    raise RuntimeError("non raggiungibile")


def controlla_robots() -> None:
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(f"{BASE}/robots.txt")
    rp.read()
    if not rp.can_fetch(UA, INDICE):
        sys.exit("robots.txt di antigone.it vieta /osservatorio_detenzione/: raccolta interrotta")


def testo(s: str) -> str:
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", htmlmod.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


# --- indice e schede ---------------------------------------------------------

def regioni(pagina: str) -> list[str]:
    esclusi = {"regioni", "chi-siamo", "login"}
    slug = re.findall(r'href="/osservatorio_detenzione/([a-z\-]+)"', pagina)
    return sorted({s for s in slug if s not in esclusi})


def schede_regione(pagina: str, regione: str) -> list[str]:
    return sorted(set(re.findall(rf'href="(/osservatorio_detenzione/{regione}/\d+-[^"#?]+)"', pagina)))


def fogli_scheda(pagina: str) -> list[dict]:
    """Collegamenti ai fogli Google con l'anno indicato nel testo che li precede."""
    out = []
    for m in re.finditer(r'https://docs\.google\.com/spreadsheets/d/(e/)?([A-Za-z0-9_\-]+)/pub(?:html)?\?([^"\']*)', pagina):
        gid = re.search(r"gid=(\d+)", htmlmod.unescape(m.group(3)))
        prima = testo(pagina[max(0, m.start() - 800):m.start()])
        anno = re.findall(r"visita svolta nel (\d{4})", prima)
        out.append({
            "pubblicato": bool(m.group(1)),
            "chiave": m.group(2),
            "gid": gid.group(1) if gid else "0",
            "anno_etichetta": anno[-1] if anno else "",
        })
    # un foglio può comparire due volte (link + iframe): tieni la prima occorrenza
    visti, unici = set(), []
    for f in out:
        k = (f["chiave"], f["gid"])
        if k not in visti:
            visti.add(k)
            unici.append(f)
    return unici


def url_csv(f: dict) -> str:
    pre = "e/" if f["pubblicato"] else ""
    return f"https://docs.google.com/spreadsheets/d/{pre}{f['chiave']}/pub?gid={f['gid']}&single=true&output=csv"


def url_pubhtml(f: dict) -> str:
    pre = "e/" if f["pubblicato"] else ""
    return f"https://docs.google.com/spreadsheets/d/{pre}{f['chiave']}/pubhtml?gid={f['gid']}&single=true"


# --- lettura dei fogli -------------------------------------------------------

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.replace("\xa0", " ").replace("\xad", ""))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", s).strip()


class Foglio:
    def __init__(self, testo_csv: str):
        self.righe = [[c.strip() for c in r] for r in csv.reader(io.StringIO(testo_csv))]
        self.celle = [[(j, c) for j, c in enumerate(r) if c] for r in self.righe]

    def valore(self, *etichette: str) -> str | None:
        """Prima cella non vuota dopo la cella che inizia con una delle etichette."""
        for etichetta in etichette:
            e = norm(etichetta)
            for celle in self.celle:
                for k, (_, c) in enumerate(celle):
                    if norm(c).startswith(e):
                        dopo = [x for _, x in celle[k + 1:]]
                        return dopo[0] if dopo else None
        return None

    def testo_sotto(self, etichetta: str) -> str | None:
        """Testo libero nella riga sotto un'etichetta (usato solo per estrarre numeri)."""
        e = norm(etichetta)
        for i, celle in enumerate(self.celle):
            if celle and norm(celle[0][1]).startswith(e):
                for r in self.celle[i + 1:i + 3]:
                    if r and len(r[0][1]) > 20:
                        return r[0][1]
        return None


def intero(v: str | None) -> int | None:
    if v is None:
        return None
    v = v.replace(".", "").replace(" ", "")
    m = re.fullmatch(r"(\d+)", v)
    return int(m.group(1)) if m else None


def si_no(v: str | None) -> str | None:
    if not v:
        return None
    v = norm(v)
    if v.startswith("si"):
        return "si"
    if v.startswith("no"):
        return "no"
    if v in {"nd", "n.d.", "n/d"}:
        return "nd"
    return None


def data_iso(v: str | None) -> str | None:
    if not v:
        return None
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(v.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


NUMERI = {"una": 1, "uno": 1, "singol": 1, "due": 2, "doppi": 2, "tre": 3, "quattro": 4, "cinque": 5, "sei": 6,
          "sette": 7, "otto": 8, "nove": 9, "dieci": 10}


def num_parola(s: str) -> int | None:
    s = s.lower()
    if s.isdigit():
        return int(s)
    for k, v in NUMERI.items():
        if s.startswith(k):
            return v
    return None


def celle_dal_testo(t: str | None) -> dict:
    """Numeri sulle celle estratti dal testo libero, solo da frasi non ambigue.
    Esempio: "celle da 2 posti occupate da 3 persone" -> posti 2, persone 3. [estratto dal testo]"""
    out = {"celle_posti_previsti": None, "celle_persone": None, "celle_frase": None}
    if not t:
        return out
    n = r"(\d+|una|uno|due|tre|quattro|cinque|sei|sette|otto|nove|dieci|singol\w*|doppi\w*)"
    pattern = [
        rf"cell[ea]\s+(?:da|per)\s+{n}\s*(?:posti|persone|detenut\w*|letti|brande)?[^.;]{{0,60}}?(?:occupat\w*|ospita\w*|con|abitat\w*|ci sono|vi sono)\s+(?:da\s+)?{n}\s*(?:persone|detenut\w*|ristrett\w*)",
        rf"cell[ea]\s+{n}\s*(?:posti|post[io] lett[io])\s+[^.;]{{0,40}}?{n}\s*(?:persone|detenut\w*)",
    ]
    for p in pattern:
        m = re.search(p, t, re.I)
        if m:
            a, b = num_parola(m.group(1)), num_parola(m.group(2))
            if a and b:
                out.update(celle_posti_previsti=a, celle_persone=b, celle_frase=m.group(0)[:160])
                return out
    return out


def leggi_visita(testo_csv: str) -> dict:
    f = Foglio(testo_csv)
    nome = f.celle[0][0][1] if f.celle and f.celle[0] else None
    v = {
        "nome_foglio": nome,
        "data_visita": data_iso(f.valore("Data della visita")),
        "tipologia": f.valore("Tipologia"),
        "presenti_visita": intero(f.valore("Numero al momento della visita", "Numero detenuti al momento della visita", "Numero presenti")),
        "capienza_visita": intero(f.valore("Capienza regolamentare")),
        "tre_mq_calpestabili": si_no(f.valore("In tutte le celle visitate sono garantiti 3 mq", "In tutte le celle visitate sono garantiti 3mq")),
        "riscaldamento": si_no(f.valore("La celle visitate sono tutte riscaldate", "Le celle visitate sono tutte riscaldate", "Le celle sono riscaldate")),
        "acqua_calda": si_no(f.valore("È garantita l’acqua calda", "E' garantita l'acqua calda", "È garantita l'acqua calda", "E garantita l acqua calda", "C'è acqua calda")),
        "wc_separato": si_no(f.valore("Il wc è in ambiente separato", "Il wc e in ambiente separato")),
        "doccia_in_cella": si_no(f.valore("È presente la doccia nelle celle", "E' presente la doccia", "C'è la doccia in cella")),
        "spazi_non_in_uso": si_no(f.valore("Spazi detentivi attualmente non in uso")),
        "anno_costruzione": f.valore("Anno di costruzione"),
        "anno_apertura": f.valore("Anno di apertura"),
        "pp_prevista": intero(f.valore("Polizia penitenziaria prevista")),
        "pp_presente": intero(f.valore("Polizia penitenziaria effettivamente presente")),
        "edu_previsti": intero(f.valore("Numero educatori previsti")),
        "edu_presenti": intero(f.valore("Numero educatori effettivamente presenti")),
    }
    v.update(celle_dal_testo(f.testo_sotto("Condizioni generali delle celle visitate")))
    e = {
        "autolesionismo": intero(f.valore("N. casi di autolesionismo nel corso dell'anno precedente")),
        "suicidi": intero(f.valore("N. di suicidi nel corso dell'anno precedente")),
        "tentati_suicidi": intero(f.valore("N. di tentati suicidi nel corso dell'anno precedente")),
        "morti_altre_cause": intero(f.valore("N. di morti nel corso dell'anno precedente")),
        "isolamento_disciplinare": intero(f.valore('"Provvedimenti di isolamento disciplinare', "Provvedimenti di isolamento disciplinare")),
        "isolamento_al_momento": intero(f.valore("Numero persone in isolamento al momento della visita")),
    }
    return {"visita": v, "eventi": e}


# --- programma ---------------------------------------------------------------

def salva(p: Path, contenuto: bytes) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(contenuto)


def main() -> None:
    global PAUSA
    ap = argparse.ArgumentParser()
    ap.add_argument("--aggiorna", action="store_true", help="riscarica anche i fogli già presenti")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--pausa", type=float, default=1.5)
    ap.add_argument("--solo-parsing", action="store_true")
    a = ap.parse_args()
    PAUSA = a.pausa
    errori: list[str] = []
    rete = not a.solo_parsing

    if rete:
        controlla_robots()
        idx = scarica(INDICE).text
        salva(RAW / "pagine" / "regioni.html", idx.encode())
    else:
        idx = (RAW / "pagine" / "regioni.html").read_text(encoding="utf-8")

    elenco = []  # (regione, path)
    for reg in regioni(idx):
        p = RAW / "pagine" / f"regione_{reg}.html"
        if rete:
            pag = scarica(f"{BASE}/osservatorio_detenzione/{reg}").text
            salva(p, pag.encode())
        elif p.exists():
            pag = p.read_text(encoding="utf-8")
        else:
            continue
        elenco += [(reg, s) for s in schede_regione(pag, reg)]
    if a.limite:
        elenco = elenco[: a.limite]
    print(f"schede trovate: {len(elenco)}", file=sys.stderr)

    schede, visite, eventi = [], [], []
    for n, (reg, path) in enumerate(elenco, 1):
        sid = re.search(r"/(\d+)-", path).group(1)
        url = BASE + path
        p = RAW / "pagine" / f"scheda_{sid}.html"
        try:
            if rete:
                pag = scarica(url).text
                salva(p, pag.encode())
            else:
                pag = p.read_text(encoding="utf-8")
        except Exception as ex:  # noqa: BLE001
            errori.append(f"scheda {sid} {url}: {ex}")
            continue
        titolo = re.search(r'<h2[^>]*itemprop="(?:name|headline)"[^>]*>(.*?)</h2>', pag, re.S) or re.search(r"<title>(.*?)</title>", pag, re.S)
        nome = testo(titolo.group(1)) if titolo else path.rsplit("/", 1)[-1]
        fogli = fogli_scheda(pag)
        schede.append({"scheda_id": sid, "nome_antigone": nome, "regione_slug": reg, "url": url, "fogli": len(fogli)})
        if not fogli:
            errori.append(f"scheda {sid} ({nome}): nessun foglio Google")
        for f in fogli:
            h = hashlib.sha1(f"{f['chiave']}:{f['gid']}".encode()).hexdigest()[:10]
            pf = RAW / "fogli" / f"{sid}_{f['anno_etichetta'] or 'xxxx'}_{h}.csv"
            try:
                if rete and (a.aggiorna or not pf.exists()):
                    salva(pf, scarica(url_csv(f)).content)
                if not pf.exists():
                    continue
                letto = leggi_visita(pf.read_text(encoding="utf-8", errors="replace"))
            except Exception as ex:  # noqa: BLE001
                errori.append(f"foglio {sid}/{f['anno_etichetta']}: {ex}")
                continue
            base = {"scheda_id": sid, "anno_etichetta": f["anno_etichetta"], "url_scheda": url, "url_foglio": url_pubhtml(f)}
            if not letto["visita"]["data_visita"]:
                errori.append(f"foglio {sid}/{f['anno_etichetta']}: data della visita non trovata")
            visite.append({**base, **letto["visita"]})
            eventi.append({**base, "data_visita": letto["visita"]["data_visita"], **letto["eventi"]})
        print(f"[{n}/{len(elenco)}] {nome}: {len(fogli)} fogli", file=sys.stderr)

    OUT.mkdir(parents=True, exist_ok=True)
    scrivi(OUT / "schede.csv", schede)
    scrivi(OUT / "visite.csv", sorted(visite, key=lambda r: (r["scheda_id"], r["data_visita"] or "")))
    scrivi(OUT / "eventi_critici.csv", sorted(eventi, key=lambda r: (r["scheda_id"], r["data_visita"] or "")))
    (OUT / "indice.json").write_text(json.dumps({
        "raccolta": oggi(),
        "fonte": INDICE,
        "metodo": "fogli Google pubblicati collegati alle schede, scaricati in CSV e letti per etichetta",
        "user_agent": UA,
        "schede": len(schede),
        "visite": len(visite),
        "visite_con_data": sum(1 for v in visite if v["data_visita"]),
        "errori": errori,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"schede {len(schede)}, visite {len(visite)}, errori {len(errori)}", file=sys.stderr)


def scrivi(p: Path, righe: list[dict]) -> None:
    if not righe:
        p.write_text("", encoding="utf-8")
        return
    cols = list(righe[0].keys())
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        w.writerows(righe)


if __name__ == "__main__":
    main()
