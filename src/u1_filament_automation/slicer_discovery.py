from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


SlicerKind = Literal["snapmaker_orca", "orca_slicer"]


@dataclass(frozen=True)
class SlicerInstallation:
    kind: SlicerKind
    path: Path
    profile_count: int
    source: str
    preferred: bool


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


def candidate_slicer_roots(
    home: Path | None = None,
    system: str | None = None,
    environ: dict[str, str] | None = None,
) -> list[tuple[SlicerKind, Path, str]]:
    """Return read-only Snapmaker Orca and Orca Slicer candidates.

    Snapmaker Orca stays preferred because it is the currently integrated
    U1FA workflow. Standard Orca Slicer is discovered separately and is not
    allowed to silently replace the Snapmaker installation.
    """

    env = os.environ if environ is None else environ
    resolved_home = Path.home() if home is None else home
    current_system = platform.system() if system is None else system
    candidates: list[tuple[SlicerKind, Path, str]] = []

    if env.get("U1FA_SNAPMAKER_ORCA_DIR"):
        candidates.append(
            ("snapmaker_orca", Path(env["U1FA_SNAPMAKER_ORCA_DIR"]).expanduser(), "environment")
        )
    if env.get("U1FA_ORCA_SLICER_DIR"):
        candidates.append(
            ("orca_slicer", Path(env["U1FA_ORCA_SLICER_DIR"]).expanduser(), "environment")
        )

    if current_system == "Darwin":
        base = resolved_home / "Library" / "Application Support"
        candidates.extend([
            ("snapmaker_orca", base / "Snapmaker_Orca", "macOS"),
            ("orca_slicer", base / "OrcaSlicer", "macOS"),
        ])
    elif current_system == "Windows":
        appdata = env.get("APPDATA")
        if appdata:
            base = Path(appdata)
            candidates.extend([
                ("snapmaker_orca", base / "Snapmaker_Orca", "Windows"),
                ("orca_slicer", base / "OrcaSlicer", "Windows"),
            ])
    else:
        candidates.extend([
            ("snapmaker_orca", resolved_home / ".config" / "Snapmaker_Orca", "Linux config"),
            ("snapmaker_orca", resolved_home / ".local" / "share" / "Snapmaker_Orca", "Linux data"),
            ("orca_slicer", resolved_home / ".config" / "OrcaSlicer", "Linux config"),
            ("orca_slicer", resolved_home / ".local" / "share" / "OrcaSlicer", "Linux data"),
        ])
    return candidates


def discover_slicers(
    home: Path | None = None,
    system: str | None = None,
    environ: dict[str, str] | None = None,
) -> list[SlicerInstallation]:
    """Discover both slicers without modifying either installation."""

    found: list[SlicerInstallation] = []
    seen: set[tuple[SlicerKind, Path]] = set()
    for kind, root, source in candidate_slicer_roots(
        home=home, system=system, environ=environ
    ):
        possible = [root] if root.name == "filament" else _user_filament_dirs(root)
        for filament_dir in possible:
            normalized = filament_dir.expanduser().resolve()
            key = (kind, normalized)
            if key in seen or not normalized.is_dir():
                continue
            seen.add(key)
            found.append(
                SlicerInstallation(
                    kind=kind,
                    path=normalized,
                    profile_count=_profile_count(normalized),
                    source=source,
                    preferred=(kind == "snapmaker_orca"),
                )
            )

    return sorted(
        found,
        key=lambda item: (
            0 if item.preferred else 1,
            item.path.as_posix().casefold(),
        ),
    )
