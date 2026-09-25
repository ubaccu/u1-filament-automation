"""Keep newly created Orca profiles aligned with Spoolman filament density.

U1FA materializes a complete Snapmaker base profile so the U1 sender can match
custom vendor/type/colour identities.  The base also carries Snapmaker's own
filament density.  For a brand-new U1FA profile the physical filament metadata
entered in Spoolman is the better source of truth, so this patch replaces only
that one field after a successful creation.

Existing profiles are deliberately left untouched: users may have edited them
manually and 1.8.1 must not silently rewrite established presets.
"""

from __future__ import annotations

import json
import math
import uuid
from functools import wraps
from pathlib import Path
from typing import Any


def _clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _density_text(value: Any) -> str | None:
    if value is None:
        return None
    try:
        number = float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number) or number <= 0:
        return None
    return f"{number:.12g}"


def _filament_for_spool(spool: dict[str, Any], inventory: Any) -> dict[str, Any]:
    nested = spool.get("filament")
    if isinstance(nested, dict):
        return nested
    filament_id = spool.get("filament_id")
    return next(
        (
            item
            for item in getattr(inventory, "filaments", ())
            if isinstance(item, dict) and str(item.get("id")) == str(filament_id)
        ),
        {},
    )


def _vendor_for_filament(filament: dict[str, Any], inventory: Any) -> str:
    nested = filament.get("vendor")
    if isinstance(nested, dict):
        return _clean(nested.get("name"))
    vendor_id = filament.get("vendor_id")
    vendor = next(
        (
            item
            for item in getattr(inventory, "vendors", ())
            if isinstance(item, dict) and str(item.get("id")) == str(vendor_id)
        ),
        {},
    )
    return _clean(vendor.get("name"))


def _density_by_profile(inventory: Any, make_profile_name: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for spool in getattr(inventory, "spools", ()):
        if not isinstance(spool, dict):
            continue
        filament = _filament_for_spool(spool, inventory)
        if not filament:
            continue
        vendor = _vendor_for_filament(filament, inventory)
        material = _clean(filament.get("material"))
        name = _clean(filament.get("name"))
        density = _density_text(filament.get("density"))
        if not vendor or not material or not name or density is None:
            continue
        profile_name = make_profile_name(vendor, material, name)
        result.setdefault(profile_name.casefold(), density)
    return result


def _write_density(
    user_dir: Path,
    profile_name: str,
    density: str,
    safe_filename: Any,
) -> bool:
    path = user_dir / f"{safe_filename(profile_name)}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict) or payload.get("name") != profile_name:
        return False
    settings_id = payload.get("filament_settings_id")
    if settings_id not in ([profile_name], (profile_name,)):
        return False
    if payload.get("from") not in (None, "User"):
        return False

    desired = [density]
    if payload.get("filament_density") == desired:
        return False
    payload["filament_density"] = desired
    serialized = json.dumps(payload, indent=4, ensure_ascii=False) + "\n"
    json.loads(serialized)

    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.density.tmp")
    try:
        temporary.write_text(serialized, encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return True


def install_sync_density_patch(sync_module: Any) -> None:
    """Patch ``sync_profiles`` so new profiles use Spoolman's real density."""
    current = sync_module.sync_profiles
    if getattr(current, "_u1fa_spoolman_density", False):
        return

    @wraps(current)
    def sync_with_density(inventory: Any, user_dir: Path, *args: Any, **kwargs: Any):
        report = current(inventory, user_dir, *args, **kwargs)
        if not getattr(report, "apply", False):
            return report

        density_map = _density_by_profile(inventory, sync_module.make_profile_name)
        if not density_map:
            return report

        target = Path(user_dir).expanduser().resolve()
        for action in getattr(report, "actions", ()):
            # New profiles are safe to align. Existing presets are intentionally
            # not rewritten in 1.8.1, even when Spoolman later changes.
            if getattr(action, "status", "") != "created":
                continue
            profile_name = getattr(action, "profile_name", "")
            density = density_map.get(str(profile_name).casefold())
            if density is None:
                continue
            _write_density(
                target,
                str(profile_name),
                density,
                sync_module.safe_filename,
            )
        return report

    setattr(sync_with_density, "_u1fa_spoolman_density", True)
    sync_module.sync_profiles = sync_with_density
