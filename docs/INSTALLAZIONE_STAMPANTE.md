# Installazione del calibratore sulla Snapmaker U1

Questa procedura installa **U1FA AutoPA Mod** sulla U1 Stock. Il nome tecnico
interno `CHAIN v6` viene mantenuto nei file e nei comandi per compatibilità:

- `flow_calibrator.py` CHAIN v6;
- `adaptive_pa_macro.cfg` ULTRA v6;
- l'include della macro in `printer.cfg`, solo quando necessario.

## Configurazione degli indirizzi

Dalla v1.4 non è presente alcun IP U1 preimpostato. Avviando la GUI senza
`--moonraker-url`, la pagina **Connessioni** chiede:

- IP o hostname mostrato dalla Snapmaker U1;
- indirizzo Spoolman facoltativo; lasciandolo vuoto viene rilevato automaticamente.

Il rilevamento prova nell'ordine Spoolman sul computer corrente (`127.0.0.1`, che
indica sempre il computer dell'utente), gli endpoint pubblicati da Moonraker/PAXX
e la U1 sulla porta standard `7912`. Il campo resta disponibile per forzare un
indirizzo o una porta non standard.

Il pulsante **Verifica e salva** interroga Moonraker e Spoolman in sola lettura,
non invia G-code e ricava automaticamente SSH come `root@HOST`. Vengono salvati
soltanto i due indirizzi nel profilo personale del sistema operativo; la password
SSH non viene memorizzata. La stessa pagina consente di aggiornare l'indirizzo se
il router cambia l'IP della stampante.

## Requisiti

- stampa terminata e U1 completamente inattiva;
- Moonraker raggiungibile;
- accesso SSH attivo per l'utente `root`, con chiave oppure password;
- file originale oppure v6 con SHA-256 riconosciuto.

Su Windows è richiesto **OpenSSH Client** soltanto per questa configurazione; si
abilita dalle Funzionalità facoltative del sistema. Non occorre OpenSSH Server. Su
Linux installare il pacchetto `openssh-client` se il comando `ssh` non è presente.
macOS include già il client. U1FA rileva l'assenza prima dell'accesso e non tenta di
installare componenti di sistema.

Prima di usare la GUI, abilitare dal display della U1 due funzioni distinte:

1. `Settings / Impostazioni → Maintenance / Manutenzione → Advanced Mode /
   Modalità avanzata → Agree / Accetto → Enable / Abilita`: rende accessibile
   Fluidd dall'indirizzo IP della stampante;
2. `Settings / Impostazioni → Maintenance / Manutenzione → Root Access /
   Accesso Root → Agree / Accetto → Open / Apri`: abilita il collegamento SSH
necessario per backup e installazione.

Se non è stata modificata dall'utente, la password SSH predefinita è
`snapmaker`. La GUI la indica come promemoria ma non la precompila e non la salva.

Il file modificato non è una copia separata: è il file originale usato da Klipper,
`/home/lava/klipper/klippy/extras/flow_calibrator.py`. La GUI lo mostra prima
della conferma e non lo sostituisce se SHA-256 o stato stampante non corrispondono
alle condizioni validate.

In alternativa alla chiave SSH, aggiungere `--ask-ssh-password`: la password viene
chiesta in modo nascosto e non viene salvata. Questa modalità non aggiunge chiavi né
modifica `/root/.ssh/authorized_keys` sulla U1.

## Controllo in sola lettura

```bash
u1fa printer-check \
  --ssh-target root@IP_DELLA_U1 \
  --moonraker-url http://IP_DELLA_U1 \
  --ask-ssh-password
```

Il controllo legge lo stato ufficiale Moonraker e lo SHA-256 del calibratore. Se la
stampante sta stampando o è in pausa, il comando si ferma prima di leggere il file
via SSH.

Controlla anche lo SHA-256 della macro personalizzata installata sulla U1 Stock in
`/home/lava/printer_data/config/adaptive_pa_macro.cfg` e verifica tramite l'elenco
oggetti Moonraker che `APA_COIL_RUN_ULTRA` sia effettivamente caricata da Klipper.
Tutte queste operazioni sono in sola lettura.

Nel firmware ufficiale Snapmaker lo stato macchina inattivo è
`MachineMainState.IDLE = 0`: l'app accetta `0`/`IDLE` e blocca ogni altro valore.

## Anteprima

```bash
u1fa printer-install \
  --ssh-target root@IP_DELLA_U1 \
  --moonraker-url http://IP_DELLA_U1
```

Mostra cosa verrebbe eseguito sui tre componenti, senza scrivere file e senza
riavviare Klipper.

## Applicazione reale

```bash
u1fa printer-install \
  --ssh-target root@IP_DELLA_U1 \
  --moonraker-url http://IP_DELLA_U1 \
  --apply \
  --confirm-printer-write
```

Ordine delle protezioni:

1. verifica `printer/info`, `print_stats`, `virtual_sdcard`, `idle_timeout` e lo
   stato macchina Snapmaker quando disponibile;
2. lettura e confronto SHA-256;
3. seconda verifica dello stato stampa;
4. blocco di qualunque calibratore o macro con SHA-256 sconosciuto;
5. riconoscimento degli include esatti e glob in `printer.cfg`;
6. backup esclusivi datati dei file esistenti da modificare;
7. controllo sintattico Python della v6;
8. scritture atomiche con permessi e proprietario coerenti;
9. verifica SHA-256 e rollback automatico in caso di errore;
10. richiesta esplicita di spegnimento completo e riaccensione.

I percorsi dei backup vengono stampati a fine operazione. Una macro già presente
ma sconosciuta non viene sovrascritta. Il master backup validato
documenta che `RESTART` non ricarica `flow_calibrator.py` nella sessione U1 già
attiva. Per questo l'app non invia riavvii: bisogna spegnere la U1, attendere 10–15
secondi e riaccenderla prima di usare i comandi CHAIN.

## Ripristino

```bash
u1fa printer-restore \
  --ssh-target root@IP_DELLA_U1 \
  --moonraker-url http://IP_DELLA_U1 \
  --backup-path /home/lava/klipper/klippy/extras/NOME_BACKUP \
  --apply \
  --confirm-printer-write
```

Il backup deve avere lo SHA-256 dell'originale validato e deve essere:

- un backup creato dall'app con prefisso `flow_calibrator.py.U1FA_BACKUP_`; oppure
- il backup storico `flow_calibrator.py.BACKUP_ORIGINALE_20260824` recuperato dal
  progetto precedente.

Anche dopo il ripristino occorre lo stesso spegnimento completo; un semplice
`RESTART` di Klipper non è sufficiente.

## Sandbox locale

La sandbox è il solo comando da usare durante lo sviluppo. Se la U1 è occupata,
non eseguire alcun comando reale:

```bash
u1fa printer-install --sandbox-root ~/Downloads/u1fa-printer-sandbox --apply
```

Replica i percorsi Linux della U1 dentro la cartella scelta e prova calibratore,
macro e include. Non apre connessioni SSH o HTTP e non vede la stampante reale.
