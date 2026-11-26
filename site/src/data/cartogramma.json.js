// Data loader: cartogramma di Demers, calcolato una volta in fase di build.
//
// Ogni istituto è un quadrato centrato sulla sua posizione reale (coordinate DAP, proiezione
// trasversa di Mercatore). Una simulazione di forze lo tira verso quella posizione e una forza di
// collisione tra quadrati (non cerchi) lo sposta quanto basta per non sovrapporsi agli altri.
// L'ingombro di ogni quadrato è il più grande tra presenti e posti regolamentari: così anche il
// quadrato tratteggiato della capienza non tocca i vicini.
//
// Due disposizioni: "desktop" e "mobile" (più compatta, quadrati relativamente più grandi).
// Il lato si calcola nel browser: lato = k · √persone, con k salvato qui per ogni disposizione.
// Uscita: posizioni, k, sagoma dell'Italia (regioni ISTAT unite e semplificate) come percorso SVG.
import {execFileSync} from "node:child_process";
import {readFileSync} from "node:fs";
import {fileURLToPath} from "node:url";
import {geoPath, geoTransverseMercator} from "d3-geo";
import {forceSimulation, forceX, forceY} from "d3-force";
import {quadtree} from "d3-quadtree";
import {feature, merge} from "topojson-client";
import {presimplify, simplify, quantile} from "topojson-simplify";

const qui = (p) => fileURLToPath(new URL(p, import.meta.url));

// Gli istituti vengono dallo stesso loader del resto del sito (una sola unione dei dati).
const dati = JSON.parse(execFileSync("python3", [qui("./istituti.json.py")], {maxBuffer: 64 << 20, stdio: ["ignore", "pipe", "ignore"]}).toString());
const topo = JSON.parse(readFileSync(qui("./regioni.topojson"), "utf8"));

// Sagoma: regioni unite in un solo poligono multiplo, semplificata molto (serve solo a riconoscere la forma).
const topoLeggero = simplify(presimplify(structuredClone(topo)), quantile(presimplify(structuredClone(topo)), 0.35));
const italia = merge(topoLeggero, topoLeggero.objects.regioni.geometries);
const italiaPiena = feature(topo, topo.objects.regioni);

const DISPOSIZIONI = {
  desktop: {w: 860, h: 980, riempimento: 0.55, margine: 12, passo: 1.5},
  mobile: {w: 360, h: 420, riempimento: 0.6, margine: 6, passo: 1}
};

const istituti = dati.istituti
  .filter((i) => i.lat != null && i.lon != null)
  .map((i) => ({
    codice: i.codice,
    presenti: i.scheda?.presenti ?? 0,
    posti_reg: i.scheda?.posti_reg ?? 0,
    lon: i.lon,
    lat: i.lat
  }));

function disponi({w, h, riempimento, margine, passo}) {
  const proiezione = geoTransverseMercator().rotate([-12.5, -42]).fitExtent([[margine, margine], [w - margine, h - margine]], italiaPiena);
  const percorso = geoPath(proiezione);
  const areaItalia = percorso.area(italiaPiena);
  // k tale che l'area totale degli ingombri sia una quota fissa della superficie dell'Italia.
  const sommaPersone = istituti.reduce((s, i) => s + Math.max(i.presenti, i.posti_reg), 0);
  const k = Math.sqrt((riempimento * areaItalia) / sommaPersone);
  const nodi = istituti.map((i) => {
    const [x0, y0] = proiezione([i.lon, i.lat]);
    return {...i, x0, y0, x: x0, y: y0, lato: Math.max(3, k * Math.sqrt(Math.max(i.presenti, i.posti_reg)))};
  });
  const latoMax = Math.max(...nodi.map((n) => n.lato));

  // Collisione tra quadrati allineati agli assi: separa ogni coppia lungo l'asse di minor sovrapposizione.
  function collisione(alpha) {
    const albero = quadtree(nodi, (d) => d.x, (d) => d.y);
    for (const a of nodi) {
      const r = (a.lato + latoMax) / 2 + passo;
      albero.visit((q, x1, y1, x2, y2) => {
        if (!q.length) {
          do {
            const b = q.data;
            if (b !== a && b.codice > a.codice) {
              const dx = b.x - a.x, dy = b.y - a.y;
              const min = (a.lato + b.lato) / 2 + passo;
              const ox = min - Math.abs(dx), oy = min - Math.abs(dy);
              if (ox > 0 && oy > 0) {
                const pa = b.lato ** 2 / (a.lato ** 2 + b.lato ** 2), pb = 1 - pa; // il piccolo si sposta di più
                if (ox < oy) {
                  const s = (dx === 0 ? 1 : Math.sign(dx)) * ox * Math.min(1, alpha * 2 + 0.5);
                  a.x -= s * pa; b.x += s * pb;
                } else {
                  const s = (dy === 0 ? 1 : Math.sign(dy)) * oy * Math.min(1, alpha * 2 + 0.5);
                  a.y -= s * pa; b.y += s * pb;
                }
              }
            }
          } while ((q = q.next));
        }
        return x1 > a.x + r || x2 < a.x - r || y1 > a.y + r || y2 < a.y - r;
      });
    }
  }

  const sim = forceSimulation(nodi)
    .force("x", forceX((d) => d.x0).strength(0.08))
    .force("y", forceY((d) => d.y0).strength(0.08))
    .force("collisione", collisione)
    .stop();
  for (let t = 0; t < 600; t++) sim.tick();
  for (let t = 0; t < 80; t++) collisione(0); // ultime passate senza attrazione: nessuna sovrapposizione residua

  let sovrapposizioni = 0;
  for (let i = 0; i < nodi.length; i++)
    for (let j = i + 1; j < nodi.length; j++) {
      const a = nodi[i], b = nodi[j], min = (a.lato + b.lato) / 2;
      if (Math.abs(a.x - b.x) < min - 0.5 && Math.abs(a.y - b.y) < min - 0.5) sovrapposizioni++;
    }
  const spost = nodi.map((n) => Math.hypot(n.x - n.x0, n.y - n.y0));
  const r1 = (v) => Math.round(v * 10) / 10;
  return {
    w, h, k: Math.round(k * 1e5) / 1e5,
    sagoma: percorso(italia),
    controlli: {sovrapposizioni, spostamento_medio_px: r1(spost.reduce((a, b) => a + b, 0) / spost.length), spostamento_max_px: r1(Math.max(...spost))},
    quadrati: nodi.map((n) => ({codice: n.codice, x: r1(n.x), y: r1(n.y), x0: r1(n.x0), y0: r1(n.y0)}))
  };
}

const out = {generato: dati.generato, fonte_sagoma: "ISTAT, confini regionali 1.1.2026 (openpolis/geojson-italy), CC BY 4.0", disposizioni: {}};
for (const [nome, p] of Object.entries(DISPOSIZIONI)) {
  out.disposizioni[nome] = disponi(p);
  console.warn(`[cartogramma] ${nome}:`, JSON.stringify(out.disposizioni[nome].controlli));
}
process.stdout.write(JSON.stringify(out));
