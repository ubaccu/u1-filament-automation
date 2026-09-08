# Changelog

## 1.8.0b8 — 2026-09-09

- Aggiunti selettori grafici per i colori delle bobine multicolore: due colori
  iniziali, pulsante per aggiungerne fino a otto e codici HEX sincronizzati.
- Le bobine PLA multicolore usano automaticamente il profilo base **Snapmaker
  PLA Silk**, anche quando il nome commerciale non contiene `Silk`.

## 1.8.0b7 — 2026-09-09

- Aggiunto il materiale PLA Silk: il profilo base Silk viene scelto quando il
  nome del filamento contiene `Silk`, con compatibilità per i nomi Orca nuovi e legacy.
- Aggiunto il tipo colore **Multicolore** nella creazione bobina: da 2 a 8 HEX
  vengono salvati in Spoolman e riportati nell'ordine corretto nel profilo Orca.
- La sincronizzazione automatica gestisce anche bobine multicolore create
  direttamente dal sito Spoolman, senza sovrascrivere profili esistenti.

## 1.8.0b6 — 2026-09-08

- Gli errori transitori di lettura Moonraker, compreso `HTTP 504`, vengono
  ritentati con attese progressive senza reinviare i comandi di calibrazione.
- Ridotto il carico sul registro Moonraker: 750 risposte ogni 3 secondi e timeout
  breve per la singola richiesta, separato dal limite complessivo del test.
- Aggiunto nella schermata d'errore il recupero dell'ultima calibrazione completa:
  è una lettura sicura, non invia G-code e aggiorna soltanto il profilo selezionato
  dopo aver creato il consueto backup.
- Il recupero confronta l'orario della suite con l'avvio del test e blocca risultati
  appartenenti a calibrazioni precedenti.
- Rafforzati in GUI e documentazione gli avvisi bilingui per lasciare U1FA aperta
  e Snapmaker Orca completamente chiuso fino al completamento.

## 1.8.0b5 — 2026-09-08

- Sostituito l'envelope fisso della GUI con la modalità automatica consigliata,
  calcolata dal `filament_max_volumetric_speed` realmente ereditato in Orca.
- Aggiunti limiti lineari min/max facoltativi dichiarati dal produttore e una
  modalità manuale avanzata entro i limiti U1FA.
- L'anteprima mostra origine del flusso, fattore limitante, velocità, flussi dei
  tre punti e un avviso quando un limite prudente può ridurre il segnale.
- La selezione mantiene il materiale Spoolman e continua a verificare profilo,
  slot fisico, temperatura e limiti prima di inviare comandi alla U1.

## 1.8.0b4 — 2026-08-30

- Se Spoolman/Docker è spento all'avvio, il monitor resta in attesa e riprova
  automaticamente ogni 10 secondi invece di dichiararsi attivo senza funzionare.
- La home distingue chiaramente tra sincronizzazione attiva e sincronizzazione
  in attesa.
- Aggiunto un self-test del runtime desktop al pacchetto Windows compilato.
- Documentazione pubblica organizzata con README inglese principale, README
  italiano completo e istruzioni stampante separate nelle due lingue.
- Aggiunto un avviso bilingue di sicurezza, assenza di garanzia e limitazione
  di responsabilità nei README e prima di qualsiasi modifica della stampante.
- Rimosse dalla documentazione pubblica le note interne sui vecchi esperimenti;
  licenza, attribuzioni e crediti upstream restano completi.

## 1.8.0b3 — 2026-08-30

- Sostituita l'apertura nel browser con una vera finestra desktop U1FA basata
  sui componenti nativi di macOS, Windows e Linux.
- L'indirizzo locale `127.0.0.1:8765` resta un dettaglio interno e non viene più
  mostrato nella barra del browser.
- La chiusura della finestra arresta in modo ordinato il servizio locale e
  consente di riaprire normalmente l'app.
- Anche il pulsante di chiusura della Home termina insieme finestra, monitor e
  processo desktop, evitando istanze residue al riavvio.
- Ripristinata l'icona U1FA nel Dock di macOS e mantenuto il blocco della chiusura
  durante una calibrazione attiva.

## 1.8.0b2 — 2026-08-30

- Rimossa dalla GUI la copia duplicata del profilo nella sandbox: per ogni
  filamento viene creato un solo profilo reale in Snapmaker Orca.
