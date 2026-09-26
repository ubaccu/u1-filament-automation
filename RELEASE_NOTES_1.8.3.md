# U1FA 1.8.3

## Italiano

U1FA 1.8.3 mantiene la grafica e il flusso principale della 1.8.2, aggiungendo compatibilità firmware più ampia, calibrazione multi-bobina sequenziale e supporto opzionale a Orca Slicer standard.

- resta supportata la linea firmware Snapmaker U1 1.5.2 con il flusso AutoPA legacy;
- aggiunto supporto fail-closed per PAXX `1.5.2-paxx12-21-2a8893`, consentito solo con identità build e hash Klipper convalidati;
- aggiunto il porting AutoPA dedicato per firmware Snapmaker U1 `2.0.0.205_20260914173503`;
- gli asset firmware 2.0.0.205 incorporati sono byte-per-byte identici ai file validati sulla U1 reale e protetti tramite SHA-256;
- riconosciuta anche la variante `print_task_config.py` Adaptive PA realmente rilevata sulla U1 2.0.0.205 (`3770801d…`), dopo confronto con l'originale: sono accettati solo gli hash esatti convalidati e qualsiasi altra variante resta bloccata;
- la calibrazione firmware 2.0 usa la CHAIN a 5 punti, LOOP=6, modalità MEASURE-ONLY e stabilizzazione termica di 3 secondi, senza sovrascrivere il Flow K nativo Snapmaker;
- corretto il packaging Windows degli asset protetti, evitando conversioni LF→CRLF che alteravano gli hash;
- migliorata la diagnosi SSH quando Root Access risulta attivo ma il servizio SSH rifiuta la connessione;
- l'app desktop non riapre più silenziosamente un vecchio processo U1FA 1.8.2 rimasto sulla porta locale: una 1.8.3 riusa soltanto un'istanza della stessa versione e segnala esplicitamente una versione precedente;
- aggiunta una coda da 2 a 4 bobine: le calibrazioni vengono eseguite rigorosamente una alla volta, ogni profilo viene salvato prima di passare al successivo e la coda si ferma al primo errore;
- dopo la creazione di una bobina la schermata finale distingue chiaramente tra **Calibra questa bobina ora** e **Crea un'altra bobina / calibra più bobine dopo**, così il percorso multi-bobina non richiede di avviare calibrazioni singole intermedie;
- Snapmaker Orca resta lo slicer principale;
- Orca Slicer standard può essere rilevato separatamente e, solo dopo opt-in esplicito, ricevere un mirror protetto dei profili U1FA; la Home mostra ora anche un badge **Orca Slicer** per rendere visibile questa compatibilità;
- aggiunti i profili filamento U1 0,4 mm di Snapmaker Orca 2.4.0 per **TPU**, **PEBA 90A** e **PLA Rainbow**, usando le basi ufficiali Snapmaker e i relativi valori iniziali di temperatura/densità;
- verificato direttamente nel sorgente Snapmaker Orca 2.4.0 che i controlli **Adaptive PA** sono nascosti dalla GUI per scelta prodotto, ma le opzioni `adaptive_pressure_advance`, il modello e la logica di slicing restano attivi; U1FA li scrive direttamente nel profilo filamento e mostra dopo la calibrazione lo stato **Adaptive PA ATTIVA nel profilo**;
- per TPU e PEBA la calibrazione Adaptive PA passa automaticamente l'intervallo K **0,15–0,45**, coerente con `filament_parameters.py` del firmware 2.0.0.205; PLA Rainbow mantiene **0,005–0,040**;
- U1FA 1.8.3 resta focalizzata sui profili filamento U1 **0,4 mm**: i nuovi preset 2.4.0 esclusivi 0,2/0,6/0,8 mm non vengono dichiarati supportati e i preset processo/stampa non richiedono un proprio write-back PA;
- profili Orca Slicer esterni o modificati manualmente non vengono sovrascritti: i target gestiti sono tracciati tramite SHA-256, con backup prima degli aggiornamenti;
- la modalità singola e la modalità manuale avanzata restano disponibili;
- Fast Max Flow automatico resta escluso;
- updater verificato per il passaggio da 1.8.2 stabile a 1.8.3 stabile: le beta 1.8.3 non vengono proposte automaticamente agli utenti stabili;
- pacchetti già verificati su Windows x64, Linux x86_64, macOS Intel e macOS Apple Silicon;
- README GitHub italiano/inglese e guide incluse nel DMG aggiornati al flusso finale 1.8.3.
- archivio sorgente GPL corrispondente verificato separatamente.

