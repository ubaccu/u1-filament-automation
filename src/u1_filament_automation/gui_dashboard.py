"""Read-only compact dashboard and home-page organization for the desktop UI.

The dashboard derives its state only from configuration and controller snapshots
already owned by the GUI. Rendering it never contacts the printer and never
writes Spoolman, Orca or Adaptive PA data.
"""

from __future__ import annotations

import html
import re
from typing import Any, Callable


DASHBOARD_ID = "u1fa-dashboard-v19"
_DASHBOARD_STYLE_ID = "u1fa-dashboard-style-v19"
_HOME_GROUPS_ID = "u1fa-home-groups-v19"

_DASHBOARD_CSS = f"""
<style id="{_DASHBOARD_STYLE_ID}">
#{DASHBOARD_ID}{{margin:2px 0 18px}}
.u1fa-dash-head{{display:flex;justify-content:space-between;gap:16px;align-items:flex-start;margin-bottom:14px}}
.u1fa-dash-title{{font-size:24px;font-weight:800;line-height:1.15}}
.u1fa-dash-sub{{color:#aeb9c8;margin-top:5px}}
.u1fa-badge{{display:inline-flex;align-items:center;gap:7px;padding:7px 10px;border-radius:999px;background:#202a36;border:1px solid #354356;font-size:13px;font-weight:700;white-space:nowrap}}
.u1fa-dot{{width:9px;height:9px;border-radius:50%;display:inline-block;background:#7d8a99}}
.u1fa-dot.ok{{background:#55d98d}} .u1fa-dot.warn{{background:#ffd166}} .u1fa-dot.bad{{background:#ff7474}}
.u1fa-status-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}
.u1fa-status-card{{background:#151b23;border:1px solid #303a48;border-radius:14px;padding:15px;min-width:0}}
.u1fa-status-label{{font-size:12px;color:#91a0b4;text-transform:uppercase;letter-spacing:.06em;font-weight:800}}
.u1fa-status-value{{font-size:16px;font-weight:800;margin-top:7px}}
.u1fa-status-detail{{font-size:12px;color:#aeb9c8;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.u1fa-actions{{display:flex;flex-wrap:wrap;gap:9px;margin-top:14px}}
.u1fa-dash-foot{{margin:12px 2px 0;color:#8290a3;font-size:12px}}
.u1fa-home-group{{background:#171d26;border:1px solid #303a48;border-radius:14px;margin:14px 0;overflow:hidden}}
.u1fa-home-group>summary{{cursor:pointer;list-style:none;padding:16px 18px;font-size:18px;font-weight:800;user-select:none}}
.u1fa-home-group>summary::-webkit-details-marker{{display:none}}
.u1fa-home-group>summary::after{{content:'▸';float:right;color:#8fa0b5;transition:transform .15s ease}}
.u1fa-home-group[open]>summary::after{{transform:rotate(90deg)}}
.u1fa-home-group-body{{padding:0 14px 14px}}
.u1fa-home-group-body>.card{{margin:10px 0;background:#151b23}}
@media(max-width:900px){{.u1fa-status-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}
@media(max-width:620px){{.u1fa-dash-head{{display:block}}.u1fa-badge{{margin-top:10px}}.u1fa-status-grid{{grid-template-columns:1fr}}}}
</style>
"""


def _snapshot(controller: Any, method: str) -> Any | None:
    getter = getattr(controller, method, None)
    if not callable(getter):
        return None
    try:
        return getter()
    except (AttributeError, RuntimeError, ValueError, OSError):
        return None


def _job_status(controller: Any, language: str) -> tuple[str, str]:
    snapshot = _snapshot(controller, "snapshot")
    state = str(getattr(snapshot, "state", "idle") or "idle")
    if state in {"checking", "running", "recovering"}:
        return ("In corso" if language != "en" else "Running", "warn")
    if state == "completed":
        return ("Completata" if language != "en" else "Completed", "ok")
    if state in {"error", "blocked"}:
        return ("Attenzione" if language != "en" else "Attention", "bad")
    return ("Pronta" if language != "en" else "Ready", "ok")


