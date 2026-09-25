# Italiano

## U1 Filament Automation 1.8.0b23

### Prima configurazione più semplice
- aggiunto il rilevamento automatico della U1/Moonraker nella rete locale;
- la scansione identifica Moonraker con richieste HTTP `GET /server/info` e conferma la presenza dell'oggetto Snapmaker `machine_state_manager` tramite `GET /printer/objects/list`;
- la scansione non invia G-code, non avvia stampe, non riscalda e non modifica la stampante;
- U1FA mostra sempre la U1 compatibile rilevata e chiede conferma prima di salvare qualsiasi connessione;
- dopo **Verifica e salva**, U1FA esegue la normale verifica di collegamento e usa la logica già esistente per individuare automaticamente Spoolman;
- se vengono trovate più U1 compatibili, U1FA chiede quale utilizzare;
- la configurazione manuale resta sempre disponibile.

### Posizione bobina più chiara
- il campo è ora **Posizione bobina / stoccaggio (facoltativa)**;
- esempi: Rack 3, scaffale PLA, cassetto 2;
- questa informazione viene salvata come posizione di stoccaggio e non viene mai interpretata come estrusore U1;
- l'estrusore fisico 1–4 continua a essere richiesto separatamente quando si prepara una calibrazione Adaptive PA.

### Anteprima nuova bobina
- la posizione di stoccaggio viene mostrata nel riepilogo quando è compilata;
- **Modifica dati** riporta al modulo mantenendo i valori inseriti, invece di azzerarli.

### Aggiornamenti
- le note di versione nella pagina Aggiornamenti vengono ora renderizzate in modo leggibile invece di mostrare i simboli Markdown grezzi.

### Sicurezza
- nessuna scansione automatica della LAN viene eseguita in background senza azione dell'utente: il rilevamento parte dal pulsante dedicato;
- la scansione di rete è esclusivamente in lettura;
- nessuna modifica a firmware, configurazione U1, profili Orca, Spoolman o Adaptive PA viene eseguita dalla funzione di rilevamento;
- il salvataggio delle connessioni avviene soltanto dopo conferma esplicita dell'utente.

---

# English

## U1 Filament Automation 1.8.0b23

### Easier first setup
- added automatic U1/Moonraker discovery on the local LAN;
- the scan identifies Moonraker with HTTP `GET /server/info` and confirms the Snapmaker `machine_state_manager` object with `GET /printer/objects/list`;
- scanning never sends G-code, starts prints, heats the printer or changes printer configuration;
- U1FA always shows the compatible U1 it found and asks for confirmation before saving any connection;
- after **Verify and save**, U1FA performs the normal connection verification and uses the existing automatic Spoolman discovery logic;
- when multiple compatible U1 endpoints are found, U1FA asks the user which one to use;
- manual configuration remains available at all times.

### Clearer spool location
- the field is now **Spool location / storage (optional)**;
- examples: Rack 3, PLA shelf, drawer 2;
- this is stored as inventory/storage information and is never interpreted as a U1 extruder;
- physical extruder 1–4 is still selected separately when preparing an Adaptive PA calibration.

### New spool preview
- the storage location is shown in the preview when provided;
- **Edit data** returns to the form with the entered values preserved instead of clearing them.

### Updates
- release notes on the Updates page are now rendered in a readable format instead of showing raw Markdown markers.

### Safety
- no LAN scan runs silently in the background without a user action: discovery starts from the dedicated button;
- the LAN scan is read-only;
- the discovery feature does not modify firmware, U1 configuration, Orca profiles, Spoolman or Adaptive PA;
- connections are saved only after explicit user confirmation.
