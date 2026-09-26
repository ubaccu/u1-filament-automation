"""U1FA b24 conservative Orca profile de-duplication patch."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Callable

from . import pa_profile as pa_profile_module
from . import sync as sync_module
from .profile_equivalence import equivalent_profile_paths, profile_names_equivalent


def _patch_sync_profile_exists() -> None:
    current = sync_module._profile_exists
    if getattr(current, "_u1fa_b24_equivalent_profiles", False):
        return

    def patched(user_dir: Path, filename: str) -> bool:
        if current(user_dir, filename):
            return True
        return bool(equivalent_profile_paths(user_dir, filename))

    setattr(patched, "_u1fa_b24_equivalent_profiles", True)
    sync_module._profile_exists = patched


def _patch_find_profile_path(gui_module: Any) -> None:
    current: Callable[[Path, str], Path] = pa_profile_module.find_profile_path
    if getattr(current, "_u1fa_b24_equivalent_profiles", False):
        gui_module.find_profile_path = current
        return

    def patched(user_dir: Path, profile_name: str) -> Path:
        try:
            return current(user_dir, profile_name)
        except pa_profile_module.PAProfileError as exc:
            # Only broaden a clean "not found" result. Safety/ambiguity/symlink
            # failures from the established resolver remain blocking.
            if not str(exc).startswith("Profilo Orca non trovato:"):
                raise
            matches = equivalent_profile_paths(user_dir, profile_name)
            if len(matches) == 1:
                match = matches[0]
                root = user_dir.expanduser().resolve()
                if match.parent != root:
                    raise pa_profile_module.PAProfileError(
                        "Il profilo equivalente esce dalla cartella autorizzata: scrittura bloccata"
                    )
                return match
            if len(matches) > 1:
                names = ", ".join(path.name for path in matches)
                raise pa_profile_module.PAProfileError(
                    f"Più profili Orca equivalenti corrispondono a {profile_name}: {names}. "
                    "Nessuna modifica eseguita."
                )
            raise

    setattr(patched, "_u1fa_b24_equivalent_profiles", True)
    pa_profile_module.find_profile_path = patched
    gui_module.find_profile_path = patched


def _patch_spool_created(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._spool_created
    if getattr(current, "_u1fa_b24_equivalent_notice", False):
        return

    def patched(receipt: Any, token: str, language: str = "it") -> str:
        page = current(receipt, token, language=language)
        expected = receipt.result.plan.profile_name
        actual_path = receipt.real_profile_path
        actual_name = actual_path.stem
        if (
            actual_name.casefold() != sync_module.safe_filename(expected).casefold()
            and profile_names_equivalent(expected, actual_name)
        ):
            if language == "en":
                note = (
                    "Equivalent Orca profile already present and reused: "
                    f"<strong>{html.escape(actual_name)}</strong>. No duplicate profile was created."
                )
            else:
                note = (
                    "Profilo Orca equivalente già presente e riutilizzato: "
                    f"<strong>{html.escape(actual_name)}</strong>. Nessun profilo duplicato è stato creato."
                )
            marker = f'<span class="muted">{html.escape(str(actual_path))}</span></p>'
            if marker in page:
                page = page.replace(marker, marker + f'<p class="ok">{note}</p>', 1)
        return page

    setattr(patched, "_u1fa_b24_equivalent_notice", True)
    gui_module._spool_created = patched


def _patch_new_spool_preview(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._new_spool_preview
    if getattr(current, "_u1fa_b24_equivalent_copy", False):
        return

    def patched(prepared: Any, token: str, language: str = "it") -> str:
        page = current(prepared, token, language=language)
        old_it = (
            "La conferma scrive in Spoolman e crea un solo nuovo profilo in Snapmaker Orca. "
            "Un profilo Orca già esistente non viene mai sovrascritto. Non invia ancora alcun comando alla stampante."
        )
        old_en = (
            "Confirmation writes to Spoolman and creates one new profile in Snapmaker Orca. "
            "An existing Orca profile is never overwritten. No command is sent to the printer yet."
        )
        new_it = (
            "La conferma scrive in Spoolman. Se il profilo Orca non esiste viene creato; "
            "se U1FA trova un unico profilo legacy equivalente lo riutilizza senza creare duplicati. "
            "Un profilo esistente non viene sovrascritto in questa fase. Non invia ancora alcun comando alla stampante."
        )
        new_en = (
            "Confirmation writes to Spoolman. If the Orca profile does not exist it is created; "
            "if U1FA finds one equivalent legacy profile it reuses it without creating a duplicate. "
            "An existing profile is not overwritten at this stage. No command is sent to the printer yet."
        )
        page = page.replace(old_en if language == "en" else old_it, new_en if language == "en" else new_it, 1)
        return page

    setattr(patched, "_u1fa_b24_equivalent_copy", True)
    gui_module._new_spool_preview = patched


def install_b24_patch(gui_module: Any) -> None:
    """Install b24 de-duplication without touching U1, Spoolman or Orca on import."""
    _patch_sync_profile_exists()
    _patch_find_profile_path(gui_module)
    _patch_spool_created(gui_module)
    _patch_new_spool_preview(gui_module)
