# U1 Filament Automation 2.0.5

This release fixes the Italian/English language handling throughout U1FA and improves the calibration filament picker with alphabetical ordering and Spoolman colour indicators.

- The selected UI language is now persistent: choosing **IT** or **EN** is remembered after closing and reopening U1FA.
- Invalid or incomplete language requests no longer silently reset the interface to Italian.
- English mode now translates dynamic calibration/status messages, Moonraker retry and recovery messages, batch queue messages, preview details and technical GUI errors that could previously appear partly in Italian.
- Translation coverage was extended to printer setup, firmware diagnostics shown by the GUI, envelope/profile errors, Spoolman/Orca-facing GUI errors and filament deletion edge cases.
- Calibration filament/profile selectors are now sorted alphabetically **A → Z**.
- The filament colour stored in Spoolman is shown next to the selected profile, including multiple HEX values for multicolour filaments.
- No changes were made to Adaptive PA calibration logic, U1 firmware compatibility rules, Orca profile write behaviour, Spoolman write/business logic or PAXX support.
