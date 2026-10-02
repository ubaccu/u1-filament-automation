# U1 Filament Automation 2.0.4

This release improves how U1FA surfaces application updates at startup.

- U1FA continues to check GitHub Releases automatically in the background when the app starts.
- If the Home page opens while the check is still running, it refreshes automatically so the result becomes visible without pressing **Check now**.
- When a newer version is available, the Home page shows a clear notice with a direct **View update / Mostra aggiornamento** action.
- Manual **Check now** remains available to force another check.
- Download, package SHA-256 verification and installer opening remain separate, explicit user-confirmed steps.
- No changes to Snapmaker U1 firmware compatibility, Adaptive PA calibration logic, Spoolman synchronization or Orca filament profiles.

The full test suite passed before release.
