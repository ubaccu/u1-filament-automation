from __future__ import annotations

from typing import Any, Callable


_MIXED_SEARCH_PLACEHOLDER = "Cerca filamento / Search filament…"
_MIXED_EMPTY_MESSAGE = "Nessun filamento trovato / No filament found"


def localize_picker_search(page: str, language: str = "it") -> str:
    """Localize the legacy searchable calibration picker without changing its UI logic."""
    if language == "en":
        search_placeholder = "Search filament…"
        empty_message = "No filament found"
    else:
        search_placeholder = "Cerca filamento…"
        empty_message = "Nessun filamento trovato"

    return page.replace(
        _MIXED_SEARCH_PLACEHOLDER,
        search_placeholder,
    ).replace(
        _MIXED_EMPTY_MESSAGE,
        empty_message,
    )


def install_picker_language_206(gui_module: Any) -> None:
    """Apply the 2.0.6 picker-language hotfix after the existing UI patches."""
    current: Callable[..., str] | None = getattr(gui_module, "_home", None)
    if not callable(current) or getattr(current, "_u1fa_picker_language_206", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        return localize_picker_search(page, language)

    setattr(patched, "_u1fa_picker_language_206", True)
    gui_module._home = patched
