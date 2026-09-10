<div align="center">

# U1 Filament Automation

### Spoolman → Snapmaker Orca → Adaptive Pressure Advance

**Companion desktop per Snapmaker U1 by Bottega3DLab**  
Gestisce bobine reali, genera o riutilizza in sicurezza i profili Orca, guida la calibrazione Adaptive PA e mantiene gli aggiornamenti dell'app separati dal firmware della stampante.

[![Release](https://img.shields.io/github/v/release/ubaccu/u1-filament-automation?label=release)](https://github.com/ubaccu/u1-filament-automation/releases)
![Piattaforme](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-4c8bf5)
![Licenza](https://img.shields.io/badge/license-GPL--3.0-blue)
![Stato](https://img.shields.io/badge/status-stabile-brightgreen)

**[Scarica U1FA](https://github.com/ubaccu/u1-filament-automation/releases)** · **[Segnala un bug](https://github.com/ubaccu/u1-filament-automation/issues/new/choose)** · **[Documentazione](docs/INSTALLAZIONE_STAMPANTE.md)** · **[English](README.md)**

<a href="https://www.buymeacoffee.com/riccelliiv9" target="_blank" rel="noopener noreferrer"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" height="50"></a>

</div>

---

## Cos'è U1FA?

U1 Filament Automation è un'applicazione desktop community indipendente per **Snapmaker U1**. Collega i dati filamento presenti in **Spoolman** ai profili utente di **Snapmaker Orca**, poi guida la calibrazione **Adaptive Pressure Advance** e salva il risultato validato nel profilo selezionato dopo aver creato un backup.

Il repository pubblico è il canale ufficiale per **distribuzione, documentazione e supporto**. Lo sviluppo viene mantenuto separatamente. Le release pubbliche includono installer per le piattaforme supportate, checksum SHA-256 e un archivio sorgente GPL corrispondente alla stessa versione.

> **Compatibilità firmware:** U1FA 1.8.0 e il relativo flusso protetto di configurazione stampante / AutoPA Mod sono stati testati su **firmware Snapmaker U1 1.5**. **Il firmware 1.6.0 non è stato validato per installazione/ripristino dei file stampante in questa release.** Dopo un aggiornamento non dare per scontata la compatibilità: esegui il controllo in sola lettura e fermati se U1FA segnala uno stato sconosciuto o bloccato. Vedi [Compatibilità firmware U1](docs/COMPATIBILITA_FIRMWARE.md).

## Funzioni principali

- **Workflow Spoolman reale** — crea o riutilizza vendor e filamenti, poi crea bobine reali con colore, peso, tara, temperature, posizione di stoccaggio e lotto.
- **Bobine mono e multicolore** — da 2 a 8 colori HEX vengono mantenuti nel profilo Orca generato.
- **Rilevamento automatico U1** — il primo setup può rilevare in rete locale un endpoint Snapmaker U1/Moonraker compatibile tramite controlli in sola lettura prima di salvare qualsiasi configurazione.
- **Scelta automatica del profilo base Snapmaker Orca** — materiale e nome tecnico determinano il profilo compatibile.
- **Gestione anti-doppione dei profili** — un profilo esatto già esistente viene riutilizzato; anche un singolo profilo legacy equivalente riconosciuto in modo prudente può essere riutilizzato senza crearne un secondo.
- **Envelope di calibrazione specifico per filamento** — la modalità automatica legge il flusso volumetrico massimo ereditato da Orca e può applicare limiti produttore più prudenziali.
- **Workflow Adaptive PA** — calibrazione guidata, recupero risultati, backup profilo e scrittura automatica PA.
- **Controllo configurazione stampante** — installazione e ripristino di U1FA AutoPA Mod protetti da validazione file, controllo stato stampante e conferme esplicite.
- **Updater integrato** — seleziona il pacchetto corretto per la piattaforma e lo verifica tramite SHA-256. Aggiornare U1FA **non aggiorna il firmware U1**.

## Download

Apri **[GitHub Releases](https://github.com/ubaccu/u1-filament-automation/releases)** e scegli il pacchetto corretto:

| Piattaforma | Pacchetto | Note |
|---|---|---|
| macOS Apple Silicon | `macOS-arm64.dmg` | Mac Apple Silicon |
| macOS Intel | `macOS-x86_64.dmg` | Mac Intel |
| Windows | `Windows-x64-Setup.exe` | Windows 10/11 x64 |
| Linux | `Linux-x86_64.AppImage` | AppImage x86_64 |
| Sorgente | `Source.zip` | Sorgente GPL corrispondente alla versione |

Ogni release include anche **`SHA256SUMS.txt`**.

### Primo avvio su macOS

Le build macOS attuali non sono notarizzate da Apple. Dopo aver trascinato **U1 Filament Automation** in **Applicazioni**, al primo avvio usa **tasto destro / Control-click → Apri → Apri**. Se macOS continua a bloccarla, vai in **Impostazioni di Sistema → Privacy e Sicurezza → Apri comunque**.

### Linux

```bash
chmod +x U1-Filament-Automation-*-Linux-x86_64.AppImage
./U1-Filament-Automation-*-Linux-x86_64.AppImage
```

`openssh-client` serve soltanto per le operazioni protette di configurazione stampante.

## Come funziona

1. Inserisci o seleziona la bobina fisica in U1FA.
2. U1FA crea o riutilizza vendor e filamento in Spoolman, quindi crea la bobina.
3. Crea il relativo profilo utente Snapmaker Orca soltanto se serve. I profili esatti già esistenti vengono riutilizzati; anche un singolo profilo legacy equivalente riconosciuto in sicurezza può essere riutilizzato.
4. Calcola l'envelope consigliato partendo dal limite di flusso volumetrico ereditato dal profilo.
5. Ti mostra velocità, flussi e operazioni previste prima della conferma esplicita della calibrazione.
6. A calibrazione conclusa crea un backup del JSON Orca e scrive i valori PA validati nello stesso profilo.

Per l'uso normale è consigliata la modalità **Automatico dal profilo filamento**. La modalità manuale avanzata resta disponibile per utenti esperti.

## Sicurezza progettata nell'app

U1FA può modificare file di configurazione della stampante e può avviare movimenti e riscaldamento durante la calibrazione, quindi le protezioni sono volutamente rigide:

- i controlli stampante iniziano in modalità **sola lettura**;
- firmware e file sconosciuti vengono bloccati;
- le modifiche richiedono conferma esplicita e stampante completamente inattiva;
- i file originali vengono validati e viene creato un backup prima della sostituzione;
- i profili Orca esistenti non vengono sovrascritti durante la creazione bobina/profilo;
- i profili Orca vengono salvati prima di scrivere i valori PA;
- la password SSH non viene memorizzata;
- gli aggiornamenti dell'app vengono verificati tramite dimensione e SHA-256;
- aggiornare U1FA non installa né modifica il firmware Snapmaker U1;
- durante il setup U1FA non esegue riavvii automatici della stampante.

Durante una calibrazione lascia U1FA aperta e Snapmaker Orca chiuso. Non inviare comandi non collegati al test da Fluidd o dal touchscreen.

## Prima configurazione della U1

Prima della configurazione protetta abilita dal touchscreen:

1. **Impostazioni → Manutenzione → Modalità avanzata → Accetto → Abilita**
2. **Impostazioni → Manutenzione → Accesso Root → Accetto → Apri**

Poi usa **Controlla configurazione stampante** dentro U1FA. L'app può prima rilevare automaticamente in rete locale l'endpoint U1/Moonraker tramite controlli in sola lettura; la configurazione manuale resta disponibile. **Il flusso protetto sui file stampante di U1FA 1.8.0 è validato sul firmware 1.5; il firmware 1.6.0 non è ancora validato.** Dopo ogni aggiornamento firmware U1, esegui nuovamente il controllo prima di calibrare e non forzare un'installazione bloccata.

Guide complete:

- [Installazione e ripristino della stampante](docs/INSTALLAZIONE_STAMPANTE.md)
- [Compatibilità firmware U1](docs/COMPATIBILITA_FIRMWARE.md)
- [Aggiornamenti dell'app](docs/AGGIORNAMENTI_APP.md)
- [Supporto e segnalazione bug](SUPPORT.it.md)

## Famiglie profilo filamento supportate

U1FA include mapping automatici per le famiglie PLA/PETG supportate da Snapmaker Orca, comprese le varianti standard, rapid/high-speed, silk, wood, translucent e carbon-fibre quando è disponibile un profilo base compatibile.

Esempi:

- PLA standard → **Snapmaker PLA Basic**
- PLA Rapid / Hyper / High Speed / HS / HF → **Snapmaker PLA SnapSpeed**
- PLA Silk → **Snapmaker PLA Silk**
- famiglie PETG → relativo profilo compatibile **Snapmaker PETG**

Il riconoscimento dei profili equivalenti è volutamente prudente. Se U1FA trova più di un profilo equivalente, blocca la scelta automatica invece di indovinare.

## Supporto e segnalazione bug

Hai trovato un bug? Usa **[GitHub Issues](https://github.com/ubaccu/u1-filament-automation/issues/new/choose)** e indica versione U1FA, sistema operativo, versione firmware U1, versione Snapmaker Orca, cosa ti aspettavi, cosa è successo e, quando utili, screenshot o log ripuliti da dati sensibili.

Per problemi di sicurezza non pubblicare credenziali, indirizzi IP privati, log completi o dati personali. Segui invece [SECURITY.md](.github/SECURITY.md).

Consulta [SUPPORT.it.md](SUPPORT.it.md) per la procedura completa.

## Privacy

U1FA è pensato per uso locale. Le credenziali non vengono memorizzate e indirizzi o dati bobina non vengono inviati a Bottega3DLab. L'accesso di rete viene usato solo per i servizi configurati dall'utente e per il canale pubblico degli aggiornamenti dell'app.

## Licenza e crediti

U1 Filament Automation è distribuito sotto **GNU General Public License v3.0**. Vedi [LICENSE](LICENSE) e [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

L'integrazione Adaptive PA deriva da [U1 Adaptive Pressure Advance Auto Calibration](https://github.com/djsplice/u1-adaptive-pa-autocal) di djsplice e contributori, anch'esso distribuito sotto GNU GPL v3.0. Restano inoltre i crediti al calibratore Snapmaker U1, OrcaSlicer Adaptive Pressure Advance e al lavoro metodologico upstream indicato nelle note di terze parti.

Klipper, firmware Snapmaker, Moonraker, OrcaSlicer e Spoolman mantengono le rispettive licenze. Questo progetto non li rilicenzia.

## Disclaimer

U1FA è software community indipendente per calibrazione e sperimentazione. **Non è affiliato né approvato da Snapmaker, OrcaSlicer o dagli altri progetti citati.**

Usalo soltanto su una stampante di tua proprietà o per la quale sei autorizzato. Conserva backup verificati, assicurati che la stampante sia inattiva prima della configurazione, sorveglia le calibrazioni e fermati se qualcosa non è chiaro. Il software viene fornito **senza garanzia**, come previsto dalle sezioni 15 e 16 della GPLv3.