def _update_status(controller: Any, language: str) -> tuple[str, str]:
    snapshot = _snapshot(controller, "update_snapshot")
    state = str(getattr(snapshot, "state", "idle") or "idle")
    if state == "available":
        return ("Aggiornamento disponibile" if language != "en" else "Update available", "warn")
    if state == "error":
        return ("Controllo non disponibile" if language != "en" else "Check unavailable", "bad")
    if state in {"checking", "downloading"}:
        return ("Controllo in corso" if language != "en" else "Checking", "warn")
    if state in {"current", "downloaded"}:
        return ("Aggiornata" if language != "en" else "Up to date", "ok")
    return ("Pronta" if language != "en" else "Ready", "ok")


def _card(label: str, value: str, detail: str, tone: str) -> str:
    return (
        '<div class="u1fa-status-card">'
        f'<div class="u1fa-status-label">{html.escape(label)}</div>'
        f'<div class="u1fa-status-value"><span class="u1fa-dot {tone}"></span> {html.escape(value)}</div>'
        f'<div class="u1fa-status-detail" title="{html.escape(detail)}">{html.escape(detail)}</div>'
        '</div>'
    )


def build_dashboard(controller: Any, language: str = "it") -> str:
    """Render the compact control center without network or write actions."""
    moonraker = str(getattr(controller, "moonraker_url", "") or "").strip()
    spoolman = str(getattr(controller, "spoolman_url", "") or "").strip()
    orca_dir = getattr(controller, "real_orca_dir", None)

    job_value, job_tone = _job_status(controller, language)
    update_value, update_tone = _update_status(controller, language)

    if language == "en":
        title = "U1FA Control Center"
        subtitle = "Quick status of the main U1FA services and functions."
        configured = "Endpoint configured"
        not_configured = "Needs setup"
        detected = "Profiles detected"
        not_detected = "Not detected"
        no_url = "No endpoint configured"
        orca_detail = str(orca_dir) if orca_dir else "Snapmaker Orca user profiles not detected"
        actions = (
            '<a class="button" href="/new-spool">＋ New spool</a>'
            '<a class="button secondary" href="#u1fa-filament-group">Calibration</a>'
            '<a class="button secondary" href="/connections">Connections</a>'
            '<a class="button secondary" href="/updates">U1FA updates</a>'
        )
        foot = "Read-only dashboard: opening this page sends no command to the Snapmaker U1."
    else:
        title = "U1FA Control Center"
        subtitle = "Stato rapido dei principali servizi e funzioni di U1FA."
        configured = "Endpoint configurato"
        not_configured = "Da configurare"
        detected = "Profili rilevati"
        not_detected = "Non rilevato"
        no_url = "Nessun endpoint configurato"
        orca_detail = str(orca_dir) if orca_dir else "Profili utente Snapmaker Orca non rilevati"
        actions = (
            '<a class="button" href="/new-spool">＋ Nuova bobina</a>'
            '<a class="button secondary" href="#u1fa-filament-group">Calibrazione</a>'
            '<a class="button secondary" href="/connections">Connessioni</a>'
            '<a class="button secondary" href="/updates">Aggiornamenti U1FA</a>'
        )
        foot = "Dashboard in sola lettura: aprire questa pagina non invia alcun comando alla Snapmaker U1."

    status_cards = "".join(
        (
            _card("U1 / Moonraker", configured if moonraker else not_configured, moonraker or no_url, "ok" if moonraker else "warn"),
            _card("Spoolman", configured if spoolman else not_configured, spoolman or no_url, "ok" if spoolman else "warn"),
            _card("Snapmaker Orca", detected if orca_dir else not_detected, orca_detail, "ok" if orca_dir else "warn"),
            _card("Adaptive PA", job_value, "Calibration controller" if language == "en" else "Controller calibrazione", job_tone),
        )
    )
    return (
        f'<section id="{DASHBOARD_ID}" class="card">'
        '<div class="u1fa-dash-head">'
        f'<div><div class="u1fa-dash-title">{html.escape(title)}</div>'
        f'<div class="u1fa-dash-sub">{html.escape(subtitle)}</div></div>'
        f'<div class="u1fa-badge"><span class="u1fa-dot {update_tone}"></span>{html.escape(update_value)}</div>'
        '</div>'
        f'<div class="u1fa-status-grid">{status_cards}</div>'
        f'<div class="u1fa-actions">{actions}</div>'
        f'<div class="u1fa-dash-foot">{html.escape(foot)}</div>'
        '</section>'
    )