- Al termine della calibrazione PA viene aggiornato soltanto il profilo Orca
  selezionato, dopo averne creato un backup verificato.
- Le modalità sandbox dei comandi tecnici da terminale restano disponibili per
  sviluppo e collaudo, ma non fanno parte del flusso desktop destinato agli utenti.

## 1.8.0b1 — 2026-08-29

- Aggiunto il controllo automatico non bloccante delle release U1FA all'avvio.
- La home mostra se l'app è aggiornata oppure se è disponibile una nuova versione,
  con testi completi in italiano e inglese.
- Selezione automatica del pacchetto corretto per macOS Apple Silicon/Intel,
  Windows x64 e Linux x86_64.
- Aggiunta una pagina di conferma con versione, note, dimensione e SHA-256 prima
  del download.
- Il pacchetto viene conservato soltanto se dimensione e SHA-256 coincidono con
  i dati della release GitHub; un download incompleto o alterato viene eliminato.
- L'installer verificato viene aperto soltanto dopo un'ulteriore conferma. U1FA
  non sostituisce sé stessa mentre è in esecuzione.
- Separati esplicitamente aggiornamento dell'app e firmware U1: il controllo
  release non invia comandi alla stampante e non installa firmware.
- Il canale beta riceve beta e release stabili; il canale stabile ignora le
  pre-release. Non vengono richiesti né salvati token GitHub personali.
- Le build multipiattaforma vengono eseguite anche a ogni aggiornamento di
  `main`, così i collaudatori possono scaricare gli artefatti prima di creare una
  release; soltanto un tag `v*` pubblica la release.

## 1.7.0b1 — 2026-08-29

- Prima beta desktop privata multipiattaforma, destinata al collaudo prima della
  pubblicazione stabile.
- Aggiunto un unico workflow GitHub Actions che esegue tutti i test e produce due
  DMG macOS, un installer Windows x64 e un'AppImage Linux x86_64; i tag beta
  vengono pubblicati come pre-release.
- Aggiunto l'installer Windows bilingue per utente, senza richiesta di privilegi
  amministrativi e con runtime Python incorporato.
- Aggiunta l'AppImage Linux portabile con logo, desktop entry e runtime Python
  incorporato.
- Unificato l'avvio desktop e le cartelle dati/log personali per macOS, Windows e
  Linux; nessun percorso contiene il nome o l'IP dell'ambiente di sviluppo.
- Su Windows la richiesta password SSH usa l'eseguibile U1FA in modalità interna:
  la password resta nell'ambiente temporaneo del processo, non compare nel comando
  e non viene salvata. Se manca OpenSSH Client viene mostrata un'istruzione chiara.
- Aggiunto un avviso visibile di beta privata e una checklist bilingue per i
  collaudatori.
- Confermata in tutte le distribuzioni l'installazione automatica protetta di
  `adaptive_pa_macro.cfg` e del relativo include, insieme al calibratore.
- Trasformata la configurazione stampante in un flusso esplicito di ripristino
  post-aggiornamento: reinstalla mod, macro e include soltanto su originali
  riconosciuti. Il nuovo firmware U1 1.6.0 resta bloccato in attesa di convalida.

## 1.6.0 — 2026-08-29

- Rimossa dal progetto e dalla distribuzione la vecchia bozza sperimentale
  Bespok3D: non era utilizzata dall'app standalone e poteva creare confusione.
- Aggiunto l'entrypoint macOS compilabile come vera applicazione grafica autonoma,
  con runtime Python incorporato, log e sandbox nelle cartelle personali.
- Aggiunto il generatore macOS che crea un DMG con l'app e il collegamento alla
  cartella Applicazioni; l'utente finale non deve aprire il Terminale né installare
  Python.
- Aggiunto un workflow GitHub Actions per produrre DMG separati Intel `x86_64` e
  Apple Silicon `arm64` e allegarli automaticamente alle release con tag.
- I file tecnici indispensabili continuano a essere validati separatamente nella
  cartella `vendor`; un eventuale plugin Bespok3D sarà un progetto futuro distinto.

## 1.5.0 — 2026-08-29

- Aggiunta l'app macOS `U1 Filament Automation.app`: avvia la GUI con doppio
  clic, trova automaticamente un Python 3.10 o superiore e apre il browser.
- Il launcher non contiene IP personali: usa la configurazione delle connessioni
  già salvata dall'utente e mantiene la sandbox in `Application Support`.
