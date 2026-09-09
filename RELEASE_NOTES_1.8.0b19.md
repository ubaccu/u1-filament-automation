# U1 Filament Automation 1.8.0b19

## Italiano

Questa beta pulisce la schermata iniziale dopo il collaudo della nuova dashboard.

### Novità

- Rimossi dalla dashboard i riquadri T0/T1/T2/T3 per l'assegnazione bobina: non avevano ancora una funzione operativa reale e potevano creare confusione.
- Il **U1FA Control Center** resta compatto e mostra solo:
  - U1 / Moonraker
  - Spoolman
  - Snapmaker Orca
  - Adaptive PA
  - stato aggiornamenti
- Lo stato U1 e Spoolman usa ora la dicitura **Endpoint configurato** per non confondere la presenza dell'indirizzo con una verifica live della connessione.
- Rimossi dalla home i riquadri duplicati di **Aggiornamenti U1FA** e **Connessioni**: restano accessibili direttamente dai pulsanti del Control Center.
- Le sezioni operative della home sono ora raggruppate in pannelli richiudibili:
  - **Sistema e manutenzione**
  - **Gestione filamenti** (aperto di default)
  - **Sicurezza e applicazione**
- La gestione filamenti mantiene intatti nuova bobina, calibrazione Adaptive PA e sincronizzazione automatica.
- Aggiunto un accesso rapido alla calibrazione dal Control Center.

### Sicurezza

- La modifica riguarda soltanto la presentazione della home.
- Nessun comando stampante o G-code aggiunto o modificato.
- Nessuna modifica a firmware, Klipper, PAXX, Adaptive PA, profili Orca o dati Spoolman.
- Il comportamento dell'updater e la verifica SHA-256 restano invariati.

## English

This beta cleans up the home screen after testing the new dashboard.

### New

- Removed the T0/T1/T2/T3 spool-assignment cards from the dashboard because they did not yet provide a real operational function.
- The **U1FA Control Center** now stays compact and only shows U1/Moonraker, Spoolman, Snapmaker Orca, Adaptive PA and update status.
- U1 and Spoolman now say **Endpoint configured** instead of implying a live connectivity check.
- Removed duplicate **U1FA updates** and **Connections** cards from the home page; both remain directly accessible from the Control Center.
- Existing home actions are grouped into collapsible sections:
  - **System and maintenance**
  - **Filament management** (open by default)
  - **Safety and application**
- New spool, Adaptive PA calibration and automatic synchronization remain unchanged.

### Safety

- This release changes home-page presentation only.
- No printer command or G-code changes.
- No firmware, Klipper, PAXX, Adaptive PA, Orca profile or Spoolman data changes.
- Updater behavior and SHA-256 verification remain unchanged.
