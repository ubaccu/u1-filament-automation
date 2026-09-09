# U1 Filament Automation 1.8.0b21

## Home cleanup

- Removes the duplicated **0. Configurazione o ripristino U1FA AutoPA Mod** card from the home page.
- Keeps the first-printer-setup warning and its **Controlla configurazione stampante / Check printer setup** button as the single entry point for printer setup checks.
- Hides the **Sistema e manutenzione / System and maintenance** group when it has no remaining visible actions, reducing duplicate navigation.
- Keeps the existing printer-setup route and safety confirmations unchanged.

## Distribution and validation

- Adds stricter release validation for macOS Intel, macOS ARM, Windows and Linux builds.
- Adds a validated corresponding-source archive for distributed GPL releases.
- Keeps update downloads served from the public U1FA release channel.

## Safety

This release does not automatically modify the printer, Snapmaker Orca profiles, Spoolman data, Adaptive PA configuration or firmware. The home-page change is navigation/presentation only; printer setup actions still require the existing checks and confirmations.
