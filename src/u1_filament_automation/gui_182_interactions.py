"""Final navigation/brand polish for U1FA 1.8.2 home.

Presentation-only patch installed after the final home shell. It restores robust
in-page navigation, adds the requested filament-management shortcut and branded
social/integration icons, without changing printer/Spoolman/Orca/PA logic.
"""

from __future__ import annotations

import re
from typing import Any, Callable

_FILAMENT_ID = "u1fa-filament-group"
_CALIBRATION_ID = "u1fa-calibration-card"
_SYSTEM_ID = "u1fa-system-group"
_QUICK_ID = "u1fa-quick-zone"
_COMMUNITY_ID = "u1fa-community-182"
_SIDEBAR_ID = "u1fa-sidebar-final-182"
_STYLE_ID = "u1fa-182-interaction-fix"
_SCRIPT_ID = "u1fa-182-navigation-script"

_TIKTOK_URL = "https://www.tiktok.com/@bottega3dlab"
_GITHUB_URL = "https://github.com/ubaccu/u1-filament-automation"
_COFFEE_URL = "https://www.buymeacoffee.com/riccelliiv9"


def _svg(name: str) -> str:
    icons = {
        "spoolman": (
            '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/>'
            '<circle cx="12" cy="12" r="2.6"/><path d="M5.7 8.7h12.6M5.7 15.3h12.6"/></svg>'
        ),
        "orca": (
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.2 13.6c2.1-4.6 6-7 10.2-6.1 2 .4 3.5 1.4 5 3-1.4.2-2.4.7-3.2 1.5 2 .5 3.5 1.7 4.6 3.3-2.6 1.1-5.2 1.2-7.5.3-3.6 2.1-6.8 1.4-9.1-2z"/>'
            '<path d="M7.3 12.3h.1"/></svg>'
        ),
        "klipper": (
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 4v16M7 12l8-8M7 12l8 8"/>'
            '<circle cx="6" cy="4" r="1.4"/><circle cx="6" cy="20" r="1.4"/><circle cx="16" cy="4" r="1.4"/><circle cx="16" cy="20" r="1.4"/></svg>'
        ),
        "paxx": (
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 17V7h5.2c2.3 0 3.8 1.2 3.8 3.2s-1.5 3.3-3.8 3.3H7.1V17"/>'
            '<path d="M14.2 8.5 18.8 15M18.8 8.5 14.2 15"/></svg>'
        ),
        "adaptive": (
            '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="7.5"/>'
            '<circle cx="12" cy="12" r="2.5"/><path d="M2.5 12H6M18 12h3.5M12 2.5V6M12 18v3.5"/></svg>'
        ),
        "tiktok": (
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14.4 3v10.2a4.6 4.6 0 1 1-4-4.6v3a1.8 1.8 0 1 0 1.2 1.7V3z"/>'
            '<path d="M14.4 3c.4 2.4 1.8 3.8 4.4 4.2v3c-1.8-.1-3.2-.6-4.4-1.6"/></svg>'
        ),
        "github": (
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8a9.2 9.2 0 0 0-2.9 17.9c.5.1.7-.2.7-.5v-1.8c-2.8.6-3.4-1.2-3.4-1.2-.5-1.2-1.1-1.5-1.1-1.5-.9-.6.1-.6.1-.6 1 .1 1.5 1 1.5 1 .9 1.5 2.3 1.1 2.9.8.1-.6.3-1.1.6-1.4-2.3-.3-4.7-1.1-4.7-5a3.9 3.9 0 0 1 1-2.7 3.6 3.6 0 0 1 .1-2.7s.9-.3 2.9 1a10 10 0 0 1 5.3 0c2-1.3 2.9-1 2.9-1a3.6 3.6 0 0 1 .1 2.7 3.9 3.9 0 0 1 1 2.7c0 3.9-2.4 4.7-4.7 5 .4.3.7 1 .7 1.9v2.8c0 .3.2.6.7.5A9.2 9.2 0 0 0 12 2.8z"/></svg>'
        ),
        "coffee": (
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 7h11v6.2A4.8 4.8 0 0 1 11.2 18H9.8A4.8 4.8 0 0 1 5 13.2z"/>'
            '<path d="M16 9h1.6a2.4 2.4 0 0 1 0 4.8H16M7 3.5c0 1 1 1.2 1 2.2M11 3.5c0 1 1 1.2 1 2.2"/></svg>'
        ),
        "folder": (
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 6.5h6l1.8 2H20.5v9.5a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/></svg>'
        ),
    }
    return icons[name]


