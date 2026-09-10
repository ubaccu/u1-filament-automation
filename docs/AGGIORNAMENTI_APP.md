# Aggiornamenti dell'app U1FA

**Italiano** | [English](APP_UPDATES.md)

U1FA controlla in sottofondo le release pubbliche del progetto quando si avvia. Il controllo riguarda esclusivamente l'applicazione installata sul computer: **non interroga, non aggiorna e non riavvia il firmware della Snapmaker U1**.

## Come funziona

1. L'app legge le release pubbliche tramite HTTPS senza usare credenziali personali.
2. Una versione stabile considera soltanto release stabili; una beta può ricevere beta successive e release stabili.
3. Viene selezionato esclusivamente il pacchetto adatto al sistema operativo e all'architettura: DMG macOS, installer Windows oppure AppImage Linux.
4. Prima del download vengono mostrati versione, note di rilascio, dimensione e SHA-256.
5. Il download viene scritto inizialmente in un file temporaneo e diventa utilizzabile soltanto se dimensione e SHA-256 coincidono con i dati pubblicati nella release.
6. L'utente deve confermare separatamente il download e l'apertura dell'installer.
7. U1FA non sostituisce mai il proprio eseguibile mentre è in esecuzione.

## Canale pubblico di distribuzione

Lo sviluppo di U1FA viene mantenuto separatamente dal repository pubblico. Il repository pubblico contiene documentazione, supporto e release destinate agli utenti finali.

Ogni release distribuita include:

- pacchetti per le piattaforme supportate;
- `SHA256SUMS.txt`;
- archivio sorgente GPL corrispondente alla stessa versione.

L'updater integrato legge esclusivamente questo canale pubblico e non richiede token o account GitHub.

## Aggiornamenti firmware U1

Gli aggiornamenti dell'app e quelli della stampante sono due operazioni diverse.

Dopo un aggiornamento firmware Snapmaker U1:

1. apri U1FA con la stampante completamente inattiva;
2. usa **Controlla configurazione stampante**;
3. esegui prima il controllo in sola lettura;
4. se U1FA segnala file o firmware sconosciuti, fermati e non forzare manualmente l'installazione.

Consulta [Compatibilità firmware U1](COMPATIBILITA_FIRMWARE.md) prima di applicare modifiche ai file della stampante.

## macOS

Le build macOS attuali non sono notarizzate da Apple. Dopo aver installato una nuova versione, al primo avvio può essere necessario usare **tasto destro / Control-click → Apri → Apri**. Se macOS continua a bloccare l'app, usa **Impostazioni di Sistema → Privacy e Sicurezza → Apri comunque**.

Non è necessario disattivare Gatekeeper e U1FA non richiede comandi `xattr` per l'installazione normale.
