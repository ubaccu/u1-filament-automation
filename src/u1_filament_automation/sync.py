from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .models import SpoolmanInventory
from .orca_profile import ProfileMaterializationError, build_detached_profile_payload


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


def choose_base(
    vendor: str,
    material: str,
    name: str,
    multicolor: bool = False,
) -> str | None:
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

    # Snapmaker Orca 2.4.0 added these U1 filament families for the
    # 0.4 mm nozzle. Keep them ahead of the generic PLA/PETG rules so Rainbow
    # multicolor spools are not accidentally routed to PLA Silk.
    if "peba" in normalized:
        return "Snapmaker PEBA 90A @U1 0.4 nozzle"

    if "tpu" in normalized:
        return "Snapmaker TPU @U1 0.4 nozzle"

    if "asa" in tokens:
        return "Snapmaker ASA @U1"

    if "abs" in tokens:
        return "Snapmaker ABS @U1"

    if "petg" in normalized:
        if "cf" in tokens or "carbon fiber" in normalized or "carbon fibre" in normalized:
            return "Snapmaker PETG-CF @U1 0.4 nozzle"
        if any(word in normalized for word in ("translucent", "transparent", "clear")):
            return "Snapmaker PETG Translucent @U1 0.4 nozzle"
        if fast:
            return "Snapmaker PETG HF"
        return "Snapmaker PETG @U1"

    if "pla" in normalized:
        if "rainbow" in normalized:
            return "Snapmaker PLA Rainbow @U1 0.4 nozzle"
        if "cf" in tokens or "carbon fiber" in normalized or "carbon fibre" in normalized:
            return "Snapmaker PLA-CF @U1 0.4 nozzle"
        if "silk" in normalized or (multicolor and not fast):
            # Il profilo Silk U1 è nominato così nelle installazioni Orca
            # recenti; la risoluzione del file sotto gestisce anche il nome
            # legacy con suffisso @U1. Le bobine PLA multicolore usano la
            # stessa base Silk anche quando il nome commerciale non contiene
            # esplicitamente la parola Silk.
            return "Snapmaker PLA Silk"
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


def _filament_colors(filament: dict[str, Any]) -> tuple[str, ...]:
    raw = filament.get("multi_color_hexes")
    if isinstance(raw, str):
        values = re.split(r"[,;\s]+", raw.strip())
    elif isinstance(raw, (list, tuple)):
        values = list(raw)
    else:
        values = []
    colors: list[str] = []
    for value in values:
        color = clean(value).lstrip("#").upper()
        if re.fullmatch(r"[0-9A-F]{6}", color) and color not in colors:
            colors.append(color)
    if len(colors) >= 2:
        return tuple(colors)
    color = clean(filament.get("color_hex")).lstrip("#").upper()
    return (color,) if re.fullmatch(r"[0-9A-F]{6}", color) else ()


def _normalized_profile_stem(value: str) -> str:
    text = value.casefold().replace("@", " ").replace("_", " ").replace("-", " ")
    return " ".join(re.findall(r"[a-z0-9.]+", text))


def _u1_family_candidates(system_dir: Path, family: str) -> list[Path]:
    """Return safe local aliases for one U1 material family.

    Snapmaker has changed filament preset naming across Orca resource bundles.
    Prefer an installed U1 0.4-mm preset when available, then the U1 base.
    Benchy and other nozzle-specific presets are deliberately excluded.
    """
    wanted = family.casefold()
    ranked: list[tuple[int, str, Path]] = []
    try:
        paths = tuple(system_dir.glob("*.json"))
    except OSError:
        return []
    for path in paths:
        stem = _normalized_profile_stem(path.stem)
        tokens = set(stem.split())
        if "snapmaker" not in tokens or wanted not in tokens or "u1" not in tokens:
            continue
        if "benchy" in tokens:
            continue
        if any(nozzle in stem for nozzle in ("0.2 nozzle", "0.6 nozzle", "0.8 nozzle")):
            continue
        score = 0
        if "0.4 nozzle" in stem:
            score += 30
        if "base" not in tokens:
            score += 20
        if stem == f"snapmaker {wanted} u1":
            score += 40
        ranked.append((-score, path.name.casefold(), path))
    return [path for _, _, path in sorted(ranked)]


