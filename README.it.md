<div align="center">

# U1 Filament Automation

### Spoolman → Snapmaker Orca → Adaptive Pressure Advance

**Companion desktop per Snapmaker U1 by Bottega3DLab**  
Gestisce bobine reali, genera profili Orca, guida la calibrazione Adaptive PA e mantiene gli aggiornamenti dell'app separati dal firmware della stampante.

[![Release](https://img.shields.io/github/v/release/ubaccu/u1-filament-automation?include_prereleases&label=release)](https://github.com/ubaccu/u1-filament-automation/releases)
![Piattaforme](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-4c8bf5)
![Licenza](https://img.shields.io/badge/license-GPL--3.0-blue)
![Stato](https://img.shields.io/badge/status-beta-orange)

**[Scarica U1FA](https://github.com/ubaccu/u1-filament-automation/releases)** · **[English](README.md)** · **[Configurazione stampante](docs/INSTALLAZIONE_STAMPANTE.md)** · **[Compatibilità firmware](docs/FIRMWARE_COMPATIBILITY.md)**

<a href="https://www.buymeacoffee.com/riccelliiv9" target="_blank" rel="noopener noreferrer"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" height="50"></a>

</div>

---

## Cos'è U1FA?

U1 Filament Automation è un'applicazione desktop community indipendente per **Snapmaker U1**. Collega i dati filamento presenti in **Spoolman** ai profili usati da **Snapmaker Orca**, poi guida la calibrazione **Adaptive Pressure Advance** e salva il risultato validato nel profilo selezionato dopo aver creato un backup.

Questo repository è il **canale pubblico di distribuzione** di U1FA. Lo sviluppo viene mantenuto separatamente; le release pubbliche includono installer per le varie piattaforme, checksum SHA-256 e un archivio sorgente GPL corrispondente alla stessa versione.

## Funzioni principali

- **Workflow Spoolman reale** — crea o riutilizza vendor e filamenti, poi crea bobine reali con colore, peso, tara, temperature, posizione e lotto.
- **Bobine mono e multicolore** — da 2 a 8 colori HEX vengono mantenuti nel profilo Orca generato.
- **Scelta automatica del profilo base Snapmaker Orca** — materiale e nome tecnico determinano il profilo compatibile.
- **Envelope di calibrazione specifico per filamento** — la modalità automatica legge il flusso volumetrico massimo ereditato da Orca e può applicare limiti produttore più prudenziali.
- **Workflow Adaptive PA** — calibrazione guidata, recupero risultati, backup profilo e scrittura automatica PA.
- **Controllo configurazione stampante** — installazione e ripristino di U1FA AutoPA Mod protetti da validazione file, controllo stato stampante e conferme esplicite.
- **Updater integrato** — seleziona il pacchetto corretto per la piattaforma e lo verifica tramite SHA-256. Aggiornare U1FA **non aggiorna il firmware U1**.

## Download

Apri **[GitHub Releases](https://github.com/ubaccu/u1-filament-automation/releases)** e scegli il pacchetto corretto:

| Piattaforma | Pacchetto | Note |
|---|---|---|
| macOS Apple Silicon | `macOS-arm64.dmg` | M1 / M2 / M3 / M4 e successivi |
| macOS Intel | `macOS-x86_64.dmg` | Mac Intel |
| Windows | `Windows-x64-Setup.exe` | Windows 10/11 x64 |
| Linux | `Linux-x86_64.AppImage` | AppImage x86_64 |
| Sorgente | `Source.zip` | Sorgente GPL corrispondente alla versione |

Ogni release include anche **`SHA256SUMS.txt`**.

### Primo avvio su macOS

Le build beta attuali non sono notarizzate da Apple. Dopo aver trascinato **U1 Filament Automation** in **Applicazioni**, al primo avvio usa **tasto destro / Control-click → Apri → Apri**. Se macOS continua a bloccarla, vai in **Impostazioni di Sistema → Privacy e Sicurezza → Apri comunque**.

### Linux

```bash
chmod +x U1-Filament-Automation-*-Linux-x86_64.AppImage
./U1-Filament-Automation-*-Linux-x86_64.AppImage
```

`openssh-client` serve solo per le operazioni di configurazione stampante.

## Come funziona

1. Inserisci o seleziona la bobina fisica in U1FA.
2. U1FA crea o riutilizza vendor e filamento in Spoolman, quindi crea la bobina.
3. Genera il relativo profilo utente Snapmaker Orca senza sovrascrivere un profilo già esistente.
4. Calcola l'envelope consigliato partendo dal limite di flusso volumetrico ereditato dal profilo.
5. Ti mostra velocità, flussi e operazioni previste prima della conferma esplicita.
6. A calibrazione conclusa crea un backup del JSON Orca e scrive i valori PA validati nello stesso profilo.

Per l'uso normale è consigliata la modalità **Automatico dal profilo filamento**. La modalità manuale avanzata resta disponibile per utenti esperti.

## Sicurezza progettata nell'app

U1FA può modificare file di configurazione della stampante e può avviare movimenti e riscaldamento durante la calibrazione, quindi le protezioni sono volutamente rigide:

- i controlli stampante iniziano in modalità **sola lettura**;
- firmware e file sconosciuti vengono bloccati;
- le modifiche richiedono conferma esplicita e stampante completamente inattiva;
- i file originali vengono validati e viene creato un backup prima della sostituzione;
- i profili Orca vengono salvati prima di scrivere i valori PA;
- la password SSH non viene memorizzata;
- gli aggiornamenti dell'app vengono verificati tramite dimensione e SHA-256;
- aggiornare U1FA non installa né modifica il firmware Snapmaker U1;
- durante il setup U1FA non esegue riavvii automatici della stampante.

Durante una calibrazione lascia U1FA aperta e Snapmaker Orca chiuso. Non inviare comandi non collegati al test da Fluidd o dal touchscreen.

## Prima configurazione della U1

Prima di configurare la stampante abilita dal touchscreen:

1. **Impostazioni → Manutenzione → Modalità avanzata → Accetto → Abilita**
2. **Impostazioni → Manutenzione → Accesso Root → Accetto → Apri**

Poi usa **Controlla configurazione stampante** dentro U1FA. Dopo ogni aggiornamento firmware U1, esegui nuovamente il controllo prima di calibrare.

Guide complete:

- [Installazione e ripristino della stampante](docs/INSTALLAZIONE_STAMPANTE.md)
- [Compatibilità firmware U1](docs/FIRMWARE_COMPATIBILITY.md)
- [Aggiornamenti dell'app](docs/AGGIORNAMENTI_APP.md)
- [Printer setup / recovery](docs/PRINTER_SETUP.md)

## Famiglie profilo filamento supportate

U1FA include attualmente i mapping automatici per le famiglie PLA/PETG supportate da Snapmaker Orca, comprese le varianti standard, rapid/high-speed, silk, wood, translucent e carbon-fibre quando è disponibile un profilo base compatibile.

Esempi:

- PLA standard → **Snapmaker PLA Basic**
- PLA Rapid / Hyper / High Speed / HS / HF → **Snapmaker PLA SnapSpeed**
- PLA Silk → **Snapmaker PLA Silk**
- famiglie PETG → relativo profilo compatibile **Snapmaker PETG**

Durante la creazione un profilo Orca già esistente non viene sovrascritto.

## Privacy

U1FA è pensato per uso locale. Le credenziali non vengono memorizzate e indirizzi o dati bobina non vengono inviati a Bottega3DLab. L'accesso di rete viene usato solo per i servizi configurati dall'utente e per il canale pubblico degli aggiornamenti dell'app.

## Licenza e crediti

U1 Filament Automation è distribuito sotto **GNU General Public License v3.0**. Vedi [LICENSE](LICENSE) e [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

L'integrazione Adaptive PA deriva da [U1 Adaptive Pressure Advance Auto Calibration](https://github.com/djsplice/u1-adaptive-pa-autocal) di djsplice e contributori, anch'esso distribuito sotto GNU GPL v3.0. Restano inoltre i crediti al calibratore Snapmaker U1, OrcaSlicer Adaptive Pressure Advance e al lavoro metodologico upstream indicato nelle note di terze parti.

Klipper, firmware Snapmaker, Moonraker, OrcaSlicer e Spoolman mantengono le rispettive licenze. Questo progetto non li rilicenzia.

## Disclaimer

U1FA è software community indipendente per calibrazione e sperimentazione. **Non è affiliato né approvato da Snapmaker, OrcaSlicer o dagli altri progetti citati.**

Usalo soltanto su una stampante di tua proprietà o per la quale sei autorizzato. Conserva backup verificati, assicurati che la stampante sia inattiva prima della configurazione, sorveglia le calibrazioni e fermati se qualcosa non è chiaro. Il software viene fornito **senza garanzia**, come previsto dalle sezioni 15 e 16 della GPLv3.
