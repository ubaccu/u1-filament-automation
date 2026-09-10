# Snapmaker U1 Firmware Compatibility

[Italiano](COMPATIBILITA_FIRMWARE.md) | **English**

A Snapmaker firmware update can replace or change:

- `/home/lava/klipper/klippy/extras/flow_calibrator.py`;
- `/home/lava/printer_data/config/adaptive_pa_macro.cfg`;
- the corresponding include in `printer.cfg`.

U1FA carries its validated modification and macro in the release package, but it **does not install an older modified calibrator over a new unknown original**. Unknown firmware or file hashes remain blocked until they are reviewed and validated.

## Current validation state

**U1FA 1.8.0 was developed and tested with Snapmaker U1 firmware 1.5. The protected printer-file installation/recovery path has not been validated on firmware 1.6.0.**

| Firmware / baseline | Status | Allowed action |
|---|---|---|
| Snapmaker U1 firmware 1.5 — validated baseline, SHA-256 `dcbc26d5…a816e894` | Tested and validated | Protected installation/recovery allowed after explicit confirmation |
| Snapmaker U1 firmware 1.6.0 (2026-08-25) | Not validated in U1FA 1.8.0 | Read-only setup check only; do not force printer-file installation/recovery on an unknown or blocked state |

Snapmaker publishes current U1 firmware release notes here:

https://wiki.snapmaker.com/en/snapmaker_u1/firmware/release_notes

## After every firmware update

1. Do not manually copy a file from an older firmware release over the new one.
2. Open U1FA while the printer is completely idle.
3. Use **Check printer setup**.
4. Run the read-only check first.
5. If calibrator, macro and include are still valid, no write is required.
6. If U1FA recognizes a validated Snapmaker original, it can offer the protected recovery flow with backup and explicit confirmation.
7. If U1FA reports `unknown-blocked`, stop. The new original must be acquired, compared and validated before its hash is added to a future release.
8. After an actual protected write, completely power off the U1, wait 10–15 seconds and power it on again. Do not rely on a simple Klipper `RESTART`.

## Why U1FA blocks unknown files

Printer-file installation modifies active Klipper files. A firmware update may change Snapmaker's implementation, so blindly reapplying a patch made for an older file could break calibration or printer behavior.

For this reason U1FA checks known SHA-256 values and intentionally fails closed when the source file is not recognized. Do not bypass this safeguard manually.

See [Printer setup and recovery](PRINTER_SETUP.md) for the complete workflow.
