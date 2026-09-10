from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_SPECIAL_FAST = ("snapspeed", "high speed", "rapid", "hyper")
_SPECIAL_TRANSLUCENT = ("translucent", "transparent", "clear")


@dataclass(frozen=True)
class ProfileRecommendation:
    """Read-only recommendation based on Snapmaker profiles already installed.

    ``suggested_profile`` is informational in b22: callers must not silently
    replace the validated base profile with this value.
    """

    expected_profile: str
    suggested_profile: str | None
    confidence: str
    candidates: tuple[str, ...] = ()

    @property
    def is_exact(self) -> bool:
        return self.confidence == "exact"


def _normalized(value: str) -> str:
    text = value.casefold().replace("_", " ").replace("-", " ")
    return " ".join(re.findall(r"[a-z0-9.]+", text))


def _tokens(value: str) -> set[str]:
    return set(_normalized(value).split())


def _material_family(value: str) -> str:
    tokens = _tokens(value)
    if "petg" in tokens:
        return "petg"
    if "pla" in tokens:
        return "pla"
    return ""


def _subtype(value: str) -> str:
    normalized = _normalized(value)
    tokens = set(normalized.split())
    if "cf" in tokens or "carbon fiber" in normalized or "carbon fibre" in normalized:
        return "cf"
    if "silk" in tokens:
        return "silk"
    if "wood" in tokens:
        return "wood"
    if any(marker in normalized for marker in _SPECIAL_TRANSLUCENT):
        return "translucent"
    if (
        any(marker in normalized for marker in _SPECIAL_FAST)
        or "hf" in tokens
        or "hs" in tokens
    ):
        return "fast"
    return "basic"


def installed_snapmaker_profiles(system_dir: Path) -> tuple[str, ...]:
    """Return JSON profile stems without modifying or parsing Orca files."""
    try:
        profiles = {
            path.stem
            for path in system_dir.expanduser().resolve().glob("*.json")
            if path.is_file()
        }
    except OSError:
        return ()
    return tuple(sorted(profiles, key=str.casefold))


def _exact_alias(profile: str, expected: str) -> bool:
    if profile.casefold() == expected.casefold():
        return True
    # Snapmaker has shipped the PLA Silk profile both with and without @U1.
    silk_aliases = {
        "snapmaker pla silk",
        "snapmaker pla silk @u1",
    }
    return profile.casefold() in silk_aliases and expected.casefold() in silk_aliases


def _score_candidate(profile: str, expected: str) -> int:
    wanted_family = _material_family(expected)
    wanted_subtype = _subtype(expected)
    family = _material_family(profile)
    subtype = _subtype(profile)
    if not wanted_family or family != wanted_family:
        return -1000

    normalized = _normalized(profile)
    tokens = set(normalized.split())
    score = 35
    if subtype == wanted_subtype:
        score += 45
    else:
        score -= 55

    if wanted_subtype == "basic" and "basic" in tokens:
        score += 12
    if wanted_subtype == "fast" and "snapspeed" in normalized:
        score += 12
    if "snapmaker" in tokens:
        score += 8
    if "u1" in tokens:
        score += 6
    if "0.4" in tokens or "nozzle" in tokens:
        score += 2
    return score


def recommend_installed_profile(
    system_dir: Path,
    expected_profile: str,
) -> ProfileRecommendation:
    """Suggest the closest installed Snapmaker base profile, read-only.

    Confidence levels:
    - ``exact``: the expected profile (or a known naming alias) is installed;
    - ``smart``: one strong, unambiguous profile matches family and subtype;
    - ``ambiguous``: multiple plausible profiles are too close to choose safely;
    - ``unavailable``: no sufficiently compatible installed profile was found.
    """
    expected = expected_profile.strip()
    if not expected:
        return ProfileRecommendation("", None, "unavailable")

    profiles = installed_snapmaker_profiles(system_dir)
    for profile in profiles:
        if _exact_alias(profile, expected):
            return ProfileRecommendation(expected, profile, "exact", (profile,))

    ranked = sorted(
        (
            (_score_candidate(profile, expected), profile)
            for profile in profiles
        ),
        key=lambda item: (-item[0], item[1].casefold()),
    )
    plausible = [(score, profile) for score, profile in ranked if score >= 70]
    if not plausible:
        return ProfileRecommendation(expected, None, "unavailable")

    top_score, top_profile = plausible[0]
    alternatives = tuple(profile for _, profile in plausible[:3])
    if len(plausible) > 1 and top_score - plausible[1][0] < 8:
        return ProfileRecommendation(expected, None, "ambiguous", alternatives)
    return ProfileRecommendation(expected, top_profile, "smart", alternatives)
