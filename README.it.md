# Lingua / Language

[English](README.md) | **Italiano**

# U1 Filament Automation

Applicazione desktop community di **Bottega3DLab** per collegare Spoolman,
Snapmaker Orca e la calibrazione Adaptive Pressure Advance della Snapmaker U1.

Disponibile in italiano e inglese per macOS, Windows e Linux.

<a href="https://www.buymeacoffee.com/riccelliiv9" target="_blank" rel="noopener noreferrer"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" height="60" width="217"></a>

## Cosa fa

- crea o riutilizza vendor e filamenti in Spoolman;
- crea la bobina con colore, peso, tara, temperature, posizione e lotto;
- supporta bobine a colore singolo e multicolore (da 2 a 8 colori HEX),
  mantenendo tutte le tinte nel profilo Orca;
- genera **un solo profilo reale** in Snapmaker Orca;
- rileva anche le bobine aggiunte direttamente dal sito di Spoolman;
- installa o ripristina in sicurezza **U1FA AutoPA Mod** sulla U1 Stock;
- guida la calibrazione Adaptive PA e salva automaticamente il risultato nel
  profilo Orca selezionato;
- calcola un envelope specifico per il filamento dal flusso volumetrico massimo
  ereditato in Orca, con limiti facoltativi del produttore;
- controlla la disponibilità di nuove versioni dell'app senza aggiornare il
  firmware della stampante.

Non richiede PAXX o altri plugin. Può però utilizzare uno Spoolman già fornito da
PAXX oppure installato su un altro dispositivo della rete.

## Flusso automatico

1. Inserisci i dati della bobina nell'app.
2. U1FA crea o riutilizza vendor e filamento, quindi crea la bobina in Spoolman.
3. U1FA genera il relativo profilo nella cartella reale di Snapmaker Orca.
4. Selezioni slot fisico e temperatura. La modalità automatica consigliata legge
   da Orca il flusso volumetrico massimo ereditato dal profilo; eventuali
   velocità min/max del produttore possono imporre un limite più prudente.
5. Controlli velocità, flussi e comandi calcolati, quindi confermi la calibrazione.
6. Al termine U1FA crea un backup del JSON e inserisce automaticamente nello
   stesso profilo PA statico, tabella Adaptive PA e PA ponti.

Per una bobina multicolore selezionare **Multicolore** nella creazione bobina.
I selettori grafici mostrano già due colori: usare il selettore, aggiungere fino
a otto colori con **Aggiungi colore** e mantenerli nell'ordine della bobina.
I codici HEX vengono sincronizzati automaticamente. Le bobine PLA multicolore
usano automaticamente il profilo base Snapmaker PLA Silk. Selezionare anche la
disposizione: **bicolore affiancati (coassiale)** per Sunset Ember e filamenti
con due colori affiancati; **cambio lungo il filo** per i filamenti con transizione
longitudinale.

Non è necessario copiare manualmente i risultati. Durante tutta la calibrazione
lasciare U1FA aperta e Snapmaker Orca completamente chiuso. Riaprire lo slicer
soltanto dopo che U1FA mostra `calibrazione completata`, così caricherà il profilo
appena aggiornato.

Se Moonraker restituisce un errore temporaneo, compreso `HTTP 504`, U1FA riprova
automaticamente senza riavviare la calibrazione. Se i tentativi non bastano, nella
schermata di stato compare **Recupera ultima calibrazione**: il pulsante rilegge la
suite appena completata e aggiorna lo stesso profilo con backup, senza inviare
G-code. Non ripetere il test e non riavviare la U1 prima di aver tentato il recupero.

La calibrazione richiede indicativamente **circa 10 minuti**. Durante il test non
spegnere o riavviare la U1 e non inviare altri comandi da Fluidd o dal display.

## Download e installazione

