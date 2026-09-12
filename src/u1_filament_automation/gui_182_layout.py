"""Final 1.8.2 home layout fixes.

The deletion feature is installed before the compact dashboard is created. This
small last-stage patch moves its card into the visible Filament management
section so it cannot end up under Safety and application because of wrapper
ordering.
"""

from __future__ import annotations

import re
from typing import Any, Callable


_DELETE_CARD_RE = re.compile(
    r'<!-- u1fa-filament-delete --><div class="card"><h2>.*?</div>\s*',
    re.DOTALL,
)


def install_182_layout_patch(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._home
    if getattr(current, "_u1fa_182_layout", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        match = _DELETE_CARD_RE.search(page)
        if match is None:
            return page
        card = match.group(0)
        page = page[: match.start()] + page[match.end() :]
        marker = (
            '<details id="u1fa-filament-group" class="u1fa-home-group" open>'
        )
        start = page.find(marker)
        if start < 0:
            return page.replace("</main>", card + "</main>", 1)
        body_marker = '<div class="u1fa-home-group-body">'
        body_start = page.find(body_marker, start)
        if body_start < 0:
            return page.replace("</main>", card + "</main>", 1)
        insert_at = body_start + len(body_marker)
        return page[:insert_at] + card + page[insert_at:]

    setattr(patched, "_u1fa_182_layout", True)
    gui_module._home = patched
