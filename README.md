# Language / Lingua

**English** | [Italiano](README.it.md)

# U1 Filament Automation

A bilingual desktop community application by **Bottega3DLab** that connects
Spoolman, Snapmaker Orca and Adaptive Pressure Advance calibration on the
Snapmaker U1.

Available for macOS, Windows and Linux.

## What it does

- creates or reuses vendors and filaments in Spoolman;
- creates a spool with colour, weight, empty-spool weight, temperatures,
  location and lot information;
- supports single-colour and multicolour spools (2 to 8 HEX colours),
  preserving every colour in the Orca profile;
- generates **one real filament profile** in Snapmaker Orca;
- detects spools added directly from the Spoolman web interface;
- safely installs or restores **U1FA AutoPA Mod** on a Stock U1;
- guides Adaptive PA calibration and writes the result automatically to the
  selected Orca profile;
- calculates a filament-specific calibration envelope from Orca's inherited
  maximum volumetric speed, with optional manufacturer limits;
- checks for application updates without updating the printer firmware.

PAXX and other plugins are not required. U1FA can, however, use a Spoolman
instance supplied by PAXX or hosted on another device on the local network.

## Automatic workflow

1. Enter the spool data in U1FA.
2. U1FA creates or reuses the vendor and filament, then creates the Spoolman
   spool.
3. U1FA generates the corresponding profile in the real Snapmaker Orca user
   directory.
4. Select the physical tool slot and temperature. The recommended automatic
   mode reads the filament's inherited maximum volumetric speed from Orca;
   optional manufacturer min/max print speeds can impose a stricter limit.
5. Review the calculated speeds, flows and commands, then confirm calibration.
6. When calibration finishes, U1FA backs up the JSON and writes static PA, the
   Adaptive PA table and bridge PA to that same profile.

For a multicolour spool, select **Multicolor** in the new-spool form. Choose
the colours with the graphical colour pickers (two are shown initially), add
up to eight colours if needed, and keep them in the order shown on the spool.
The HEX values are kept in sync automatically. PLA multicolour spools use the
Snapmaker PLA Silk base profile automatically.

No result needs to be copied manually. Keep U1FA open and Snapmaker Orca
completely closed throughout calibration. Reopen the slicer only after U1FA
shows `calibration completed`, so it loads the newly updated profile.

If Moonraker returns a temporary error, including `HTTP 504`, U1FA retries
automatically without restarting calibration. If those attempts are exhausted,
the status page provides **Recover latest calibration**. It reads the newly
completed suite and updates the same profile after creating a backup, without
sending G-code. Do not repeat the test or restart the U1 before trying recovery.

A complete calibration takes approximately **10 minutes**. Do not power off or
restart the U1 and do not send other commands from Fluidd or the touchscreen
while calibration is running.

## Download and installation

