// Numeri e date in formato italiano: virgola decimale, punto per le migliaia, "24 novembre 2026".
const cache = new Map();
function nf(min, max) {
  const k = `${min}-${max}`;
  if (!cache.has(k)) cache.set(k, new Intl.NumberFormat("it-IT", {minimumFractionDigits: min, maximumFractionDigits: max, useGrouping: "always"}));
  return cache.get(k);
}
export const num = (v, cifre = 0) => (v == null || !Number.isFinite(+v) ? "–" : nf(cifre, cifre).format(+v));
export const pct = (v, cifre = 0) => (v == null || !Number.isFinite(+v) ? "–" : `${num(v * 100, cifre)}%`);
export const m2 = (v, cifre = 1) => (v == null ? "–" : `${num(v, cifre)} m²`);

const df = new Intl.DateTimeFormat("it-IT", {day: "numeric", month: "long", year: "numeric", timeZone: "UTC"});
// "2026-11-24" -> "24 novembre 2026"
export function data(iso) {
  if (!iso) return "–";
  const d = new Date(`${String(iso).slice(0, 10)}T00:00:00Z`);
  return Number.isNaN(+d) ? String(iso) : df.format(d);
}
// Nome dell'istituto con il tipo, per titoli e tooltip.
export const nomeCompleto = (i) => `${i.nome} (${i.tipo})`;
// Regione con l'iniziale maiuscola: "EMILIA ROMAGNA" -> "Emilia Romagna".
export const regione = (s) => String(s ?? "").toLowerCase().replace(/(^|[\s'-])\p{L}/gu, (m) => m.toUpperCase());
