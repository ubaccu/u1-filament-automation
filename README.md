# U1 Filament Automation

Applicazione standalone community per:

- creazione guidata di vendor, filamenti e bobine in Spoolman;
- generazione automatica dei profili filamento Snapmaker Orca;
- calibrazione Adaptive Pressure Advance guidata e applicazione automatica;
- Spoolman già installato localmente o raggiungibile in rete;
- installazione e ripristino sicuri di U1FA AutoPA Mod sulla U1 Stock;
- compatibilità con Spoolman locale o fornito da sistemi esterni come PAXX;
- profili filamento di Snapmaker Orca;
- acquisizione offline delle tabelle Adaptive Pressure Advance dai log ULTRA v6.

La v1.0.0 recupera il sincronizzatore già sviluppato nel progetto precedente. Trova i
servizi, legge bobine e filamenti e ricava nome, colore e profilo base dalle
informazioni inserite in Spoolman. `doctor` e `sync` sono in sola lettura;
la scrittura reale è bloccata senza una conferma distinta e intenzionale.

La v0.8.0 collega inoltre il risultato della calibrazione ULTRA v6 alla bobina
Spoolman e al relativo profilo Orca. In anteprima non scrive nulla; in applicazione
crea prima un backup e modifica esclusivamente i campi Pressure Advance.

La v0.9.0 aggiunge l'acquisizione automatica di una nuova calibrazione dalla cache
Moonraker: ascolta in sola lettura, ignora tutto ciò che era già presente all'avvio
e applica il risultato soltanto dopo aver ricevuto tutti i cinque punti.

La v1.0.0 consente inoltre di recuperare l'ultima suite completa dalla cache quando
la calibrazione è riuscita ma l'associazione automatica del nome è stata bloccata.

U1FA AutoPA Mod usa internamente il motore tecnico `CHAIN v6`. Include inoltre il
backup esatto `APA CHAIN v6 SAFE`, un lettore offline dei suoi
log e l'installatore del `flow_calibrator.py` v6 con controllo stampa, backup,
verifica sintattica, sostituzione atomica e ripristino. L'app è standalone e
funziona sulla U1 Stock: non richiede PAXX, Bespok3D o plugin esterni. Un'eventuale
integrazione Bespok3D sarà mantenuta come progetto separato.

## Beta privata desktop / Private desktop beta

La versione corrente è **1.8.0 Beta 1**. Prima della pubblicazione stabile viene
distribuita in un repository privato a un piccolo gruppo di collaudatori. Seguire
la checklist [docs/BETA_TESTING.md](docs/BETA_TESTING.md) e iniziare sempre dai
controlli in sola lettura. La procedura per gli aggiornamenti U1 è in
[docs/FIRMWARE_COMPATIBILITY.md](docs/FIRMWARE_COMPATIBILITY.md).

The current build is **1.8.0 Beta 1**. It is distributed from a private repository
to selected testers before the stable public release. Follow
[docs/BETA_TESTING.md](docs/BETA_TESTING.md) and always begin with read-only checks.

I pacchetti sono autonomi e includono Python:

- macOS Apple Silicon: `macOS-arm64.dmg`;
- macOS Intel: `macOS-x86_64.dmg`;
- Windows 10/11 x64: `Windows-x64-Setup.exe`;
- Linux x86_64: `.AppImage`.

### macOS

### DMG per gli utenti / DMG for users

Dalla v1.6.0 la distribuzione macOS avviene con due DMG autonomi:

- `macOS-arm64` per Mac Apple Silicon (M1, M2, M3 e successivi);
- `macOS-x86_64` per Mac Intel.

Aprire il DMG, trascinare **U1 Filament Automation** in **Applicazioni** e avviare
l'app. Python è incorporato: l'utente non deve installarlo né usare il Terminale.
Le build di test non ancora firmate e notarizzate possono richiedere, soltanto al
primo avvio, **tasto destro sull'app → Apri → Apri**.

