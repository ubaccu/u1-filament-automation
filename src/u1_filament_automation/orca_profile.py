from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ProfileMaterializationError(RuntimeError):
    """Raised when an Orca system preset cannot be flattened safely."""


def _read_profile(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProfileMaterializationError(
            f"profilo Orca non leggibile: {path.name}"
        ) from exc
    if not isinstance(payload, dict):
        raise ProfileMaterializationError(
            f"profilo Orca non valido: {path.name}"
        )
    return payload


def flatten_filament_profile(
    base_file: Path,
    *,
    _seen: set[Path] | None = None,
) -> dict[str, Any]:
    """Resolve an Orca filament preset inheritance chain into one payload.

    Snapmaker's current U1 sender only considers manufacturer-specific presets
    whose preset base is the preset itself.  U1FA therefore has to materialize
    the effective Snapmaker settings before removing ``inherits``; simply
    deleting ``inherits`` from the lightweight child would lose base settings.
    """
    resolved = base_file.resolve()
    seen = set() if _seen is None else set(_seen)
    if resolved in seen:
        raise ProfileMaterializationError(
            f"ciclo di ereditarietà Orca: {base_file.name}"
        )
    seen.add(resolved)

    payload = _read_profile(base_file)
    parent_name = payload.get("inherits")
    if isinstance(parent_name, str) and parent_name.strip():
        parent_file = base_file.parent / f"{parent_name}.json"
        if not parent_file.is_file():
            raise ProfileMaterializationError(
                f"profilo padre Orca non trovato: {parent_name}"
            )
        merged = flatten_filament_profile(parent_file, _seen=seen)
        merged.update(payload)
    else:
        merged = dict(payload)

    # A materialized profile must be its own preset base for Snapmaker's
    # vendor/type/colour matcher to consider it.
    merged.pop("inherits", None)
    return merged


def filament_identity_name(profile_name: str) -> str:
    """Return the user filament name in the same form Orca hashes for IDs."""
    if "@" not in profile_name:
        return profile_name.strip()
    return profile_name.split("@", 1)[0].rstrip()


def user_filament_id(profile_name: str) -> str:
    """Mirror Orca's deterministic user-filament ID convention.

    Orca generates user filament IDs as ``P`` + the first seven hex chars of
    the MD5 of the filament identity string.  Matching this convention keeps
    U1FA-created presets stable across re-creation and compatible with Orca's
    filament grouping/matching logic.
    """
    identity = filament_identity_name(profile_name)
    digest = hashlib.md5(identity.encode("utf-8")).hexdigest()
    return "P" + digest[:7]


def build_detached_profile_payload(
    base_file: Path,
    profile_name: str,
    vendor: str,
    colors: tuple[str, ...] | str,
    version: str,
) -> dict[str, Any]:
    if isinstance(colors, str):
        normalized_colors = (colors,) if colors else ()
    else:
        normalized_colors = tuple(colors)
    profile_colors = [
        f"#{color}" if color else "#FFFFFF"
        for color in (normalized_colors or ("",))
    ]

    payload = flatten_filament_profile(base_file)

    # Never copy system/cloud identity into a user preset.  The actual
    # material settings and compatibility constraints remain in the flattened
    # payload; identity is then replaced with U1FA/Spoolman data.
    payload.pop("setting_id", None)
    payload.pop("instantiation", None)

    payload.update(
        {
            "type": "filament",
            "name": profile_name,
            "from": "User",
            "filament_id": user_filament_id(profile_name),
            "filament_settings_id": [profile_name],
            "filament_vendor": [vendor],
            "default_filament_colour": profile_colors,
            "filament_colour": profile_colors,
            "is_custom_defined": "0",
            "version": version,
        }
    )
    payload.pop("inherits", None)
    return payload