- Se U1FA è già in esecuzione, un nuovo doppio clic riapre semplicemente la pagina
  senza avviare una seconda istanza.
- Aggiunto alla home il comando bilingue `Chiudi applicazione / Close application`.
  La chiusura è bloccata durante una calibrazione, così il risultato PA non può
  andare perso interrompendo accidentalmente il monitor.
- Numero della versione visibile accanto al marchio Bottega3DLab.
- Documentata la prima apertura tramite `tasto destro → Apri` richiesta dalle
  build di test macOS non ancora firmate e notarizzate.

## 1.4.2 — 2026-08-29

- Quando U1FA AutoPA Mod è già completa, l'anteprima non mostra più password,
  checkbox o pulsante di applicazione: presenta soltanto l'esito del controllo e
  i pulsanti per tornare alla home o ripetere la verifica.
- Sostituita nella GUI la dicitura tecnica “catena già installata” con il nome
  pubblico `U1FA AutoPA Mod`.
- Il file rilevato viene descritto come “controllato” quando non deve essere
  sostituito, evitando un avviso inutilmente allarmante.

## 1.4.1 — 2026-08-29

- Il campo Spoolman può essere lasciato vuoto: l'app prova automaticamente il
  servizio sul computer corrente (`127.0.0.1`), gli endpoint dichiarati da
  Moonraker/PAXX e il servizio sulla U1 alla porta standard `7912`.
- Chiarito nella GUI che `127.0.0.1` significa sempre “questo computer” e non è
  l'indirizzo personale del computer di sviluppo.
- L'indirizzo Spoolman resta compilabile per consentire una configurazione
  manuale quando il servizio usa un host o una porta non standard.

## 1.4.0 — 2026-08-29

- Eliminata la dipendenza da un IP U1 inserito nel comando: al primo avvio la
  GUI chiede IP/hostname della stampante e indirizzo Spoolman.
- La verifica delle connessioni usa soltanto richieste di lettura, ricava
  automaticamente l'endpoint SSH `root@HOST` e non invia G-code.
- Gli indirizzi verificati vengono salvati nella configurazione personale
  dell'utente; password SSH e altri segreti non vengono mai memorizzati.
- Il comando `gui` accetta ora `--moonraker-url` e `--spoolman-url` come opzioni
  facoltative, mantenendole disponibili per utenti avanzati e automazioni.
- Aggiunta una pagina bilingue per modificare gli indirizzi quando cambia l'IP
  della U1 o quando Spoolman è fornito localmente, da PAXX o da un altro host.

## 1.3.2 — 2026-08-29

- Corretti i percorsi mostrati nella configurazione della stampante: la modalità
  italiana usa soltanto le etichette italiane e la modalità inglese soltanto le
  etichette inglesi, senza più mescolare le due lingue.
- Migliorato il titolo inglese della pagina in `Stock Snapmaker U1 setup`.
- Aggiunto sotto il campo SSH un promemoria bilingue della password predefinita
  `snapmaker`, senza precompilarla né salvarla.

## 1.3.1 — 2026-08-29

- Nome pubblico ufficiale della modifica: `U1FA AutoPA Mod`, sviluppata e
  integrata nel progetto di Ivan Riccelli / Bottega3DLab.
- `CHAIN v6` resta esclusivamente un identificatore tecnico interno per mantenere
  compatibili macro, file recuperati e comandi già validati.
- I crediti upstream di djsplice restano separati e riguardano il progetto
  Adaptive PA di partenza distribuito sotto GPLv3.
- GUI e README indicano una durata orientativa di circa 10 minuti e ricordano di
  non spegnere, riavviare o comandare la U1 durante la calibrazione.

## 1.3.0 — 2026-08-29

- GUI completa selezionabile in Italiano o English tramite i pulsanti IT/EN.
- Aggiunto un avviso obbligatorio con i due prerequisiti distinti sul display:
  `Settings → Maintenance → Advanced Mode` per Fluidd e
  `Settings → Maintenance → Root Access` per SSH.
- L'anteprima indica esplicitamente che l'installazione sostituisce il vero
  `/home/lava/klipper/klippy/extras/flow_calibrator.py`, solo dopo backup,
  controllo SHA-256, stato stampante inattivo e seconda conferma.
- Il monitor Spoolman è ora integrato nella GUI e attivo ogni 10 secondi: rileva
  anche bobine aggiunte manualmente dal sito Spoolman e crea automaticamente i
  profili mancanti nella cartella reale di Snapmaker Orca.
