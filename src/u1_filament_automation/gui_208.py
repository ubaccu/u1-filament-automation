"""U1FA 2.0.8 desktop UX patch.

Adds the official Discord community shortcut and turns the mandatory per-session
printer compatibility gate into an explicit guided action instead of leaving a
generic calibration error on the page. Presentation only: no printer, Spoolman
or Orca write logic is changed here.
"""

from __future__ import annotations

import html
from typing import Any, Callable

_DISCORD_URL = "https://discord.gg/VVf7ubPdAT"
_STYLE_ID = "u1fa-208-ux"
_NOTICE_ID = "u1fa-208-printer-check"

_CHECK_ERRORS = (
    "Compatibilità firmware non verificata in questa sessione",
    "Firmware compatibility has not been verified in this session",
)


def _discord_icon() -> str:
    return (
        '<svg viewBox="0 0 24 24" aria-hidden="true">'
        '<path d="M7.1 7.2c3.2-1.5 6.6-1.5 9.8 0 1.3 2 2.1 4.1 2.3 6.4'
        '-1.3 1.8-2.9 2.9-4.7 3.5l-1.1-1.5c.8-.2 1.5-.6 2.2-1'
        '-2.3 1.1-4.9 1.1-7.2 0 .7.4 1.4.8 2.2 1l-1.1 1.5'
        'c-1.8-.6-3.4-1.7-4.7-3.5.2-2.3 1-4.4 2.3-6.4z"/>'
        '<circle cx="9.3" cy="12.1" r=".9"/><circle cx="14.7" cy="12.1" r=".9"/>'
        '</svg>'
    )


_CSS = f"""<style id="{_STYLE_ID}">
.u1fa-side-discord{{display:flex;align-items:center;justify-content:center;gap:8px;margin:0 4px 10px;padding:10px;border-radius:11px;background:#5865f2;color:#fff!important;text-decoration:none!important;font-size:12px;font-weight:900;box-shadow:0 8px 22px rgba(88,101,242,.18);transition:.17s ease}}
.u1fa-side-discord:hover{{transform:translateY(-2px);box-shadow:0 12px 28px rgba(88,101,242,.28)}}
.u1fa-side-discord svg{{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}}
.u1fa-discord-community{{border-color:#5865f2!important;background:#202969!important;color:#fff!important}}
.u1fa-discord-community:hover{{border-color:#7c86ff!important;background:#293587!important}}
.u1fa-discord-community svg{{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round;margin-right:7px}}
.u1fa-208-check{{background:#2a2114;border:1px solid #b9872f;border-radius:14px;padding:18px 20px;margin:14px 0 18px;box-shadow:0 12px 28px rgba(0,0,0,.16)}}
.u1fa-208-check strong{{display:block;color:#ffd166;font-size:18px;margin-bottom:7px}}
.u1fa-208-check p{{margin:6px 0 13px;color:#e5e8ed}}
.u1fa-208-check .button{{margin-right:8px}}
@media(max-width:680px){{.u1fa-side-discord{{margin:0 8px 10px}}}}
</style>"""


def _requires_printer_check(error: str) -> bool:
    value = str(error or "")
    return any(marker in value for marker in _CHECK_ERRORS)


def _printer_check_notice(language: str) -> str:
    if language == "en":
        title = "⚠️ Printer check required before calibration"
        text = (
            "For safety, U1FA must verify the U1 firmware and AutoPA Mod once per app "
            "session before the first calibration. No calibration command was sent."
        )
        button = "Check now"
    else:
        title = "⚠️ Controllo U1 richiesto prima della calibrazione"
        text = (
            "Per sicurezza U1FA deve verificare firmware e AutoPA Mod una volta a ogni "
            "avvio dell'app, prima della prima calibrazione. Non è stato inviato alcun "
            "comando di calibrazione."
        )
        button = "Controlla ora"
    return (
        f'<section id="{_NOTICE_ID}" class="u1fa-208-check">'
        f'<strong>{html.escape(title)}</strong>'
        f'<p>{html.escape(text)}</p>'
        f'<a class="button danger" href="/printer-setup">{html.escape(button)}</a>'
        '</section>'
    )


