# scripts/launchd

Lavori pianificati sul Mac con `launchd`. **Nessuno è installato in automatico**: si installano a mano,
uno per uno, solo se servono.

I percorsi nei plist sono assoluti e puntano a `/Volumes/other-eyes/Carceri-2.0/carceri-italia`: se il
repository si sposta, vanno corretti. Se il volume `other-eyes` non è montato all'ora prevista, il lavoro
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

Terza copia delle fonti, ogni lunedì alle 09:00: aggiorna il repository (`git pull`) e lancia
`scripts/archivebox_local.sh`, che aggiunge ad ArchiveBox (`~/ArchiveBoxData`) le fonti di
`sources.yml`, le 190 schede trasparenza, `archive/extra_urls.txt`, i documenti della rassegna e, se il
repository privato è nella cartella accanto, la sua rassegna stampa. Le pagine che cambiano ricevono una
copia datata a ogni lancio; documenti e articoli una copia sola.

Prima, una volta: ArchiveBox installato (`archivebox` è in `~/.local/bin`), archivio inizializzato in
`~/ArchiveBoxData`, virtualenv del repository creato (serve `pyyaml`). Prova a mano:

```bash
cd /Volumes/other-eyes/Carceri-2.0/carceri-italia
PATH="$PWD/.venv/bin:$PATH" ./scripts/archivebox_local.sh --prova     # solo l'elenco degli URL
PATH="$PWD/.venv/bin:$PATH" ARCHIVEBOX_DATA=~/ArchiveBoxData ./scripts/archivebox_local.sh
```

La prima volta sono circa 200 URL e possono servire ore; le volte successive circa 200 copie datate a settimana.

Installazione:

```bash
cp scripts/launchd/it.lucalonga.carceri.archivebox.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/it.lucalonga.carceri.archivebox.plist
launchctl kickstart gui/$(id -u)/it.lucalonga.carceri.archivebox   # prova subito
tail -f ~/Library/Logs/carceri-archivebox.log
```

Disinstallazione:

```bash
launchctl bootout gui/$(id -u)/it.lucalonga.carceri.archivebox
rm ~/Library/LaunchAgents/it.lucalonga.carceri.archivebox.plist
```