- Il monitor non sovrascrive profili esistenti e mantiene lo stato dei profili già
  gestiti, rispettando una successiva cancellazione manuale in Orca.
- Stato dell'ultima sincronizzazione visibile nella pagina iniziale e nuovo
  parametro `--sync-interval` (minimo 5 secondi).
- Aggiunti test locali per entrambe le lingue, prerequisiti stampante e creazione
  automatica di un profilo derivato da una bobina Spoolman esterna.

## 1.2.0 — 2026-08-29

- La GUI crea direttamente il nuovo profilo nella cartella reale di Snapmaker
  Orca: non è più necessario installare lo script di sincronizzazione precedente.
- La scrittura reale è limitata al profilo appena confermato; un profilo con lo
  stesso nome non viene mai sovrascritto. Rimane anche una copia nella sandbox.
- Al termine della calibrazione PA vengono aggiornati sia il profilo sandbox sia
  quello reale selezionato, creando il backup prima della modifica.
- Aggiunta alla GUI la configurazione iniziale U1 Stock con controllo in sola
  lettura, seconda conferma e password SSH non memorizzata.
- L'installatore completo gestisce `flow_calibrator.py`, la macro ULTRA v6 e
  l'include in `printer.cfg`; riconosce anche include glob come `*.cfg`.
- File sconosciuti, stato macchina attivo o cambiamenti fra anteprima e conferma
  bloccano ogni operazione. Scritture parziali vengono annullate con rollback.
- Nessun riavvio viene inviato automaticamente: dopo modifiche alla U1 resta
  obbligatorio lo spegnimento completo per 10–15 secondi.
- Test completamente locali per profilo Orca reale simulato, installazione,
  backup, rollback, script SSH e doppia conferma GUI.

## 1.1.1 — 2026-08-28

- Corretto il selettore colore che Chrome su macOS mostrava come una sottile
  striscia grigia nonostante il valore scelto fosse valido.
- Aggiunti campo HEX visibile, campione colore separato e sincronizzazione in
  tempo reale tra selettore, codice e anteprima.
- Verificato il caso reale rosa RGB `210,144,223` → `#D290DF` senza modifiche al
  valore inviato a Spoolman.

## 1.1.0 — 2026-08-28

- Aggiunta alla GUI la creazione completa della bobina: vendor, filamento e spool
  tramite gli endpoint REST ufficiali di Spoolman.
- Vendor e filamento corrispondenti vengono riutilizzati senza duplicarli; una
  bobina nuova viene invece creata esplicitamente per ogni conferma.
- Nuovo modulo di anteprima che mostra profilo Orca e base Snapmaker prima di
  qualsiasi scrittura; dati non supportati o base assente bloccano l'operazione.
- Ticket di conferma monouso contro doppi invii e ricaricamenti della pagina.
- Dopo la creazione, il profilo viene generato esclusivamente nella sandbox e la
  GUI passa direttamente alla selezione dello slot e alla calibrazione PA.
- Inserimento guidato di marca, materiale, nome tecnico, colore, densità, diametro,
  peso nominale/rimasto, tara, temperature, posizione e lotto.
- Aggiunti test con Spoolman simulato: nessuna scrittura su servizi reali, payload
  verificati, riuso degli oggetti e conferma monouso.
- Corretto il pacchetto installabile affinché includa anche il logo PNG.

## 1.0.1 — 2026-08-28

- Integrato il logo ufficiale U1FA scelto per il progetto, derivato dal marchio
  Bottega3DLab.
- Logo mostrato nell'intestazione di tutte le schermate e utilizzato come favicon.
- PNG con trasparenza reale incluso negli asset del pacchetto e verificato dai test.

## 1.0.0 — 2026-08-28

- Nuova interfaccia locale nel browser con selezione del profilo Spoolman,
  estrusore fisico 1–4, temperatura ed envelope U1 convalidato.
- Mapping protetto e visibile: slot fisico `1→0`, `2→1`, `3→2`, `4→3` per il
  parametro Klipper `EXTRUDER`.
- Doppia conferma tramite anteprima dei comandi prima dell'invio.
- Preflight obbligatorio: stampante inattiva, macro `APA_COIL_SET_ENVELOPE` e
  `APA_COIL_RUN_ULTRA` caricate, profilo esatto presente nella sandbox.
