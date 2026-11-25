# Dati del progetto DV-24.01 (2024)

- `master_2024.csv`: foglio MASTER del dataset 2024 (`Carceri e condizioni detentive - dataset.xlsx`),
  tabella di raccordo tra nomi Antigone e nomi del Ministero, con coordinate geocodificate,
  capienza e presenti del 2024.
- Nel file Excel originale 10 istituti (i più grandi) hanno capienza e/o presenti salvati come **orari**
  (formato `h.mm`): un numero scritto come "1.616" è stato letto come 1 ora e 616 minuti. Il valore
  originale non si ricostruisce con certezza, quindi qui quelle celle sono **vuote**.
  Istituti interessati: Napoli Poggioreale, Napoli Secondigliano, Roma Rebibbia N.C., Roma Regina Coeli,
  Bollate, Milano San Vittore, Opera, Torino, Lecce, Palermo Pagliarelli.
  Lo stesso problema riguarda altri fogli del file (Sheet9, Sheet11, serie per età): da non riusare senza controllo.
- Il foglio "suicidi 2023-2024" contiene nomi di persone: **non è pubblicato** in questo repository.