The final distribution provides separate self-contained DMGs for Apple Silicon
and Intel Macs. Open the DMG, drag **U1 Filament Automation** to **Applications**
and launch it. Python is bundled; no Terminal command or separate installation is
required. An unsigned test build may require **right-click → Open → Open** once.

### Windows 10/11 x64

Avviare `U1-Filament-Automation-...-Windows-x64-Setup.exe` e seguire
l'installazione bilingue. L'app viene installata nel profilo dell'utente e non
richiede diritti amministrativi. Una beta non firmata può mostrare un avviso
Microsoft Defender SmartScreen.

Per configurare o ripristinare U1FA AutoPA Mod deve essere presente soltanto
**OpenSSH Client** di Windows; non serve OpenSSH Server. Se manca, l'app lo segnala
senza modificare la U1. Si abilita da **Impostazioni → Sistema → Funzionalità
facoltative → Visualizza funzionalità → OpenSSH Client**. Creazione bobine,
sincronizzazione Spoolman e profili Orca restano utilizzabili anche prima di
installare il client SSH.

Run the Windows setup and follow the bilingual installer. The app is installed per
user and does not require administrator rights. **OpenSSH Client** is required only
for installing or restoring the printer-side modification; it is never bundled or
silently installed by U1FA.

### Linux x86_64

Scaricare l'AppImage, renderla eseguibile e avviarla:

```bash
chmod +x U1-Filament-Automation-*-Linux-x86_64.AppImage
./U1-Filament-Automation-*-Linux-x86_64.AppImage
```

Per la configurazione stampante serve il pacchetto di sistema `openssh-client`.
L'AppImage include Python ma non modifica i pacchetti della distribuzione. La beta
iniziale supporta Linux x86_64; ARM64 Linux verrà valutato dopo il collaudo.

Per arrestare correttamente il servizio e il monitor Spoolman usare
**Chiudi applicazione / Close application** nella home. La chiusura rimane bloccata
durante la calibrazione fino al salvataggio del risultato.

### Interfaccia guidata v1.8 / Guided interface v1.8

La v1.8 completa la catena in un'unica interfaccia locale selezionabile in
Italiano o English:

1. al primo avvio chiede e verifica IP/hostname della U1 e indirizzo Spoolman;
2. controlla e configura in sicurezza calibratore e macro sulla U1 Stock;
3. inserisce o riutilizza il vendor e il filamento in Spoolman;
4. crea la nuova bobina con peso, tara, colore, temperature, posizione e lotto;
5. genera automaticamente il nuovo profilo nella cartella reale di Snapmaker Orca
   e una copia nella sandbox, scegliendo la base dalle parole del nome (`RAPID`,
   `HYPER`, `HS`, `HF`, ecc.);
6. porta direttamente alla selezione dello slot fisico e all'anteprima dei comandi;
7. avvia la calibrazione solo dopo una seconda conferma e applica il risultato PA
   al profilo reale selezionato e alla copia sandbox, con backup.
8. mentre la GUI è aperta, controlla Spoolman ogni 10 secondi e genera anche i
   profili relativi a bobine aggiunte manualmente dal sito Spoolman.
9. controlla in sottofondo la disponibilità di nuove versioni U1FA e propone il
   pacchetto corretto per il sistema operativo, verificandone lo SHA-256 prima di
   conservarlo.

Gli aggiornamenti dell'app sono descritti in [docs/AGGIORNAMENTI_APP.md](docs/AGGIORNAMENTI_APP.md).
Il controllo usa soltanto le release pubbliche del progetto e non richiede token
GitHub. Durante il collaudo in repository privato può quindi risultare non
disponibile: si attiverà normalmente quando pubblicheremo le release. Nessuna
verifica dell'app aggiorna il firmware o invia comandi alla stampante.

Dopo ogni aggiornamento firmware U1, riaprire la sezione di configurazione: la mod,
`adaptive_pa_macro.cfg` o l'include potrebbero essere stati rimossi. L'app propone
il ripristino soltanto per un originale Snapmaker con SHA-256 già convalidato;
qualunque nuova versione viene bloccata finché non è stata confrontata e testata.
Il firmware U1 1.6.0 è attualmente indicato come **in verifica** nella Beta 1.