- Acquisizione automatica della nuova suite completa e aggiornamento del profilo
  selezionato, con backup, scrittura atomica, PA ponti e nessuna scrittura nei
  profili Orca reali.
- Server vincolato a `127.0.0.1`, token di sessione e blocco degli input fuori
  intervallo.

## 0.9.3 — 2026-08-28

- Corretto `adaptive_pressure_advance_bridges`: è un valore numerico, non un
  interruttore booleano.
- Il valore ponti viene ora calcolato automaticamente come metà del fallback PA
  statico, arrotondato a sei decimali, seguendo il punto iniziale consigliato da
  OrcaSlicer.
- Per il Deeplee PLA PRO RAPID BLUE calibrato a `0.013635`, il valore ponti è
  `0.006818`.

## 0.9.2 — 2026-08-28

- Corretto il riepilogo di `pa-profile`, `pa-auto` e `pa-latest`: quando viene
  indicato `--profile-name`, l'associazione è dichiarata esplicitamente e un
  eventuale ID bobina precedente rimasto nella cache Moonraker non viene più
  mostrato come se avesse scelto il profilo.
- Nessun cambiamento ai valori PA già calcolati e nessuna necessità di ripetere
  la calibrazione.

## 0.9.1 — 2026-08-28

- Nuovo comando di recupero `pa-latest`: legge l'ultima suite completa ancora
  presente nella cache Moonraker senza richiedere una nuova calibrazione.
- Controllo dell'età tramite timestamp Moonraker; risultati troppo vecchi o con
  orologio incoerente vengono bloccati.
- Possibilità di indicare esplicitamente il profilo di destinazione quando il nome
  generico restituito dal firmware non coincide con il nome tecnico Spoolman.
- Il recupero usa soltanto `GET /server/gcode_store`, non invia G-code e mantiene
  tutte le protezioni sandbox, backup e scrittura atomica della v0.9.0.
- Aggiunti test di recupero completo, timestamp, destinazione esplicita e blocco
  della scrittura reale prima di qualsiasi collegamento.

## 0.9.0 — 2026-08-28

- Nuovo comando `pa-auto`: monitora in sola lettura la cache ufficiale delle
  risposte G-code Moonraker e riconosce automaticamente una nuova suite ULTRA v6.
- Usa esclusivamente `GET /server/gcode_store`; non apre SSH, non invia G-code e
  non avvia, interrompe o riavvia la stampante.
- Tutti i messaggi già presenti all'avvio vengono marcati come vecchi e ignorati:
  una calibrazione precedente non può essere riapplicata per errore.
- Rilevamento incrementale compatibile con lo scorrimento FIFO della cache; perdita
  di continuità o azzeramento della coda bloccano l'operazione.
- Una suite incompleta non produce file e resta in attesa dei cinque punti.
- Al completamento riusa l'associazione sicura Spoolman → profilo Orca della v0.8,
  con backup, scrittura atomica e sandbox separata.
- La scrittura reale continua a essere bloccata prima di qualsiasi connessione se
  mancano contemporaneamente `--apply` e `--confirm-orca-write`.
- Aggiunti test con cache vecchia più calibrazione nuova, coda invariata,
  scorrimento FIFO, discontinuità e verifica dell'unico endpoint HTTP utilizzato.

## 0.8.0 — 2026-08-28

- Nuovo comando `pa-profile`: legge un log ULTRA v6 già salvato, estrae i cinque
  punti e li associa automaticamente al profilo Orca derivato da Spoolman.
- Associazione prioritaria tramite `Spoolman id` presente nel log; ripiego sul nome
  del filamento consentito soltanto quando individua un unico profilo.
- Ambiguità, bobina assente, profilo mancante e JSON non valido bloccano ogni
  scrittura invece di scegliere automaticamente un risultato incerto.
- Aggiornamento limitato ai sei campi Pressure Advance ufficiali di OrcaSlicer;
  tutti gli altri valori del profilo vengono conservati.
- La mediana dei cinque punti viene salvata come fallback PA statico, mentre le
  cinque righe `PA,flusso,accelerazione` formano il modello Adaptive PA.
- Anteprima predefinita senza alterazione di contenuto, hash o data del profilo.
- Applicazione con backup datato in `.u1fa/backups`, JSON validato e sostituzione
  atomica; un secondo passaggio identico non riscrive e non crea altri backup.
