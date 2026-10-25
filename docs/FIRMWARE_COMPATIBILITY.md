# Snapmaker U1 Firmware Compatibility

[Italiano](COMPATIBILITA_FIRMWARE.md) | **English**

A Snapmaker firmware update can replace or change:

- `/home/lava/klipper/klippy/extras/flow_calibrator.py`;
- `/home/lava/printer_data/config/adaptive_pa_macro.cfg`;
- the corresponding include in `printer.cfg`.

U1FA carries its validated modification and macro in the release package, but it **does not install an older modified calibrator over a new unknown original**. Unknown firmware or file hashes remain blocked until they are reviewed and validated.

## Current validation state

| Firmware / baseline | Status | Allowed action |
|---|---|---|
| Snapmaker U1 1.5.2 / recognized legacy baseline | Validated | Protected installation/recovery allowed after explicit confirmation |
| PAXX `2.0.0-paxx12-24` / base Snapmaker 2.0.0.205 | Validated fail-closed from the official tagged release/source plus a live read-only U1FA fingerprint | Uses the U1FA firmware-2.0 AutoPA port only when the exact full version and all validated component SHA-256 values match |
| PAXX `1.6.0-paxx12-22-31c5a38` / full version `1.6.0.267_20260815150420` | Validated fail-closed from the official PAXX release binary + U1FA sandbox install | Uses the U1FA firmware-2.0 AutoPA port only when the exact build identity and all validated PAXX component hashes match |
| PAXX `1.5.2-paxx12-21-2a88932` | Validated legacy fail-closed | Kept for users still on PAXX 12-21; exact identity and validated component hashes are required |
| Snapmaker U1 2.0.0.205 (`2.0.0.205_20260914173503`) | Validated | Dedicated firmware-2.0 AutoPA port; both the validated stock `print_task_config.py` and the validated Adaptive-PA variant SHA-256 `3770801d…` are accepted |
| Future U1 versions or components with a different hash | Blocked | No writes or calibration until reviewed |

Snapmaker publishes current U1 firmware release notes here:

https://wiki.snapmaker.com/en/snapmaker_u1/firmware/release_notes

## After every firmware update

1. Do not manually copy a file from an older firmware release over the new one.
2. Open U1FA while the printer is completely idle.
3. Use **Check printer setup**.
4. Run the read-only check first.
5. If calibrator, macro and include are still valid, no write is required.
6. If U1FA recognizes a validated Snapmaker original, it can offer the protected recovery flow with backup and explicit confirmation.
7. On stock firmware 1.5.2 and PAXX 12-21 U1FA uses the legacy AutoPA path; on stock 2.0.0.205 and validated PAXX 12-22/12-24 it uses the firmware-2.0 AutoPA port. The compatibility fingerprints remain separate and fail closed.
8. PAXX 12-24 is accepted only as `VERSION=2.0.0`, `FULLVERSION=2.0.0-paxx12-24` with the reviewed component SHA-256 values, including `print_task_config.py` SHA-256 `8298babc42526ef4a4026207927e91c52fd1ca5f1e1afe6b1f08b0dbdced82c0`. PAXX 12-22 and 12-21 remain separate fingerprints.
9. If U1FA reports `unknown-blocked`, stop. The new original must be acquired, compared and validated before its hash is added to a future release.
10. After an actual protected write, completely power off the U1, wait 10–15 seconds and power it on again. Do not rely on a simple Klipper `RESTART`.

## Why U1FA blocks unknown files

Printer-file installation modifies active Klipper files. A firmware update may change Snapmaker's implementation, so blindly reapplying a patch made for an older file could break calibration or printer behavior.

For this reason U1FA checks known SHA-256 values and intentionally fails closed when the source file is not recognized. On firmware 2.0.0.205, the Adaptive-PA variant with hash `3770801d859dcc33cd12eaf5bff775973df46d79cd70622e26b46bd029714d4a` was compared against the stock fixture: it adds only guards that suppress PA resets and authorize the FORCE parameter during the Adaptive-PA flow. Every other variant remains blocked. Do not bypass this safeguard manually.

See [Printer setup and recovery](PRINTER_SETUP.md) for the complete workflow.


### First setup on PAXX

Before the first U1FA printer setup, `/home/lava/printer_data/config/adaptive_pa_macro.cfg` may legitimately be absent. U1FA creates the validated macro during the guarded installation flow. Do not copy or install the macro manually just to satisfy the preflight check.

### PAXX 12-22 validation method

U1FA 2.0.0 validation did not rely on the version label alone. The official `U1_extended_1.6.0-paxx12-22_upgrade.bin` release asset was downloaded, checked against its published SHA-256, unpacked with the PAXX firmware tools and its root filesystem inspected directly. The exact Klipper component hashes were then compared with the U1FA firmware-2.0 baseline. PAXX 12-22 ships a `flow_calibrator.py` that is byte-for-byte identical to the stock Snapmaker 2.0.0.205 calibrator used as the U1FA 2.0 AutoPA base. The required API surface was checked and the complete U1FA protected installation was exercised in a filesystem sandbox built from the extracted PAXX rootfs. This is firmware-image/sandbox validation; no physical PAXX 12-22 printer was available for hardware execution testing.


### PAXX 12-24 validation method

U1FA 2.0.9 validates PAXX 12-24 without treating the version label alone as sufficient. The official release/tag `v2.0.0-paxx12-24` identifies Snapmaker stock `2.0.0.205` as its base. The tagged PAXX source changes affecting `print_task_config.py` were reviewed, and a live U1FA read-only report from a printer running PAXX 12-24 confirmed that the existing validated 2.0.0.205 component fingerprints still match except for `print_task_config.py`, whose observed SHA-256 is `8298babc42526ef4a4026207927e91c52fd1ca5f1e1afe6b1f08b0dbdced82c0`. U1FA therefore accepts only this exact full-version/component combination; any different future PAXX build or component hash remains blocked.
