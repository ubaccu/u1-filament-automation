# Third-Party Notices

## U1FA AutoPA Mod

- Development and integration: Ivan Riccelli / Bottega3DLab and U1FA
  contributors.
- Project and derivative-work licence: GNU General Public License v3.0.

U1FA AutoPA Mod integrates and adapts the automatic calibration workflow for
the Snapmaker U1. The following notices credit the upstream components and work
from which part of the implementation is derived. They do not claim ownership
of third-party projects or relicense them.

## U1 Adaptive Pressure Advance Auto Calibration

- Author and maintainer: djsplice and contributors
- Source: https://github.com/djsplice/u1-adaptive-pa-autocal
- Licence: GNU General Public License v3.0

The Adaptive PA integration is derived from this upstream project. Derivative
changes remain under GNU GPL v3.0 and retain this notice and the upstream
credits.

Related work credited by the upstream project includes:

- the Snapmaker U1 flow calibrator and inductance-coil residual `area`
  measurement;
- OrcaSlicer Adaptive Pressure Advance;
- CNC Kitchen and PrusaPATuner-style visualisation as methodological
  inspirations.

Klipper, Snapmaker firmware, Moonraker, OrcaSlicer and Spoolman remain subject
to their own licences. U1FA is an independent community project and is not
affiliated with or endorsed by those projects or companies.

Firmware-derived and third-party files are included only where required for
traceability, comparison and reproducible patch application. This repository
does not replace or alter their original licences.

## Desktop distribution tools and runtimes

Desktop packages include or use the following projects during the build. Each
project remains under its own licence:

- Python — Python Software Foundation License:
  https://docs.python.org/3/license.html
- PyInstaller — GNU GPL with its bootloader distribution exception:
  https://pyinstaller.org/en/stable/license.html
- pywebview — BSD 3-Clause License:
  https://github.com/r0x0r/pywebview/blob/master/LICENSE
- AppImageKit/appimagetool and the AppImage runtime — MIT License:
  https://github.com/AppImage/AppImageKit/blob/master/LICENSE
- Inno Setup — used to generate the Windows installer under its own licence:
  https://jrsoftware.org/files/is/license.txt

OpenSSH Client is neither bundled nor installed automatically. On Windows and
Linux, U1FA uses the system-provided client only for the protected printer-file
configuration workflow.
