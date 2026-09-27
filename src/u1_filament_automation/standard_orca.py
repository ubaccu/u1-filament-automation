from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from .pa_profile import PAProfileError, find_profile_path
from .sync import safe_filename


class StandardOrcaMirrorError(RuntimeError):
    pass


MirrorAction = Literal["create", "adopt", "update", "unchanged", "blocked"]


@dataclass(frozen=True)
class StandardOrcaMirrorPlan:
    profile_name: str
    source_path: Path
    target_path: Path
    source_sha256: str
    target_sha256: str
    action: MirrorAction
    reason: str = ""

    def to_dict(self) -> dict[str, str]:
        payload = asdict(self)
        payload["source_path"] = str(self.source_path)
        payload["target_path"] = str(self.target_path)
        return payload


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _state_path(target_dir: Path) -> Path:
    return target_dir / ".u1fa" / "standard-orca-mirror.json"


def _enabled_path(target_dir: Path) -> Path:
    return target_dir / ".u1fa" / "standard-orca-enabled"


def standard_orca_mirror_enabled(target_dir: Path) -> bool:
    target_dir = target_dir.expanduser().resolve()
    metadata = target_dir / ".u1fa"
    if metadata.is_symlink():
        return False
    marker = _enabled_path(target_dir)
    return marker.is_file() and not marker.is_symlink()


def set_standard_orca_mirror_enabled(target_dir: Path, enabled: bool) -> None:
    target_dir = target_dir.expanduser().resolve()
    if not target_dir.is_dir():
        raise StandardOrcaMirrorError(
            f"Cartella profili Orca Slicer standard non trovata: {target_dir}"
        )
    metadata = target_dir / ".u1fa"
    if metadata.exists() and metadata.is_symlink():
        raise StandardOrcaMirrorError(
            "La cartella stato Orca contiene un link simbolico: operazione bloccata"
        )
    metadata.mkdir(parents=True, exist_ok=True)
    marker = _enabled_path(target_dir)
    if enabled:
        try:
            marker.write_text("enabled\n", encoding="utf-8")
        except OSError as exc:
            raise StandardOrcaMirrorError(
                f"Impossibile abilitare il mirror Orca Slicer: {exc}"
            ) from exc
    else:
        try:
            marker.unlink(missing_ok=True)
        except OSError as exc:
            raise StandardOrcaMirrorError(
                f"Impossibile disabilitare il mirror Orca Slicer: {exc}"
            ) from exc


