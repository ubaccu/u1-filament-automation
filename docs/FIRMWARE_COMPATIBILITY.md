# Compatibilità firmware U1 / U1 firmware compatibility

Un aggiornamento firmware Snapmaker può sostituire:

- `/home/lava/klipper/klippy/extras/flow_calibrator.py`;
- `/home/lava/printer_data/config/adaptive_pa_macro.cfg`;
- l'include della macro in `printer.cfg`.

U1FA conserva nel proprio pacchetto la modifica e la macro, quindi non dipende dai
backup rimasti sulla stampante. Non reinstalla però un vecchio calibratore sopra un
originale nuovo e sconosciuto.

A Snapmaker firmware update may replace the calibrator, Adaptive PA macro and its
include. U1FA carries its validated assets, but it never installs an old modified
calibrator over a new unknown original.

## Stato corrente / Current status

| Firmware | Stato | Azione |
|---|---|---|
| Baseline originale pre-1.6 con SHA-256 `dcbc26d5…a816e894` | Convalidato | Installazione/ripristino consentiti dopo doppia conferma |
| U1 1.6.0 (2026-08-25) | In verifica | Solo controllo in lettura; fermarsi se l'hash è sconosciuto |

Snapmaker indica V1.6.0 come firmware corrente nelle note ufficiali:
https://wiki.snapmaker.com/en/snapmaker_u1/firmware/release_notes

## Dopo ogni aggiornamento / After every update

1. Non reinstallare manualmente file provenienti dal vecchio firmware.
2. Aprire U1FA con la stampante completamente inattiva.
3. Selezionare **Configurazione o ripristino U1FA AutoPA Mod**.
4. Eseguire soltanto il controllo in lettura.
5. Se calibratore, macro e include sono ancora validi, non serve alcuna scrittura.
6. Se compare l'originale Snapmaker con hash già convalidato, U1FA propone il
   ripristino completo con backup e doppia conferma.
7. Se compare `unknown-blocked`, fermarsi. Il nuovo originale deve essere acquisito
   e confrontato; la patch va rifusa e testata su quel sorgente prima di aggiungere
   la nuova coppia di hash alla release.
8. Dopo un ripristino effettivo, spegnere completamente la U1, attendere 10–15
   secondi e riaccenderla. Non usare un semplice `RESTART`.

The English procedure is identical: never copy the previous firmware's Python file
blindly; run the read-only check; restore only a recognized original; stop on
`unknown-blocked`; validate and rebuild the patch for every changed Snapmaker
source; power-cycle only after an actual write.
