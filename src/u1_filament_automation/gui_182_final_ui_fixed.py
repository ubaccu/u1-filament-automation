"""Validated final-home wrapper for U1FA 1.8.2.

Keeps the established business logic untouched and applies the final visual
layout after the existing 1.8.2 home patches.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from . import gui_182_final_ui as ui

_HERO_RE = re.compile(
    rf'<section id="{re.escape(ui._HERO_ID)}"[^>]*>.*?</section>\s*',
    re.DOTALL,
)
_SETUP_RE = re.compile(
    rf'<section id="{re.escape(ui._SETUP_ID)}"[^>]*>.*?</section>\s*',
    re.DOTALL,
)
_COMMUNITY_RE = re.compile(
    rf'<section id="{re.escape(ui._COMMUNITY_ID)}"[^>]*>.*?</section>\s*',
    re.DOTALL,
)
_QUICK_RE = re.compile(
    r'<div class="u1fa-quick-grid">.*?</div>\s*',
    re.DOTALL,
)


def finalize_home(page: str, language: str = "it") -> str:
    """Apply only presentation/reordering; preserve every existing handler."""
    if f'id="{ui._STYLE_ID}"' not in page:
        page = page.replace("</head>", ui._CSS + "</head>", 1)
    if f'id="{ui._SIDEBAR_ID}"' not in page:
        page = page.replace("<body>", "<body>" + ui._sidebar(language), 1)

    page = _HERO_RE.sub(ui._hero(language), page, count=1)
    page = ui._decorate_status_cards(page)
    page, setup = ui._extract(page, _SETUP_RE)
    page, community = ui._extract(page, _COMMUNITY_RE)
    page, quick_grid = ui._extract(page, _QUICK_RE)
    quick = ui._decorate_quick_grid(quick_grid, language)

    page = re.sub(
        rf'(<details[^>]*id="{ui._FILAMENT_ID}"[^>]*?)\sopen(?=[\s>])',
        r'\1',
        page,
        count=1,
    )

    insert = setup + quick + community
    dash_start = page.find(f'id="{ui._DASHBOARD_ID}"')
    if dash_start >= 0:
        dash_end = page.find("</section>", dash_start)
        if dash_end >= 0:
            at = dash_end + len("</section>")
            page = page[:at] + insert + page[at:]
        else:
            page = page.replace("</main>", insert + "</main>", 1)
    else:
        page = page.replace("</main>", insert + "</main>", 1)
    return page


def install_182_final_ui_fixed(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._home
    if getattr(current, "_u1fa_182_final_ui_fixed", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        return finalize_home(page, language)

    setattr(patched, "_u1fa_182_final_ui_fixed", True)
    gui_module._home = patched