def _load_state(target_dir: Path) -> dict[str, dict[str, str]]:
    metadata = target_dir / ".u1fa"
    if metadata.is_symlink():
        raise StandardOrcaMirrorError(
            "La cartella stato Orca contiene un link simbolico: operazione bloccata"
        )
    state_path = _state_path(target_dir)
    if not state_path.exists():
        return {}
    if state_path.is_symlink():
        raise StandardOrcaMirrorError(
            "La cartella stato Orca contiene un link simbolico: operazione bloccata"
        )
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StandardOrcaMirrorError(
            f"Stato mirror Orca non valido: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise StandardOrcaMirrorError("Stato mirror Orca non valido")
    records = payload.get("profiles", {})
    if not isinstance(records, dict):
        raise StandardOrcaMirrorError("Stato mirror Orca non valido")
    result: dict[str, dict[str, str]] = {}
    for key, value in records.items():
        if isinstance(key, str) and isinstance(value, dict):
            result[key] = {
                "profile_name": str(value.get("profile_name", "")),
                "source_sha256": str(value.get("source_sha256", "")),
                "target_sha256": str(value.get("target_sha256", "")),
            }
    return result


def _write_state(
    target_dir: Path,
    records: dict[str, dict[str, str]],
) -> None:
    metadata = target_dir / ".u1fa"
    if metadata.exists() and metadata.is_symlink():
        raise StandardOrcaMirrorError(
            "La cartella stato Orca contiene un link simbolico: operazione bloccata"
        )
    metadata.mkdir(parents=True, exist_ok=True)
    state_path = _state_path(target_dir)
    payload = {
        "schema": 1,
        "profiles": records,
    }
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".standard-orca-mirror-",
        suffix=".tmp",
        dir=metadata,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, state_path)
    except Exception:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def _portable_profile_bytes(path: Path, profile_name: str) -> bytes:
    if path.is_symlink():
        raise StandardOrcaMirrorError(
            f"Il profilo sorgente {path.name} è un link simbolico"
        )
    try:
        data = path.read_bytes()
        payload = json.loads(data.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StandardOrcaMirrorError(
            f"Profilo Snapmaker Orca non valido: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise StandardOrcaMirrorError("Profilo Snapmaker Orca non valido")
    if payload.get("name") != profile_name:
        raise StandardOrcaMirrorError(
            "Il nome interno del profilo non corrisponde al profilo selezionato"
        )
    setting_id = payload.get("filament_settings_id")
    if setting_id not in ([profile_name], (profile_name,)):
        raise StandardOrcaMirrorError(
            "Profilo non riconosciuto come profilo U1FA portabile"
        )
    inherits = payload.get("inherits")
    if isinstance(inherits, str) and inherits.strip():
        raise StandardOrcaMirrorError(
            "Il profilo dipende ancora da una base Snapmaker e non può essere copiato "
            "in Orca Slicer standard"
        )
    if payload.get("from") not in (None, "User"):
        raise StandardOrcaMirrorError(
            "Profilo non riconosciuto come profilo utente U1FA"
        )
    return data


def plan_standard_orca_mirror(
    source_dir: Path,
    target_dir: Path,
    profile_name: str,
) -> StandardOrcaMirrorPlan:
    source_dir = source_dir.expanduser().resolve()
    target_dir = target_dir.expanduser().resolve()
    if source_dir == target_dir:
        raise StandardOrcaMirrorError(
            "Snapmaker Orca e Orca Slicer standard puntano alla stessa cartella"
        )
    if not target_dir.is_dir():
        raise StandardOrcaMirrorError(
            f"Cartella profili Orca Slicer standard non trovata: {target_dir}"
        )

    try:
        source_path = find_profile_path(source_dir, profile_name)
    except PAProfileError as exc:
        raise StandardOrcaMirrorError(str(exc)) from exc
    source_bytes = _portable_profile_bytes(source_path, profile_name)
    source_hash = _sha256(source_bytes)

    target_path = target_dir / f"{safe_filename(profile_name)}.json"
    if target_path.is_symlink():
        return StandardOrcaMirrorPlan(
            profile_name,
            source_path,
            target_path,
            source_hash,
            "",
            "blocked",
            "Il profilo destinazione è un link simbolico",
        )

    state = _load_state(target_dir)
    key = target_path.name.casefold()
    record = state.get(key)

    if not target_path.exists():
        return StandardOrcaMirrorPlan(
            profile_name,
            source_path,
            target_path,
            source_hash,
            "",
            "create",
        )
    if not target_path.is_file():
        return StandardOrcaMirrorPlan(
            profile_name,
            source_path,
            target_path,
            source_hash,
            "",
            "blocked",
            "La destinazione esiste ma non è un file regolare",
        )

    try:
        target_bytes = target_path.read_bytes()
    except OSError as exc:
        raise StandardOrcaMirrorError(
            f"Impossibile leggere il profilo Orca Slicer standard: {exc}"
        ) from exc
    target_hash = _sha256(target_bytes)

    if target_hash == source_hash:
        action: MirrorAction = "unchanged" if record else "adopt"
        return StandardOrcaMirrorPlan(
            profile_name,
            source_path,
            target_path,
            source_hash,
            target_hash,
            action,
        )

    if record is None:
        return StandardOrcaMirrorPlan(
            profile_name,
            source_path,
            target_path,
            source_hash,
            target_hash,
            "blocked",
            "Esiste già un profilo Orca Slicer con lo stesso nome e non è gestito da U1FA",
        )

    if (
        record.get("profile_name") != profile_name
        or record.get("target_sha256") != target_hash
    ):
        return StandardOrcaMirrorPlan(
            profile_name,
            source_path,
            target_path,
            source_hash,
            target_hash,
            "blocked",
            "Il profilo mirror è stato modificato fuori da U1FA; nessuna sovrascrittura",
        )

    return StandardOrcaMirrorPlan(
        profile_name,
        source_path,
        target_path,
        source_hash,
        target_hash,
        "update",
    )


def _backup_target(target_path: Path) -> Path:
    metadata = target_path.parent / ".u1fa"
    backups = metadata / "backups"
    if metadata.exists() and metadata.is_symlink():
        raise StandardOrcaMirrorError(
            "La cartella stato Orca contiene un link simbolico: operazione bloccata"
        )
    if backups.exists() and backups.is_symlink():
        raise StandardOrcaMirrorError(
            "La cartella backup Orca contiene un link simbolico: operazione bloccata"
        )
    backups.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    backup = backups / f"{target_path.name}.pre-u1fa-mirror-{stamp}.bak"
    counter = 0
    while backup.exists():
        counter += 1
        backup = backups / (
            f"{target_path.name}.pre-u1fa-mirror-{stamp}-{counter}.bak"
        )
    with backup.open("xb") as handle:
        handle.write(target_path.read_bytes())
        handle.flush()
        os.fsync(handle.fileno())
    return backup


def _atomic_write(target_path: Path, data: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target_path.name}.u1fa-",
        suffix=".tmp",
        dir=target_path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target_path)
    except Exception:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def _ensure_info_file(target_path: Path) -> None:
    info_path = target_path.with_suffix(".info")
    if info_path.exists():
        return
    payload = (
        "sync_info = update\n"
        "user_id =\n"
        "setting_id =\n"
        "base_id =\n"
        f"updated_time = {int(time.time())}\n"
    )
    try:
        with info_path.open("x", encoding="utf-8") as handle:
            handle.write(payload)
    except FileExistsError:
        pass


def apply_standard_orca_mirror(
    plan: StandardOrcaMirrorPlan,
) -> StandardOrcaMirrorPlan:
    if plan.action == "blocked":
        raise StandardOrcaMirrorError(plan.reason or "Mirror Orca bloccato")

    source_bytes = _portable_profile_bytes(plan.source_path, plan.profile_name)
    current_source_hash = _sha256(source_bytes)
    if current_source_hash != plan.source_sha256:
        raise StandardOrcaMirrorError(
            "Il profilo Snapmaker Orca è cambiato dopo l'anteprima"
        )

    target_dir = plan.target_path.parent
    state = _load_state(target_dir)
    key = plan.target_path.name.casefold()

    if plan.action == "create":
        try:
            with plan.target_path.open("xb") as handle:
                handle.write(source_bytes)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError as exc:
            raise StandardOrcaMirrorError(
                "Il profilo destinazione è comparso dopo l'anteprima"
            ) from exc
        _ensure_info_file(plan.target_path)
    elif plan.action == "update":
        if not plan.target_path.is_file() or plan.target_path.is_symlink():
            raise StandardOrcaMirrorError(
                "Il profilo destinazione è cambiato dopo l'anteprima"
            )
        current_target_hash = _sha256(plan.target_path.read_bytes())
        if current_target_hash != plan.target_sha256:
            raise StandardOrcaMirrorError(
                "Il profilo Orca Slicer è cambiato dopo l'anteprima"
            )
        _backup_target(plan.target_path)
        _atomic_write(plan.target_path, source_bytes)
    elif plan.action in {"adopt", "unchanged"}:
        if not plan.target_path.is_file() or plan.target_path.is_symlink():
            raise StandardOrcaMirrorError(
                "Il profilo destinazione è cambiato dopo l'anteprima"
            )
        current_target_hash = _sha256(plan.target_path.read_bytes())
        if current_target_hash != current_source_hash:
            raise StandardOrcaMirrorError(
                "Il profilo Orca Slicer è cambiato dopo l'anteprima"
            )

    final_hash = _sha256(plan.target_path.read_bytes())
    state[key] = {
        "profile_name": plan.profile_name,
        "source_sha256": current_source_hash,
        "target_sha256": final_hash,
    }
    _write_state(target_dir, state)

    return StandardOrcaMirrorPlan(
        plan.profile_name,
        plan.source_path,
        plan.target_path,
        current_source_hash,
        final_hash,
        "unchanged",
        "Mirror Orca Slicer verificato",
    )
