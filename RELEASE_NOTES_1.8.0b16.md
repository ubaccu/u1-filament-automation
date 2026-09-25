# U1 Filament Automation 1.8.0b16

Questa beta completa il test di aggiornamento automatico avviato con la b15.

## Novità
- Il menu di creazione bobina espone tutte le famiglie già supportate da U1FA: PLA, PLA Rapid, PLA Silk, PLA Wood, PLA Translucent, PLA-CF, PETG, PETG HF, PETG Translucent e PETG-CF.
- `PLA Rapid` è la voce generica per i PLA ad alta velocità di produttori terzi e viene collegata al profilo base `Snapmaker PLA SnapSpeed @U1`.
- Dopo l'apertura di un installer verificato, U1FA chiude automaticamente l'app corrente per permettere la sostituzione su macOS senza l'errore “app in uso”.
- La chiusura automatica viene bloccata se è in corso una calibrazione Adaptive PA.
- I valori iniziali dei materiali restano modificabili e vanno adattati alle specifiche reali della bobina.

## Sicurezza
- Nessuna modifica al firmware della Snapmaker U1.
- Nessuna modifica automatica ai profili Orca live durante l'aggiornamento.
- Nessun comando stampante viene inviato dal flusso di aggiornamento.
- Pacchetti verificati tramite SHA-256.

## Test
La build è validata su macOS Intel, macOS Apple Silicon, Windows x64 e Linux x86_64 prima della pubblicazione.