_CSS = f'''<style id="{_STYLE_ID}">
.u1fa-badge-icon svg{{width:14px;height:14px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}}
.u1fa-badge-icon .u1fa-brand-fill{{fill:currentColor;stroke:none}}
#{_QUICK_ID} .u1fa-quick-grid{{grid-template-columns:repeat(5,minmax(0,1fr))!important}}
.u1fa-manage-card{{border-color:#356497!important;background:linear-gradient(145deg,#142b42,#101b29)!important}}
.u1fa-manage-card .u1fa-final-quick-icon{{background:#3c8fdc!important}}
.u1fa-side-coffee{{display:flex;align-items:center;justify-content:center;gap:8px;margin:2px 4px 12px;padding:11px 10px;border-radius:11px;background:linear-gradient(135deg,#ffd84f,#ffb52d);color:#181209!important;text-decoration:none!important;font-size:12px;font-weight:950;box-shadow:0 8px 22px rgba(255,185,45,.14);transition:.17s ease}}
.u1fa-side-coffee:hover{{transform:translateY(-2px);box-shadow:0 12px 28px rgba(255,185,45,.23)}}
.u1fa-side-coffee svg,.u1fa-social-brand svg{{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}}
.u1fa-social-brand{{display:inline-flex;align-items:center;justify-content:center;gap:8px}}
.u1fa-social-brand.github svg{{fill:currentColor;stroke:none}}
.u1fa-social-brand.tiktok svg{{stroke-width:1.9}}
.u1fa-final-chip .u1fa-badge-icon{{box-shadow:inset 0 0 0 1px rgba(255,255,255,.03)}}
@media(max-width:1180px){{#{_QUICK_ID} .u1fa-quick-grid{{grid-template-columns:repeat(3,minmax(0,1fr))!important}}}}
@media(max-width:900px){{#{_QUICK_ID} .u1fa-quick-grid{{grid-template-columns:repeat(2,minmax(0,1fr))!important}}}}
@media(max-width:680px){{#{_QUICK_ID} .u1fa-quick-grid{{grid-template-columns:1fr!important}} .u1fa-side-coffee{{margin:0 8px}}}}
</style>'''

_SCRIPT = f'''<script id="{_SCRIPT_ID}">
(function(){{
  function jump(groupId, innerId){{
    var group=document.getElementById(groupId);
    if(!group) return false;
    if(group.tagName && group.tagName.toLowerCase()==='details') group.open=true;
    var target=innerId ? document.getElementById(innerId) : group;
    if(!target) target=group;
    window.requestAnimationFrame(function(){{
      target.scrollIntoView({{behavior:'smooth',block:'start'}});
      target.classList.add('u1fa-jump-highlight');
      window.setTimeout(function(){{target.classList.remove('u1fa-jump-highlight');}},900);
    }});
    return true;
  }}
  document.addEventListener('click',function(ev){{
    var link=ev.target.closest ? ev.target.closest('[data-u1fa-jump]') : null;
    if(!link) return;
    var group=link.getAttribute('data-u1fa-jump');
    var inner=link.getAttribute('data-u1fa-inner');
    if(jump(group,inner)) ev.preventDefault();
  }});
}})();
</script>
<style>.u1fa-jump-highlight{{outline:1px solid rgba(64,183,255,.65);box-shadow:0 0 0 4px rgba(64,183,255,.08),0 14px 35px rgba(0,0,0,.18)!important;transition:.2s ease}}</style>'''


def _ensure_group_id(page: str, labels: tuple[str, ...], group_id: str) -> str:
    label_alt = "|".join(re.escape(label) for label in labels)
    pattern = re.compile(
        rf'<details(?P<attrs>[^>]*)>\s*<summary>(?P<label>{label_alt})</summary>',
        re.IGNORECASE,
    )

    def repl(match: re.Match[str]) -> str:
        attrs = match.group("attrs")
        if re.search(r'\bid\s*=', attrs):
            return match.group(0)
        return f'<details id="{group_id}"{attrs}><summary>{match.group("label")}</summary>'

    return pattern.sub(repl, page, count=1)


def _brand_hero(page: str) -> str:
    replacements = (
        ('<span class="u1fa-badge-icon spool">◎</span>Spoolman', f'<span class="u1fa-badge-icon spool">{_svg("spoolman")}</span>Spoolman'),
        ('<span class="u1fa-badge-icon">◈</span>Snapmaker Orca', f'<span class="u1fa-badge-icon">{_svg("orca")}</span>Snapmaker Orca'),
        ('<span class="u1fa-badge-icon klipper">V</span>Klipper', f'<span class="u1fa-badge-icon klipper">{_svg("klipper")}</span>Klipper'),
        ('<span class="u1fa-badge-icon paxx">P</span>PAXX', f'<span class="u1fa-badge-icon paxx">{_svg("paxx")}</span>PAXX'),
        ('<span class="u1fa-badge-icon">⚡</span>Adaptive PA', f'<span class="u1fa-badge-icon">{_svg("adaptive")}</span>Adaptive PA'),
    )
    for old, new in replacements:
        page = page.replace(old, new, 1)
    return page


