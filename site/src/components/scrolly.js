// Scrollytelling senza librerie: una figura fissa (sticky) e i passi del testo che scorrono.
// Un IntersectionObserver guarda quale passo attraversa la fascia centrale dello schermo e chiama
// attiva(indice). Su mobile la figura sta in alto e i passi scorrono sotto (CSS in style.css).
// Con prefers-reduced-motion le transizioni sono spente dal CSS: i cambi di stato sono istantanei.
export function scrolly(passi, {figura, attiva, etichetta = "Racconto"}) {
  const radice = document.createElement("section");
  radice.className = "scrolly";
  radice.setAttribute("aria-label", etichetta);
  const fig = document.createElement("div");
  fig.className = "scrolly-figura";
  fig.append(figura);
  const colonna = document.createElement("div");
  colonna.className = "scrolly-passi";
  const nodi = passi.map((p, k) => {
    const d = document.createElement("div");
    d.className = "scrolly-passo";
    d.dataset.indice = k;
    d.id = `passo-${k + 1}`;
    d.append(p.contenuto);
    colonna.append(d);
    return d;
  });
  radice.append(fig, colonna);

  let corrente = -1;
  const imposta = (k) => {
    if (k === corrente) return;
    corrente = k;
    nodi.forEach((n, j) => n.classList.toggle("attivo", j === k));
    attiva(k);
  };
  const osservatore = new IntersectionObserver(
    (voci) => {
      for (const v of voci) if (v.isIntersecting) imposta(+v.target.dataset.indice);
    },
    {rootMargin: "-45% 0px -45% 0px", threshold: 0}
  );
  nodi.forEach((n) => osservatore.observe(n));
  imposta(0);
  // Un link a #passo-N porta direttamente a quel passo (utile per condividere un passo).
  const m = /^#passo-(\d+)$/.exec(location.hash);
  if (m && nodi[+m[1] - 1]) requestAnimationFrame(() => nodi[+m[1] - 1].scrollIntoView({block: "center"}));
  // Framework chiama invalidation quando la cella viene ricalcolata: si smette di osservare.
  radice.ferma = () => osservatore.disconnect();
  return radice;
}

// Strati della figura: uno solo visibile alla volta (gli altri restano nel DOM, nascosti e inerti).
export function strati(mappa) {
  const box = document.createElement("div");
  box.className = "strati";
  const elenco = Object.entries(mappa).map(([nome, nodo]) => {
    const s = document.createElement("div");
    s.className = "strato";
    s.dataset.nome = nome;
    s.append(nodo);
    box.append(s);
    return s;
  });
  box.mostra = (nome) => {
    for (const s of elenco) {
      const on = s.dataset.nome === nome;
      s.classList.toggle("visibile", on);
      s.toggleAttribute("inert", !on);
      s.setAttribute("aria-hidden", on ? "false" : "true");
    }
  };
  return box;
}
