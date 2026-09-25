# U1 Filament Automation 1.8.0b22

## Italiano

### Rilevamento intelligente dei profili Snapmaker Orca

- U1FA legge in **sola lettura** i profili Snapmaker già installati nella cartella di sistema di Orca.
- Nella conferma di una nuova bobina mostra se il profilo base previsto è presente con corrispondenza esatta.
- Se il nome del profilo è cambiato ma famiglia e variante risultano compatibili, U1FA mostra un **suggerimento intelligente**.
- Se più profili risultano ugualmente plausibili, U1FA li segnala come ambigui e **non sceglie automaticamente**.
- La b22 non sostituisce automaticamente il profilo base con quello suggerito: il suggerimento è soltanto informativo.

### Sicurezza

Questa funzione non modifica i profili Snapmaker Orca di sistema, non scrive in Spoolman, non modifica Adaptive PA e non invia comandi alla stampante. La creazione effettiva di una bobina continua a richiedere la conferma esplicita già prevista da U1FA.

---

## English

### Smart Snapmaker Orca profile discovery

- U1FA reads the Snapmaker profiles already installed in Orca's system profile folder in **read-only mode**.
- The new-spool confirmation shows whether the expected base profile is installed as an exact match.
- If a profile name changes while its material family and subtype still match, U1FA shows a **smart suggestion**.
- If several profiles are equally plausible, U1FA reports the match as ambiguous and **does not choose automatically**.
- b22 does not automatically replace the validated base profile with the suggested one: the suggestion is informational only.

### Safety

This feature does not modify Snapmaker Orca system profiles, does not write to Spoolman, does not modify Adaptive PA and does not send commands to the printer. Actual spool creation still requires U1FA's existing explicit confirmation.
