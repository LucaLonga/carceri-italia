// Banda dello spazio per persona e classificazione. Usato da mappa, elenco, scheda e metodo.
import {ARREDO_M2_PERSONA, SOGLIA_M2} from "./parametri.js";

// Le quattro classi, nell'ordine della legenda. Colori: una sola tinta (blu) in tre passi,
// dal chiaro (banda sopra la soglia) allo scuro (banda sotto); grigio senza riempimento per il dato mancante.
export const CLASSI = [
  {id: "sopra", etichetta: "banda tutta sopra 3 m²", breve: "sopra"},
  {id: "attraversa", etichetta: "la banda attraversa 3 m²", breve: "attraversa"},
  {id: "sotto", etichetta: "banda tutta sotto 3 m²", breve: "sotto"},
  {id: "mancante", etichetta: "dato mancante", breve: "mancante"}
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
