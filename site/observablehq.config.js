// Configurazione di Observable Framework per il sito di carceri-italia.
import {readFileSync} from "node:fs";

// Codici DAP degli istituti (chiave principale): una pagina per riga di istituti.csv.
// Milano San Vittore ha due schede (BB01;BB32) ma una sola pagina, con il codice principale BB01.
function codici() {
  const righe = readFileSync(new URL("../data/reference/istituti.csv", import.meta.url), "utf8").trim().split(/\r?\n/);
  const intestazione = righe[0].split(",");
  const col = intestazione.indexOf("codice_dap");
  return righe.slice(1).map((r) => r.split(",")[col]).filter(Boolean);
}

// Nome utente GitHub: non scritto qui. In GitHub Actions arriva da GITHUB_REPOSITORY_OWNER;
// in locale si può impostare SITO_UTENTE. Serve solo per i link assoluti (repository).
const UTENTE = process.env.SITO_UTENTE || process.env.GITHUB_REPOSITORY_OWNER || "";
const REPO = UTENTE ? `https://github.com/${UTENTE}/carceri-italia` : "";

export default {
  title: "Quanto spazio",
  root: "src",
  // Framework usa link relativi: il sito funziona sotto /carceri-italia/ anche senza base.
  // base serve solo alla pagina 404.
  base: process.env.SITO_BASE || "/carceri-italia/",
  pages: [
    {name: "Mappa e istituti", path: "/"},
    {name: "Il racconto", path: "/racconto"},
    {name: "Metodo", path: "/metodo"},
    {name: "Dati", path: "/dati"}
  ],
  dynamicPaths: codici().map((c) => `/istituto/${c}`),
  style: "style.css",
  globalStylesheets: [],     // niente Google Fonts (default di Framework): i font sono nel sito
  search: false,
  toc: false,
  pager: false,
  head: `<meta name="description" content="Quanto spazio ha davvero una persona detenuta in Italia, istituto per istituto.">
<meta name="referrer" content="no-referrer">
<script>document.documentElement.lang = "it";</script>`,
  header: "",
  footer: `Dati: Ministero della Giustizia (DAP), Antigone; confini ISTAT via openpolis (CC BY 4.0).
Codice MIT. ${REPO ? `<a href="${REPO}">Repository</a> · ` : ""}<a href="https://lucalonga.com/projects/dv-24-01">Poster del 2024</a>.
Nessun cookie, nessun tracciamento.`
};
