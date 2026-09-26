"""Read-only firmware fingerprints for guarded live installation and calibration.

Versions alone never authorize a write: dependency and calibrator hashes must
match the reviewed source. No downloads, G-code, or automatic repairs occur here.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath

EXTRAS = PurePosixPath('/home/lava/klipper/klippy/extras')
VERSION_PATH = PurePosixPath('/etc/VERSION')
FULLVERSION_PATH = PurePosixPath('/etc/FULLVERSION')
BUILD_VERSION_PATH = PurePosixPath('/etc/BUILD_VERSION')
MACRO_PATH = PurePosixPath('/home/lava/printer_data/config/adaptive_pa_macro.cfg')
LEGACY_STOCK = 'dcbc26d5c726eb464b8e2a31d2856a816f3170bbda1ed5facb57fb19a816e894'
LEGACY_V6 = '74ff744304657547e513fe74c3d42beb55f35eebd4d8f3e0749f0c7febc089ce'
MACRO_SHA256 = 'db181aa5ee12b93886230a6b71cfd105c92a56cf4651e5e5dca7788aac7daeb4'
STOCK_205 = 'c8e9576a2ce891877c8bc8b216ca80790b12b89d92a703c3c0a2a4c6e7e4ebfa'
# Canonical firmware-2.0 assets are byte-for-byte identical to the files
# validated on the real U1. Keep the TESTED aliases for compatibility with
# existing internal imports; they intentionally resolve to the same digest.
CANDIDATE_205 = '6225503bb6a5aa5bf1680160b590efc0904bf44da01ed8c3eaf84d3ab649a47b'
TESTED_205 = CANDIDATE_205
MACRO_205_SHA256 = 'a1e8ec08e0f07f8cb264b60bc10960e38ae6e40560fd46749e93cd0474f150a7'
MACRO_205_TESTED_SHA256 = MACRO_205_SHA256
FULLVERSION_205 = '2.0.0.205_20260914173503'
PAXX_152_V21_BUILD = '1.5.2-paxx12-21-2a8893'
PAXX_152_V21_PRINT_TASK_CONFIG = '83c9a6614e4b6ff8d39c60b5cd9d458479126df0e6f687c95def9193141f539a'
DEPENDENCIES_152 = {
    'filament_parameters.py': 'd353a6d055155448b16cb4b16f19768ee86166c9aeb706dac7be06a1dcbc3770',
    'machine_state_manager.py': 'aadb9762606480a5fd9985634c22d8434c8a295dec2a133d87068fa0bb22c2f0',
    'print_task_config.py': '717be6d2766d84d63b271791c4cb9a83be91a5efc0748ea6f09e6013f8784fcd',
}
DEPENDENCIES_205 = {
    'filament_parameters.py': '7af7b9537a1b6e202aae41a7cd95d2b414d2cee1f2fc3e416610529d6dcba7e4',
    'machine_state_manager.py': '8e63a052b2e0ba02d111e59658d4a0af237ec9851817687cd6424ded667f7ccc',
    'print_task_config.py': 'c3f90b20f2bb64fd363ed13df5464920477f87d092f115b80683e304089643f4',
}


@dataclass(frozen=True)
class FirmwareCompatibility:
    version: str
    full_version: str
    build_version: str
    state: str
    message: str
    hashes: dict[str, str]
    missing: tuple[str, ...]
    live_install_allowed: bool = False
    live_calibration_allowed: bool = False

    def to_dict(self):
        return asdict(self)


def inspect_firmware(target) -> FirmwareCompatibility:
    """Read only fixed, non-secret paths using the existing local/SSH target."""
    missing = []

    def read(path):
        try:
            return target.read_path_bytes(path)
        except FileNotFoundError:
            missing.append(str(path))
            return None

    def version_text(path):
        data = read(path)
        if data is None:
            return ''
        try:
            value = data.decode('utf-8').strip()
        except UnicodeDecodeError:
            return ''
        return value if len(value) <= 120 and all(c.isprintable() for c in value) else ''

    version = version_text(VERSION_PATH)
    full = version_text(FULLVERSION_PATH)
    # PAXX keeps its own build identity in /etc/BUILD_VERSION. This file is
    # optional on stock firmware and is used only as an additional guard.
    try:
        build = target.read_path_bytes(BUILD_VERSION_PATH).decode('utf-8').strip()
        if len(build) > 120 or not all(c.isprintable() for c in build):
            build = ''
    except (FileNotFoundError, UnicodeDecodeError):
        build = ''
    hashes = {}
    for name in ('flow_calibrator.py', *DEPENDENCIES_205):
        data = read(EXTRAS / name)
        if data is not None:
            hashes[name] = hashlib.sha256(data).hexdigest()
    data = read(MACRO_PATH)
    if data is not None:
        hashes['adaptive_pa_macro.cfg'] = hashlib.sha256(data).hexdigest()

    state = 'unknown-blocked'
    message = 'Firmware/componenti non convalidati / Firmware or components not validated.'
    install = calibration = False
    calibrator = hashes.get('flow_calibrator.py')
    legacy_identity = version == '1.5.2' and (full == '1.5.2' or full.startswith('1.5.2.'))
    legacy_dependencies = all(hashes.get(k) == v for k, v in DEPENDENCIES_152.items())
    paxx_v21_dependencies = (
        build == PAXX_152_V21_BUILD
        and hashes.get('filament_parameters.py') == DEPENDENCIES_152['filament_parameters.py']
        and hashes.get('machine_state_manager.py') == DEPENDENCIES_152['machine_state_manager.py']
        and hashes.get('print_task_config.py') == PAXX_152_V21_PRINT_TASK_CONFIG
    )
    if legacy_identity and (legacy_dependencies or paxx_v21_dependencies):
        if calibrator in {LEGACY_STOCK, LEGACY_V6}:
            if paxx_v21_dependencies:
                state = 'paxx-152-v21-compatible'
                message = (
                    'PAXX 1.5.2-paxx12-21 riconosciuto con componenti U1FA convalidati / '
                    'PAXX 1.5.2-paxx12-21 recognized with validated U1FA components.'
                )
            else:
                state = 'legacy-compatible'
                message = 'Baseline originale 1.5.2 riconosciuta / Original 1.5.2 baseline recognized.'
            install = True
            calibration = calibrator == LEGACY_V6 and hashes.get('adaptive_pa_macro.cfg') == MACRO_SHA256
    elif version == '2.0.0' and full == FULLVERSION_205:
        if all(hashes.get(k) == v for k, v in DEPENDENCIES_205.items()):
            if calibrator == STOCK_205:
                state = 'stock-205-compatible'
                message = ('Firmware 2.0.0.205 originale riconosciuto; installazione AutoPA '
                           'controllata consentita / Original 2.0.0.205 firmware recognized; '
                           'guarded AutoPA installation allowed.')
                install = True
            elif calibrator in {CANDIDATE_205, TESTED_205}:
                state = 'candidate-205-installed'
                message = ('AutoPA per firmware 2.0.0.205 riconosciuto / '
                           'AutoPA for firmware 2.0.0.205 recognized.')
                install = True
                calibration = hashes.get('adaptive_pa_macro.cfg') in {
                    MACRO_205_SHA256, MACRO_205_TESTED_SHA256
                }
            elif calibrator == LEGACY_V6:
                state = 'legacy-v6-on-new-firmware-blocked'
                message = ('Vecchio AutoPA v6 su firmware nuovo: incompatibile / '
                           'Old AutoPA v6 on new firmware: incompatible.')
    if state == 'unknown-blocked':
        details = []
        if version == '2.0.0':
            if full != FULLVERSION_205:
                details.append(
                    f"FULLVERSION trovato={full or '<vuoto>'} atteso={FULLVERSION_205}"
                )
            for name, expected in DEPENDENCIES_205.items():
                actual = hashes.get(name)
                if actual != expected:
                    details.append(
                        f"{name} trovato={actual or '<mancante>'} atteso={expected}"
                    )
            if calibrator not in {
                STOCK_205,
                CANDIDATE_205,
                TESTED_205,
                LEGACY_V6,
            }:
                details.append(
                    f"flow_calibrator.py trovato={calibrator or '<mancante>'}"
                )
        elif version == '1.5.2':
            details.append(
                "baseline 1.5.2/PAXX non corrisponde agli hash convalidati"
            )
            if build:
                details.append(f"BUILD_VERSION={build}")
        else:
            details.append(
                f"VERSION trovato={version or '<vuoto>'} FULLVERSION={full or '<vuoto>'}"
            )
        if missing:
            details.append("file mancanti=" + ", ".join(missing))
        message = (
            "Firmware/componenti non convalidati: "
            + "; ".join(details)
            + " / Firmware or components not validated."
        )
    return FirmwareCompatibility(version, full, build, state, message, hashes, tuple(missing), install, calibration)


def require_live_firmware(target, *, calibration=False):
    from .printer import PrinterInstallError
    report = inspect_firmware(target)
    allowed = report.live_calibration_allowed if calibration else report.live_install_allowed
    if not allowed:
        raise PrinterInstallError(report.message)
    return report
