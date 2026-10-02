# U1 Filament Automation 2.0

## Italiano

U1FA 2.0.0 introduce il supporto fail-closed della release stabile **PAXX v1.6.0-paxx12-22** e consolida il percorso AutoPA firmware-2.0 già validato su Snapmaker U1 2.0.0.205.

### PAXX 12-22
- Firmware ufficiale PAXX scaricato e verificato tramite SHA-256 della release.
- Identità esatta convalidata:
  - `VERSION=1.6.0`
  - `FULLVERSION=1.6.0.267_20260815150420`
  - `BUILD_VERSION=1.6.0-paxx12-22-31c5a38`
  - profilo `extended`
- Convalidati gli SHA-256 reali di `flow_calibrator.py`, `filament_parameters.py`, `machine_state_manager.py` e `print_task_config.py`.
- Il `flow_calibrator.py` stock di PAXX 12-22 è byte-per-byte identico al calibratore stock Snapmaker 2.0.0.205 usato come base del porting AutoPA 2.0 U1FA.
- Verificata la superficie API richiesta dal porting AutoPA 2.0.
- Completata con successo un'installazione U1FA protetta in sandbox costruita direttamente dal rootfs del firmware PAXX ufficiale.
- Build PAXX, FULLVERSION o componenti con hash differenti restano bloccati.

### Compatibilità mantenuta
- Snapmaker U1 1.5.2 legacy.
- PAXX 12-21 legacy con fingerprint esatto.
- Snapmaker U1 2.0.0.205.
- PAXX 12-22 stabile con fingerprint esatto.
- Nessun supporto automatico a firmware futuri o sconosciuti.

### Aggiornamento
Chi usa **U1FA 1.8.3 o 1.8.4 può aggiornare direttamente a 2.0.0** tramite l'updater integrato: non è necessario installare prima una versione intermedia.

> Nota: PAXX 12-22 è stato validato dal firmware ufficiale e con installazione completa in sandbox. Non era disponibile una stampante fisica con PAXX 12-22 per un test hardware diretto.

## English

U1FA 2.0.0 adds fail-closed support for the current stable **PAXX v1.6.0-paxx12-22** release and consolidates the firmware-2.0 AutoPA path already validated on Snapmaker U1 2.0.0.205.

### PAXX 12-22
- The official PAXX firmware release was downloaded and verified against its release SHA-256.
- Exact validated identity:
  - `VERSION=1.6.0`
  - `FULLVERSION=1.6.0.267_20260815150420`
  - `BUILD_VERSION=1.6.0-paxx12-22-31c5a38`
  - `extended` profile
- Real SHA-256 fingerprints were validated for `flow_calibrator.py`, `filament_parameters.py`, `machine_state_manager.py` and `print_task_config.py`.
- PAXX 12-22's stock `flow_calibrator.py` is byte-for-byte identical to the stock Snapmaker 2.0.0.205 calibrator used as the U1FA firmware-2.0 AutoPA base.
- The runtime API surface required by the AutoPA 2.0 port was verified.
- A complete guarded U1FA installation succeeded in a sandbox built directly from the extracted official PAXX rootfs.
- Different PAXX build identities, FULLVERSION values or component hashes remain blocked.

### Compatibility retained
- Snapmaker U1 1.5.2 legacy.
- PAXX 12-21 legacy with exact fingerprint.
- Snapmaker U1 2.0.0.205.
- Stable PAXX 12-22 with exact fingerprint.
- No automatic support for future or unknown firmware.

### Updating
Users on **U1FA 1.8.3 or 1.8.4 can update directly to 2.0.0** through the built-in updater. No intermediate version is required.

> Note: PAXX 12-22 was validated from the official firmware image and with a complete sandbox installation. No physical PAXX 12-22 printer was available for direct hardware execution testing.

