// Converte i confini regionali (GeoJSON di openpolis/geojson-italy, dati ISTAT 1.1.2026, CC BY 4.0)
// in un TopoJSON semplificato per la mappa: node scripts/confini.js <regioni.geojson>
// Il risultato (src/data/regioni.topojson) è nel repository: il sito non scarica nulla a runtime.
import {readFileSync, writeFileSync} from "node:fs";
import {topology} from "topojson-server";
import {presimplify, simplify, quantile} from "topojson-simplify";
const src = process.argv[2];
if (!src) throw new Error("uso: node scripts/confini.js <regioni.geojson>");
const geo = JSON.parse(readFileSync(src, "utf8"));
for (const f of geo.features) f.properties = {regione: f.properties.reg_name, cod: f.properties.reg_istat_code_num};
let topo = presimplify(topology({regioni: geo}, 2e4));
topo = simplify(topo, quantile(topo, 0.04));
const out = JSON.stringify(topo);
writeFileSync("src/data/regioni.topojson", out);
console.log("regioni:", geo.features.length, "kB:", Math.round(out.length / 1024));
