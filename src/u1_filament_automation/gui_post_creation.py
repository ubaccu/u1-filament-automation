"""Post-creation UI helpers for U1FA 1.8.2.

Adds an explicit way to return to the dashboard after creating a spool without
starting the Adaptive PA flow immediately. This is UI-only: no printer command
is sent and the created Spoolman/Orca data is left untouched.
"""

from __future__ import annotations

from typing import Any, Callable


def install_post_creation_ui_patch(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._spool_created
    if getattr(current, "_u1fa_defer_pa", False):
        return

    def patched(receipt: Any, token: str, language: str = "it") -> str:
        page = current(receipt, token, language=language)
        primary = (
            "Check and show PA commands"
            if language == "en"
            else "Controlla e mostra i comandi PA"
        )
        secondary = (
            "Defer and calibrate later"
            if language == "en"
            else "Sospendi e calibra successivamente"
        )
        old = f'<p><button type="submit">{primary}</button></p></form>'
        new = (
            f'<p><button type="submit">{primary}</button> '
            f'<a class="button secondary" href="/">{secondary}</a></p></form>'
        )
        return page.replace(old, new, 1)

    setattr(patched, "_u1fa_defer_pa", True)
    gui_module._spool_created = patched
