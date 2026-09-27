# Compatibilità firmware Snapmaker U1

**Italiano** | [English](FIRMWARE_COMPATIBILITY.md)

Un aggiornamento firmware Snapmaker può sostituire o modificare:

- `/home/lava/klipper/klippy/extras/flow_calibrator.py`;
- `/home/lava/printer_data/config/adaptive_pa_macro.cfg`;
- il relativo include in `printer.cfg`.

U1FA include nel proprio pacchetto la modifica e la macro validate, ma **non installa un vecchio calibratore modificato sopra un nuovo originale sconosciuto**. Firmware o hash file sconosciuti restano bloccati finché non vengono esaminati e convalidati.

## Stato di validazione corrente

| Firmware / baseline | Stato | Azione consentita |
|---|---|---|
| Snapmaker U1 1.5.2 / baseline legacy riconosciuta | Convalidato | Installazione/ripristino protetti consentiti dopo conferma esplicita |
| PAXX `1.6.0-paxx12-22-31c5a38` / full version `1.6.0.267_20260815150420` | Convalidato fail-closed dal firmware PAXX ufficiale + installazione U1FA in sandbox | Usa il porting AutoPA firmware-2.0 solo se identità build e tutti gli hash PAXX convalidati corrispondono esattamente |
| PAXX `1.5.2-paxx12-21-2a88932` | Convalidato legacy fail-closed | Mantenuto per gli utenti ancora su PAXX 12-21; richiede identità e hash esatti |
| Snapmaker U1 2.0.0.205 (`2.0.0.205_20260914173503`) | Convalidato | Porting AutoPA dedicato; accettati sia il `print_task_config.py` stock convalidato sia la variante Adaptive PA convalidata SHA-256 `3770801d…` |
| Versioni U1 future o componenti con hash diverso | Bloccato | Nessuna scrittura né calibrazione finché non vengono esaminati |

Snapmaker pubblica le note ufficiali del firmware U1 qui:

https://wiki.snapmaker.com/en/snapmaker_u1/firmware/release_notes

## Dopo ogni aggiornamento firmware

1. Non copiare manualmente un file proveniente da un firmware precedente sopra quello nuovo.
2. Apri U1FA con la stampante completamente inattiva.
3. Usa **Controlla configurazione stampante**.
4. Esegui prima il controllo in sola lettura.
5. Se calibratore, macro e include risultano ancora validi, non serve alcuna scrittura.
6. Se U1FA riconosce un originale Snapmaker già convalidato, può proporre il ripristino protetto con backup e conferma esplicita.
7. Su firmware stock 1.5.2 e PAXX 12-21 U1FA usa il flusso AutoPA legacy; su stock 2.0.0.205 e PAXX 12-22 convalidato usa il porting AutoPA firmware-2.0. Le impronte di compatibilità restano separate e fail-closed.
8. PAXX 12-22 viene accettato soltanto con l'identità ufficiale esatta `1.6.0 / 1.6.0.267_20260815150420 / 1.6.0-paxx12-22-31c5a38` e con gli SHA-256 dei componenti convalidati. PAXX 12-21 resta una impronta legacy separata.
9. Se compare `unknown-blocked`, fermati. Il nuovo originale deve essere acquisito, confrontato e convalidato prima che il relativo hash venga aggiunto a una release futura.
10. Dopo una scrittura protetta effettiva, spegni completamente la U1, attendi 10–15 secondi e riaccendila. Non affidarti a un semplice `RESTART` di Klipper.

## Perché U1FA blocca i file sconosciuti

L'installazione sulla stampante modifica file Klipper attivi. Un aggiornamento firmware può cambiare l'implementazione Snapmaker, quindi riapplicare alla cieca una patch preparata per un file precedente potrebbe compromettere la calibrazione o il comportamento della stampante.

Per questo U1FA confronta SHA-256 conosciuti e si blocca intenzionalmente quando il file sorgente non è riconosciuto. Sul firmware 2.0.0.205 la variante Adaptive PA con hash `3770801d859dcc33cd12eaf5bff775973df46d79cd70622e26b46bd029714d4a` è stata confrontata con il fixture stock: aggiunge esclusivamente i guard per sospendere i reset PA e autorizzare il parametro FORCE durante il flusso Adaptive PA. Qualsiasi altra variante resta bloccata. Non aggirare manualmente questa protezione.

Consulta [Installazione e ripristino della stampante](INSTALLAZIONE_STAMPANTE.md) per la procedura completa.


### Primo setup su PAXX

Prima del primo setup stampante con U1FA, `/home/lava/printer_data/config/adaptive_pa_macro.cfg` può essere legittimamente assente. U1FA crea la macro convalidata durante l'installazione protetta. Non copiare o installare manualmente la macro solo per superare il controllo preliminare.

### Metodo di validazione PAXX 12-22

La convalida U1FA 2.0.0 non si basa soltanto sul numero di versione. È stato scaricato il firmware ufficiale `U1_extended_1.6.0-paxx12-22_upgrade.bin`, verificato con lo SHA-256 pubblicato da PAXX, estratto con gli strumenti del progetto PAXX e analizzato direttamente nel rootfs. Gli hash reali dei componenti Klipper sono stati confrontati con la baseline firmware-2.0 di U1FA. Il `flow_calibrator.py` di PAXX 12-22 è risultato byte-per-byte identico al calibratore stock Snapmaker 2.0.0.205 usato come base del porting AutoPA 2.0 U1FA. È stata inoltre verificata la superficie API richiesta ed è stata eseguita con successo l'intera installazione protetta U1FA in una sandbox costruita dal rootfs PAXX estratto. Si tratta di validazione del firmware e in sandbox; non era disponibile una stampante fisica con PAXX 12-22 per un test hardware diretto.
