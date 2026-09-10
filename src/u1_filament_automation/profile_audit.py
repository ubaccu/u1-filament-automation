from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .models import ProfileComparison, ProfilePreview


MAX_PROFILE_BYTES = 2 * 1024 * 1024
NOZZLE_SUFFIX = re.compile(
    r"\s*@\s*(?:snapmaker\s+)?u1\s*\(?\s*\d+(?:[.,]\d+)?\s+nozzle\s*\)?\s*$",
    flags=re.IGNORECASE,
)


def normalize_profile_name(value: str) -> str:
    # Il segno + fa parte del materiale: PLA e PLA+ non sono equivalenti.
    return " ".join(re.findall(r"[^\W_]+\+?", value.casefold(), flags=re.UNICODE))


def _token_signature(value: str) -> tuple[str, ...]:
    return tuple(sorted(normalize_profile_name(value).split()))


def _core_tokens(value: str) -> tuple[str, ...]:
    without_suffix = NOZZLE_SUFFIX.sub("", value)
    return tuple(normalize_profile_name(without_suffix).split())


def _token_similarity(left: tuple[str, ...], right: tuple[str, ...]) -> float:
    if not left or not right:
        return 0.0
    shared = sum((Counter(left) & Counter(right)).values())
    return (2.0 * shared) / (len(left) + len(right))


def _identity_values(payload: Any) -> Iterable[str]:
    if not isinstance(payload, dict):
        return
    for key in ("name", "filament_settings_id"):
        value = payload.get(key)
        if isinstance(value, str):
            yield value
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    yield item


def scan_profile_names(directories: Iterable[Path]) -> tuple[set[str], list[str]]:
    names: set[str] = set()
    warnings: list[str] = []
    for directory in directories:
        try:
            files = sorted(directory.rglob("*.json"))
        except OSError as exc:
            warnings.append(f"Impossibile elencare {directory}: {exc}")
            continue
        for path in files:
            if not path.is_file():
                continue
            names.add(path.stem)
            try:
                if path.stat().st_size > MAX_PROFILE_BYTES:
                    warnings.append(f"Profilo ignorato perché troppo grande: {path.name}")
                    continue
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                warnings.append(f"Profilo non leggibile {path.name}: {exc}")
                continue
            names.update(_identity_values(payload))
    return names, warnings


def compare_previews(
    previews: Iterable[ProfilePreview],
    existing_names: Iterable[str],
    similarity_threshold: float = 0.88,
) -> list[ProfileComparison]:
    by_normalized: dict[str, list[str]] = {}
    for name in existing_names:
        normalized = normalize_profile_name(name)
        if normalized:
            by_normalized.setdefault(normalized, []).append(name)

    comparisons: list[ProfileComparison] = []
    for preview in previews:
        target_normalized = normalize_profile_name(preview.nozzle_profile)
        exact = tuple(sorted(set(by_normalized.get(target_normalized, []))))
        target_signature = _token_signature(preview.nozzle_profile)
        equivalent: tuple[str, ...] = ()
        if not exact:
            equivalent = tuple(
                sorted(
                    {
                        original
                        for normalized, original_names in by_normalized.items()
                        if normalized != target_normalized
                        and _token_signature(normalized) == target_signature
                        for original in original_names
                    },
                    key=str.casefold,
                )
            )

        scored: list[tuple[float, str]] = []
        if not exact and not equivalent:
            target_core = _core_tokens(preview.nozzle_profile)
            for normalized, original_names in by_normalized.items():
                score = _token_similarity(target_core, _core_tokens(normalized))
                if score >= similarity_threshold:
                    for original in original_names:
                        scored.append((score, original))

        similar: tuple[str, ...] = ()
        if scored:
            best_score = max(score for score, _ in scored)
            similar = tuple(
                sorted(
                    {
                        name
                        for score, name in scored
                        if best_score - score <= 0.02
                    },
                    key=str.casefold,
                )
            )

        if exact:
            status = "existing"
        elif equivalent:
            status = "equivalent"
        elif len(similar) > 1:
            status = "ambiguous"
        elif similar:
            status = "similar"
        else:
            status = "missing"
        comparisons.append(
            ProfileComparison(
                target=preview.nozzle_profile,
                status=status,
                exact_matches=exact,
                equivalent_matches=equivalent,
                similar_matches=similar,
            )
        )
    return comparisons
