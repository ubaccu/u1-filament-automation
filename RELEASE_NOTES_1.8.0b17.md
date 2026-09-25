# U1 Filament Automation 1.8.0b17

## Italiano

Questa beta è pensata come release candidate prima della prima stabile 1.8.0.

### Novità

- Nuova **U1FA Control Center** nella schermata iniziale.
- Stato rapido di:
  - U1 / Moonraker
  - Spoolman
  - Snapmaker Orca
  - Adaptive PA
- Quattro riquadri dedicati ai toolhead **T0, T1, T2 e T3**, preparati per la futura assegnazione bobine.
- Accesso rapido a **Nuova bobina** e **Aggiornamenti U1FA**.
- Indicatore sintetico dello stato aggiornamenti.
- Testo dell'updater allineato al nuovo comportamento: dopo l'apertura del pacchetto già verificato, U1FA si chiude automaticamente per evitare l'errore macOS «app in uso».
- Il DMG macOS include **LEGGIMI PRIMA - macOS.html**, con i passaggi guidati per autorizzare il primo avvio tramite clic destro → Apri oppure Impostazioni di Sistema → Privacy e sicurezza → Apri comunque, senza disattivare Gatekeeper.

### Sicurezza

- La dashboard è **soltanto in lettura**: non effettua richieste alla stampante e non invia G-code.
- Nessuna modifica a firmware, configurazione U1, Klipper, Adaptive PA o profili Orca viene eseguita aprendo la dashboard.
- L'apertura dell'installer resta bloccata durante una calibrazione attiva.
- Download e verifica SHA-256 restano invariati.
- La guida macOS non esegue script o comandi Terminale: è un semplice file HTML informativo incluso nel DMG.

### Materiali già disponibili

- PLA
- PLA Rapid → profilo base Snapmaker PLA SnapSpeed
- PLA Silk
- PLA Wood
- PLA Translucent
- PLA-CF
- PETG
- PETG HF
- PETG Translucent
- PETG-CF

## English

This beta is intended as a release candidate before the first 1.8.0 stable release.

### New

- New **U1FA Control Center** on the home screen.
- Quick status for U1 / Moonraker, Spoolman, Snapmaker Orca and Adaptive PA.
- Dedicated **T0, T1, T2 and T3** cards, ready for future spool assignment.
- Quick links to New spool and U1FA updates.
- Compact update-status indicator.
- Updater copy now matches the auto-close behavior after opening an already verified installer package.
- The macOS DMG now includes **LEGGIMI PRIMA - macOS.html**, with first-launch Gatekeeper instructions using right-click → Open or System Settings → Privacy & Security → Open Anyway, without disabling Gatekeeper.

### Safety

- The dashboard is read-only and sends no printer command or G-code.
- Opening the dashboard does not modify firmware, U1 configuration, Klipper, Adaptive PA or Orca profiles.
- Opening an installer remains blocked while calibration is active.
- Download and SHA-256 verification behavior is unchanged.
- The macOS guide is a static HTML file and runs no script or Terminal command.
