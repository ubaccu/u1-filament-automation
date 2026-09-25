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
| Baseline originale pre-1.6 con SHA-256 `dcbc26d5…a816e894` | Convalidato | Installazione/ripristino protetti consentiti dopo conferma esplicita |
| Snapmaker U1 2.0.0.205 (`2.0.0.205_20260914173503`) | Convalidato per collaudo privato controllato | Installazione protetta consentita sugli hash esatti; calibrazione solo dopo riconoscimento di modulo AutoPA e macro |
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
7. Per il firmware 2.0.0.205 questa beta propone il porting dedicato solo se
   versione completa, dipendenze e calibratore originale hanno gli hash esatti.
   Prima del primo collaudo reale fermati al riepilogo in sola lettura e verifica
   il report; la calibrazione si sblocca solo dopo il riconoscimento anche della
   macro AutoPA.
8. Se compare `unknown-blocked`, fermati. Il nuovo originale deve essere acquisito, confrontato e convalidato prima che il relativo hash venga aggiunto a una release futura.
9. Dopo una scrittura protetta effettiva, spegni completamente la U1, attendi 10–15 secondi e riaccendila. Non affidarti a un semplice `RESTART` di Klipper.

## Perché U1FA blocca i file sconosciuti

L'installazione sulla stampante modifica file Klipper attivi. Un aggiornamento firmware può cambiare l'implementazione Snapmaker, quindi riapplicare alla cieca una patch preparata per un file precedente potrebbe compromettere la calibrazione o il comportamento della stampante.

Per questo U1FA confronta SHA-256 conosciuti e si blocca intenzionalmente quando il file sorgente non è riconosciuto. Non aggirare manualmente questa protezione.

Consulta [Installazione e ripristino della stampante](INSTALLAZIONE_STAMPANTE.md) per la procedura completa.
