from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .models import SpoolmanInventory


@dataclass(frozen=True)
class SyncAction:
    status: str
    profile_name: str
    base: str | None
    color: str
    spool_ids: tuple[int | str, ...]
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SyncReport:
    user_dir: Path
    system_dir: Path
    apply: bool
    actions: tuple[SyncAction, ...]

    def counts(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for action in self.actions:
            result[action.status] = result.get(action.status, 0) + 1
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": "apply" if self.apply else "preview",
            "user_dir": str(self.user_dir),
            "system_dir": str(self.system_dir),
            "counts": self.counts(),
            "actions": [action.to_dict() for action in self.actions],
        }


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def safe_filename(value: str) -> str:
    return value.replace("/", "-").replace(":", "-")


def choose_base(vendor: str, material: str, name: str) -> str | None:
    """Regole recuperate dal sincronizzatore Spoolman -> Snapmaker Orca."""
    text = f"{vendor} {material} {name}".lower()
    normalized = text.replace("-", " ").replace("_", " ")
    tokens = set(normalized.split())
    fast = (
        "snapspeed" in normalized
        or "high speed" in normalized
        or "hs" in tokens
        or "hf" in tokens
        or "rapid" in tokens
        or "hyper" in tokens
    )

    if "petg" in normalized:
        if "cf" in tokens or "carbon fiber" in normalized or "carbon fibre" in normalized:
            return "Snapmaker PETG-CF @U1 0.4 nozzle"
        if any(word in normalized for word in ("translucent", "transparent", "clear")):
            return "Snapmaker PETG Translucent @U1 0.4 nozzle"
        if fast:
            return "Snapmaker PETG HF"
        return "Snapmaker PETG @U1"

    if "pla" in normalized:
        if "cf" in tokens or "carbon fiber" in normalized or "carbon fibre" in normalized:
            return "Snapmaker PLA-CF @U1 0.4 nozzle"
        if "wood" in tokens:
            return "Snapmaker PLA Wood @U1 0.4 nozzle"
        if any(word in normalized for word in ("translucent", "transparent", "clear")):
            return "Snapmaker PLA Translucent @U1 0.4 nozzle"
        if fast:
            return "Snapmaker PLA SnapSpeed @U1"
        return "Snapmaker PLA Basic @U1"

    return None


def make_profile_name(vendor: str, material: str, name: str) -> str:
    """Mantiene il nome Spoolman senza ripetere vendor o materiale."""
    clean_vendor = re.sub(r"\s+", " ", vendor).strip()
    clean_material = re.sub(r"\s+", " ", material).strip()
    clean_name = re.sub(r"\s+", " ", name).strip()

    token_pattern = re.compile(r"[^\W_]+", flags=re.UNICODE)
    vendor_tokens = [item.casefold() for item in token_pattern.findall(clean_vendor)]
    name_matches = list(token_pattern.finditer(clean_name))
    name_tokens = [item.group(0).casefold() for item in name_matches]

    # Se il nome comincia già con il vendor, lo rimuove e poi usa una sola volta
    # il vendor registrato in Spoolman.
    if vendor_tokens and name_tokens[: len(vendor_tokens)] == vendor_tokens:
        end = name_matches[len(vendor_tokens) - 1].end()
        clean_name = clean_name[end:].lstrip(" -_:")
        name_tokens = [item.casefold() for item in token_pattern.findall(clean_name)]

    material_tokens = [
        item.casefold() for item in token_pattern.findall(clean_material)
    ]
    material_present = bool(material_tokens) and all(
        token in name_tokens for token in material_tokens
    )
    parts = [clean_vendor]
    if not material_present:
        parts.append(clean_material)
    parts.append(clean_name)
    technical_name = " ".join(value for value in parts if value)
    return technical_name + " @Snapmaker U1 (0.4 nozzle)"


def _profile_exists(user_dir: Path, filename: str) -> bool:
    wanted = filename.casefold()
    try:
        return any(
            path.is_file() and path.stem.casefold() == wanted
            for path in user_dir.glob("*.json")
        )
    except OSError:
        return False


def default_system_dir(user_dir: Path) -> Path:
    resolved = user_dir.resolve()
    try:
        root = resolved.parents[2]
    except IndexError as exc:
        raise ValueError(f"Cartella Orca non riconosciuta: {user_dir}") from exc
    if resolved.parent.parent.name != "user":
        raise ValueError(
            "Impossibile ricavare la cartella dei profili Snapmaker di sistema; "
            "usare --system-dir."
        )
    return root / "system" / "Snapmaker" / "filament"


def _filament_for_spool(
    spool: dict[str, Any], inventory: SpoolmanInventory
) -> dict[str, Any]:
    nested = spool.get("filament")
    if isinstance(nested, dict):
        return nested
    filament_id = spool.get("filament_id")
    return next(
        (item for item in inventory.filaments if item.get("id") == filament_id),
        {},
    )