La calibrazione Adaptive PA richiede indicativamente **circa 10 minuti**. Il tempo
può variare leggermente in funzione della temperatura e dello stato iniziale della
U1. Durante l'esecuzione non spegnere o riavviare la stampante e non inviare altri
comandi da Fluidd o dal display.

Version 1.8 provides the same full workflow in English: first-run connection
setup, printer setup, Spoolman spool creation, automatic Snapmaker Orca profile generation, Adaptive PA
calibration, background detection of spools created outside the app and safe
desktop update notifications.
An Adaptive PA calibration takes approximately **10 minutes**. The duration may
vary slightly; do not power off or restart the printer and do not send other
commands from Fluidd or the touchscreen while it is running.

La pagina iniziale permette anche di calibrare direttamente una bobina Spoolman
già esistente. Il comando seguente resta disponibile come alternativa avanzata
da Terminale:

```bash
PYTHONPATH=src python3 -m u1_filament_automation gui \
  --sandbox-dir ~/Downloads/u1fa-gui-sandbox
```

Al primo avvio l'interfaccia chiede l'IP/hostname della U1. Il campo Spoolman può
restare vuoto: l'app prova automaticamente il servizio sul computer corrente
(`127.0.0.1`, che significa sempre “questo computer”), gli indirizzi dichiarati
da Moonraker/PAXX e infine la U1 sulla porta standard `7912`. È possibile inserire
manualmente l'indirizzo quando si usa un host o una porta differente. L'app
verifica gli endpoint in sola lettura, ricava automaticamente SSH come `root@HOST`
e salva soltanto gli indirizzi nella configurazione personale dell'utente. La
password non viene mai salvata. Gli utenti avanzati possono ancora specificare
`--moonraker-url` e `--spoolman-url` nel comando.

L'interfaccia ascolta esclusivamente su `127.0.0.1`. La creazione della bobina usa
un ticket monouso: un aggiornamento o un doppio invio della pagina non può creare
una seconda bobina. Vendor e filamento esistenti con identità esatta vengono
riutilizzati. Prima della creazione viene inoltre verificata la presenza del
profilo base Snapmaker, così un dato non supportato viene bloccato prima di scrivere
in Spoolman.

L'app contiene direttamente l'automatismo Spoolman → Snapmaker Orca: gli altri
utenti non devono installare lo script separato usato durante lo sviluppo. La GUI
scrive il profilo appena confermato e monitora anche le bobine create dal sito di
Spoolman. Non sovrascrive mai un JSON già presente con lo stesso nome e, dopo aver
gestito un profilo, rispetta una sua eventuale cancellazione manuale da Orca.

Prima della configurazione stampante, dal display U1 abilitare entrambe le voci:

1. `Settings / Impostazioni → Maintenance / Manutenzione → Advanced Mode /
   Modalità avanzata → Agree / Accetto → Enable / Abilita` per accedere a Fluidd;
2. `Settings / Impostazioni → Maintenance / Manutenzione → Root Access /
   Accesso Root → Agree / Accetto → Open / Apri` per consentire il collegamento SSH.

L'installazione sostituisce realmente
`/home/lava/klipper/klippy/extras/flow_calibrator.py`, ma soltanto dopo controllo
in sola lettura, riconoscimento SHA-256, backup verificato, stampante inattiva e
seconda conferma. La password SSH non viene salvata.
Se non è stata modificata, la password SSH predefinita della configurazione U1
è `snapmaker`.

Prima della calibrazione l'app verifica che la stampante sia
inattiva e che entrambe le macro APA siano caricate. La conversione degli slot è
sempre mostrata prima dell'avvio: fisico 1→0, 2→1, 3→2, 4→3. Il preset iniziale è
l'envelope U1 convalidato `100/218/336 mm/s` e `2000/6000/10000 mm/s²`.

Al termine, la suite completa viene associata al profilo selezionato prima della
calibrazione; vengono creati i backup e aggiornati PA statico, tabella Adaptive PA
e PA ponti nella copia sandbox e nel profilo Snapmaker Orca reale.