- Test completo in sandbox: nessuna scrittura nella cartella Orca reale e nessun
  collegamento alla stampante.

## 0.7.0 — 2026-08-28

- Nuovo comando `watch`: sorveglia Spoolman e crea automaticamente soltanto i
  profili Orca mancanti quando vengono aggiunte nuove bobine.
- Monitoraggio idempotente: nessun profilo esistente viene modificato o sovrascritto.
- Stato locale atomico: un profilo eliminato volontariamente da Orca non viene
  ricreato automaticamente dal ciclo successivo.
- Sandbox obbligatoriamente separata da Orca disponibile anche per il monitoraggio.
- Scrittura reale ancora protetta da `--apply` più `--confirm-orca-write`.
- Rilevamento opzionale di Spoolman dalla configurazione Moonraker o dalla stessa U1;
  supporta installazioni esterne/PAXX senza richiederle sulla U1 Stock.
- Nessun collegamento SSH e nessuna modifica alla stampante durante `sync` o `watch`.

## 0.6.1 — 2026-08-28

- Corretto un errore nella documentazione: la U1 reale usata per la verifica è
  Stock e non ha PAXX installato.
- `/home/lava/printer_data/config` è trattato come percorso configurazione
  Klipper/Moonraker osservato sulla U1 Stock, non come prova della presenza di PAXX.
- Chiarito che l'app è standalone; PAXX e Bespok3D restano soltanto compatibilità
  future e opzionali.

## 0.6.0 — 2026-08-28

- `printer-check` controlla ora l'intera catena Adaptive PA in sola lettura.
- Aggiunta validazione SHA-256 esatta di
  `/home/lava/printer_data/config/adaptive_pa_macro.cfg`.
- Aggiunta verifica Moonraker che `APA_COIL_RUN_ULTRA` sia realmente caricata da
  Klipper, non soltanto presente sul disco.
- La catena è completa solo con calibratore CHAIN v6, macro ULTRA v6 e macro runtime
  caricata; file assenti o sconosciuti restano bloccati.
- Percorso della macro verificato sulla U1 Stock reale dell'autore senza alcuna
  scrittura.

## 0.5.2 — 2026-08-28

- Aggiunta l'opzione `--ask-ssh-password` per chi non vuole autorizzare una chiave
  permanente sulla stampante.
- Password richiesta in modo nascosto, mai inserita negli argomenti del processo e
  mai salvata nei file; viene mantenuta soltanto durante il comando corrente.
- Autenticazione password limitata a un tentativo e helper temporaneo eliminato
  immediatamente dopo ogni collegamento SSH.
- La modalità predefinita continua a rifiutare richieste interattive impreviste.

## 0.5.1 — 2026-08-28

- Corretto il controllo dello stato proprietario Snapmaker: il firmware U1 espone
  `MachineMainState.IDLE` tramite Moonraker come valore numerico `0`.
- `printer-check` accetta esclusivamente `0` oppure `IDLE` come stato macchina
  inattivo e continua a bloccare tutti gli stati numerici da `1` a `13`.
- Aggiunti test sul valore reale osservato sulla U1 e su tutti gli stati macchina
  attivi definiti dal firmware ufficiale Snapmaker.

## 0.5.0 — 2026-08-28

- Nuovi comandi `printer-check`, `printer-install` e `printer-restore`.
- Installazione standalone del `flow_calibrator.py` CHAIN v6 recuperato dal backup.
- Controllo obbligatorio di Klipper, `print_stats`, virtual SD, `idle_timeout` e
  stato macchina Snapmaker tramite Moonraker.
- Blocco completo quando la U1 stampa, è in pausa o il firmware è sconosciuto.
- Doppia conferma obbligatoria per ogni scrittura reale sulla stampante.
- Backup esclusivo datato, scrittura temporanea, sostituzione atomica e verifica
  SHA-256 mantenendo permessi e proprietario del file originale.
- Controllo sintattico Python prima della sostituzione.
- Nessun soft restart automatico: il master backup dimostra che sulla U1 non
  ricarica questo modulo; viene richiesto un power cycle di 10–15 secondi.
- Ripristino compatibile con i backup creati dall'app e con il backup storico
  `flow_calibrator.py.BACKUP_ORIGINALE_20260824`.
- Sandbox stampante locale che non apre connessioni SSH o HTTP.
- Asset originali e v6 incorporati nel pacchetto con hash verificato a runtime.

