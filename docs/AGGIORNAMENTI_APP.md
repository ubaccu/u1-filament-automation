# Aggiornamenti dell'app / Application updates

U1FA controlla in sottofondo le release pubbliche del progetto quando si avvia.
Il controllo riguarda esclusivamente l'applicazione installata sul computer:
non interroga, non aggiorna e non riavvia il firmware della Snapmaker U1.

U1FA checks the project's public releases in the background at startup. This
check only concerns the desktop application: it does not inspect, update or
restart the Snapmaker U1 firmware.

## Procedura / Workflow

1. L'app legge le release pubbliche tramite HTTPS senza credenziali personali.
2. Una versione stabile considera soltanto release stabili; una beta può ricevere
   beta successive e release stabili.
3. Viene selezionato esclusivamente il pacchetto adatto al sistema e
   all'architettura: DMG macOS, installer Windows oppure AppImage Linux.
4. Prima del download vengono mostrati versione, note, dimensione e SHA-256.
5. Il download viene scritto inizialmente in un file temporaneo. Diventa un
   pacchetto utilizzabile soltanto se dimensione e SHA-256 coincidono con i dati
   pubblicati dalla release.
6. L'utente deve confermare separatamente il download e l'apertura dell'installer.
   U1FA non sostituisce mai il proprio eseguibile mentre è aperta.

The app reads public releases over HTTPS without personal credentials, selects
the exact package for the current OS and architecture, downloads it to a temporary
file, verifies both size and SHA-256, and opens it only after a second explicit
confirmation. U1FA never replaces its running executable.

## Repository privato / Private repository

L'aggiornamento integrato non memorizza token GitHub. Per questo motivo, durante
il collaudo da un repository privato, il controllo può mostrare che il servizio
non è disponibile. È intenzionale: i tester ricevono manualmente le prime build.
Quando le release saranno pubbliche, l'avviso funzionerà senza configurazioni o
account GitHub per gli utenti finali.

The updater never stores a GitHub token. It may therefore be unavailable while
testing from a private repository; early builds are delivered manually. Once the
releases are public, end users receive notifications without configuration or a
GitHub account.

## Aggiornamenti firmware U1 / U1 firmware updates

Gli aggiornamenti dell'app e quelli della stampante sono due operazioni diverse.
Dopo un aggiornamento firmware usare **Configurazione o ripristino U1FA AutoPA
Mod**: l'app esegue prima un controllo in sola lettura e blocca file originali
non ancora convalidati. Consultare [FIRMWARE_COMPATIBILITY.md](FIRMWARE_COMPATIBILITY.md).

App updates and printer firmware updates are separate operations. After a
firmware update, use **Set up or restore U1FA AutoPA Mod**; the app first performs
a read-only check and blocks unvalidated original files.