def _strip_generic_error(page: str, error: str) -> str:
    if not error:
        return page
    escaped = html.escape(error)
    return page.replace(f'<p class="warn">{escaped}</p>', "", 1)


def _add_discord(page: str, language: str) -> str:
    label = "U1FA Discord" if language == "en" else "Discord U1FA"
    if "u1fa-discord-community" not in page:
        community_link = (
            f'<a class="u1fa-social-btn u1fa-discord-community" href="{_DISCORD_URL}" '
            'target="_blank" rel="noopener noreferrer" title="Community Discord U1FA">'
            f'{_discord_icon()}<span>{html.escape(label)}</span></a>'
        )
        community_close = '</div></section>'
        community_pos = page.find('id="u1fa-community-182"')
        if community_pos >= 0:
            close_pos = page.find(community_close, community_pos)
            if close_pos >= 0:
                page = page[:close_pos] + community_link + page[close_pos:]

    if "u1fa-side-discord" not in page:
        side_link = (
            f'<a class="u1fa-side-discord" href="{_DISCORD_URL}" '
            'target="_blank" rel="noopener noreferrer" title="Community Discord U1FA">'
            f'{_discord_icon()}<span>{html.escape(label)}</span></a>'
        )
        coffee_marker = '<a class="u1fa-side-coffee"'
        coffee_pos = page.find(coffee_marker)
        if coffee_pos >= 0:
            end = page.find("</a>", coffee_pos)
            if end >= 0:
                end += len("</a>")
                page = page[:end] + side_link + page[end:]
        else:
            language_marker = '<div class="u1fa-side-language">'
            if language_marker in page:
                page = page.replace(language_marker, side_link + language_marker, 1)
    return page


def _decorate_home(page: str, error: str, language: str) -> str:
    page = _add_discord(page, language)
    if f'id="{_STYLE_ID}"' not in page:
        page = page.replace("</head>", _CSS + "</head>", 1)
    if _requires_printer_check(error) and f'id="{_NOTICE_ID}"' not in page:
        page = _strip_generic_error(page, error)
        notice = _printer_check_notice(language)
        marker = '<section id="u1fa-dashboard-v20"'
        if marker in page:
            page = page.replace(marker, notice + marker, 1)
        else:
            page = page.replace("<main>", "<main>" + notice, 1)
    return page


def _decorate_batch(page: str, error: str, language: str) -> str:
    if f'id="{_STYLE_ID}"' not in page:
        page = page.replace("</head>", _CSS + "</head>", 1)
    if _requires_printer_check(error) and f'id="{_NOTICE_ID}"' not in page:
        page = _strip_generic_error(page, error)
        notice = _printer_check_notice(language)
        if "<h1>" in page:
            close = page.find("</h1>")
            page = page[: close + 5] + notice + page[close + 5 :]
        else:
            page = page.replace("<main>", "<main>" + notice, 1)
    return page


def install_208_ux_patch(gui_module: Any) -> None:
    current_home: Callable[..., str] = gui_module._home
    if not getattr(current_home, "_u1fa_208_ux", False):
        def home(
            controller: Any,
            token: str,
            error: str = "",
            language: str = "it",
        ) -> str:
            return _decorate_home(
                current_home(controller, token, error=error, language=language),
                error,
                language,
            )

        setattr(home, "_u1fa_208_ux", True)
        gui_module._home = home

    current_batch: Callable[..., str] = gui_module._batch_form
    if not getattr(current_batch, "_u1fa_208_ux", False):
        def batch(
            controller: Any,
            token: str,
            error: str = "",
            language: str = "it",
        ) -> str:
            return _decorate_batch(
                current_batch(controller, token, error=error, language=language),
                error,
                language,
            )

        setattr(batch, "_u1fa_208_ux", True)
        gui_module._batch_form = batch
