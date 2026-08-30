# U1 Filament Automation

Applicazione desktop community di **Bottega3DLab** per collegare Spoolman,
Snapmaker Orca e la calibrazione Adaptive Pressure Advance della Snapmaker U1.

Disponibile in italiano e inglese per macOS, Windows e Linux.

## Cosa fa

- crea o riutilizza vendor e filamenti in Spoolman;
- crea la bobina con colore, peso, tara, temperature, posizione e lotto;
- genera **un solo profilo reale** in Snapmaker Orca;
- rileva anche le bobine aggiunte direttamente dal sito di Spoolman;
- installa o ripristina in sicurezza **U1FA AutoPA Mod** sulla U1 Stock;
- guida la calibrazione Adaptive PA e salva automaticamente il risultato nel
  profilo Orca selezionato;
- controlla la disponibilità di nuove versioni dell'app senza aggiornare il
  firmware della stampante.

Non richiede PAXX o altri plugin. Può però utilizzare uno Spoolman già fornito da
PAXX oppure installato su un altro dispositivo della rete.

## Flusso automatico

1. Inserisci i dati della bobina nell'app.
2. U1FA crea o riutilizza vendor e filamento, quindi crea la bobina in Spoolman.
3. U1FA genera il relativo profilo nella cartella reale di Snapmaker Orca.
4. Selezioni slot fisico e temperatura, controlli i comandi e confermi la
   calibrazione.
5. Al termine U1FA crea un backup del JSON e inserisce automaticamente nello
   stesso profilo PA statico, tabella Adaptive PA e PA ponti.

Non è necessario copiare manualmente i risultati. Se Snapmaker Orca era già
aperto, chiuderlo e riaprirlo dopo il completamento per ricaricare il profilo.

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
Esempi:

- PLA normale → Snapmaker PLA Basic;
- PLA Rapid, Hyper, High Speed, HS o HF → Snapmaker PLA SnapSpeed;
- PETG → relativo profilo Snapmaker PETG compatibile.

Un profilo Orca già esistente non viene sovrascritto durante la creazione. Prima
di applicare i risultati PA al profilo selezionato viene sempre creato un backup
datato.

## Sicurezza e privacy

- l'interfaccia è accessibile soltanto dal computer locale;
- password e credenziali non vengono salvate;
- nessun indirizzo o dato dell'utente viene inviato a Bottega3DLab;
- i firmware e i file sconosciuti vengono bloccati;
- gli aggiornamenti dell'app vengono verificati tramite dimensione e SHA-256;
- l'aggiornamento dell'app non installa né modifica il firmware della U1.

## English quick start

U1 Filament Automation is a bilingual desktop community app by Bottega3DLab. It
creates Spoolman inventory entries, generates one real Snapmaker Orca filament
profile and runs the guided Adaptive Pressure Advance workflow.

When calibration is complete, U1FA backs up and automatically updates the
selected Orca profile. No manual PA value entry is required.

Before printer setup, enable both features on the U1 touchscreen:

1. **Settings → Maintenance → Advanced Mode → Agree → Enable**;
2. **Settings → Maintenance → Root Access → Agree → Open**.

The SSH password is never stored. If unchanged, the default U1 configuration
password is `snapmaker`. A calibration takes approximately **10 minutes**. Do not
power off or restart the printer and do not send other commands while it is
running.

After a U1 firmware update, run **Check printer setup** again. Unknown firmware or
file hashes are blocked instead of being overwritten.

## Licenza, crediti e responsabilità

U1 Filament Automation è distribuita sotto **GNU General Public License v3.0**.
Vedere [LICENSE](LICENSE).

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
