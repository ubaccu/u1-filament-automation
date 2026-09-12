from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# Area of the extrusion line used by U1FA AutoPA Mod (mm2).  The same
# constant is used by the printer macro when it reports volumetric flow.
PA_LINE_AREA_MM2 = 0.081416
U1_MAX_CALIBRATION_SPEED = 336


class EnvelopeError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedVolumetricSpeed:
    value: float
    profile_name: str
    path: Path


@dataclass(frozen=True)
class AutomaticEnvelope:
    low_speed: int
    mid_speed: int
    high_speed: int
    max_speed_from_flow: int
    limiting_source: str
    weak_signal_warning: bool

    def flow_at(self, speed: int) -> float:
        return speed * PA_LINE_AREA_MM2


def _positive_number(value: Any) -> float | None:
    values = value if isinstance(value, list) else [value]
    parsed: list[float] = []
    for item in values:
        try:
            number = float(item)
        except (TypeError, ValueError, OverflowError):
            continue
        if math.isfinite(number) and number > 0:
            parsed.append(number)
    # If a profile unexpectedly contains multiple values, the lowest one is
    # the conservative choice.
    return min(parsed) if parsed else None


def _safe_profile_path(root: Path, profile_name: str) -> Path | None:
    root = root.expanduser().resolve()
    if not profile_name or Path(profile_name).name != profile_name:
        return None
    candidate = (root / f"{profile_name}.json").resolve()
    if candidate.parent != root or not candidate.is_file():
        return None
    return candidate


def _named_profile_path(root: Path, profile_name: str) -> Path | None:
    direct = _safe_profile_path(root, profile_name)
    if direct is not None:
        return direct
    root = root.expanduser().resolve()
    if not root.is_dir():
        return None
    for candidate in root.glob("*.json"):
        resolved = candidate.resolve()
        if resolved.parent != root or not resolved.is_file():
            continue
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if str(payload.get("name", "")).strip().casefold() == profile_name.casefold():
            return resolved
    return None


def resolve_max_volumetric_speed(
    profile_path: Path,
    user_dir: Path,
    system_dir: Path,
) -> ResolvedVolumetricSpeed | None:
    """Resolve Orca's inherited filament_max_volumetric_speed safely."""

    user_root = user_dir.expanduser().resolve()
    system_root = system_dir.expanduser().resolve()
    current = profile_path.expanduser().resolve()
    if current.parent not in {user_root, system_root} or not current.is_file():
        raise EnvelopeError("Il profilo Orca non appartiene a una cartella autorizzata")

    visited: set[Path] = set()
    for _ in range(24):
        if current in visited:
            raise EnvelopeError("Ciclo rilevato nell'ereditarietà dei profili Orca")
        visited.add(current)
        try:
            payload = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise EnvelopeError(f"Profilo Orca non leggibile: {current.name}: {exc}") from exc
        if not isinstance(payload, dict):
            raise EnvelopeError(f"Profilo Orca non valido: {current.name}")

        value = _positive_number(payload.get("filament_max_volumetric_speed"))
        if value is not None:
            return ResolvedVolumetricSpeed(
                value=value,
                profile_name=str(payload.get("name") or current.stem),
                path=current,
            )

        inherited = str(payload.get("inherits") or "").strip()
        if not inherited:
            return None
        next_path = _named_profile_path(user_root, inherited)
        if next_path is None:
            next_path = _named_profile_path(system_root, inherited)
        if next_path is None:
            return None
        current = next_path

    raise EnvelopeError("Catena di ereditarietà Orca troppo lunga")


def calculate_automatic_envelope(
    max_volumetric_speed: float,
    manufacturer_min_speed: float | None = None,
    manufacturer_max_speed: float | None = None,
) -> AutomaticEnvelope:
    """Build a conservative three-point envelope from real filament limits."""

    if not math.isfinite(max_volumetric_speed) or not 0 < max_volumetric_speed <= 100:
        raise EnvelopeError("Il flusso volumetrico massimo deve essere tra 0 e 100 mm3/s")
    for label, value in (
        ("minima", manufacturer_min_speed),
        ("massima", manufacturer_max_speed),
    ):
        if value is not None and (not math.isfinite(value) or not 0 < value <= 1000):
            raise EnvelopeError(
                f"La velocità {label} del produttore deve essere tra 0 e 1000 mm/s"
            )
    if (
        manufacturer_min_speed is not None
        and manufacturer_max_speed is not None
        and manufacturer_min_speed >= manufacturer_max_speed
    ):
        raise EnvelopeError(
            "La velocità minima del produttore deve essere inferiore alla massima"
        )

    max_from_flow = math.floor(max_volumetric_speed / PA_LINE_AREA_MM2)
    limits = [(U1_MAX_CALIBRATION_SPEED, "machine")]
    limits.append((max_from_flow, "volumetric_flow"))
    if manufacturer_max_speed is not None:
        limits.append((math.floor(manufacturer_max_speed), "manufacturer"))
    high, limiting_source = min(limits, key=lambda item: item[0])

    if manufacturer_min_speed is not None:
        low = math.ceil(manufacturer_min_speed)
    else:
        low = max(30, min(100, high // 2))
    if high - low < 2:
        raise EnvelopeError(
            "I limiti scelti non lasciano spazio per tre velocità di calibrazione distinte"
        )
    mid = (low + high) // 2
    if not low < mid < high:
        raise EnvelopeError("Impossibile costruire un envelope crescente dai limiti scelti")

    return AutomaticEnvelope(
        low_speed=low,
        mid_speed=mid,
        high_speed=high,
        max_speed_from_flow=max_from_flow,
        limiting_source=limiting_source,
        weak_signal_warning=high < 100,
    )
