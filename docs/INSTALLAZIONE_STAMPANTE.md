# Installazione e ripristino U1FA AutoPA Mod

**Italiano** | [English](PRINTER_SETUP.md)

Questa guida descrive la configurazione protetta di **U1FA AutoPA Mod** sulla Snapmaker U1. U1FA gestisce in modo coordinato:

- il modulo attivo `/home/lava/klipper/klippy/extras/flow_calibrator.py`;
- la macro `/home/lava/printer_data/config/adaptive_pa_macro.cfg`;
- il relativo include in `printer.cfg`, solo quando necessario.

## Prima di iniziare

La stampante deve essere completamente inattiva. Non eseguire setup o ripristino durante una stampa o mentre una calibrazione è attiva.

Dal touchscreen della U1 abilita:

1. **Impostazioni → Manutenzione → Modalità avanzata → Accetto → Abilita** — rende disponibile Fluidd/Moonraker;
2. **Impostazioni → Manutenzione → Accesso Root → Accetto → Apri** — abilita SSH per backup e installazione protetta.

Se non è stata modificata dall'utente, la password SSH predefinita è `snapmaker`. U1FA può mostrarla come promemoria, ma **non la salva**.

## Rilevamento U1 e Spoolman

Al primo setup usa **Controlla configurazione stampante**.

U1FA può cercare la Snapmaker U1 sulla rete locale soltanto quando l'utente avvia esplicitamente il rilevamento. La ricerca:

- usa richieste HTTP Moonraker in sola lettura;
- identifica Moonraker tramite `/server/info`;
- conferma la presenza della U1 verificando gli oggetti stampante attesi;
- non invia G-code, non avvia movimenti, non riscalda e non modifica file;
- chiede conferma prima di salvare l'endpoint trovato.

La configurazione manuale di IP/hostname resta disponibile se il rilevamento automatico non trova la stampante.

Dopo aver verificato la U1, U1FA può rilevare Spoolman controllando le sorgenti previste dalla configurazione locale/Moonraker/PAXX e la porta standard U1. È sempre possibile indicare manualmente un indirizzo o una porta non standard.

## Requisiti del computer

- **macOS:** il client SSH è già incluso;
- **Windows:** serve **OpenSSH Client** soltanto per la configurazione protetta dei file stampante; OpenSSH Server non è richiesto;
- **Linux:** installa `openssh-client` se il comando `ssh` non è disponibile.

U1FA rileva l'assenza del client e non installa automaticamente componenti di sistema.

## Procedura desktop consigliata

1. Apri U1FA con la stampante completamente inattiva.
2. Verifica o rileva U1/Moonraker e Spoolman.
3. Apri **Controlla configurazione stampante**.
4. Conferma di avere abilitato Modalità avanzata e Accesso Root.
5. Inserisci la password SSH soltanto quando richiesta.
6. Esegui prima il **controllo in sola lettura**.
7. Fermati se compare `unknown`, `unknown-blocked`, un SHA-256 inatteso o uno stato stampante non inattivo.
8. Controlla attentamente file e operazioni mostrati nell'anteprima.
9. Applica modifiche soltanto se tutti i componenti sono riconosciuti e dopo le conferme esplicite richieste dall'app.

Prima di ogni scrittura U1FA ricontrolla lo stato stampante e gli hash dei file. I file esistenti ricevono backup esclusivi con timestamp; le scritture sono atomiche e verificate. In caso di errore, il flusso tenta il rollback previsto.

U1FA **non invia** `RESTART` o `FIRMWARE_RESTART` per completare il setup. Dopo una vera installazione o un ripristino, spegni completamente la U1, attendi 10–15 secondi e riaccendila.

## Controllo tecnico in sola lettura

Per utenti avanzati, l'equivalente CLI del controllo è:

```bash
u1fa printer-check \
  --ssh-target root@IP_DELLA_U1 \
  --moonraker-url http://IP_DELLA_U1 \
  --ask-ssh-password
```

Il controllo legge stato Moonraker/Snapmaker e SHA-256 dei componenti necessari. Non invia G-code e non scrive file.

## Anteprima tecnica

```bash
u1fa printer-install \
  --ssh-target root@IP_DELLA_U1 \
  --moonraker-url http://IP_DELLA_U1
```

Senza `--apply`, mostra le operazioni previste senza scrivere sulla stampante.

## Applicazione tecnica protetta

```bash
u1fa printer-install \
  --ssh-target root@IP_DELLA_U1 \
  --moonraker-url http://IP_DELLA_U1 \
  --apply \
  --confirm-printer-write
```

Le protezioni includono:

1. verifica stato Moonraker e stato macchina Snapmaker;
2. lettura e confronto SHA-256;
3. seconda verifica dello stato prima della scrittura;
4. blocco di calibratori o macro sconosciuti;
5. riconoscimento degli include previsti in `printer.cfg`;
6. backup esclusivi datati dei file da modificare;
7. controllo sintattico del Python modificato;
8. scritture atomiche con permessi e proprietario coerenti;
9. verifica finale e rollback in caso di errore;
10. richiesta di power-cycle completo soltanto dopo una scrittura effettiva.

## Ripristino tecnico

```bash
u1fa printer-restore \
  --ssh-target root@IP_DELLA_U1 \
  --moonraker-url http://IP_DELLA_U1 \
  --backup-path /home/lava/klipper/klippy/extras/NOME_BACKUP \
  --apply \
  --confirm-printer-write
```

Il backup deve corrispondere a un originale validato e rispettare i criteri accettati da U1FA. Anche dopo un ripristino effettivo è necessario spegnere completamente la stampante, attendere 10–15 secondi e riaccenderla.

## Aggiornamenti firmware

Dopo ogni aggiornamento firmware Snapmaker, non copiare manualmente il vecchio calibratore sopra il nuovo. Esegui di nuovo **Controlla configurazione stampante** e fermati al controllo in sola lettura se l'originale non è riconosciuto.

Vedi [Compatibilità firmware U1](COMPATIBILITA_FIRMWARE.md).

## Sandbox di sviluppo

Durante sviluppo e test usa la sandbox locale invece della stampante reale:

```bash
u1fa printer-install --sandbox-root ~/Downloads/u1fa-printer-sandbox --apply
```

La sandbox replica i percorsi necessari in una cartella locale e non apre connessioni SSH o HTTP verso la U1.
