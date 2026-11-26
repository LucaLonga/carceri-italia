// Elenco ordinabile e filtrabile degli istituti: alternativa accessibile alla mappa.
import * as Inputs from "npm:@observablehq/inputs";
import {html} from "npm:htl";
import {banda, classe} from "./metrica.js";
import {m2, num, pct, regione} from "./formato.js";

// Righe piatte per la tabella (e per il pannello "Dati").
export function righeElenco(istituti, arredo) {
  return istituti.map((i) => {
    const b = banda(i, arredo);
    return {
      codice: i.codice,
      nome: i.nome,
      regione: regione(i.regione),
      tipo: i.tipo,
      presenti: i.scheda?.presenti ?? null,
      posti_disp: i.calc.posti_disp,
      m2_alto: b.alto,
      m2_basso: b.basso,
      persone_stanza: i.calc.persone_stanza,
      affollamento_reale: i.calc.affollamento_reale,
      classe: b.classe,
      coord_da_verificare: i.coord_da_verificare ? "sì" : ""
    };
  });
}

export function tabellaElenco(righe, {base = "."} = {}) {
  return Inputs.table(righe, {
    columns: ["nome", "regione", "tipo", "presenti", "m2_alto", "m2_basso", "persone_stanza", "affollamento_reale", "classe"],
    header: {
      nome: "Istituto",
      regione: "Regione",
      tipo: "Tipo",
      presenti: "Presenti",
      m2_alto: "m² lordi",
      m2_basso: "meno arredo",
      persone_stanza: "pers./stanza",
      affollamento_reale: "affoll.",
      classe: "Banda"
    },
    format: {
      nome: (d, i, data) => html`<a href="${base}/istituto/${data[i].codice}">${d}</a>`,
      presenti: (d) => num(d),
      m2_alto: (d) => m2(d, 2),
      m2_basso: (d) => m2(d, 2),
      persone_stanza: (d) => num(d, 1),
      affollamento_reale: (d) => pct(d),
      classe: (d) => classe(d).breve
    },
    sort: "m2_alto",
    reverse: false,
    rows: 16,
    layout: "auto",
    select: false
  });
}
