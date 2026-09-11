# U1 Filament Automation 1.8.1

## Italiano

U1FA 1.8.1 è un aggiornamento correttivo della release stabile 1.8.0 dedicato all'identità dei profili filamento creati per Snapmaker Orca.

### Correzioni

- I nuovi profili creati da U1FA salvano esplicitamente il **produttore reale di Spoolman** invece di ereditare erroneamente `Snapmaker` dal profilo di sistema usato come base.
- I nuovi profili vengono generati come profili Orca **standalone**, materializzando in sicurezza tutte le impostazioni effettive della catena di ereditarietà Snapmaker prima di rimuovere `inherits`. In questo modo il matcher Snapmaker può considerarli durante l'inoltro della stampa.
- Ogni nuovo profilo riceve un `filament_id` utente stabile compatibile con la convenzione Orca (`P` + 7 caratteri MD5 dell'identità filamento).
- Vendor, tipo e colori del filamento risultano disponibili direttamente nel profilo per l'abbinamento automatico Snapmaker.
- Se un profilo padre necessario non è disponibile, U1FA non crea un profilo incompleto: l'operazione viene saltata in sicurezza.

### Sicurezza e compatibilità

- I profili Orca **già esistenti non vengono convertiti né riscritti automaticamente** da questo bugfix.
- I valori già calibrati di **Pressure Advance e Adaptive Pressure Advance** restano quindi invariati.
- La riparazione già esistente del solo colore bianco segnaposto rimane limitata ai profili U1FA riconoscibili.
- Nessuna scrittura in Spoolman o sulla stampante viene introdotta da questa correzione.

Per ottenere il nuovo comportamento di auto-abbinamento su un profilo già creato con U1FA 1.8.0 servirà una ricreazione controllata oppure una futura migrazione esplicita: U1FA 1.8.1 non modifica silenziosamente profili già calibrati.

# English

U1FA 1.8.1 is a corrective update to stable release 1.8.0 focused on filament profile identity in Snapmaker Orca.

### Fixes

- Newly created U1FA profiles now explicitly store the **real Spoolman vendor** instead of incorrectly inheriting `Snapmaker` from the selected system base preset.
- New profiles are generated as Orca **standalone** presets. U1FA safely materializes the complete effective Snapmaker inheritance chain before removing `inherits`, allowing Snapmaker's sender matcher to consider the preset during print submission.
- Every new profile receives a stable Orca-compatible user `filament_id` (`P` + 7 MD5 characters from the filament identity).
- Vendor, material type and filament colours are directly available to Snapmaker's automatic matching logic.
- If a required parent preset is missing, U1FA fails closed and skips creation instead of writing an incomplete profile.

### Safety and compatibility

- **Existing Orca profiles are not automatically converted or rewritten** by this bugfix.
- Existing **Pressure Advance and Adaptive Pressure Advance** calibration values therefore remain untouched.
- The existing narrow white-placeholder colour repair remains limited to recognizable U1FA-managed profiles.
- This correction adds no new write operation to Spoolman or the printer.

To obtain the new automatic matching behaviour for a profile previously created by U1FA 1.8.0, a controlled recreation or an explicit future migration is required; U1FA 1.8.1 does not silently modify already calibrated profiles.
