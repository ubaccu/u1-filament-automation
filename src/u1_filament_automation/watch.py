from __future__ import annotations

import json
import os
import platform
import uuid
from pathlib import Path
from typing import Iterable

from .sync import SyncReport


class WatchStateError(RuntimeError):
    pass


def default_watch_state_path(
    target_user_dir: Path,
    sandbox: bool,
    home: Path | None = None,
    environ: dict[str, str] | None = None,
    system: str | None = None,
) -> Path:
    if sandbox:
        return target_user_dir / ".u1fa" / "watch-state.json"
    env = os.environ if environ is None else environ
    resolved_home = Path.home() if home is None else home
    current_system = platform.system() if system is None else system
    if current_system == "Darwin":
        root = resolved_home / "Library" / "Application Support"
    elif current_system == "Windows" and env.get("APPDATA"):
        root = Path(env["APPDATA"])
    else:
        root = Path(env.get("XDG_CONFIG_HOME", resolved_home / ".config"))
    return root / "U1 Filament Automation" / "watch-state.json"


def load_managed_profiles(path: Path, target_user_dir: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WatchStateError(f"Stato monitor non leggibile: {path}") from exc
    target = str(target_user_dir.expanduser().resolve())
    if (
        not isinstance(payload, dict)
        or payload.get("version") != 1
        or payload.get("target_user_dir") != target
        or not isinstance(payload.get("managed_profiles"), list)
        or not all(isinstance(item, str) for item in payload["managed_profiles"])
    ):
        raise WatchStateError(
            "Stato monitor non valido o appartenente a un'altra cartella Orca"
        )
    return {item.casefold() for item in payload["managed_profiles"]}


def managed_profiles_from_report(report: SyncReport) -> set[str]:
    managed_statuses = {"created", "existing"}
    return {
        action.profile_name.casefold()
        for action in report.actions
        if action.status in managed_statuses
    }


def save_managed_profiles(
    path: Path,
    target_user_dir: Path,
    managed_profiles: Iterable[str],
) -> None:
    payload = {
        "version": 1,
        "target_user_dir": str(target_user_dir.expanduser().resolve()),
        "managed_profiles": sorted({item.casefold() for item in managed_profiles}),
    }
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        raise WatchStateError(f"Impossibile salvare lo stato monitor: {path}") from exc
    finally:
        temporary.unlink(missing_ok=True)