_U1_ENGINEERING_FALLBACKS = {
    "Snapmaker ASA @U1": (
        "Snapmaker ASA @U1 0.4 nozzle",
        "Snapmaker ASA @U1 base",
        "Snapmaker ASA",
        "Snapmaker ASA @base",
        "fdm_filament_asa",
    ),
    "Snapmaker ABS @U1": (
        "Snapmaker ABS @U1 0.4 nozzle",
        "Snapmaker ABS @U1 base",
        "Snapmaker ABS",
        "Snapmaker ABS @base",
        "fdm_filament_abs",
    ),
}


def base_profile_path(system_dir: Path, base: str) -> Path:
    candidates = [system_dir / f"{base}.json"]
    if base == "Snapmaker PLA Silk":
        candidates.append(system_dir / "Snapmaker PLA Silk @U1.json")
    elif base == "Snapmaker PLA Silk @U1":
        candidates.append(system_dir / "Snapmaker PLA Silk.json")

    if base in _U1_ENGINEERING_FALLBACKS:
        family = "ASA" if " ASA " in f" {base} " else "ABS"
        candidates.extend(_u1_family_candidates(system_dir, family))
        candidates.extend(
            system_dir / f"{name}.json"
            for name in _U1_ENGINEERING_FALLBACKS[base]
        )

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.is_file():
            return candidate
    return candidates[0]


def _apply_u1_material_overrides(payload: dict[str, Any], base: str) -> dict[str, Any]:
    """Apply the official U1 0.4-mm ASA/ABS effective settings.

    This keeps U1FA functional when Snapmaker Orca ships the generic ASA/ABS
    chain locally but omits the lightweight U1 child preset.  We still require
    an installed Snapmaker/generic material base, so no profile is fabricated
    from nothing.
    """
    result = dict(payload)
    if base == "Snapmaker ASA @U1":
        result.update(
            {
                "compatible_printers": ["Snapmaker U1 (0.4 nozzle)"],
                "filament_type": ["ASA"],
                "filament_density": ["1.04"],
                "filament_flow_ratio": ["0.94"],
                "filament_max_volumetric_speed": ["8"],
                "hot_plate_temp": ["110"],
                "hot_plate_temp_initial_layer": ["100"],
                "nozzle_temperature": ["255"],
                "nozzle_temperature_initial_layer": ["255"],
                "nozzle_temperature_range_low": ["240"],
                "nozzle_temperature_range_high": ["280"],
                "overhang_fan_speed": ["15"],
                "fan_max_speed": ["15"],
                "fan_min_speed": ["0"],
                "filament_loading_speed_start": ["35"],
                "filament_loading_speed": ["35"],
                "filament_unloading_speed_start": ["35"],
                "filament_unloading_speed": ["35"],
                "filament_load_time": ["2"],
                "filament_unload_time": ["2"],
                "filament_cooling_moves": ["2"],
                "filament_cooling_initial_speed": ["35"],
                "filament_cooling_final_speed": ["60"],
            }
        )
    elif base == "Snapmaker ABS @U1":
        result.update(
            {
                "compatible_printers": ["Snapmaker U1 (0.4 nozzle)"],
                "filament_type": ["ABS"],
                "filament_density": ["1.04"],
                "filament_flow_ratio": ["0.95"],
                "filament_max_volumetric_speed": ["8"],
                "hot_plate_temp": ["110"],
                "hot_plate_temp_initial_layer": ["105"],
                "nozzle_temperature": ["255"],
                "nozzle_temperature_initial_layer": ["265"],
                "nozzle_temperature_range_low": ["240"],
                "nozzle_temperature_range_high": ["280"],
                "overhang_fan_speed": ["20"],
                "fan_max_speed": ["15"],
                "pressure_advance": ["0.02"],
                "filament_loading_speed_start": ["35"],
                "filament_loading_speed": ["35"],
                "filament_unloading_speed_start": ["35"],
                "filament_unloading_speed": ["35"],
                "filament_load_time": ["2"],
                "filament_unload_time": ["2"],
                "filament_cooling_moves": ["2"],
                "filament_cooling_initial_speed": ["35"],
                "filament_cooling_final_speed": ["60"],
            }
        )
    return result