def _fix_navigation(page: str) -> str:
    # Existing route links remain untouched. Only home-page jumps become explicit,
    # robust JS targets that also open collapsed detail groups.
    page = page.replace(
        f'href="#{_QUICK_ID}"',
        f'href="#{_FILAMENT_ID}" data-u1fa-jump="{_FILAMENT_ID}"',
        1,
    )
    page = page.replace(
        f'href="#{_CALIBRATION_ID}" onclick="var d=document.getElementById(\\\'{_FILAMENT_ID}\\\');if(d)d.open=true"',
        f'href="#{_CALIBRATION_ID}" data-u1fa-jump="{_FILAMENT_ID}" data-u1fa-inner="{_CALIBRATION_ID}"',
    )
    page = page.replace(
        f'href="#{_CALIBRATION_ID}"',
        f'href="#{_CALIBRATION_ID}" data-u1fa-jump="{_FILAMENT_ID}" data-u1fa-inner="{_CALIBRATION_ID}"',
    )
    page = page.replace(
        'href="#u1fa-dashboard-v20"',
        f'href="#{_SYSTEM_ID}" data-u1fa-jump="{_SYSTEM_ID}"',
    )
    return page


def _add_manage_quick_action(page: str, language: str) -> str:
    if 'u1fa-manage-card' in page:
        return page
    title = "Filament management" if language == "en" else "Gestione filamenti"
    text = (
        "Open the complete filament workflow and advanced controls"
        if language == "en"
        else "Apri il flusso completo filamenti e i controlli avanzati"
    )
    card = (
        f'<a class="u1fa-quick-card u1fa-manage-card" href="#{_FILAMENT_ID}" data-u1fa-jump="{_FILAMENT_ID}">'
        f'<span class="u1fa-final-quick-icon">{_svg("folder")}</span><strong>{title}</strong><small>{text}</small></a>'
    )
    pattern = re.compile(
        rf'(<section id="{_QUICK_ID}">.*?<div class="u1fa-quick-grid">)(.*?)(</div></section>)',
        re.DOTALL,
    )
    return pattern.sub(lambda m: m.group(1) + m.group(2) + card + m.group(3), page, count=1)


def _add_sidebar_coffee(page: str, language: str) -> str:
    if 'u1fa-side-coffee' in page:
        return page
    label = "Buy me a coffee" if language == "en" else "Offrimi un caffè"
    cta = (
        f'<a class="u1fa-side-coffee" href="{_COFFEE_URL}" target="_blank" rel="noopener noreferrer">'
        f'{_svg("coffee")}<span>{label}</span></a>'
    )
    marker = '<div class="u1fa-side-language">'
    return page.replace(marker, cta + marker, 1)


def _brand_social_links(page: str) -> str:
    patterns = (
        (_TIKTOK_URL, "tiktok", "TikTok", "@bottega3dlab"),
        (_GITHUB_URL, "github", "GitHub", "U1FA"),
    )
    for url, icon, name, suffix in patterns:
        pattern = re.compile(
            rf'(<a class="u1fa-social-btn" href="{re.escape(url)}"[^>]*>)(.*?)(</a>)',
            re.DOTALL,
        )
        inner = f'<span class="u1fa-social-brand {icon}">{_svg(icon)}<span>{name} · {suffix}</span></span>'
        page = pattern.sub(lambda m, inner=inner: m.group(1) + inner + m.group(3), page, count=1)
    return page


def enhance_home(page: str, language: str = "it") -> str:
    page = _ensure_group_id(page, ("Sistema e manutenzione", "System and maintenance"), _SYSTEM_ID)
    page = _brand_hero(page)
    page = _fix_navigation(page)
    page = _add_manage_quick_action(page, language)
    page = _add_sidebar_coffee(page, language)
    page = _brand_social_links(page)
    if f'id="{_STYLE_ID}"' not in page:
        page = page.replace("</head>", _CSS + "</head>", 1)
    if f'id="{_SCRIPT_ID}"' not in page:
        page = page.replace("</body>", _SCRIPT + "</body>", 1)
    return page


def install_182_interaction_fix(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._home
    if getattr(current, "_u1fa_182_interaction_fix", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        return enhance_home(page, language)

    setattr(patched, "_u1fa_182_interaction_fix", True)
    gui_module._home = patched
