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
| PAXX `1.5.2-paxx12-21-2a8893` | Convalidato in modalità fail-closed | Consentito solo con identità build esatta e hash dei componenti Klipper convalidati; file diversi restano bloccati |
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
7. Su firmware 1.5.2 U1FA usa il flusso AutoPA legacy; su 2.0.0.205 usa il porting dedicato firmware 2.0. Le due famiglie restano separate e non vengono mai mischiate.
8. La build PAXX `1.5.2-paxx12-21-2a8893` viene accettata soltanto se anche l'identità PAXX e gli hash dei componenti Klipper attesi corrispondono esattamente.
9. Se compare `unknown-blocked`, fermati. Il nuovo originale deve essere acquisito, confrontato e convalidato prima che il relativo hash venga aggiunto a una release futura.
10. Dopo una scrittura protetta effettiva, spegni completamente la U1, attendi 10–15 secondi e riaccendila. Non affidarti a un semplice `RESTART` di Klipper.

## Perché U1FA blocca i file sconosciuti

L'installazione sulla stampante modifica file Klipper attivi. Un aggiornamento firmware può cambiare l'implementazione Snapmaker, quindi riapplicare alla cieca una patch preparata per un file precedente potrebbe compromettere la calibrazione o il comportamento della stampante.

Per questo U1FA confronta SHA-256 conosciuti e si blocca intenzionalmente quando il file sorgente non è riconosciuto. Sul firmware 2.0.0.205 la variante Adaptive PA con hash `3770801d859dcc33cd12eaf5bff775973df46d79cd70622e26b46bd029714d4a` è stata confrontata con il fixture stock: aggiunge esclusivamente i guard per sospendere i reset PA e autorizzare il parametro FORCE durante il flusso Adaptive PA. Qualsiasi altra variante resta bloccata. Non aggirare manualmente questa protezione.

Consulta [Installazione e ripristino della stampante](INSTALLAZIONE_STAMPANTE.md) per la procedura completa.
