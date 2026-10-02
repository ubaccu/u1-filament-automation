# U1 Filament Automation 2.0.2

Hotfix release for Snapmaker U1 fast-PLA tray matching.

- Fixed SnapSpeed-derived Orca profiles so their runtime `filament_type` is `PLA RAPID`, matching the real U1 tray on firmware 2.0.0.205.
- The print base remains `Snapmaker PLA SnapSpeed`; print temperatures, volumetric limits, speeds and other inherited settings are unchanged.
- Spoolman data remains unchanged and continues to use `PLA RAPID`.
- The fix was validated on a real U1: the Snapmaker Orca pre-print filament mismatch disappeared after the runtime type was corrected.
- Added regression coverage for this mapping.
- `PETG HF` is intentionally unchanged pending real-printer verification.

No changes to Adaptive PA calibration logic or firmware compatibility.
