// Legenda delle classi della banda (simbolo + parola: il colore non è mai l'unico segnale).
import {html, svg} from "npm:htl";
import {CLASSI} from "./metrica.js";

export function simbolo(id, r = 6) {
  const s = r * 2 + 4;
  const manc = id === "mancante";
  return svg`<svg width=${s} height=${s} aria-hidden="true"><circle cx=${s / 2} cy=${s / 2} r=${r}
    fill=${manc ? "none" : `var(--classe-${id})`} stroke=${manc ? "var(--classe-mancante)" : "var(--superficie)"}
    stroke-width=${manc ? 1.5 : 1} stroke-dasharray=${manc ? "2 2" : null}/></svg>`;
}

export function legenda(conteggi) {
  return html`<ul class="legenda" aria-label="Legenda delle classi">${CLASSI.map(
    (c) => html`<li>${simbolo(c.id)}<span>${c.etichetta}${conteggi ? ` (${conteggi[c.id] ?? 0})` : ""}</span></li>`
  )}</ul>`;
}
