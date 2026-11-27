// Pannelli espandibili sotto ogni grafico: "Dati" (tabella esatta + CSV) e "Codice" (sorgente che gira).
import hljs from "npm:highlight.js/lib/core";
import javascript from "npm:highlight.js/lib/languages/javascript";
hljs.registerLanguage("javascript", javascript);

function csv(righe, colonne) {
  const esc = (v) => {
    const s = v == null ? "" : String(v);
    return /[",\n;]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [colonne.map((c) => c.chiave).join(","), ...righe.map((r) => colonne.map((c) => esc(r[c.chiave])).join(","))].join("\n");
}

// righe: array di oggetti; colonne: [{chiave, etichetta, formato?}]; nome: nome del file CSV.
export function pannelloDati(righe, colonne, nome, {nota} = {}) {
  const details = document.createElement("details");
  details.className = "pannello";
  const summary = document.createElement("summary");
  summary.textContent = `Dati (${righe.length} righe)`;
  details.append(summary);
  if (nota) {
    const p = document.createElement("p");
    p.className = "nota";
    p.textContent = nota;
    details.append(p);
  }
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv(righe, colonne)], {type: "text/csv;charset=utf-8"}));
  a.download = nome;
  a.textContent = `Scarica ${nome}`;
  details.append(a);
  const wrap = document.createElement("div");
  wrap.className = "tabella-scorrevole";
  const t = document.createElement("table");
  const thead = t.createTHead().insertRow();
  for (const c of colonne) {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = c.etichetta ?? c.chiave;
    thead.append(th);
  }
  const tb = t.createTBody();
  for (const r of righe) {
    const tr = tb.insertRow();
    for (const c of colonne) tr.insertCell().textContent = c.formato ? c.formato(r[c.chiave]) : r[c.chiave] ?? "n.d.";
  }
  wrap.append(t);
  details.append(wrap);
  return details;
}

// testo: il sorgente del modulo, letto con FileAttachment(...).text(): è il file che gira.
export function pannelloCodice(testo, nomeFile) {
  const details = document.createElement("details");
  details.className = "pannello";
  const summary = document.createElement("summary");
  summary.textContent = `Codice (${nomeFile})`;
  const pre = document.createElement("pre");
  const code = document.createElement("code");
  code.className = "hljs language-javascript";
  code.innerHTML = hljs.highlight(testo, {language: "javascript"}).value;
  pre.append(code);
  details.append(summary, pre);
  return details;
}