def _vendor_for_filament(
    filament: dict[str, Any], inventory: SpoolmanInventory
) -> str:
    nested = filament.get("vendor")
    if isinstance(nested, dict):
        return clean(nested.get("name"))
    vendor_id = filament.get("vendor_id")
    vendor = next(
        (item for item in inventory.vendors if item.get("id") == vendor_id),
        {},
    )
    return clean(vendor.get("name"))


def _profile_payload(profile_name: str, base: str, color: str, version: str) -> dict[str, Any]:
    return {
        "default_filament_colour": [f"#{color}" if color else "#FFFFFF"],
        "filament_settings_id": [profile_name],
        "from": "User",
        "inherits": base,
        "is_custom_defined": "0",
        "name": profile_name,
        "version": version,
    }


def _base_version(base_file: Path) -> str:
    try:
        payload = json.loads(base_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "2.2.53.2"
    version = payload.get("version") if isinstance(payload, dict) else None
    return version if isinstance(version, str) and version else "2.2.53.2"


def _write_new_profile(
    user_dir: Path,
    system_dir: Path,
    profile_name: str,
    base: str,
    color: str,
) -> None:
    base_file = system_dir / f"{base}.json"
    filename = safe_filename(profile_name)
    json_path = user_dir / f"{filename}.json"
    info_path = user_dir / f"{filename}.info"
    payload = _profile_payload(profile_name, base, color, _base_version(base_file))
    serialized = json.dumps(payload, indent=4, ensure_ascii=False) + "\n"
    json.loads(serialized)

    # La modalità esclusiva impedisce di sovrascrivere anche in caso di concorrenza.
    with json_path.open("x", encoding="utf-8") as handle:
        handle.write(serialized)
    try:
        with info_path.open("x", encoding="utf-8") as handle:
            handle.write(
                "sync_info = update\n"
                "user_id =\n"
                "setting_id =\n"
                "base_id =\n"
                f"updated_time = {int(time.time())}\n"
            )
    except Exception:
        # Il JSON resta un profilo Orca valido anche se il metadato .info fallisce.
        raise


def sync_profiles(
    inventory: SpoolmanInventory,
    user_dir: Path,
    system_dir: Path | None = None,
    apply: bool = False,
    ignored_profile_names: set[str] | None = None,
    only_profile_names: set[str] | None = None,
) -> SyncReport:
    user_dir = user_dir.expanduser().resolve()
    effective_system_dir = (
        default_system_dir(user_dir)
        if system_dir is None
        else system_dir.expanduser().resolve()
    )
    if apply:
        user_dir.mkdir(parents=True, exist_ok=True)

    actions: list[SyncAction] = []
    ignored = {
        item.casefold() for item in (ignored_profile_names or set())
    }
    selected = (
        None
        if only_profile_names is None
        else {item.casefold() for item in only_profile_names}
    )
    seen_spools: set[tuple[str, str, str, str]] = set()
    planned_names: set[str] = set()

    for spool in inventory.spools:
        filament = _filament_for_spool(spool, inventory)
        vendor = _vendor_for_filament(filament, inventory)
        material = clean(filament.get("material"))
        name = clean(filament.get("name"))
        color = clean(filament.get("color_hex")).lstrip("#").upper()
        spool_id = spool.get("id")
        spool_ids = () if spool_id is None else (spool_id,)
        key = (vendor, material, name, color)
        if key in seen_spools:
            continue
        seen_spools.add(key)

        if not vendor or not material or not name:
            actions.append(
                SyncAction("skipped", " ".join(key[:3]).strip(), None, color, spool_ids, "dati incompleti")
            )
            continue

        base = choose_base(vendor, material, name)
        profile_name = make_profile_name(vendor, material, name)
        if selected is not None and profile_name.casefold() not in selected:
            continue
        if base is None:
            actions.append(
                SyncAction("skipped", profile_name, None, color, spool_ids, "nessuna base definita")
            )
            continue
        if profile_name.casefold() in ignored:
            actions.append(
                SyncAction(
                    "dismissed",
                    profile_name,
                    base,
                    color,
                    spool_ids,
                    "già gestito; un'eventuale eliminazione manuale viene rispettata",
                )
            )
            continue
        if not (effective_system_dir / f"{base}.json").is_file():
            actions.append(
                SyncAction("skipped", profile_name, base, color, spool_ids, "base Snapmaker non trovata")
            )
            continue

        filename = safe_filename(profile_name)
        if _profile_exists(user_dir, filename):
            actions.append(SyncAction("existing", profile_name, base, color, spool_ids))
            continue
        if filename.casefold() in planned_names:
            actions.append(
                SyncAction("merged", profile_name, base, color, spool_ids, "stesso profilo tecnico")
            )
            continue
        planned_names.add(filename.casefold())

        if apply:
            try:
                _write_new_profile(user_dir, effective_system_dir, profile_name, base, color)
            except FileExistsError:
                actions.append(SyncAction("existing", profile_name, base, color, spool_ids))
                continue
            status = "created"
        else:
            status = "planned"
        actions.append(SyncAction(status, profile_name, base, color, spool_ids))

    return SyncReport(
        user_dir=user_dir,
        system_dir=effective_system_dir,
        apply=apply,
        actions=tuple(actions),
    )