## English

U1FA 1.8.3 keeps the 1.8.2 visual layout and main workflow while adding broader firmware compatibility, sequential multi-spool calibration and optional standard Orca Slicer support.

- the Snapmaker U1 1.5.2 firmware line remains supported with the legacy AutoPA path;
- adds fail-closed support for PAXX `1.5.2-paxx12-21-2a8893`, allowed only when the exact build identity and validated Klipper hashes match;
- adds a dedicated AutoPA port for Snapmaker U1 firmware `2.0.0.205_20260914173503`;
- bundled firmware-2.0 assets are byte-for-byte identical to the files validated on the real U1 and protected by SHA-256;
- also recognizes the reviewed Adaptive-PA `print_task_config.py` variant observed on the real U1 2.0.0.205 (`3770801d…`); only exact validated hashes are accepted and every other variant remains blocked;
- firmware-2.0 calibration uses the 5-point CHAIN, LOOP=6, MEASURE-ONLY mode and 3-second thermal stabilization without overwriting Snapmaker's native Flow K;
- fixes Windows packaging of protected assets so LF→CRLF conversion cannot invalidate hashes;
- improves SSH diagnostics when Root Access appears enabled but the SSH service still refuses the connection;
- the desktop app no longer silently reopens an older U1FA 1.8.2 process left on the local port: 1.8.3 reuses only an instance of the same version and explicitly reports an older one;
- adds a 2-to-4-spool queue: calibrations run strictly one at a time, each profile is saved before the next spool starts, and the queue stops at the first error;
- after creating a spool, the completion screen now clearly separates **Calibrate this spool now** from **Create another spool / calibrate multiple spools later**, so the multi-spool workflow does not require intermediate single calibrations;
- Snapmaker Orca remains the primary slicer;
- standard Orca Slicer may be detected separately and, only after explicit opt-in, receive a protected mirror of U1FA profiles; the Home hero now also shows an **Orca Slicer** badge to make this compatibility visible;
- adds the Snapmaker Orca 2.4.0 U1 0.4 mm filament profiles for **TPU**, **PEBA 90A** and **PLA Rainbow**, using the official Snapmaker bases and matching initial temperature/density values;
- verified directly in the Snapmaker Orca 2.4.0 source that the **Adaptive PA** controls are hidden from the GUI by product choice while the `adaptive_pressure_advance` settings, model and slicing logic remain active; U1FA writes them directly to the filament profile and now reports **Adaptive PA ACTIVE in profile** after calibration;
- TPU and PEBA Adaptive PA calibration automatically uses K range **0.15–0.45**, matching firmware 2.0.0.205 `filament_parameters.py`; PLA Rainbow keeps **0.005–0.040**;
- U1FA 1.8.3 remains focused on U1 **0.4 mm** filament profiles: new 2.4.0 presets exclusive to 0.2/0.6/0.8 mm are not claimed as supported, and process/print presets do not require their own PA write-back;
- foreign or manually modified standard Orca profiles are never overwritten: managed targets are tracked by SHA-256 and backed up before updates;
- single-spool and advanced manual calibration remain available;
- automatic Fast Max Flow remains out of scope;
- updater path is verified from stable 1.8.2 to stable 1.8.3: 1.8.3 betas are not offered automatically to stable users;
- packages have already been validated on Windows x64, Linux x86_64, macOS Intel and macOS Apple Silicon;
- GitHub README files and the Italian/English guides included in the DMG are updated for the final 1.8.3 workflow.
- matching GPL source archive validated separately.
