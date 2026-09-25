# Italiano

## U1 Filament Automation 1.8.0

La prima release stabile di U1FA consolida il workflow **Spoolman → Snapmaker Orca → Adaptive Pressure Advance** testato durante la serie beta 1.8.0.

### Conferma bobina più chiara e sicura

- prima di scrivere, la schermata di conferma indica separatamente cosa verrà **creato** o **riutilizzato** in Spoolman;
- mostra se il profilo Snapmaker Orca è **nuovo**, **già esistente** oppure un unico profilo legacy **equivalente** riconosciuto in modo prudente;
- se nel profilo esistente è rilevato Adaptive PA, U1FA indica esplicitamente che **non verrà modificato durante la creazione della bobina/profilo**;
- se vengono trovati più profili equivalenti, la creazione viene bloccata **prima di qualsiasi scrittura in Spoolman** invece di scegliere automaticamente;
- la preparazione dell'anteprima legge soltanto i JSON Orca e non invia comandi alla stampante.

### Workflow consolidato

- rilevamento U1/Moonraker avviato dall'utente e basato su controlli HTTP in sola lettura;
- creazione/riuso di vendor e filamenti Spoolman e gestione bobine mono o multicolore;
- selezione automatica del profilo base Snapmaker Orca per le famiglie PLA/PETG supportate;
- protezione anti-doppione per profili Orca esatti ed equivalenti riconosciuti;
- envelope di calibrazione automatico dal limite volumetrico ereditato dal profilo;
- calibrazione Adaptive PA guidata con recupero risultato, backup e scrittura sul profilo selezionato;
- updater multipiattaforma con verifica dimensione e SHA-256.

### Documentazione e supporto pubblico

- documentazione finale allineata in italiano e inglese;
- GitHub Issues diventa il canale ufficiale per bug e richieste di nuove funzioni;
- moduli strutturati per le segnalazioni e policy separata per vulnerabilità di sicurezza;
- crediti e licenze delle componenti upstream mantenuti in `THIRD_PARTY_NOTICES.md`;
- ogni release continua a includere `SHA256SUMS.txt` e il sorgente GPL corrispondente alla stessa versione.

### Sicurezza

U1FA non aggiorna il firmware Snapmaker U1. Le modifiche ai file della stampante restano protette da controlli sullo stato, SHA-256, backup e conferme esplicite. Firmware o file sconosciuti vengono bloccati. Dopo un aggiornamento firmware eseguire prima **Controlla configurazione stampante** in sola lettura.

---

# English

## U1 Filament Automation 1.8.0

The first stable U1FA release consolidates the **Spoolman → Snapmaker Orca → Adaptive Pressure Advance** workflow tested throughout the 1.8.0 beta series.

### Clearer and safer spool confirmation

- before any write, the confirmation page separately shows what will be **created** or **reused** in Spoolman;
- it reports whether the Snapmaker Orca profile is **new**, **already present**, or one conservatively recognized **equivalent** legacy profile;
- when Adaptive PA is detected in an existing profile, U1FA explicitly states that it **will not be modified during spool/profile creation**;
- if multiple equivalent profiles are found, creation is blocked **before any Spoolman write** instead of choosing automatically;
- preparing this preview only reads Orca JSON files and sends no printer command.

### Consolidated workflow

- user-triggered U1/Moonraker discovery using read-only HTTP checks;
- Spoolman vendor/filament reuse or creation plus single- and multicolour spool management;
- automatic Snapmaker Orca base-profile selection for supported PLA/PETG families;
- duplicate-safe handling for exact and conservatively recognized equivalent Orca profiles;
- automatic calibration envelope from the profile's inherited volumetric-flow limit;
- guided Adaptive PA calibration with result recovery, backup and write-back to the selected profile;
- cross-platform updater with package-size and SHA-256 verification.

### Public documentation and support

- final documentation aligned in English and Italian;
- GitHub Issues is the official channel for bugs and feature requests;
- structured report forms and a separate policy for security vulnerabilities;
- upstream credits and licences remain documented in `THIRD_PARTY_NOTICES.md`;
- every release continues to include `SHA256SUMS.txt` and version-matched GPL corresponding source.

### Safety

U1FA does not update Snapmaker U1 firmware. Printer-file changes remain protected by printer-state checks, SHA-256 validation, backups and explicit confirmation. Unknown firmware or files are blocked. After a firmware update, run **Check printer setup** in read-only mode first.