def _build_profile_payload(
    base_file: Path,
    base: str,
    profile_name: str,
    vendor: str,
    colors: tuple[str, ...] | str,
    version: str,
) -> dict[str, Any]:
    payload = build_detached_profile_payload(
        base_file,
        profile_name,
        vendor,
        colors,
        version,
    )
    return _apply_u1_material_overrides(payload, base)


def repair_profile_colors(
    user_dir: Path,
    profile_name: str,
    colors: tuple[str, ...] | str,
) -> bool:
    """Repair only an obvious white placeholder in a managed U1FA profile.

    Orca can cache a newly-created profile while the Spoolman sync is
    completing.  In that case it leaves the default swatch as ``#FFFFFF``
    even though Spoolman contains the real (possibly multicolor) values.
    We only touch profiles that have U1FA's normal profile identity fields and
    only when the current colour is missing/white, preserving intentional
    edits to an existing profile.
    """
    if isinstance(colors, str):
        normalized = (colors,) if colors else ()
    else:
        normalized = tuple(colors)
    desired = [f"#{value}" for value in normalized if value]
    if not desired:
        return False
    path = user_dir / f"{safe_filename(profile_name)}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    if payload.get("name") != profile_name:
        return False
    setting_id = payload.get("filament_settings_id")
    if setting_id not in ([profile_name], (profile_name,)):
        return False
    current = payload.get("default_filament_colour")
    if isinstance(current, str):
        current_values = [current]
    elif isinstance(current, (list, tuple)):
        current_values = list(current)
    else:
        current_values = []
    normalized_current = [str(value).upper() for value in current_values]
    if normalized_current not in ([], ["#FFFFFF"]):
        return False
    payload["default_filament_colour"] = desired
    payload["filament_colour"] = desired
    path.write_text(
        json.dumps(payload, indent=4, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return True


def migrate_legacy_profile_identity(
    user_dir: Path,
    system_dir: Path,
    profile_name: str,
    base: str,
    vendor: str,
    colors: tuple[str, ...] | str,
) -> tuple[bool, str]:
    """Safely migrate one recognizable pre-1.8.1 U1FA profile.

    U1FA 1.8.0 created lightweight user presets which inherited the Snapmaker
    system preset.  Snapmaker's sender can then ignore the real Spoolman vendor
    and fail automatic filament matching.  This migration materializes the
    current Snapmaker base exactly like a new 1.8.1 profile, then overlays all
    non-identity values from the existing user profile so calibrated PA,
    Adaptive PA, temperatures, volumetric limits and other intentional edits
    are preserved.

    Only an exact U1FA-style profile identity is eligible.  A byte-for-byte
    backup is written before the atomic replacement.  Already-correct 1.8.1
    profiles are left untouched.
    """
    path = user_dir / f"{safe_filename(profile_name)}.json"
    try:
        original_bytes = path.read_bytes()
        payload = json.loads(original_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False, ""
    if not isinstance(payload, dict):
        return False, ""
    if payload.get("name") != profile_name:
        return False, ""
    setting_id = payload.get("filament_settings_id")
    if setting_id not in ([profile_name], (profile_name,)):
        return False, ""
    if payload.get("from") not in (None, "User"):
        return False, ""

    base_file = base_profile_path(system_dir, base)
    fresh = _build_profile_payload(
        base_file,
        base,
        profile_name,
        vendor,
        colors,
        _base_version(base_file),
    )

    current_vendor = payload.get("filament_vendor")
    current_filament_id = payload.get("filament_id")
    current_filament_type = payload.get("filament_type")
    already_detached = not (
        isinstance(payload.get("inherits"), str)
        and payload.get("inherits", "").strip()
    )
    if (
        already_detached
        and current_vendor == fresh.get("filament_vendor")
        and current_filament_id == fresh.get("filament_id")
        and current_filament_type == fresh.get("filament_type")
        and "setting_id" not in payload
        and "instantiation" not in payload
    ):
        return False, ""

    # Start from the fully materialized current Snapmaker base.  Existing user
    # values win for everything except identity fields that caused the bug.
    migrated = dict(fresh)
    identity_fields = {
        "inherits",
        "setting_id",
        "instantiation",
        "type",
        "name",
        "from",
        "filament_id",
        "filament_settings_id",
        "filament_vendor",
        "filament_type",
        "is_custom_defined",
        "version",
        "default_filament_colour",
        "filament_colour",
    }
    for key, value in payload.items():
        if key not in identity_fields:
            migrated[key] = value

    # Preserve a deliberate non-white colour edit.  Missing/white placeholders
    # are replaced with the real Spoolman colour(s) from the fresh payload.
    current = payload.get("default_filament_colour")
    if isinstance(current, str):
        current_values = [current]
    elif isinstance(current, (list, tuple)):
        current_values = [str(value) for value in current]
    else:
        current_values = []
    normalized_current = [value.upper() for value in current_values]
    if current_values and normalized_current != ["#FFFFFF"]:
        migrated["default_filament_colour"] = current_values
        existing_filament_colour = payload.get("filament_colour")
        if isinstance(existing_filament_colour, str):
            migrated["filament_colour"] = [existing_filament_colour]
        elif isinstance(existing_filament_colour, (list, tuple)):
            migrated["filament_colour"] = [
                str(value) for value in existing_filament_colour
            ]
        else:
            migrated["filament_colour"] = current_values

    serialized = json.dumps(migrated, indent=4, ensure_ascii=False) + "\n"
    json.loads(serialized)
    new_bytes = serialized.encode("utf-8")
    if new_bytes == original_bytes:
        return False, ""

    backup_path = path.with_name(f"{path.name}.u1fa-pre181.bak")
    temporary_path = path.with_name(f"{path.name}.u1fa-181.tmp")

    # Keep exactly one pre-1.8.1 recovery copy per profile.  Exclusive create
    # prevents both accidental overwrite and backup accumulation on a retry
    # after an interrupted migration.
    try:
        with backup_path.open("xb") as handle:
            handle.write(original_bytes)
    except FileExistsError:
        pass
    try:
        temporary_path.write_bytes(new_bytes)
        temporary_path.replace(path)
    except Exception:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    return True, backup_path.name


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
    vendor: str,
    color: tuple[str, ...] | str,
) -> None:
    base_file = base_profile_path(system_dir, base)
    filename = safe_filename(profile_name)
    json_path = user_dir / f"{filename}.json"
    info_path = user_dir / f"{filename}.info"
    payload = _build_profile_payload(
        base_file,
        base,
        profile_name,
        vendor,
        color,
        _base_version(base_file),
    )
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
    seen_spools: set[tuple[str, str, str, str, tuple[str, ...]]] = set()
    planned_names: set[str] = set()

    for spool in inventory.spools:
        filament = _filament_for_spool(spool, inventory)
        vendor = _vendor_for_filament(filament, inventory)
        material = clean(filament.get("material"))
        name = clean(filament.get("name"))
        colors = _filament_colors(filament)
        color = colors[0] if colors else ""
        spool_id = spool.get("id")
        spool_ids = () if spool_id is None else (spool_id,)
        key = (vendor, material, name, color, colors)
        if key in seen_spools:
            continue
        seen_spools.add(key)

        if not vendor or not material or not name:
            actions.append(
                SyncAction("skipped", " ".join(key[:3]).strip(), None, color, spool_ids, "dati incompleti")
            )
            continue

        base = choose_base(vendor, material, name, multicolor=len(colors) >= 2)
        profile_name = make_profile_name(vendor, material, name)
        if selected is not None and profile_name.casefold() not in selected:
            continue
        if base is None:
            actions.append(
                SyncAction("skipped", profile_name, None, color, spool_ids, "nessuna base definita")
            )
            continue
        filename = safe_filename(profile_name)
        if profile_name.casefold() in ignored:
            # Managed names stay remembered so an intentionally deleted profile
            # is not recreated. Existing files must still receive migrations
            # when U1FA changes sender-facing identity rules.
            if not _profile_exists(user_dir, filename):
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

            migrated = False
            backup_name = ""
            migration_error = ""
            if apply:
                try:
                    migrated, backup_name = migrate_legacy_profile_identity(
                        user_dir,
                        effective_system_dir,
                        profile_name,
                        base,
                        vendor,
                        colors,
                    )
                except (OSError, ProfileMaterializationError) as exc:
                    migration_error = str(exc)

            color_repaired = (
                apply
                and not migrated
                and repair_profile_colors(user_dir, profile_name, colors)
            )
            repaired = migrated or color_repaired
            if migrated:
                message = (
                    "identità Orca/vendor/tipo materiale migrati senza perdere i valori del profilo; "
                    f"backup {backup_name}"
                )
            elif color_repaired:
                message = "colori predefiniti aggiornati"
            elif migration_error:
                message = f"profilo gestito; migrazione 1.8.1 non eseguita: {migration_error}"
            else:
                message = "già gestito"
            actions.append(
                SyncAction(
                    "repaired" if repaired else "existing",
                    profile_name,
                    base,
                    color,
                    spool_ids,
                    message,
                )
            )
            continue
        if not base_profile_path(effective_system_dir, base).is_file():
            actions.append(
                SyncAction("skipped", profile_name, base, color, spool_ids, "base Snapmaker non trovata")
            )
            continue

        if _profile_exists(user_dir, filename):
            migrated = False
            backup_name = ""
            migration_error = ""
            if apply:
                try:
                    migrated, backup_name = migrate_legacy_profile_identity(
                        user_dir,
                        effective_system_dir,
                        profile_name,
                        base,
                        vendor,
                        colors,
                    )
                except (OSError, ProfileMaterializationError) as exc:
                    migration_error = str(exc)

            color_repaired = (
                apply
                and not migrated
                and repair_profile_colors(user_dir, profile_name, colors)
            )
            repaired = migrated or color_repaired
            if migrated:
                message = (
                    "identità Orca/vendor/tipo materiale migrati senza perdere i valori del profilo; "
                    f"backup {backup_name}"
                )
            elif color_repaired:
                message = "colori predefiniti aggiornati"
            elif migration_error:
                message = f"profilo esistente; migrazione 1.8.1 non eseguita: {migration_error}"
            else:
                message = ""
            actions.append(SyncAction(
                "repaired" if repaired else "existing",
                profile_name,
                base,
                color,
                spool_ids,
                message,
            ))
            continue
        if filename.casefold() in planned_names:
            actions.append(
                SyncAction("merged", profile_name, base, color, spool_ids, "stesso profilo tecnico")
            )
            continue
        planned_names.add(filename.casefold())

        if apply:
            try:
                _write_new_profile(
                    user_dir,
                    effective_system_dir,
                    profile_name,
                    base,
                    vendor,
                    colors,
                )
            except FileExistsError:
                actions.append(SyncAction("existing", profile_name, base, color, spool_ids))
                continue
            except ProfileMaterializationError as exc:
                actions.append(
                    SyncAction(
                        "skipped",
                        profile_name,
                        base,
                        color,
                        spool_ids,
                        str(exc),
                    )
                )
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
