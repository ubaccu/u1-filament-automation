# U1 Filament Automation 1.8.1

## Italiano

U1FA 1.8.1 è un aggiornamento correttivo della release stabile 1.8.0 dedicato all'identità dei profili filamento creati per Snapmaker Orca e alla coerenza dei dati provenienti da Spoolman.

### Correzioni principali

- I nuovi profili U1FA salvano esplicitamente il **produttore reale di Spoolman** invece di ereditare `Snapmaker` dal preset di sistema usato come base.
- I profili vengono materializzati come preset Orca **standalone**: U1FA risolve in sicurezza l'intera catena di ereditarietà Snapmaker e poi rimuove `inherits`, `setting_id` e `instantiation` dall'identità utente.
- Ogni nuovo profilo riceve un `filament_id` utente stabile compatibile con la convenzione Orca (`P` + 7 caratteri MD5 dell'identità filamento).
- Per le famiglie speciali U1FA usa ora il **tipo materiale esatto visto dal matcher della Snapmaker U1**, ad esempio `PLA TRANSLUCENT`, `PLA SILK`, `PLA WOOD`, `PLA HIGH SPEED`, `PETG TRANSLUCENT`, `PETG HIGH SPEED`, `PLA-CF` e `PETG-CF`.
- Il bug reale che impediva a un profilo personalizzato Deeplee PLA Translucent di essere selezionato automaticamente in Print Preprocessing è quindi risolto.
- I profili U1FA già gestiti possono ricevere la migrazione dell'identità 1.8.1 anche se erano già presenti nel `watch-state`; una cancellazione manuale volontaria continua invece a essere rispettata.
- La migrazione conserva i valori utente già presenti, inclusi **Pressure Advance, Adaptive Pressure Advance, temperature, portata volumetrica e altre regolazioni**.
- Prima di sostituire un profilo migrato viene mantenuto un backup byte-per-byte `.u1fa-pre181.bak` senza proliferazione di copie.
- I colori Spoolman vengono mantenuti nel profilo Orca; un colore personalizzato non bianco già presente in un profilo esistente non viene sovrascritto.
- Per un **profilo appena creato**, `filament_density` viene ora allineato alla densità reale registrata in Spoolman invece di mantenere automaticamente la densità del preset Snapmaker di base. I profili esistenti non vengono riscritti soltanto perché la densità Spoolman cambia.
- Se un profilo padre Snapmaker necessario non è disponibile, U1FA non crea un preset incompleto e si blocca in sicurezza.

### Validazione reale Snapmaker U1

La correzione è stata verificata su una Snapmaker U1 reale con un filamento **Deeplee PLA Translucent**:

- vendor U1/Orca: `Deeplee`;
- tipo runtime: `PLA TRANSLUCENT`;
- colore: `CAF0FE`;
- slot fisico: 2;
- Orca ha associato automaticamente il filamento allo slot 2 nella schermata **Print Preprocessing**, senza modifica manuale del JSON;
- dopo la correzione finale della densità, il profilo ricreato da Spoolman contiene `filament_density: ["1.25"]` mantenendo vendor, tipo e colore corretti.

La suite finale contiene **238 test** ed è risultata completamente verde. Sono state inoltre validate le build macOS Intel, macOS Apple Silicon, Windows x64, Linux x86_64 e l'archivio sorgente corrispondente.

### Sicurezza e compatibilità

- La migrazione automatica riguarda solo profili con identità U1FA riconoscibile.
- I profili personalizzati non riconosciuti come U1FA non vengono modificati.
- I profili già corretti non vengono riscritti a ogni sincronizzazione.
- Questa release non aggiorna il firmware Snapmaker U1 e non riduce le protezioni già presenti per configurazione stampante, backup e scritture PA.

---

## English

U1FA 1.8.1 is a corrective update to stable release 1.8.0 focused on Snapmaker Orca filament-profile identity and consistency with Spoolman metadata.

### Main fixes

- Newly created U1FA profiles explicitly store the **real Spoolman vendor** instead of inheriting `Snapmaker` from the selected system preset.
- Profiles are materialized as Orca **standalone** presets: U1FA safely resolves the complete Snapmaker inheritance chain and then removes `inherits`, `setting_id` and `instantiation` from the user preset identity.
- Every new profile receives a stable Orca-compatible user `filament_id` (`P` + 7 MD5 characters from the filament identity).
- Special material families now use the **exact sender-facing material type reported by the Snapmaker U1**, including `PLA TRANSLUCENT`, `PLA SILK`, `PLA WOOD`, `PLA HIGH SPEED`, `PETG TRANSLUCENT`, `PETG HIGH SPEED`, `PLA-CF` and `PETG-CF`.
- This fixes the real issue that prevented a custom Deeplee PLA Translucent profile from being selected automatically in Print Preprocessing.
- Existing managed U1FA profiles can receive the 1.8.1 identity migration even when already present in `watch-state`; an intentional manual deletion is still respected.
- Migration preserves existing user values, including **Pressure Advance, Adaptive Pressure Advance, temperatures, volumetric-flow limits and other tuning**.
- A byte-for-byte `.u1fa-pre181.bak` recovery copy is kept before migration without creating repeated backup files.
- Spoolman colours are retained in the Orca profile; an intentional non-white custom colour in an existing profile is preserved.
- For a **newly created profile**, `filament_density` is now aligned with the real density stored in Spoolman instead of automatically keeping the Snapmaker base-preset density. Existing profiles are not rewritten merely because the Spoolman density later changes.
- If a required Snapmaker parent preset is unavailable, U1FA fails closed instead of creating an incomplete preset.

### Real Snapmaker U1 validation

The fix was validated on a real Snapmaker U1 using **Deeplee PLA Translucent**:

- U1/Orca vendor: `Deeplee`;
- runtime type: `PLA TRANSLUCENT`;
- colour: `CAF0FE`;
- physical slot: 2;
- Orca automatically matched the filament to slot 2 in **Print Preprocessing** without any manual JSON edit;
- after the final density fix, recreating the profile from Spoolman produced `filament_density: ["1.25"]` while keeping the correct vendor, type and colour.

The final suite contains **238 tests**, all passing. macOS Intel, macOS Apple Silicon, Windows x64, Linux x86_64 and the corresponding source archive were also validated successfully.

### Safety and compatibility

- Automatic migration is limited to profiles with a recognizable U1FA identity.
- Unrecognized custom profiles are not modified.
- Already-correct profiles are not rewritten on every sync.
- This release does not update Snapmaker U1 firmware and does not weaken the existing safeguards around printer setup, backups or PA writes.
