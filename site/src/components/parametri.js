// Parametri del metodo. Un solo punto: ogni pagina e ogni grafico li legge da qui.

// Soglia della Corte EDU (Torreggiani c. Italia, 2013): 3 m² calpestabili per persona.
export const SOGLIA_M2 = 3;

// Superficie occupata dagli arredi fissi per persona (letto, armadietto, sgabello), in m².
// Serve per il limite basso della banda: spazio calpestabile ≈ spazio lordo − arredo.
// [ipotesi] DA FISSARE con una fonte
export const ARREDO_M2_PERSONA = 1.5;

// Capienza regolamentare (nota del Ministero alla tabella mensile): 9 m² per il primo posto
// della stanza, 5 m² per ogni posto in più.
export const M2_PRIMO_POSTO = 9;
export const M2_ALTRI_POSTI = 5;
