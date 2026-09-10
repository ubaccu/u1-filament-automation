# Italiano

## U1 Filament Automation 1.8.0b24

### Profili Orca equivalenti senza doppioni
- U1FA riconosce in modo conservativo il vecchio schema di nome che può differire solo per il materiale già incorporato nel nome commerciale, ad esempio `ePLA-Lite` rispetto a `PLA ePLA-Lite`;
- se esiste un unico profilo Orca equivalente, U1FA lo riutilizza invece di creare un secondo profilo quasi identico;
- il riconoscimento automatico è volutamente ristretto ai casi sicuri PLA/PETG e non unisce profili arbitrari;
- la calibrazione PA può risolvere lo stesso profilo equivalente e aggiornare quello già presente, mantenendo il normale backup `.u1fa`;
- se esistono più profili equivalenti, la scrittura resta bloccata per evitare di scegliere quello sbagliato;
- nessun profilo viene rinominato o cancellato automaticamente.

### Sicurezza
- il rilevamento di equivalenza legge soltanto i JSON presenti nella cartella profili Orca;
- nessun comando viene inviato alla U1;
- nessuna modifica a firmware, PAXX, Spoolman o Adaptive PA viene eseguita durante il rilevamento;
- la normale scrittura del PA continua ad avvenire solo dopo conferma esplicita e con backup.

---

# English

## U1 Filament Automation 1.8.0b24

### Equivalent Orca profiles without duplicates
- U1FA conservatively recognizes the legacy naming pattern where the only difference is a material token already embedded in the commercial product name, for example `ePLA-Lite` versus `PLA ePLA-Lite`;
- when exactly one equivalent Orca profile exists, U1FA reuses it instead of creating a second nearly-identical profile;
- automatic equivalence is intentionally limited to safe PLA/PETG cases and does not merge arbitrary profiles;
- PA calibration can resolve the same equivalent profile and update the existing JSON while keeping the normal `.u1fa` backup;
- if multiple equivalent profiles exist, writing remains blocked rather than guessing;
- profiles are never automatically renamed or deleted.

### Safety
- equivalence detection only reads JSON files from the Orca profile directory;
- no command is sent to the U1;
- firmware, PAXX, Spoolman and Adaptive PA are not modified by equivalence detection;
- PA writing still happens only after explicit confirmation and with a backup.