## 0.4.0 — 2026-08-28

- Recuperato dai progetti salvati il pacchetto completo `APA_CHAIN_v6_SAFE.zip`.
- Conservati senza modifiche macro v6, `flow_calibrator.py` v6, copia originale,
  diff e note, con SHA-256 verificabili.
- Nuovo parser offline `pa-parse`: estrae cinque punti PA da un log già salvato,
  produce le righe per la tabella Adaptive PA e calcola la mediana di fallback.
- Il parser non contatta stampante, Moonraker, Spoolman o Snapmaker Orca.
- Aggiunta la sorgente sperimentale del plugin Bespok3D; non è ancora pubblicata né
  installabile perché identità repository e adapter U1 devono essere validati.
- Test che applica il diff alla copia originale e ricostruisce esattamente la v6.
- Corretto il documento di recupero che dichiarava erroneamente mancanti i file v6.

## 0.3.2 — 2026-08-28

- `sync --apply` da solo viene bloccato per impedire scritture accidentali nei
  profili reali di Snapmaker Orca.
- Nuovo `--sandbox-dir`: genera i JSON in una cartella di prova separata.
- La scrittura reale richiede una seconda conferma esplicita.
- Rimossa dall'anteprima l'indicazione che invitava ad aggiungere semplicemente
  `--apply`.

## 0.3.1 — 2026-08-27

- Correzione basata sull'anteprima reale delle nove bobine dell'utente.
- Il nome registrato in Spoolman resta la sorgente del profilo Orca.
- Rimossi vendor e materiale duplicati, per esempio `Deeplee ... DEEPLEE ...` e
  `R3d R3D ...`.
- Rimossa l'aggiunta automatica di `PLA Plus` ai Deeplee Rapid quando Spoolman
  dichiara il materiale come `PLA`.
- Il controllo dei profili esistenti ignora le sole differenze di maiuscole e
  minuscole, senza bloccare profili realmente diversi.

## 0.3.0 — 2026-08-27

- Ripristinata integralmente la logica del precedente
  `spoolman_to_snapmaker_orca_v2.py` per la scelta dei profili base Snapmaker.
- Nuovo comando `sync`: anteprima predefinita e creazione esplicita con `--apply`.
- Generazione dei file Orca `.json` e `.info` con nome e colore da Spoolman.
- Nessuna sovrascrittura: i profili con lo stesso nome vengono lasciati intatti.
- I profili soltanto simili non bloccano la creazione; i doppioni possono essere
  eliminati direttamente nello slicer.
- Adozione del suffisso reale `@Snapmaker U1 (0.4 nozzle)` osservato nei profili.
- Riconoscimento sicuro di maiuscole, punteggiatura e ordine diverso delle parole.
- Nuovi stati `EQUIVALENTE` e `AMBIGUO`.
- `PLA` e `PLA+` restano materiali distinti.
- Soglia dei profili simili resa più conservativa per non confondere i colori.
- Test sui nove abbinamenti reali osservati nel report dell'utente.
- `doctor` e `sync` restano in sola lettura; soltanto `sync --apply` crea file
  nuovi senza sovrascrivere quelli esistenti.

## 0.2.0 — 2026-08-28

- Pulizia automatica dei nomi duplicati provenienti da Spoolman.
- Confronto in sola lettura con i profili JSON esistenti.
- Stati `ESISTE`, `SIMILE` e `MANCANTE`.
- Report JSON con contatori espliciti delle scritture, tutti impostati a zero.
- Test di non alterazione: contenuto, SHA-256 e data del profilo restano invariati.
- Nessuna funzione di scrittura nella cartella Snapmaker Orca.

## 0.1.0 — 2026-08-27

- Prima diagnostica in sola lettura.
- Rilevamento multipiattaforma delle cartelle Snapmaker Orca.
- Collegamento agli endpoint REST vendor, filament e spool di Spoolman.
- Ricerca dello Spoolman locale su porta 7912.
- Estrazione di possibili URL Spoolman dalla configurazione Moonraker.
- Anteprima deduplicata dei profili tecnici per filamento e ugello.
- Aggiunti test automatici, licenza GPL v3 e attribuzioni upstream.

La versione 0.1.0 non incorporava ancora il modulo Adaptive PA; l'integrazione
successiva mantiene licenza, crediti e tracciabilità delle modifiche.
