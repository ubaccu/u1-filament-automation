# U1 Filament Automation 1.8.1

## Italiano

U1FA 1.8.1 è un aggiornamento correttivo della release stabile 1.8.0 dedicato all'identità dei profili filamento creati per Snapmaker Orca.

### Correzioni

- I nuovi profili creati da U1FA salvano esplicitamente il **produttore reale di Spoolman** invece di ereditare erroneamente `Snapmaker` dal profilo di sistema usato come base.
- I nuovi profili vengono generati come profili Orca **standalone**, materializzando in sicurezza tutte le impostazioni effettive della catena di ereditarietà Snapmaker prima di rimuovere `inherits`. In questo modo il matcher Snapmaker può considerarli durante l'inoltro della stampa.
- Ogni nuovo profilo riceve un `filament_id` utente stabile compatibile con la convenzione Orca (`P` + 7 caratteri MD5 dell'identità filamento).
- Vendor, tipo e colori del filamento risultano disponibili direttamente nel profilo per l'abbinamento automatico Snapmaker.
- I profili U1FA 1.8.0 già esistenti e riconoscibili vengono migrati in modo controllato alla nuova identità 1.8.1: il profilo Snapmaker di base viene materializzato, `inherits` viene rimosso e vendor/`filament_id` vengono corretti.
- Durante la migrazione vengono conservati i valori utente già presenti, compresi **Pressure Advance, Adaptive Pressure Advance, temperature, portata volumetrica e altre regolazioni**.
- Prima di sostituire un profilo migrato viene creato un backup byte-per-byte con suffisso `.u1fa-pre181-...bak`.
- Un colore personalizzato non bianco già presente nel profilo viene preservato; solo un colore mancante o bianco segnaposto viene riallineato ai dati Spoolman.
- Se un profilo padre necessario non è disponibile, U1FA non crea né migra un profilo incompleto: l'operazione viene saltata in sicurezza.

### Sicurezza e compatibilità

- La migrazione automatica riguarda solo profili con identità U1FA riconoscibile (`name` e `filament_settings_id` coerenti e profilo utente).
- I profili già corretti in formato 1.8.1 non vengono riscritti a ogni sincronizzazione.
- I profili personalizzati non riconosciuti come U1FA non vengono modificati.
- Nessuna scrittura in Spoolman o sulla stampante viene introdotta da questa correzione.

Dopo l'aggiornamento a 1.8.1, una normale sincronizzazione può quindi correggere anche un profilo creato con U1FA 1.8.0 senza richiedere di cancellarlo e ricrearlo e senza perdere una calibrazione PA già salvata.

# English

U1FA 1.8.1 is a corrective update to stable release 1.8.0 focused on filament profile identity in Snapmaker Orca.

### Fixes

- Newly created U1FA profiles now explicitly store the **real Spoolman vendor** instead of incorrectly inheriting `Snapmaker` from the selected system base preset.
- New profiles are generated as Orca **standalone** presets. U1FA safely materializes the complete effective Snapmaker inheritance chain before removing `inherits`, allowing Snapmaker's sender matcher to consider the preset during print submission.
- Every new profile receives a stable Orca-compatible user `filament_id` (`P` + 7 MD5 characters from the filament identity).
- Vendor, material type and filament colours are directly available to Snapmaker's automatic matching logic.
- Recognizable existing U1FA 1.8.0 profiles are migrated in a controlled way to the 1.8.1 identity: the Snapmaker base is materialized, `inherits` is removed, and vendor/`filament_id` are corrected.
- Migration preserves existing user values, including **Pressure Advance, Adaptive Pressure Advance, temperatures, volumetric-flow limits and other profile tuning**.
- A byte-for-byte backup with a `.u1fa-pre181-...bak` suffix is created before a migrated profile is replaced.
- An intentional non-white custom colour is preserved; only a missing or white placeholder colour is realigned with Spoolman data.
- If a required parent preset is unavailable, U1FA fails closed and does not create or migrate an incomplete profile.

### Safety and compatibility

- Automatic migration is limited to profiles with a recognizable U1FA identity (`name` and `filament_settings_id` agree and the preset is a user profile).
- Profiles already corrected to the 1.8.1 format are not rewritten on every sync.
- Unrecognized custom profiles are not modified.
- This correction adds no new write operation to Spoolman or the printer.

After updating to 1.8.1, a normal sync can therefore repair a profile previously created by U1FA 1.8.0 without requiring deletion/recreation and without losing an existing PA calibration.
