# Collaudo privato U1FA 1.8 / U1FA 1.8 private testing

Questa beta non è una release pubblica stabile. Ogni collaudatore deve conoscere
in anticipo quali passaggi leggono dati, quali scrivono in Spoolman/Orca e quale
passaggio può modificare la U1.

This beta is not a stable public release. Testers must understand which steps are
read-only, which write to Spoolman/Orca and which step can modify the U1.

## Dati da annotare / Test information

- sistema operativo e architettura;
- versione Snapmaker Orca;
- U1 Stock oppure U1 con PAXX/altre modifiche;
- posizione di Spoolman: stesso computer, PAXX/U1 oppure altro host;
- versione firmware U1;
- esito e messaggio esatto di ogni fase.

Non pubblicare password, IP privati, nomi personali o log non controllati.

Record the OS/architecture, Snapmaker Orca version, Stock/PAXX setup, Spoolman
location, U1 firmware and the exact result of each stage. Do not publish passwords,
private IP addresses, personal names or unreviewed logs.

## Ordine obbligatorio / Required order

1. Installare il pacchetto corretto e verificare che l'app apra la pagina locale
   `127.0.0.1:8765`.
2. Configurare U1 e Spoolman. Questo controllo è in sola lettura.
3. Aprire **Configurazione o ripristino U1FA AutoPA Mod** e fare soltanto
   **Controlla in sola lettura**.
4. Se compare `unknown`, `sconosciuto`, un SHA-256 inatteso o una stampante non
   inattiva, fermarsi e inviare il report: non applicare nulla.
5. Verificare una bobina già presente e l'anteprima del mapping fisico
   `1→0, 2→1, 3→2, 4→3`; non avviare ancora la calibrazione.
6. Provare la creazione di una bobina soltanto su un'istanza Spoolman di test o con
   dati che si desidera realmente conservare. Controllare che il profilo Orca sia
   stato creato una sola volta e che un profilo esistente non sia sovrascritto.
7. L'applicazione della modifica sulla U1 è riservata inizialmente a un tester con
   U1 Stock, stampante completamente inattiva e disponibilità a eseguire il power
   cycle richiesto. Devono essere mostrati due riepiloghi/conferme.
8. Controllare che l'app installi/verifichi sia
   `/home/lava/klipper/klippy/extras/flow_calibrator.py` sia
   `/home/lava/printer_data/config/adaptive_pa_macro.cfg` e il relativo include.
9. Eseguire una calibrazione PA completa solo dopo avere verificato profilo,
   estrusore e temperatura. Dura circa 10 minuti: non inviare altri comandi e non
   spegnere la U1.
10. Verificare backup del profilo Orca, cinque punti Adaptive PA, PA statica e PA
    ponti. Chiudere l'app con il pulsante dedicato.
11. Verificare la scheda **Aggiornamenti U1FA**. Nel repository privato il
    controllo pubblico può risultare non disponibile; non inserire token GitHub.
    Dopo la prima pre-release pubblica verificare selezione del pacchetto,
    dimensione, SHA-256 e doppia conferma prima dell'apertura dell'installer.

Per il firmware U1 1.6.0 la Beta 1 autorizza soltanto il controllo in lettura. Non
applicare U1FA AutoPA Mod finché la coppia originale/patchata 1.6 non compare come
convalidata in `FIRMWARE_COMPATIBILITY.md`.

Follow the same order in English: install and open the local app, verify
connections, run the printer read-only check, stop on unknown hashes, review slot
mapping, test Spoolman/Orca without overwrites, and let only an informed Stock U1
tester apply the printer modification. Confirm both the calibrator and
`adaptive_pa_macro.cfg`, then run the approximately ten-minute PA calibration only
after checking profile, extruder and temperature.

## Criteri per la release stabile / Stable release gate

- suite automatica verde su macOS Intel, macOS Apple Silicon, Windows x64 e Linux
  x86_64;
- apertura e chiusura corrette su almeno un computer reale per ogni sistema;
- nessun IP o percorso personale nei pacchetti;
- creazione Spoolman e profilo Orca confermata senza sovrascritture;
- controllo U1 Stock confermato almeno da due macchine;
- installazione e ripristino verificati almeno su una U1 Stock;
- calibrazione PA completa e salvataggio profilo verificati;
- README, licenza GPLv3, crediti upstream e checksum degli installer presenti.
- avviso aggiornamento verificato con una release di prova più nuova e rifiuto di
  un pacchetto con SHA-256 errato.
