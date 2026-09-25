from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import SpoolmanInventory
from .pa import PASuite, _format_number
from .sync import (
    _filament_for_spool,
    _vendor_for_filament,
    clean,
    make_profile_name,
    safe_filename,
)


_TRACKING_RE = re.compile(
    r"Tracking:\s*(?P<label>.*?)\s*\([^\n]*?Spoolman\s+id:\s*(?P<id>\d+)",
    re.IGNORECASE,
)
_SPOOL_ID_RE = re.compile(r"Spoolman\s+id:\s*(\d+)", re.IGNORECASE)
_FLOW_FILAMENT_RE = re.compile(
    r"\[flow_calibrate\]\s+filament:\s*(.*?)\s*,\s*calib_param\s*:",
    re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"[^\W_]+", flags=re.UNICODE)


class PAProfileError(RuntimeError):
    pass


@dataclass(frozen=True)
class CalibrationIdentity:
    spool_id: int | None = None
    tracking_label: str | None = None
    flow_label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProfileCandidate:
    profile_name: str
    spool_ids: tuple[int | str, ...]
    material: str = ""
    filament_name: str = ""


@dataclass(frozen=True)
class PAProfileReport:
    status: str
    profile_name: str
    profile_path: Path
    identity: CalibrationIdentity
    static_fallback: str
    adaptive_model: str
    changed_fields: tuple[str, ...]
    manual_profile: bool = False
    backup_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "profile_name": self.profile_name,
            "profile_path": str(self.profile_path),
            "identity": self.identity.to_dict(),
            "static_fallback": self.static_fallback,
            "adaptive_model": self.adaptive_model,
            "changed_fields": list(self.changed_fields),
            "manual_profile": self.manual_profile,
            "backup_path": (
                None if self.backup_path is None else str(self.backup_path)
            ),
        }


def calibration_identity(
    text: str,
    end_offset: int | None = None,
) -> CalibrationIdentity:
    relevant_text = text if end_offset is None else text[:end_offset]
    tracking_matches = list(_TRACKING_RE.finditer(relevant_text))
    tracking = tracking_matches[-1] if tracking_matches else None
    spool_matches = list(_SPOOL_ID_RE.finditer(relevant_text))
    flow_matches = list(_FLOW_FILAMENT_RE.finditer(relevant_text))
    return CalibrationIdentity(
        spool_id=(
            int(tracking.group("id"))
            if tracking is not None
            else int(spool_matches[-1].group(1))
            if spool_matches
            else None
        ),
        tracking_label=(
            _clean_label(tracking.group("label")) if tracking is not None else None
        ),
        flow_label=(
            _clean_label(flow_matches[-1].group(1)) if flow_matches else None
        ),
    )


def _clean_label(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" -_:,")


def _normalized_tokens(value: str) -> tuple[str, ...]:
    return tuple(item.casefold() for item in _TOKEN_RE.findall(value))


def _spool_id_equal(left: Any, right: int) -> bool:
    try:
        return int(left) == right
    except (TypeError, ValueError):
        return False


def profile_candidates(inventory: SpoolmanInventory) -> tuple[ProfileCandidate, ...]:
    grouped: dict[str, tuple[str, list[int | str], str, str]] = {}
    for spool in inventory.spools:
        filament = _filament_for_spool(spool, inventory)
        vendor = _vendor_for_filament(filament, inventory)
        material = clean(filament.get("material"))
        name = clean(filament.get("name"))
        if not vendor or not material or not name:
            continue
        profile_name = make_profile_name(vendor, material, name)
        key = profile_name.casefold()
        if key not in grouped:
            grouped[key] = (profile_name, [], material, name)
        spool_id = spool.get("id")
        if spool_id is not None and spool_id not in grouped[key][1]:
            grouped[key][1].append(spool_id)
    return tuple(
        ProfileCandidate(
            profile_name=profile_name,
            spool_ids=tuple(spool_ids),
            material=material,
            filament_name=filament_name,
        )
        for profile_name, spool_ids, material, filament_name in grouped.values()
    )


def resolve_profile_name(
    identity: CalibrationIdentity,
    inventory: SpoolmanInventory,
    override: str | None = None,
) -> str:
    if override and override.strip():
        return override.strip()

    candidates = profile_candidates(inventory)
    if identity.spool_id is not None:
        matches = [
            item
            for item in candidates
            if any(_spool_id_equal(spool_id, identity.spool_id) for spool_id in item.spool_ids)
        ]
        if len(matches) == 1:
            return matches[0].profile_name
        if not matches:
            raise PAProfileError(
                f"La bobina Spoolman ID {identity.spool_id} non è presente nell'inventario"
            )
        raise PAProfileError(
            f"La bobina Spoolman ID {identity.spool_id} corrisponde a più profili"
        )

    label = identity.tracking_label or identity.flow_label
    if not label:
        raise PAProfileError(
            "Il log non contiene né un ID bobina Spoolman né un nome filamento"
        )
    wanted = set(_normalized_tokens(label))
    matches = [
        item
        for item in candidates
        if wanted and wanted.issubset(set(_normalized_tokens(item.profile_name)))
    ]
    if len(matches) == 1:
        return matches[0].profile_name
    if not matches:
        raise PAProfileError(
            f"Nessun profilo Spoolman corrisponde al filamento del log: {label}"
        )
    names = ", ".join(item.profile_name for item in matches)
    raise PAProfileError(
        f"Nome filamento ambiguo ({label}); profili possibili: {names}"
    )


