# Recupero dei due progetti precedenti

Questo progetto unifica il lavoro conservato nelle cartelle:

- `Snapmaker creatore profili filamento e spoolmann`;
- `Snapmaker U1 – Adaptive Pressure Advance`.

## Creatore profili Spoolman → Snapmaker Orca

La v0.5.0 usa direttamente le regole recuperate da
`spoolman_to_snapmaker_orca_v2.py`:

- PLA normale → `Snapmaker PLA Basic @U1`;
- PLA Rapid, Hyper, High Speed, HS, HF o SnapSpeed →
  `Snapmaker PLA SnapSpeed @U1`;
- PETG normale → `Snapmaker PETG @U1`;
- PETG veloce → `Snapmaker PETG HF`;
- basi dedicate per PLA/PETG CF, PLA Wood e PLA/PETG Translucent;
- nome, materiale, produttore e colore vengono letti da Spoolman;
- vendor e materiale già presenti nel nome Spoolman non vengono ripetuti;
- il suffisso generato è `@Snapmaker U1 (0.4 nozzle)`;
- il JSON eredita la versione dal profilo base Snapmaker trovato sul computer.

La cartella utente viene individuata partendo dalla home del sistema: non contiene
il nome di uno specifico utente macOS. La creazione usa modalità esclusiva e non
sovrascrive, elimina o rinomina file esistenti.

## Adaptive Pressure Advance recuperato

Dal master backup del 24 agosto 2026 risulta validato questo stato:

- macro `ULTRA v6 CHAIN`;
- `flow_calibrator.py CHAIN v6`;
- 5 punti, `LINEAR_FITTING`, `LOOP=6`, `DIST_SCALE=1.0`;
- pulizia per ogni K preservata;
- evento di calibrazione e temperatura mantenuti fra le celle;
- chiusura completa solo nell'ultima cella o in caso di errore;
- comando `APA_COIL_RUN_ULTRA EXTRUDER=X TEMP=YYY`;
- tempo validato della suite completa: circa 9 minuti e 39 secondi.

Il backup completo `APA_CHAIN_v6_SAFE.zip` è stato successivamente individuato nel
progetto già salvato. Contiene esattamente:

- `flow_calibrator.py`, versione CHAIN v6 attiva;
- `flow_calibrator_U1_ORIGINALE_BACKUP.py`, sorgente originale di riferimento;
- `adaptive_pa_macro.cfg`, macro ULTRA v6 CHAIN;
- `flow_calibrator_v6_changes.diff`, patch riproducibile;
- `LEGGIMI_PRIMA.txt`, note operative del backup.

La v0.5.0 conserva questi file in `vendor/apa-chain-v6-safe` con gli SHA-256 del
backup. Un test applica il diff alla copia originale e verifica che il risultato sia
identico byte per byte al `flow_calibrator.py` v6 recuperato.

La vecchia bozza sperimentale Bespok3D è stata rimossa dal pacchetto principale
nella v1.6.0 perché non veniva usata dall'applicazione standalone. Un'eventuale
integrazione futura sarà mantenuta e distribuita separatamente.

## Installatore standalone recuperato dalla procedura manuale

La v0.5.0 automatizza nella nostra applicazione il passaggio che era stato eseguito
manualmente sulla U1:

- target: `/home/lava/klipper/klippy/extras/flow_calibrator.py`;
- originale atteso: SHA-256 `dcbc26d5...a816e894`;
- CHAIN v6 attesa: SHA-256 `74ff7443...bc089ce`;
- backup storico riconosciuto:
  `flow_calibrator.py.BACKUP_ORIGINALE_20260824`.

Lo stato di stampa viene interrogato tramite Moonraker prima di qualsiasi accesso
SSH e nuovamente subito prima della scrittura. I test eseguono installazione,
verifica e ripristino soltanto su una struttura locale che replica la U1.

Il master backup specifica inoltre che il soft `RESTART` di Klipper non ricaricava
il modulo Python modificato. La nostra app non prova quindi a mascherare il limite:
dopo installazione o ripristino indica come obbligatori spegnimento completo, attesa
di 10–15 secondi e riaccensione.
