"""Last-stage sidebar repair for the 1.8.2 final home."""

from __future__ import annotations

import re
from typing import Any, Callable

_FILAMENT_ID = "u1fa-filament-group"
_STYLE_ID = "u1fa-182-nav-repair"


def _icon() -> str:
    return (
        '<svg viewBox="0 0 24 24" aria-hidden="true">'
        '<circle cx="9" cy="12" r="5.7"/><circle cx="9" cy="12" r="1.8"/>'
        '<path d="M4.6 9h8.8M4.6 15h8.8M16.5 7.5v9M13.5 12h6"/>'
        '</svg>'
    )


def repair_sidebar(page: str, language: str = "it") -> str:
    combined = "Filaments &amp; PA" if language == "en" else "Filamenti &amp; PA"
    system = "System" if language == "en" else "Sistema"
    if f"<span>{combined}</span>" in page:
        return page
    link = (
        f'<a class="u1fa-nav-pa" href="#{_FILAMENT_ID}" data-u1fa-jump="{_FILAMENT_ID}">'
        f'{_icon()}<span>{combined}</span></a>'
    )
    pattern = re.compile(
        rf'(<a[^>]*>\s*<svg(?:(?!</a>).)*?</svg>\s*<span>{re.escape(system)}</span>\s*</a>)',
        re.DOTALL,
    )
    page, count = pattern.subn(lambda m: link + m.group(1), page, count=1)
    if count == 0:
        page = page.replace('</nav>', link + '</nav>', 1)
    if f'id="{_STYLE_ID}"' not in page:
        page = page.replace(
            '</head>',
            f'<style id="{_STYLE_ID}">.u1fa-side-nav .u1fa-nav-pa span{{white-space:nowrap}}</style></head>',
            1,
        )
    return page


def install_182_nav_repair(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._home
    if getattr(current, "_u1fa_182_nav_repair", False):
        return

    def patched(controller: Any, token: str, error: str = "", language: str = "it") -> str:
        return repair_sidebar(current(controller, token, error=error, language=language), language)

    setattr(patched, "_u1fa_182_nav_repair", True)
    gui_module._home = patched