Le scritture Spoolman usano gli endpoint REST ufficiali `/api/v1/vendor`,
`/api/v1/filament` e `/api/v1/spool`. La bobina viene creata per ultima; se un
errore avviene dopo la creazione di un elemento, l'app mostra gli ID già creati e
non esegue cancellazioni automatiche.

L'invio usa l'endpoint ufficiale Moonraker
[`POST /printer/gcode/script`](https://moonraker.readthedocs.io/en/latest/external_api/printer/#run-a-gcode-command).

La v1.0.1 integra nell'intestazione e come favicon il logo ufficiale U1FA scelto
per il progetto, con firma `by Bottega3DLab`.

```bash
cd u1-filament-automation
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
u1fa doctor
```

Il comando prova automaticamente lo Spoolman locale standard del progetto:

```text
http://127.0.0.1:7912
```

Per indicare gli indirizzi manualmente:

```bash
u1fa doctor \
  --spoolman-url http://127.0.0.1:7912 \
  --moonraker-url http://IP_DELLA_U1
```

Per produrre un report JSON condivisibile senza scrivere configurazioni:

```bash
u1fa doctor --json
```

## Sincronizzazione Spoolman → Snapmaker Orca

L'anteprima è la modalità predefinita e non scrive file:

```bash
u1fa sync
```

Per provare la creazione in una cartella completamente separata da Snapmaker Orca:

```bash
u1fa sync --apply --sandbox-dir ~/Downloads/u1fa-orca-sandbox
```

Il comando crea i file `.json` e `.info` esclusivamente nella cartella indicata.
L'opzione `--apply` da sola viene rifiutata e non può scrivere nei profili reali.

Il sistema usa le regole del precedente `spoolman_to_snapmaker_orca_v2.py`:

- PLA normale → `Snapmaker PLA Basic @U1`;
- PLA Rapid/Hyper/High Speed/HS/HF/SnapSpeed → `Snapmaker PLA SnapSpeed @U1`;
- PETG normale → `Snapmaker PETG @U1`;
- PETG veloce → `Snapmaker PETG HF`;
- regole specifiche per CF, Wood e Translucent.

Il nome e il colore provengono da Spoolman. Se nel nome è già presente il vendor o
il materiale, non viene ripetuto. Un profilo con lo stesso nome non viene
mai sovrascritto; un nome diverso viene creato anche se Orca contiene un profilo
simile. Gli eventuali doppioni restano quindi eliminabili direttamente nello slicer.

## Cosa controlla

1. Cartelle di Snapmaker Orca su macOS, Windows e Linux.
2. Spoolman esplicito, configurato tramite variabile ambiente o disponibile in
   locale sulla porta 7912.
3. Possibili URL Spoolman presenti nella configurazione restituita da Moonraker.
4. Numero di vendor, filamenti e bobine leggibili.
5. Anteprima deduplicata dei profili tecnici `base` e
   `@Snapmaker U1 (<ugello> nozzle)`.
6. Confronto dei nomi con i JSON esistenti, senza modificarli.

Il confronto considera equivalenti maiuscole/minuscole, punteggiatura e ordine delle
stesse parole. Il materiale `PLA+` rimane distinto da `PLA`; profili con colori
diversi non vengono assimilati. In caso di dubbio viene mostrato `AMBIGUO` e non
viene presa alcuna decisione automatica.

Una bobina non genera necessariamente un nuovo profilo: bobine dello stesso vendor,
materiale e variante condividono il medesimo profilo tecnico.

### Monitoraggio automatico Spoolman

`watch` controlla periodicamente Spoolman. Quando compare una nuova bobina, applica
le stesse regole validate di `sync` e crea soltanto l'eventuale profilo mancante;
non modifica né sovrascrive mai i profili già esistenti.

Prova isolata:

```bash
u1fa watch \
  --apply \
  --sandbox-dir ~/Downloads/u1fa-watch-sandbox \
  --interval 30
```

Si interrompe con `Ctrl-C`. Per scrivere nella cartella reale di Orca servono ancora
sia `--apply` sia `--confirm-orca-write`. L'opzione `--moonraker-url` consente di
individuare anche uno Spoolman esposto dalla stessa U1, per esempio con PAXX, ma non
installa PAXX e non è necessaria per Spoolman locale o indicato esplicitamente.

Il monitor conserva un piccolo stato locale dei profili già gestiti. Se l'utente
elimina volontariamente un profilo da Orca, non viene ricreato al controllo seguente;
`sync` manuale rimane disponibile per rigenerarlo intenzionalmente.

## Adaptive PA da un log già salvato

Il comando seguente legge esclusivamente un file locale e ricava i cinque punti
`low_anchor`, `high_flow`, `high_force`, `stress` e `center`:

```bash
u1fa pa-parse percorso/al/log.txt
```

Mostra le righe `PA, flusso, accelerazione` utilizzabili per una tabella Adaptive PA
e la mediana come fallback PA statico. Non contatta stampante, Moonraker, Spoolman
o Snapmaker Orca e non scrive file. Per un risultato strutturato:

```bash
u1fa pa-parse percorso/al/log.txt --json
```

Il log reale già validato del progetto è incluso soltanto come fixture di test; non
contiene una procedura che si avvii automaticamente sulla stampante.

### Associazione automatica al profilo Orca

`pa-profile` usa lo stesso log, cerca prima l'ID bobina Spoolman registrato dalla
catena e ricava da Spoolman il nome tecnico esatto del profilo. Se il log contiene
soltanto il nome del filamento, procede esclusivamente quando la corrispondenza è
univoca; altrimenti si blocca mostrando il motivo.

Anteprima, senza scritture:

```bash
u1fa pa-profile percorso/al/log.txt \
  --sandbox-dir ~/Downloads/u1fa-watch-sandbox
```

Applicazione isolata sul profilo già creato nella sandbox:

```bash
u1fa pa-profile percorso/al/log.txt \
  --apply \
  --sandbox-dir ~/Downloads/u1fa-watch-sandbox
```

Non crea un profilo sostitutivo: aggiorna soltanto il profilo esatto già presente
nella cartella indicata. Conserva tutti i campi esistenti e imposta soltanto:

- `enable_pressure_advance`;
- `pressure_advance`, con la mediana dei cinque punti come fallback;
- `adaptive_pressure_advance`;
- `adaptive_pressure_advance_model`, con le cinque righe misurate;
- `adaptive_pressure_advance_overhangs`;
- `adaptive_pressure_advance_bridges`, calcolato come metà del PA statico secondo
  il punto di partenza consigliato dalla documentazione OrcaSlicer.

Questi nomi e formati corrispondono alle opzioni definite dal sorgente ufficiale di
[OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer/blob/main/src/libslic3r/PrintConfig.cpp)
e alla relativa
[documentazione Adaptive PA](https://github.com/OrcaSlicer/OrcaSlicer/wiki/adaptive_pressure_advance_calib).
Prima di ogni modifica viene creato un backup datato in `.u1fa/backups`; il JSON
nuovo viene validato e sostituito atomicamente. Se i valori sono già identici, non
riscrive il profilo e non crea un altro backup.

Il comando non contatta mai la stampante. Una scrittura nei profili reali continua
a richiedere sia `--apply` sia `--confirm-orca-write`; durante lo sviluppo e i test
va usata la sandbox.

### Attesa automatica di una nuova calibrazione

`pa-auto` evita il salvataggio manuale del log. Va avviato prima della calibrazione:

```bash
u1fa pa-auto \
  --moonraker-url http://IP_DELLA_U1 \
  --apply \
  --sandbox-dir ~/Downloads/u1fa-watch-sandbox
```

Il comando esegue soltanto richieste HTTP `GET` all'endpoint ufficiale
[`/server/gcode_store`](https://moonraker.readthedocs.io/en/latest/external_api/server/#request-cached-gcode-responses)
di Moonraker. Non invia G-code e non avvia la calibrazione: dopo che il monitor è
in attesa, l'utente lancia normalmente `APA_COIL_RUN_ULTRA` da Fluidd. Quando
compaiono i cinque risultati completi, l'app trova la bobina Spoolman e aggiorna il
profilo già presente nella sandbox.

La cache è una coda FIFO con timestamp. L'app salva come punto iniziale l'intera
coda presente all'avvio e considera esclusivamente le nuove risposte; in questo modo
non riutilizza una calibrazione vecchia. Se la cache viene azzerata, cambia server o
si perdono troppi messaggi tra due controlli, si blocca senza modificare profili.

Per un controllo breve senza attendere indefinitamente si può usare `--cycles N`.
La modalità normale continua fino alla suite completa oppure fino a `Ctrl-C`.

Se una calibrazione completa è già terminata ma il firmware ha restituito un nome
generico, `pa-latest` permette di recuperarla senza ripeterla:

```bash
u1fa pa-latest \
  --moonraker-url http://IP_DELLA_U1 \
  --profile-name "NOME ESATTO DEL PROFILO @Snapmaker U1 (0.4 nozzle)" \
  --apply \
  --sandbox-dir ~/Downloads/u1fa-watch-sandbox
```

Il comando verifica il timestamp della suite (massimo due ore per impostazione
predefinita), legge Moonraker una sola volta e non invia G-code. Il profilo indicato
deve già esistere nella cartella di destinazione.

## Installazione sicura del calibratore U1

Il percorso recuperato dal backup del progetto è:

```text
/home/lava/klipper/klippy/extras/flow_calibrator.py
```

Per eseguire l'intero ciclo soltanto in una U1 simulata locale:

```bash
u1fa printer-install \
  --sandbox-root ~/Downloads/u1fa-printer-sandbox \
  --apply
```

La sandbox viene inizializzata con l'originale validato e un `printer.cfg`
simulato; l'app installa calibratore e macro senza contattare la stampante.

I comandi reali sono documentati in `docs/INSTALLAZIONE_STAMPANTE.md`. La modalità
predefinita è diagnosi/anteprima; una modifica reale richiede contemporaneamente
`--apply` e `--confirm-printer-write`. L'app blocca l'operazione se:

- Klipper non è `ready`;
- `print_stats` è `printing` oppure `paused`;
- la virtual SD è attiva;
- `idle_timeout` segnala attività oppure lo stato macchina Snapmaker è diverso da
  `IDLE`/`0` (stampa, calibrazione, caricamento filamento o altra attività);
- il file non corrisponde esattamente né all'originale né alla v6 validata;
- lo SHA-256 cambia fra controllo e sostituzione.

Prima di ogni sostituzione viene creato un backup datato nella stessa cartella. Il
nuovo file viene scritto in un temporaneo, verificato e spostato atomicamente.
L'installatore crea inoltre `adaptive_pa_macro.cfg` se assente e aggiunge
`[include adaptive_pa_macro.cfg]` a `printer.cfg` soltanto se nessun include
esatto o glob la copre già. File esistenti non riconosciuti non vengono toccati.
Se un passaggio fallisce, quelli precedenti vengono ripristinati automaticamente.
Il master backup validato documenta che un semplice `RESTART`
non ricarica questo modulo Python sulla U1: l'app non esegue quindi riavvii automatici
e richiede spegnimento completo, attesa di 10–15 secondi e riaccensione.

L'accesso SSH può usare una chiave con `--identity-file` oppure chiedere la password
con `--ask-ssh-password`. In quest'ultimo caso la password non compare nel comando,
non viene scritta nei file e resta in memoria soltanto durante l'esecuzione.

`printer-check` valida inoltre la macro
`/home/lava/printer_data/config/adaptive_pa_macro.cfg`, ne confronta lo SHA-256
con la ULTRA v6 recuperata e chiede a Moonraker se `APA_COIL_RUN_ULTRA` è realmente
caricata da Klipper. La catena viene dichiarata completa soltanto quando file Python,
macro e caricamento runtime risultano tutti validi.

## Build desktop su GitHub

Il workflow `.github/workflows/build-release.yml` compila ciascun pacchetto sul
proprio sistema operativo, perché PyInstaller non è un cross-compiler. Prima di
ogni build esegue l'intera suite di test. Un tag contenente `-beta` crea una
pre-release; un tag stabile crea la release finale e allega tutti i pacchetti e
`SHA256SUMS.txt`. La beta con aggiornamenti integrati usa il tag
`v1.8.0-beta.1`.

La build locale macOS richiede Python 3.10 o superiore e PyInstaller:

```bash
python3 -m pip install . pyinstaller
packaging/macos/build_dmg.sh
```

Windows usa `packaging/windows/build_installer.ps1` con PyInstaller, Pillow e Inno
Setup 6. Linux usa `packaging/linux/build_appimage.sh` con PyInstaller e
`appimagetool`. Gli utenti finali non devono installare questi strumenti.

La firma ad-hoc verifica l'integrità della build. Per eliminare completamente gli
avvisi Gatekeeper serviranno in seguito un certificato Apple Developer ID e la
notarizzazione Apple.

## Variabili ambiente

| Variabile | Scopo |
|---|---|
| `U1FA_SPOOLMAN_URL` | URL di Spoolman |
| `U1FA_MOONRAKER_URL` | URL di Moonraker |
| `U1FA_ORCA_DIR` | Cartella filamenti di Snapmaker Orca |

## Test

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Sicurezza

- `doctor`, `pa-parse`, `sync`, `printer-check` e le anteprime non modificano il
  firmware;
- nessuna scansione automatica dell'intera rete locale;
- timeout breve sulle connessioni;
- nessun dato o indirizzo inviato all'esterno.
- `doctor` e `sync` senza `--apply` non scrivono nulla;
- `sync --apply` da solo viene bloccato;
- `sync --apply --sandbox-dir PERCORSO` scrive soltanto nella cartella di prova;
- `pa-profile` senza `--apply` non modifica alcun profilo;
- `pa-profile --apply --sandbox-dir PERCORSO` aggiorna soltanto un JSON esistente
  nella sandbox, creando prima un backup locale;
- associazioni PA ambigue o non verificabili vengono bloccate;
- `pa-auto` usa soltanto `GET /server/gcode_store`, ignora la cache iniziale e non
  invia alcun G-code;
- `pa-auto --apply` senza sandbox e senza `--confirm-orca-write` viene bloccato
  prima di aprire la connessione Moonraker;
- `pa-latest` recupera soltanto una suite completa e recente; la destinazione
  esplicita deve corrispondere a un profilo già esistente;
- anche con conferma esplicita, la scrittura reale usa apertura esclusiva e non
  sovrascrive, elimina o rinomina profili esistenti.
- `printer-install --apply` sulla U1 reale viene bloccato senza la seconda conferma;
- l'installatore reale controlla due volte che la stampante non stia stampando;
- nessun riavvio o spegnimento viene avviato automaticamente;
- firmware sconosciuti o aggiornati vengono bloccati, mai forzati;
- il ripristino accetta soltanto backup U1FA oppure il backup storico validato
  `flow_calibrator.py.BACKUP_ORIGINALE_20260824`.

## Licenza e crediti

Il progetto è distribuito sotto GNU GPL v3.0.

L'integrazione Adaptive PA deriva da
[U1 Adaptive Pressure Advance Auto Calibration](https://github.com/djsplice/u1-adaptive-pa-autocal)
di djsplice e contributori, distribuito sotto GNU GPL v3.0.

Si riconoscono inoltre il calibratore Snapmaker U1, OrcaSlicer Adaptive Pressure
Advance e le ispirazioni metodologiche CNC Kitchen/PrusaPATuner indicate dal progetto
upstream. Vedere `THIRD_PARTY_NOTICES.md`.

Progetto community indipendente, non affiliato né approvato dai progetti citati.

Lo stato esatto recuperato dai due progetti precedenti è documentato in
`docs/RECUPERO_PROGETTI.md`.