Download the package for your platform from
[GitHub Releases](https://github.com/ubaccu/u1-filament-automation/releases).

### macOS

- `macOS-arm64.dmg` for Apple Silicon Macs;
- `macOS-x86_64.dmg` for Intel Macs.

Open the DMG, drag **U1 Filament Automation** to **Applications** and launch it.
Unsigned beta builds may require **right-click the app → Open → Open** on first
launch. If macOS still blocks it, use **System Settings → Privacy & Security →
Open Anyway**.

U1FA opens in its own desktop window and displays an icon in the Dock. Chrome or
another external browser is not required.

### Closing U1FA correctly

On the Home screen, scroll to **Close application**, select it and confirm with
**Close U1FA**. The desktop window, Spoolman monitor and internal local service
are stopped together. Wait 2–3 seconds before reopening the application.

Closing is blocked during an active calibration so that the PA result can be
saved safely to the Orca profile.

### Windows 10/11 x64

Run `Windows-x64-Setup.exe` and follow the installer. Configuring the printer
modification requires the Windows **OpenSSH Client**; OpenSSH Server is not
required.

### Linux x86_64

Make the AppImage executable and launch it:

```bash
chmod +x U1-Filament-Automation-*-Linux-x86_64.AppImage
./U1-Filament-Automation-*-Linux-x86_64.AppImage
```

The `openssh-client` package is required for printer configuration.

## First U1 setup

Enable both features from the printer touchscreen:

1. **Settings → Maintenance → Advanced Mode → Agree → Enable**;
2. **Settings → Maintenance → Root Access → Agree → Open**.

Advanced Mode enables access to Fluidd. Root Access allows U1FA to create
backups and configure the required files over SSH.

On first launch, U1FA asks for the printer IP address or hostname and verifies
the connection. The Spoolman address can be left blank for automatic discovery
or entered manually.

The SSH password is never stored. If unchanged, the default password for this U1
configuration is `snapmaker`.

## U1FA AutoPA Mod

The guided setup:

- checks printer state in read-only mode;
- verifies the original file using SHA-256;
- creates a backup before replacement;
- configures `flow_calibrator.py`;
- installs `adaptive_pa_macro.cfg`;
- adds the corresponding include to `printer.cfg`;
- blocks unknown files and firmware;
- never performs an automatic printer restart.

Every write requires two confirmations and is blocked unless the printer is
completely idle.

After a U1 firmware update, run **Check printer setup** again. U1FA does not
modify a new original file until that version has been validated. See
[Firmware compatibility](docs/FIRMWARE_COMPATIBILITY.md).

## Filament profiles

The Snapmaker base profile is selected automatically from the material and
technical name. Examples:

- standard PLA → Snapmaker PLA Basic;
- Rapid, Hyper, High Speed, HS or HF PLA → Snapmaker PLA SnapSpeed;
- PETG → the corresponding compatible Snapmaker PETG profile.

An existing Orca profile is never overwritten during creation. Before PA values
are written to the selected profile, U1FA always creates a timestamped backup.

### Calibration envelope

Use **Automatic from filament profile** unless you have a specific reason not
to. U1FA follows Orca inheritance until it finds
`filament_max_volumetric_speed`, converts that flow limit using the calibration
line geometry and never exceeds the U1FA machine cap. If the filament maker
publishes a linear print-speed range, it can be entered as an additional,
stricter limit. The confirmation page shows the source, limiting factor, three
speeds and corresponding volumetric flows before the printer can start.

**Advanced manual** mode remains available for experienced testers and enforces
the U1FA limits of 336 mm/s and 10,000 mm/s². PLA/PETG alone is not treated as a
reliable speed rating: material selects the correct base profile, while the
actual envelope comes from that profile's flow setting.

## Safety and privacy

- the interface is accessible only from the local computer;
- passwords and credentials are never stored;
- no user address or data is sent to Bottega3DLab;
- unknown firmware and files are blocked;
- app downloads are checked by file size and SHA-256;
- updating U1FA never installs or modifies U1 firmware.

## Documentation

- [Printer setup and recovery](docs/PRINTER_SETUP.md)
- [U1 firmware compatibility](docs/FIRMWARE_COMPATIBILITY.md)
- [Application updates](docs/AGGIORNAMENTI_APP.md)
- [Private beta testing](docs/BETA_TESTING.md)

## License, credits and disclaimer

U1 Filament Automation is distributed under the **GNU General Public License
v3.0**. See [LICENSE](LICENSE).

### Safety and liability notice

U1FA modifies printer configuration files and can start calibration movements
and heating. Use it only on a printer you own or are authorised to operate, and
only if you understand the displayed operations. Keep verified backups, make
sure the printer is idle, supervise every calibration and stop if anything is
unclear.

The software is provided **without warranty**, as stated in GPLv3 sections 15
and 16. To the maximum extent permitted by applicable law, the authors and
contributors accept no liability for damage to printers, computers or networks;
data or profile loss; failed prints; consumed material; downtime; loss of
warranty; personal injury; or damage to third parties caused by use or misuse
of the software. This notice does not exclude rights or liabilities that cannot
legally be excluded.

The Adaptive PA integration is derived from
[U1 Adaptive Pressure Advance Auto Calibration](https://github.com/djsplice/u1-adaptive-pa-autocal)
by djsplice and contributors, distributed under GNU GPL v3.0.

Credit is also retained for the Snapmaker U1 flow calibrator, OrcaSlicer
Adaptive Pressure Advance and the methodological inspirations documented by the
upstream project. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Klipper, Snapmaker firmware, Moonraker, OrcaSlicer and Spoolman remain under
their respective licences. This project does not relicense them.

Independent community software for calibration and experimentation. Always
verify results on your own printer and filament. This project is not affiliated
with or endorsed by Snapmaker, OrcaSlicer or the other projects mentioned above.