def find_profile_path(user_dir: Path, profile_name: str) -> Path:
    user_dir = user_dir.expanduser().resolve()
    wanted_filename = safe_filename(profile_name).casefold()
    matches: list[Path] = []
    try:
        paths = list(user_dir.glob("*.json"))
    except OSError as exc:
        raise PAProfileError(f"Impossibile leggere la cartella profili: {exc}") from exc

    for path in paths:
        if path.is_symlink():
            if path.stem.casefold() == wanted_filename:
                raise PAProfileError(
                    f"Il profilo {path.name} è un link simbolico: scrittura bloccata"
                )
            continue
        if path.stem.casefold() == wanted_filename:
            matches.append(path)
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if (
            isinstance(payload, dict)
            and isinstance(payload.get("name"), str)
            and payload["name"].casefold() == profile_name.casefold()
        ):
            matches.append(path)

    unique = list(dict.fromkeys(path.resolve() for path in matches))
    if not unique:
        raise PAProfileError(
            f"Profilo Orca non trovato: {profile_name}. "
            "Crearlo prima con sync/watch nella stessa cartella."
        )
    if len(unique) > 1:
        raise PAProfileError(
            f"Più JSON Orca corrispondono a {profile_name}; nessuna modifica eseguita"
        )
    if unique[0].parent != user_dir:
        raise PAProfileError(
            "Il profilo risolto esce dalla cartella autorizzata: scrittura bloccata"
        )
    return unique[0]


def adaptive_pa_values(suite: PASuite) -> dict[str, list[str]]:
    bridge_pa = suite.static_fallback / 2
    return {
        "enable_pressure_advance": ["1"],
        "pressure_advance": [_format_number(suite.static_fallback, 6)],
        "adaptive_pressure_advance": ["1"],
        "adaptive_pressure_advance_model": [
            "\n".join(item.orca_row() for item in suite.results)
        ],
        "adaptive_pressure_advance_overhangs": ["0"],
        "adaptive_pressure_advance_bridges": [_format_number(bridge_pa, 6)],
    }


def _load_profile(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PAProfileError(f"JSON Orca non valido ({path.name}): {exc}") from exc
    if not isinstance(payload, dict):
        raise PAProfileError(f"JSON Orca non valido ({path.name}): oggetto atteso")
    return payload


def _backup_path(profile_path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    metadata_dir = profile_path.parent / ".u1fa"
    backups_dir = metadata_dir / "backups"
    if metadata_dir.is_symlink() or backups_dir.is_symlink():
        raise PAProfileError(
            "La cartella backup contiene un link simbolico: scrittura bloccata"
        )
    return backups_dir / f"{profile_path.name}.u1fa-backup-{stamp}"


def _write_atomic_with_backup(
    profile_path: Path,
    payload: dict[str, Any],
) -> Path:
    backup_path = _backup_path(profile_path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with backup_path.open("xb") as backup_handle:
            with profile_path.open("rb") as source_handle:
                shutil.copyfileobj(source_handle, backup_handle)
            backup_handle.flush()
            os.fsync(backup_handle.fileno())
        shutil.copystat(profile_path, backup_path)
    except Exception as exc:
        try:
            backup_path.unlink()
        except OSError:
            pass
        raise PAProfileError(f"Creazione del backup fallita: {exc}") from exc

    serialized = json.dumps(payload, indent=4, ensure_ascii=False) + "\n"
    json.loads(serialized)
    temporary_path: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{profile_path.name}.u1fa-",
            suffix=".tmp",
            dir=profile_path.parent,
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, profile_path.stat().st_mode)
        os.replace(temporary_path, profile_path)
        temporary_path = None
    except Exception as exc:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except OSError:
                pass
        try:
            shutil.copy2(backup_path, profile_path)
        except OSError:
            pass
        raise PAProfileError(f"Scrittura atomica fallita: {exc}") from exc
    return backup_path


def update_pa_profile(
    user_dir: Path,
    profile_name: str,
    identity: CalibrationIdentity,
    suite: PASuite,
    apply: bool = False,
    manual_profile: bool = False,
) -> PAProfileReport:
    profile_path = find_profile_path(user_dir, profile_name)
    payload = _load_profile(profile_path)
    values = adaptive_pa_values(suite)
    changed_fields = tuple(
        key for key, value in values.items() if payload.get(key) != value
    )
    status = "planned" if changed_fields else "unchanged"
    backup_path = None
    if apply and changed_fields:
        updated_payload = dict(payload)
        updated_payload.update(values)
        backup_path = _write_atomic_with_backup(profile_path, updated_payload)
        status = "updated"

    return PAProfileReport(
        status=status,
        profile_name=profile_name,
        profile_path=profile_path,
        identity=identity,
        static_fallback=values["pressure_advance"][0],
        adaptive_model=values["adaptive_pressure_advance_model"][0],
        changed_fields=changed_fields,
        manual_profile=manual_profile,
        backup_path=backup_path,
    )