def _remove_simple_legacy_card(page: str, heading: str) -> str:
    pattern = re.compile(
        r'<div class="card"><h2>' + re.escape(heading) + r'</h2>.*?</div>\s*',
        re.DOTALL,
    )
    return pattern.sub("", page, count=1)


def _group_legacy_home(page: str, language: str) -> str:
    """Collapse legacy home cards into three useful groups without changing actions."""
    if f'id="{_HOME_GROUPS_ID}"' in page:
        return page

    # The Control Center already exposes updates and connection access/status.
    for heading in (
        "Aggiornamenti U1FA",
        "U1FA updates",
        "Connessioni",
        "Connections",
        "Connessioni da configurare",
        "Connections need setup",
    ):
        page = _remove_simple_legacy_card(page, heading)

    page = page.replace("<h1>U1 Filament Automation</h1>\n", "", 1)
    for subtitle in (
        "Bobina Spoolman → profilo Snapmaker Orca → calibrazione Adaptive PA.",
        "Spoolman spool → Snapmaker Orca profile → Adaptive PA calibration.",
    ):
        page = page.replace(f'<p class="muted">{subtitle}</p>\n', "", 1)

    if language == "en":
        system_label = "System and maintenance"
        filament_label = "Filament management"
        safety_label = "Safety and application"
        config_marker = '<div class="card"><h2>0. Set up or restore U1FA AutoPA Mod</h2>'
        spool_marker = '<div class="card"><h2>1. New spool</h2>'
        protection_marker = '<div class="card"><p><strong>Active protection</strong></p>'
    else:
        system_label = "Sistema e manutenzione"
        filament_label = "Gestione filamenti"
        safety_label = "Sicurezza e applicazione"
        config_marker = '<div class="card"><h2>0. Configurazione o ripristino U1FA AutoPA Mod</h2>'
        spool_marker = '<div class="card"><h2>1. Nuova bobina</h2>'
        protection_marker = '<div class="card"><p><strong>Protezione attiva</strong></p>'

    system_open = (
        f'<span id="{_HOME_GROUPS_ID}" hidden></span>'
        f'<details class="u1fa-home-group"><summary>{html.escape(system_label)}</summary>'
        '<div class="u1fa-home-group-body">'
    )
    filament_open = (
        f'<details id="u1fa-filament-group" class="u1fa-home-group" open>'
        f'<summary>{html.escape(filament_label)}</summary><div class="u1fa-home-group-body">'
    )
    safety_open = (
        f'<details class="u1fa-home-group"><summary>{html.escape(safety_label)}</summary>'
        '<div class="u1fa-home-group-body">'
    )
    close_group = "</div></details>"

    grouped = False
    if config_marker in page and spool_marker in page:
        page = page.replace(config_marker, system_open + config_marker, 1)
        page = page.replace(spool_marker, close_group + filament_open + spool_marker, 1)
        grouped = True
    elif spool_marker in page:
        page = page.replace(spool_marker, f'<span id="{_HOME_GROUPS_ID}" hidden></span>' + filament_open + spool_marker, 1)
        grouped = True

    if grouped and protection_marker in page:
        page = page.replace(protection_marker, close_group + safety_open + protection_marker, 1)
        page = page.replace("</main>", close_group + "</main>", 1)
    elif grouped:
        page = page.replace("</main>", close_group + "</main>", 1)

    return page


def enhance_home_page(page: str, controller: Any, language: str = "it") -> str:
    if f'id="{DASHBOARD_ID}"' in page:
        return page
    if f'id="{_DASHBOARD_STYLE_ID}"' not in page:
        page = page.replace("</head>", _DASHBOARD_CSS + "</head>", 1)
    dashboard = build_dashboard(controller, language)
    if "<h1>" in page:
        page = page.replace("<h1>", dashboard + "\n<h1>", 1)
    elif "<main>" in page:
        page = page.replace("<main>", "<main>" + dashboard, 1)
    return _group_legacy_home(page, language)


def install_dashboard_patch(gui_module: Any) -> None:
    """Wrap ``gui._home`` once, leaving business logic untouched."""
    current: Callable[..., str] = gui_module._home
    if getattr(current, "_u1fa_dashboard_patch", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        return enhance_home_page(page, controller, language)

    setattr(patched, "_u1fa_dashboard_patch", True)
    gui_module._home = patched
