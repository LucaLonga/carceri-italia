// Banda dello spazio per persona e classificazione. Usato da mappa, elenco, scheda e metodo.
import {ARREDO_M2_PERSONA, SOGLIA_M2, VISITA_DATATA_MESI} from "./parametri.js";

// Le quattro classi, nell'ordine della legenda. Colori: una sola tinta (blu) in tre passi,
// dal chiaro (banda sopra la soglia) allo scuro (banda sotto); grigio senza riempimento per il dato mancante.
// Le etichette valgono per entrambe le fonti: la banda stimata dal Ministero o, se vale, la visita di Antigone
// (vedi valutazione() più sotto). La legenda dice sempre quale fonte vale per ogni istituto.
export const CLASSI = [
  {id: "sopra", etichetta: "sopra 3 m²", lunga: "banda tutta sopra 3 m², o visita: 3 m² in tutte le celle visitate", breve: "sopra"},
  {id: "attraversa", etichetta: "a cavallo di 3 m² (incerto)", lunga: "la banda stimata attraversa 3 m²", breve: "a cavallo"},
  {id: "sotto", etichetta: "sotto 3 m²", lunga: "banda tutta sotto 3 m², o visita: celle sotto 3 m² calpestabili", breve: "sotto"},
  {id: "mancante", etichetta: "dato mancante", lunga: "dato mancante", breve: "mancante"}
];
export const classe = (id) => CLASSI.find((c) => c.id === id);

// Banda per un istituto (oggetto di istituti.json).
//   alto  = m² lordi per persona                  [calcolato]
//   basso = alto − arredo per persona             [ipotesi]
export function banda(ist, arredo = ARREDO_M2_PERSONA) {
  const alto = ist?.calc?.m2_lordi_persona;
  if (alto == null || !Number.isFinite(alto)) return {alto: null, basso: null, classe: "mancante"};
  const basso = Math.max(0, alto - arredo);
  const c = basso >= SOGLIA_M2 ? "sopra" : alto < SOGLIA_M2 ? "sotto" : "attraversa";
  return {alto, basso, classe: c};
}

// Perché un dato manca, in parole (casi limite scritti dal data loader).
const CASI = {
  dati_incompleti: "la scheda non riporta tutti i valori",
  posti_tutti_non_disponibili: "tutti i posti sono non disponibili",
  nessuna_stanza_disponibile: "nessuna stanza disponibile",
  nessun_presente: "nessuna persona presente",
  piu_stanze_che_posti: "più stanze che posti disponibili: la stima della superficie non regge"
};
export const motivi = (ist) => (ist?.calc?.casi ?? []).map((c) => CASI[c] ?? c);

// --- Regola di affidabilità: Antigone contro Ministero -------------------------------------------

// Mesi tra due date ISO (a, b), arrotondati per difetto.
export function mesiTra(a, b) {
  if (!a || !b) return null;
  const [ya, ma, da] = a.split("-").map(Number), [yb, mb, db] = b.split("-").map(Number);
  return (yb - ya) * 12 + (mb - ma) - (db < da ? 1 : 0);
}

// Ultima visita con una risposta sì/no sui 3 m² calpestabili.
export function ultimaVisita(ist) {
  const v = ist?.visite_antigone?.visite ?? [];
  return [...v].reverse().find((x) => x.tre_mq === "si" || x.tre_mq === "no") ?? v.at(-1) ?? null;
}

// Classe finale, fonte che vale, data e divergenze tra le due fonti.
//   fonte "antigone": visita non datata con risposta sì/no sui 3 m² calpestabili [verificata sul posto]
//   fonte "stima":    banda calcolata dalle schede del Ministero [calcolato][ipotesi]
export function valutazione(ist, {arredo = ARREDO_M2_PERSONA, mesi = VISITA_DATATA_MESI} = {}) {
  const b = banda(ist, arredo);
  const v = ultimaVisita(ist);
  const rif = ist?.scheda?.agg_capienza;
  const eta = v ? mesiTra(v.data, rif) : null;
  const datata = v != null && eta != null && eta > mesi;
  const valida = v != null && !datata && (v.tre_mq === "si" || v.tre_mq === "no");
  const classeFinale = valida ? (v.tre_mq === "no" ? "sotto" : "sopra") : b.classe;
  const divergenze = [];
  if (v) {
    if (v.tre_mq === "no" && b.classe === "sopra") divergenze.push({campo: "3 m²", testo: "la visita trova celle sotto 3 m² calpestabili, la stima dal Ministero no"});
    if (v.tre_mq === "si" && b.classe === "sotto") divergenze.push({campo: "3 m²", testo: "la visita trova 3 m² in tutte le celle visitate, la stima dal Ministero no"});
    const cap = ist.scheda?.posti_reg;
    if (v.capienza != null && cap && Math.abs(v.capienza - cap) / cap > 0.05)
      divergenze.push({campo: "capienza", testo: `capienza ${v.capienza} alla visita, ${cap} posti regolamentari nella scheda`});
    if (v.celle && v.celle[1] > v.celle[0])
      divergenze.push({campo: "celle", testo: `celle da ${v.celle[0]} occupate da ${v.celle[1]} persone (dal testo della visita)`});
  }
  return {banda: b, classe: classeFinale, fonte: valida ? "antigone" : "stima", visita: v, eta_mesi: eta, datata, divergenze};
}
