# U1 Filament Automation 1.8.0b15

Beta di collaudo destinata anche a verificare l'aggiornamento automatico dalla `1.8.0b14`.

## Novità

- Aggiunto **PLA Wood** alla scelta materiale della creazione bobina nell'app desktop.
- La selezione riusa la logica già presente in U1FA e associa il materiale al profilo base **`Snapmaker PLA Wood @U1 0.4 nozzle`**.
- I valori iniziali restano volutamente quelli del PLA standard (`1.24 g/cm³`, `220 °C` ugello, `60 °C` piano): U1FA non inventa parametri specifici del produttore e invita a correggerli prima dell'anteprima quando la bobina dichiara valori diversi.
- Aggiunta guida bilingue Italiano/English e test automatici per selettore, associazione e installazione idempotente dell'estensione UI.
- Versione pacchetto e runtime aggiornata a **`1.8.0b15`**.

## Sicurezza

Questa beta non modifica la logica Adaptive PA, i comandi di calibrazione, il firmware o i file di configurazione della Snapmaker U1. La nuova opzione interviene soltanto nella creazione guidata della bobina; le protezioni già presenti per Spoolman e Snapmaker Orca restano invariate.