Scaricare il pacchetto adatto dalla pagina
[GitHub Releases](https://github.com/ubaccu/u1-filament-automation/releases).

### macOS

- `macOS-arm64.dmg` per Mac con chip Apple Silicon;
- `macOS-x86_64.dmg` per Mac Intel.

Aprire il DMG, trascinare **U1 Filament Automation** in **Applicazioni** e
avviarla. Se la build non è firmata, al primo avvio usare
**tasto destro sull'app → Apri → Apri**.

U1FA si apre in una normale finestra desktop con icona nel Dock; non richiede di
usare Chrome o un altro browser.

### Come chiudere correttamente U1FA

Per terminare completamente l'app, dalla schermata iniziale scorrere fino alla
sezione **Chiudi applicazione**, premere il pulsante omonimo e confermare con
**Chiudi davvero U1FA**. In questo modo vengono arrestati insieme la finestra, il
monitor Spoolman e il servizio interno. Attendere 2–3 secondi prima di riaprirla.

La chiusura viene bloccata durante una calibrazione attiva, per evitare che il
risultato PA non venga salvato nel profilo Orca.

### Windows 10/11 x64

Avviare il file `Windows-x64-Setup.exe` e seguire l'installazione. Per configurare
la modifica sulla stampante serve **OpenSSH Client** di Windows; non serve
OpenSSH Server.

### Linux x86_64

Rendere eseguibile l'AppImage e avviarla:

```bash
chmod +x U1-Filament-Automation-*-Linux-x86_64.AppImage
./U1-Filament-Automation-*-Linux-x86_64.AppImage
```

Per configurare la stampante deve essere installato `openssh-client`.

## Prima configurazione della U1

Dal touchscreen della stampante abilitare:

1. **Impostazioni → Manutenzione → Modalità avanzata → Accetto → Abilita**;
2. **Impostazioni → Manutenzione → Accesso Root → Accetto → Apri**.

Modalità avanzata abilita l'accesso a Fluidd. Accesso Root consente all'app di
creare il backup e configurare i file necessari tramite SSH.

Al primo avvio U1FA chiede l'IP o hostname della stampante e verifica la
connessione. L'indirizzo Spoolman può essere lasciato vuoto per la ricerca
automatica oppure inserito manualmente.

La password SSH non viene salvata. Se non è stata modificata, quella predefinita
della configurazione U1 è `snapmaker`.

## U1FA AutoPA Mod

La configurazione guidata:

- controlla lo stato della stampante in sola lettura;
- verifica il file originale tramite SHA-256;
- crea un backup prima della sostituzione;
- configura `flow_calibrator.py`;
- installa `adaptive_pa_macro.cfg`;
- aggiunge il relativo include a `printer.cfg`;
- blocca file o firmware non riconosciuti;
- non esegue riavvii automatici.

Ogni operazione reale richiede due conferme e viene bloccata se la stampante non
è completamente inattiva.

Dopo un aggiornamento firmware U1, eseguire nuovamente **Controlla configurazione
stampante**. Se il nuovo file originale non è ancora riconosciuto, U1FA non lo
modifica. Maggiori informazioni sono disponibili in
[Compatibilità firmware](docs/FIRMWARE_COMPATIBILITY.md).

## Profili filamento

La base Snapmaker viene scelta automaticamente dal materiale e dal nome tecnico.
Nel modulo di creazione è disponibile anche **PLA Silk**: usa la base Snapmaker
PLA Silk e propone 230 °C come temperatura ugello.
Esempi:

- PLA normale → Snapmaker PLA Basic;
- PLA Silk → Snapmaker PLA Silk;
- PLA Rapid, Hyper, High Speed, HS o HF → Snapmaker PLA SnapSpeed;
- PETG → relativo profilo Snapmaker PETG compatibile.

Un profilo Orca già esistente non viene sovrascritto durante la creazione. Prima
di applicare i risultati PA al profilo selezionato viene sempre creato un backup
datato.

### Envelope di calibrazione

Usare **Automatico dal profilo filamento** salvo esigenze specifiche. U1FA segue
l'ereditarietà Orca fino a trovare `filament_max_volumetric_speed`, converte il
limite di flusso usando la geometria della linea di calibrazione e non supera mai
il limite macchina U1FA. Se il produttore dichiara un intervallo lineare di
velocità di stampa, lo si può inserire come ulteriore limite più prudente. Prima
dell'avvio la pagina di conferma mostra origine del dato, limite determinante,
tre velocità e relativi flussi volumetrici.

La modalità **Manuale avanzato** resta disponibile per collaudatori esperti e
impone i massimi U1FA di 336 mm/s e 10.000 mm/s². La sola dicitura PLA/PETG non è
considerata una velocità affidabile: il materiale seleziona la base corretta,
mentre l'envelope deriva dal flusso del profilo.

## Sicurezza e privacy

- l'interfaccia è accessibile soltanto dal computer locale;
- password e credenziali non vengono salvate;
- nessun indirizzo o dato dell'utente viene inviato a Bottega3DLab;
- i firmware e i file sconosciuti vengono bloccati;
- gli aggiornamenti dell'app vengono verificati tramite dimensione e SHA-256;
- l'aggiornamento dell'app non installa né modifica il firmware della U1.

## Documentazione

- [Installazione e ripristino della stampante](docs/INSTALLAZIONE_STAMPANTE.md)
- [Compatibilità firmware U1](docs/FIRMWARE_COMPATIBILITY.md)
- [Aggiornamenti dell'app](docs/AGGIORNAMENTI_APP.md)
- [Collaudo beta privato](docs/BETA_TESTING.md)

## Licenza, crediti e responsabilità

U1 Filament Automation è distribuita sotto **GNU General Public License v3.0**.
Vedere [LICENSE](LICENSE).

### Avviso di sicurezza e responsabilità

U1FA modifica file di configurazione della stampante e può avviare movimenti e
riscaldamento durante la calibrazione. Utilizzarla soltanto su una stampante
propria o per la quale si è autorizzati, e soltanto se si comprendono le
operazioni mostrate. Conservare backup verificati, assicurarsi che la stampante
sia inattiva, sorvegliare ogni calibrazione e fermarsi in caso di dubbi.

Il software è fornito **senza garanzia**, come previsto dalle sezioni 15 e 16
della GPLv3. Nei limiti massimi consentiti dalla legge applicabile, autori e
contributori non rispondono di danni a stampante, computer o rete; perdita di
dati o profili; stampe fallite; materiale consumato; fermo macchina; perdita
della garanzia; lesioni personali; o danni a terzi derivanti dall'uso o uso
improprio del software. Restano salvi i diritti e le responsabilità che la legge
non consente di escludere.

L'integrazione Adaptive PA deriva dal progetto
[U1 Adaptive Pressure Advance Auto Calibration](https://github.com/djsplice/u1-adaptive-pa-autocal)
di djsplice e contributori, distribuito sotto GNU GPL v3.0.

Si riconoscono inoltre il calibratore Snapmaker U1, OrcaSlicer Adaptive Pressure
Advance e le ispirazioni metodologiche indicate dal progetto upstream. Vedere
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Klipper, Snapmaker firmware, Moonraker, OrcaSlicer e Spoolman mantengono le
rispettive licenze. Questo progetto non li rilicenzia.

Strumento community indipendente per calibrazione e sperimentazione. Verificare
sempre i risultati sulla propria stampante e sul proprio filamento. Il progetto
non è affiliato né approvato da Snapmaker, OrcaSlicer o dagli altri progetti
citati.
