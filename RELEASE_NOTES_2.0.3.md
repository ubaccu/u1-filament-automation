# U1 Filament Automation 2.0.3

Hotfix for the filament-type regression introduced in U1FA 2.0.2.

- Snapmaker PLA SnapSpeed profiles now keep the official Orca `filament_type` value `PLA` instead of forcing `PLA RAPID`.
- PETG HF and translucent profiles keep the official `PETG` type; Silk, Wood and Translucent PLA keep `PLA`.
- PLA-CF and PETG-CF keep their official specific types.
- Fast-filament words such as RAPID, HYPER, HS and HF still select the correct SnapSpeed/HF base profile; they no longer alter the runtime `filament_type`.
- The fix matches the official Snapmaker Orca U1 profiles and the real U1 case where `PLA RAPID` caused a malformed-command / G-code parse failure.
- Added regression coverage for the affected PLA/PETG families.

No firmware compatibility, Adaptive PA, calibration or printer-file logic is changed by this release.
