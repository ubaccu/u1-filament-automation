from __future__ import annotations

import os
import platform
from pathlib import Path

from .models import OrcaInstallation


def _profile_count(path: Path) -> int:
    try:
        return sum(1 for item in path.rglob("*.json") if item.is_file())
    except OSError:
        return 0


def _user_filament_dirs(root: Path) -> list[Path]:
    user_root = root / "user"
    if not user_root.is_dir():
        return []
    result: list[Path] = []
    try:
        for profile_dir in user_root.iterdir():
            filament_dir = profile_dir / "filament"
            if filament_dir.is_dir():
                result.append(filament_dir)
    except OSError:
        return []
    return result


def candidate_roots(
    home: Path | None = None,
    system: str | None = None,
    environ: dict[str, str] | None = None,
) -> list[tuple[Path, str]]:
    env = os.environ if environ is None else environ
    resolved_home = Path.home() if home is None else home
    current_system = platform.system() if system is None else system
    candidates: list[tuple[Path, str]] = []

    if env.get("U1FA_ORCA_DIR"):
        candidates.append((Path(env["U1FA_ORCA_DIR"]).expanduser(), "environment"))

    if current_system == "Darwin":
        candidates.append(
            (
                resolved_home
                / "Library"
                / "Application Support"
                / "Snapmaker_Orca",
                "macOS",
            )
        )
    elif current_system == "Windows":
        appdata = env.get("APPDATA")
        if appdata:
            candidates.append((Path(appdata) / "Snapmaker_Orca", "Windows"))
    else:
        candidates.extend(
            [
                (resolved_home / ".config" / "Snapmaker_Orca", "Linux config"),
                (resolved_home / ".local" / "share" / "Snapmaker_Orca", "Linux data"),
            ]
        )
    return candidates


def discover_orca(
    explicit_dir: str | None = None,
    home: Path | None = None,
    system: str | None = None,
    environ: dict[str, str] | None = None,
) -> list[OrcaInstallation]:
    found: list[OrcaInstallation] = []
    seen: set[Path] = set()
    if explicit_dir:
        direct = Path(explicit_dir).expanduser().resolve()
        if direct.is_dir():
            found.append(
                OrcaInstallation(
                    path=direct,
                    profile_count=_profile_count(direct),
                    source="command line",
                )
            )
            seen.add(direct)

    for path, source in candidate_roots(home=home, system=system, environ=environ):
        possible = [path] if path.name == "filament" else _user_filament_dirs(path)
        for filament_dir in possible:
            normalized = filament_dir.resolve()
            if normalized in seen or not normalized.is_dir():
                continue
            seen.add(normalized)
            found.append(
                OrcaInstallation(
                    path=normalized,
                    profile_count=_profile_count(normalized),
                    source=source,
                )
            )
    return found
