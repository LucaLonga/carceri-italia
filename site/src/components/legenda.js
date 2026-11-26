// Legenda delle classi (simbolo + parola: il colore non è mai l'unico segnale).
import {html, svg} from "npm:htl";
import {CLASSI} from "./metrica.js";

export function simbolo(id, lato = 12) {
  const s = lato + 4;
  const manc = id === "mancante";
  return svg`<svg width=${s} height=${s} aria-hidden="true"><rect x="2" y="2" width=${lato} height=${lato}
    fill=${manc ? "none" : `var(--classe-${id})`} stroke=${manc ? "var(--classe-mancante)" : "none"}
    stroke-width=${manc ? 1.5 : 0} stroke-dasharray=${manc ? "2 2" : null}/></svg>`;
}

export function simboloVisita(lato = 12) {
  const s = lato + 4;
  return svg`<svg width=${s} height=${s} aria-hidden="true"><rect x="2" y="2" width=${lato} height=${lato} fill="var(--theme-foreground-faint)"/>
    <path d=${`M${2 + lato - 5},2H${2 + lato}V7Z`} fill="var(--theme-foreground)"/></svg>`;
}

export function legenda(conteggi, {visita = false} = {}) {
  return html`<ul class="legenda" aria-label="Legenda delle classi">${CLASSI.map(
    (c) => html`<li title=${c.lunga}>${simbolo(c.id)}<span>${c.etichetta}${conteggi ? ` (${conteggi[c.id] ?? 0})` : ""}</span></li>`
  )}${visita ? html`<li>${simboloVisita()}<span>la classe viene da una visita di Antigone</span></li>` : ""}</ul>`;
}
