<div align="center">

# U1 Filament Automation

### Spoolman → Snapmaker Orca → Adaptive Pressure Advance

**Desktop companion for Snapmaker U1 by Bottega3DLab**  
Manage real filament spools, generate or safely reuse Orca profiles, guide Adaptive PA calibration, and keep application updates separate from printer firmware.

[![Release](https://img.shields.io/github/v/release/ubaccu/u1-filament-automation?label=release)](https://github.com/ubaccu/u1-filament-automation/releases)
![Platforms](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-4c8bf5)
![License](https://img.shields.io/badge/license-GPL--3.0-blue)
![Status](https://img.shields.io/badge/status-stable-brightgreen)

**[Download U1FA](https://github.com/ubaccu/u1-filament-automation/releases)** · **[Report a bug](https://github.com/ubaccu/u1-filament-automation/issues/new/choose)** · **[Documentation](docs/PRINTER_SETUP.md)** · **[Italiano](README.it.md)**

<a href="https://www.buymeacoffee.com/riccelliiv9" target="_blank" rel="noopener noreferrer"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me a Coffee" height="50"></a>

</div>

---

## What is U1FA?

U1 Filament Automation is an independent community desktop application for the **Snapmaker U1**. It connects the filament data stored in **Spoolman** with user profiles in **Snapmaker Orca**, then guides **Adaptive Pressure Advance** calibration and writes validated PA results back to the selected Orca profile after creating a backup.

The public repository is the official **distribution, documentation and support channel**. Development is maintained separately. Public releases include installers for supported platforms, SHA-256 checksums and a version-matched GPL corresponding-source archive.

> **Firmware compatibility:** U1FA 1.8.0 and its protected printer-configuration / AutoPA Mod workflow were tested on **Snapmaker U1 firmware 1.5**. **Firmware 1.6.0 has not been validated for printer-file installation/recovery in this release.** Do not assume compatibility after updating the printer; run the read-only setup check and stop if U1FA reports an unknown or blocked state. See [U1 firmware compatibility](docs/FIRMWARE_COMPATIBILITY.md).

## Highlights

- **Real Spoolman workflow** — create or reuse vendors and filaments, then create real spools with colour, weight, tare, temperatures, storage location and lot information.
- **Single and multicolour spools** — 2 to 8 HEX colours are preserved in generated Orca profiles.
- **Automatic U1 discovery** — the first-setup workflow can discover a compatible Snapmaker U1/Moonraker endpoint on the local network with read-only checks before anything is saved.
- **Automatic Snapmaker Orca profile selection** — material and technical name determine the compatible Snapmaker base profile.
- **Duplicate-safe profile handling** — an existing exact profile is reused; one conservatively recognized equivalent legacy profile can also be reused without creating a duplicate.
- **Filament-specific calibration envelope** — automatic mode reads Orca's inherited maximum volumetric speed and can apply stricter manufacturer limits.
- **Adaptive PA workflow** — guided calibration, automatic result recovery, profile backup and PA write-back.
- **Printer setup checks** — U1FA AutoPA Mod installation and recovery are guarded by file validation, printer-state checks and explicit confirmation.
- **Built-in updater** — application packages are selected by platform and verified with SHA-256. Updating U1FA does **not** update U1 firmware.

## Download

Open **[GitHub Releases](https://github.com/ubaccu/u1-filament-automation/releases)** and choose the package for your computer:

| Platform | Package | Notes |
|---|---|---|
| macOS Apple Silicon | `macOS-arm64.dmg` | Apple Silicon Macs |
| macOS Intel | `macOS-x86_64.dmg` | Intel Macs |
| Windows | `Windows-x64-Setup.exe` | Windows 10/11 x64 |
| Linux | `Linux-x86_64.AppImage` | x86_64 AppImage |
| Source | `Source.zip` | Version-matched GPL corresponding source |

Every release also includes **`SHA256SUMS.txt`**.

### macOS first launch

Current macOS packages are not Apple-notarized. After copying **U1 Filament Automation** to **Applications**, use **right-click / Control-click → Open → Open** on first launch. If macOS still blocks it, use **System Settings → Privacy & Security → Open Anyway**.

### Linux

```bash
chmod +x U1-Filament-Automation-*-Linux-x86_64.AppImage
./U1-Filament-Automation-*-Linux-x86_64.AppImage
```

`openssh-client` is required only for protected printer-configuration tasks.

## How it works

1. Enter or select the physical spool in U1FA.
2. U1FA creates or reuses the Spoolman vendor and filament, then creates the spool.
3. U1FA creates the matching Snapmaker Orca user profile only when needed. Existing exact profiles are reused; one safely recognized equivalent legacy profile can also be reused.
4. U1FA calculates the recommended calibration envelope from the profile's inherited volumetric-flow limit.
5. You review speeds, flow values and planned actions before explicitly confirming calibration.
6. When calibration finishes, U1FA backs up the selected Orca JSON and writes the validated PA values to that same profile.

For normal use, choose **Automatic from filament profile**. Advanced manual mode remains available for experienced users.

## Safety by design

U1FA can modify printer configuration files and can start calibration movements and heating, so safeguards are deliberately strict:

- printer checks begin in **read-only** mode;
- unknown firmware/files are blocked;
- configuration changes require explicit confirmation and an idle printer;
- original files are validated before replacement and backups are created first;
- existing Orca profiles are not overwritten during spool/profile creation;
- Orca profiles are backed up before PA values are written;
- the SSH password is not stored;
- application updates are verified by size and SHA-256;
- updating U1FA never installs or modifies Snapmaker U1 firmware;
- U1FA never performs an automatic printer restart during setup.

Keep U1FA open and Snapmaker Orca closed during calibration. Do not send unrelated commands from Fluidd or the touchscreen while a calibration is active.

## First U1 setup

Before protected printer configuration, enable on the U1 touchscreen:

1. **Settings → Maintenance → Advanced Mode → Agree → Enable**
2. **Settings → Maintenance → Root Access → Agree → Open**

Then use **Check printer setup** inside U1FA. The application can first discover the U1/Moonraker endpoint on the local network using read-only checks; manual configuration remains available. **The protected printer-file workflow in U1FA 1.8.0 is validated on firmware 1.5; firmware 1.6.0 is not yet validated.** After any U1 firmware update, run the setup check again before calibrating and do not force a blocked installation.

See the full guides:

- [Printer setup and recovery](docs/PRINTER_SETUP.md)
- [U1 firmware compatibility](docs/FIRMWARE_COMPATIBILITY.md)
- [Application updates](docs/APP_UPDATES.md)
- [Support and bug reporting](SUPPORT.md)

## Supported filament profile families

U1FA includes automatic mappings for supported PLA/PETG families used by Snapmaker Orca, including standard, rapid/high-speed, silk, wood, translucent and carbon-fibre variants where a compatible base profile is available.

Examples:

- standard PLA → **Snapmaker PLA Basic**
- Rapid / Hyper / High Speed / HS / HF PLA → **Snapmaker PLA SnapSpeed**
- PLA Silk → **Snapmaker PLA Silk**
- PETG families → corresponding compatible **Snapmaker PETG** profile

Profile-equivalence matching is intentionally conservative. If more than one equivalent profile is found, U1FA blocks the automatic choice instead of guessing.

## Support and bug reports

Found a bug? Use **[GitHub Issues](https://github.com/ubaccu/u1-filament-automation/issues/new/choose)** and include the U1FA version, operating system, U1 firmware version, Snapmaker Orca version, what you expected, what happened, and screenshots or sanitized logs when useful.

For security-sensitive problems, do **not** publish credentials, private IP addresses, complete logs or personal data. Follow [SECURITY.md](.github/SECURITY.md) instead.

See [SUPPORT.md](SUPPORT.md) for the complete support policy.

## Privacy

U1FA is designed for local use. Credentials are not stored and user addresses or spool data are not sent to Bottega3DLab. Network access is used only for the services you configure and for the public application update channel.

## License and credits

U1 Filament Automation is distributed under the **GNU General Public License v3.0**. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

The Adaptive PA integration is derived from [U1 Adaptive Pressure Advance Auto Calibration](https://github.com/djsplice/u1-adaptive-pa-autocal) by djsplice and contributors, also distributed under GNU GPL v3.0. Credit is retained for the Snapmaker U1 flow calibrator, OrcaSlicer Adaptive Pressure Advance and the upstream methodological work documented in the notices.

Klipper, Snapmaker firmware, Moonraker, OrcaSlicer and Spoolman remain under their respective licences. This project does not relicense them.

## Disclaimer

U1FA is independent community software for calibration and experimentation. It is **not affiliated with or endorsed by Snapmaker, OrcaSlicer or the other projects mentioned above**.

Use it only on a printer you own or are authorised to operate. Keep verified backups, make sure the printer is idle before configuration, supervise calibrations and stop if anything is unclear. The software is provided **without warranty** as described by GPLv3 sections 15 and 16.
