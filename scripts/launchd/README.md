# scripts/launchd

Lavori pianificati sul Mac con `launchd`. **Nessuno è installato in automatico**: si installano a mano,
uno per uno, solo se servono.

Attenzione: launchd non può leggere il volume esterno `other-eyes` (protezione privacy di macOS). Il servizio
ArchiveBox per questo gira da cloni sul disco interno; il plist della raccolta punta ancora al volume
esterno e, se servisse, va riscritto allo stesso modo [DA FARE solo se si usa]. Se il volume `other-eyes` non è montato all'ora prevista, il lavoro
fallisce e lo si vede nel log. Se il Mac dorme, `launchd` esegue il lavoro al risveglio.

## Raccolta (`it.lucalonga.carceri.raccolta.plist`)

Alternativa a `.github/workflows/raccolta.yml`, da usare **solo se i server di GitHub non raggiungono
giustizia.it** (il workflow si ferma al passo "giustizia.it raggiungibile?"). Esegue
`scripts/raccolta_locale.sh auto`: lunedì le schede trasparenza, il giorno 12 le tabelle mensili e
l'archivio delle fonti; poi commit e push su `main` con lo stesso messaggio del workflow.

Prima, una volta:

```bash
cd /Volumes/other-eyes/Carceri-2.0/carceri-italia
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./scripts/raccolta_locale.sh schede      # prova a mano: deve finire con un commit o "Nessun cambiamento."
```

Installazione:

```bash
cp scripts/launchd/it.lucalonga.carceri.raccolta.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/it.lucalonga.carceri.raccolta.plist
launchctl kickstart gui/$(id -u)/it.lucalonga.carceri.raccolta   # prova subito ("oggi niente da raccogliere" fuori calendario)
tail -f ~/Library/Logs/carceri-raccolta.log
```

Disinstallazione:

```bash
launchctl bootout gui/$(id -u)/it.lucalonga.carceri.raccolta
rm ~/Library/LaunchAgents/it.lucalonga.carceri.raccolta.plist
```

Se si usa la raccolta sul Mac, conviene togliere il calendario da `raccolta.yml` per non avere due
raccolte (lasciando `workflow_dispatch`). Il push usa le credenziali git del Mac (portachiavi o `gh auth`).

## ArchiveBox (`it.lucalonga.carceri.archivebox.plist`)

Terza copia delle fonti, ogni lunedì alle 09:00. **Non tocca mai il repository di lavoro** e gira tutto sul
disco interno, quindi non servono permessi speciali né "Accesso completo al disco" (launchd non può leggere
il volume esterno: "Operation not permitted", errore 126).

```
~/Library/Application Support/carceri-italia/
  archivebox_servizio.sh        copia di scripts/launchd/archivebox_servizio.sh (la esegue il plist)
  carceri-italia/               clone del pubblico: a ogni giro git fetch + git reset --hard origin/main
  carceri-italia-redazione/     clone del privato, per gli URL della rassegna stampa (stesso trattamento)
  venv/                         Python con pyyaml
~/ArchiveBoxData                archivio ArchiveBox
~/Library/Logs/carceri-archivebox.log
```

I cloni si creano da soli al primo giro; nei cloni mai commit né push. Lo script lancia
`carceri-italia/scripts/archivebox_local.sh` del clone: fonti di `sources.yml` e le 190 schede (copia datata
a ogni giro), `archive/extra_urls.txt`, la rassegna pubblica e quella stampa del privato (una copia sola).
Con `--prova` aggiorna i cloni e conta gli URL senza archiviare.

Installazione (dal repository di lavoro, una volta; si ripete solo se cambia `archivebox_servizio.sh`):

```bash
mkdir -p ~/Library/Application\ Support/carceri-italia
cp scripts/launchd/archivebox_servizio.sh ~/Library/Application\ Support/carceri-italia/
cp scripts/launchd/it.lucalonga.carceri.archivebox.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/it.lucalonga.carceri.archivebox.plist
launchctl kickstart gui/$(id -u)/it.lucalonga.carceri.archivebox
tail -f ~/Library/Logs/carceri-archivebox.log
```

Disinstallazione:

```bash
launchctl bootout gui/$(id -u)/it.lucalonga.carceri.archivebox
rm ~/Library/LaunchAgents/it.lucalonga.carceri.archivebox.plist
```
