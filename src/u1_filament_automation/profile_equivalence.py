from __future__ import annotations

import json
import re
from pathlib import Path


_TOKEN_RE = re.compile(r"[^\W_]+", flags=re.UNICODE)
# b24 intentionally limits equivalence to material families currently created
# by the desktop wizard. This keeps matching conservative and avoids merging
# genuinely different custom profiles.
_MATERIAL_TOKENS = frozenset({"pla", "petg"})


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(item.casefold() for item in _TOKEN_RE.findall(value))


def profile_names_equivalent(expected: str, existing: str) -> bool:
    """Return True for the narrow legacy duplicate pattern fixed in b24.

    Example considered equivalent:
      eSUN PLA ePLA-Lite Red @Snapmaker U1 (0.4 nozzle)
      eSUN ePLA-Lite Red @Snapmaker U1 (0.4 nozzle)

    We only accept a one-token difference where the extra token is PLA/PETG
    and the shorter name already embeds that material at a token edge (ePLA,
    ePETG, PolyPLA, ...). Arbitrary names that merely omit the material are
    not merged automatically.
    """
    left = _tokens(expected)
    right = _tokens(existing)
    if left == right:
        return True

    if len(left) == len(right) + 1:
        longer, shorter = left, right
    elif len(right) == len(left) + 1:
        longer, shorter = right, left
    else:
        return False

    for index, extra in enumerate(longer):
        if extra not in _MATERIAL_TOKENS:
            continue
        reduced = longer[:index] + longer[index + 1 :]
        if reduced != shorter:
            continue
        embedded = any(
            len(token) > len(extra)
            and (token.startswith(extra) or token.endswith(extra))
            for token in shorter
        )
        if embedded:
            return True
    return False


def equivalent_profile_paths(user_dir: Path, profile_name: str) -> tuple[Path, ...]:
    """Find valid non-symlink Orca JSON profiles equivalent to profile_name."""
    root = user_dir.expanduser().resolve()
    matches: list[Path] = []
    try:
        paths = list(root.glob("*.json"))
    except OSError:
        return ()

    for path in paths:
        if path.is_symlink() or not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        candidate = payload.get("name")
        if not isinstance(candidate, str):
            continue
        if profile_names_equivalent(profile_name, candidate):
            matches.append(path.resolve())

    return tuple(dict.fromkeys(matches))
