// Refusi delle fonti: nei dati restano come sono (data/ non si corregge), nei testi della pagina si
// correggono e la scheda dell'istituto lo dice con una nota.
const REFUSI = [
  {sbagliato: /cirondariale/gi, giusto: "circondariale", nota: "\"cirondariale\" (tabella di raccordo, tipo esteso)"}
];

// Restituisce il testo corretto e l'elenco delle correzioni fatte.
export function senzaRefusi(testo) {
  let t = String(testo ?? "");
  const note = [];
  for (const r of REFUSI) {
    if (r.sbagliato.test(t)) {
      t = t.replace(r.sbagliato, (m) => (m[0] === m[0].toUpperCase() ? r.giusto[0].toUpperCase() + r.giusto.slice(1) : r.giusto));
      note.push(r.nota);
    }
    r.sbagliato.lastIndex = 0;
  }
  return {testo: t, note};
}
export const corretto = (testo) => senzaRefusi(testo).testo;
