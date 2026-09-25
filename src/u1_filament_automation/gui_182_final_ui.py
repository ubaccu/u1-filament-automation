'''Final visual-only home shell for U1FA 1.8.2.

This module runs after the established 1.8.2 patches. It only rearranges and
styles already-rendered controls; it does not alter printer, Spoolman, Orca or
Adaptive PA behaviour.
'''

from __future__ import annotations

import re
from typing import Any, Callable

_STYLE_ID = 'u1fa-final-home-182'
_SIDEBAR_ID = 'u1fa-sidebar-final-182'
_HERO_ID = 'u1fa-hero-182'
_DASHBOARD_ID = 'u1fa-dashboard-v20'
_SETUP_ID = 'u1fa-first-setup-v20'
_COMMUNITY_ID = 'u1fa-community-182'
_FILAMENT_ID = 'u1fa-filament-group'


def _section_re(element_id: str) -> re.Pattern[str]:
    return re.compile(rf'<section id=\"{re.escape(element_id)}\"[^>]*>.*?</section>\\s*', re.DOTALL)


_HERO_RE = _section_re(_HERO_ID)
_SETUP_RE = _section_re(_SETUP_ID)
_COMMUNITY_RE = _section_re(_COMMUNITY_ID)
_QUICK_RE = re.compile(r'<div class=\"u1fa-quick-grid\">.*?</div>\\s*', re.DOTALL)
_STATUS_CARD = '<div class=\"u1fa-status-card\">'


def _svg(name: str) -> str:
    icons = {
        'home': '<svg viewBox=\"0 0 24 24\"><path d=\"M3 11.5 12 4l9 7.5v8a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z\"/></svg>',
        'spool': '<svg viewBox=\"0 0 24 24\"><circle cx=\"12\" cy=\"12\" r=\"7\"/><circle cx=\"12\" cy=\"12\" r=\"2.4\"/><path d=\"M5.8 8.6h12.4M5.8 15.4h12.4\"/></svg>',
        'target': '<svg viewBox=\"0 0 24 24\"><circle cx=\"12\" cy=\"12\" r=\"7.5\"/><circle cx=\"12\" cy=\"12\" r=\"3\"/><path d=\"M12 2v3M22 12h-3M12 22v-3M2 12h3\"/></svg>',
        'trash': '<svg viewBox=\"0 0 24 24\"><path d=\"M5 7h14M9 7V4h6v3M8 10v7M12 10v7M16 10v7M6.5 7l.8 13h9.4l.8-13\"/></svg>',
        'pulse': '<svg viewBox=\"0 0 24 24\"><path d=\"M2 12h5l2.2-6 4 12 2.2-6H22\"/></svg>',
        'printer': '<svg viewBox=\"0 0 24 24\"><rect x=\"5\" y=\"3\" width=\"14\" height=\"18\" rx=\"2\"/><path d=\"M8 7h8v5H8zM8 16h8M9 19h6\"/></svg>',
        'database': '<svg viewBox=\"0 0 24 24\"><ellipse cx=\"12\" cy=\"5\" rx=\"7\" ry=\"3\"/><path d=\"M5 5v6c0 1.7 3.1 3 7 3s7-1.3 7-3V5M5 11v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6\"/></svg>',
        'orca': '<svg viewBox=\"0 0 24 24\"><path d=\"M4 14c2.5-5 6-7 10-6 2 .5 3.4 1.5 5 3-1.3.2-2.3.6-3 1.3 1.8.6 3 1.7 4 3.2-2.3 1-4.6 1.1-6.7.4C9.6 18.3 6.5 17.7 4 14Z\"/><path d=\"M8 12.5h.01\"/></svg>',
        'settings': '<svg viewBox=\"0 0 24 24\"><circle cx=\"12\" cy=\"12\" r=\"3\"/><path d=\"M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4\"/></svg>',
        'update': '<svg viewBox=\"0 0 24 24\"><path d=\"M20 7v5h-5\"/><path d=\"M19 12a7 7 0 1 1-2-5\"/></svg>',
    }
    return icons[name]


_CSS = f'''<style id=\"{_STYLE_ID}\">
:root{{--u1fa-cyan:#2ab9ff;--u1fa-blue:#2088ff;--u1fa-green:#37dda0;--u1fa-purple:#9169ff;--u1fa-amber:#ffbd3d;--u1fa-bg:#081018;--u1fa-panel:#0f1924;--u1fa-line:#293e53;}}
body{{background:radial-gradient(circle at 72% -12%,rgba(31,133,255,.14),transparent 32%),var(--u1fa-bg)!important;padding-left:218px;min-height:100vh}}
main{{max-width:1240px!important;margin:0 auto!important;padding:26px 28px 42px!important}} main>.brand{{display:none!important}}
#{_SIDEBAR_ID}{{position:fixed;inset:0 auto 0 0;width:218px;z-index:80;box-sizing:border-box;display:flex;flex-direction:column;padding:24px 14px 18px;background:linear-gradient(180deg,#0d1722,#0a121a 70%,#081018);border-right:1px solid #1f3245;box-shadow:12px 0 34px rgba(0,0,0,.18)}}
.u1fa-side-brand{{text-align:center;padding:0 8px 20px;border-bottom:1px solid #1e2f41}} .u1fa-side-brand img{{width:86px;height:86px;object-fit:contain;background:#fff;border-radius:50%;padding:4px;box-sizing:border-box;box-shadow:0 8px 25px rgba(0,0,0,.28)}} .u1fa-side-brand strong{{display:block;margin-top:10px;font-size:15px}} .u1fa-side-brand small{{display:block;color:#91a5ba;font-size:11px;margin-top:3px}} .u1fa-side-version{{display:inline-flex;margin-top:9px;padding:5px 9px;border-radius:999px;background:#163a6b;color:#cfe8ff;font-size:11px;font-weight:900}}
.u1fa-side-nav{{display:flex;flex-direction:column;gap:6px;padding:18px 0}} .u1fa-side-nav a{{display:flex;align-items:center;gap:10px;min-height:42px;padding:0 12px;border-radius:11px;color:#b7c6d6!important;text-decoration:none!important;font-weight:750;font-size:13px;transition:.16s ease}} .u1fa-side-nav a:hover{{background:#12283b;color:#fff!important;transform:translateX(2px)}} .u1fa-side-nav a.active{{background:linear-gradient(90deg,#1391eb,#1769b1);color:#fff!important;box-shadow:0 8px 20px rgba(15,125,218,.2)}} .u1fa-side-nav svg{{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}}
.u1fa-side-language{{display:flex;gap:6px;justify-content:center;margin-top:auto;padding:12px 0 9px}} .u1fa-side-language a{{padding:7px 10px;border-radius:8px;background:#182636;color:#d7e5f3;text-decoration:none;font-weight:900;font-size:12px}} .u1fa-side-language a.active{{background:#2aafff;color:#06111b}} .u1fa-side-foot{{text-align:center;color:#7c92a8;font-size:10px;line-height:1.4}}
#{_HERO_ID}{{position:relative;overflow:hidden;display:grid;grid-template-columns:minmax(0,1.04fr) minmax(360px,.96fr);gap:22px;min-height:300px;margin:0 0 18px;padding:28px 30px;border:1px solid #2a435b;border-radius:22px;background:linear-gradient(135deg,#12263a 0%,#0e1a27 53%,#0b121a 100%);box-shadow:0 22px 55px rgba(0,0,0,.28)}} #{_HERO_ID}::before{{content:'';position:absolute;inset:-65% -35%;background:linear-gradient(112deg,transparent 43%,rgba(58,187,255,.10) 49%,rgba(126,91,255,.07) 52%,transparent 59%);animation:u1faFinalSweep 11s ease-in-out infinite;pointer-events:none}}
.u1fa-final-hero-copy{{position:relative;z-index:2;align-self:center}} .u1fa-final-kicker{{font-size:11px;font-weight:950;letter-spacing:.17em;color:#5bc8ff;margin-bottom:10px}} .u1fa-final-title{{font-size:42px;line-height:1.03;letter-spacing:-.04em;font-weight:950;color:#f8fbff}} .u1fa-final-title span{{background:linear-gradient(90deg,#4bc9ff,#5b9cff 50%,#a46cff);-webkit-background-clip:text;background-clip:text;color:transparent}} .u1fa-final-sub{{font-size:15px;line-height:1.55;color:#a7b8ca;margin:14px 0 17px;max-width:590px}}
.u1fa-final-chips{{display:flex;flex-wrap:wrap;gap:8px}} .u1fa-final-chip{{display:inline-flex;align-items:center;gap:7px;padding:7px 10px;border-radius:999px;border:1px solid #30495f;background:rgba(8,16,24,.68);color:#cfdae6;font-size:11px;font-weight:850}} .u1fa-badge-icon{{width:18px;height:18px;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;background:#14283a;color:#61cbff;font-weight:950}} .u1fa-badge-icon.spool{{color:#3de5aa;background:#12352a}} .u1fa-badge-icon.klipper{{color:#ff657b;background:#341923}} .u1fa-badge-icon.paxx{{color:#b390ff;background:#251b3a}}
.u1fa-final-machine{{position:relative;z-index:2;min-height:244px;display:flex;align-items:center;justify-content:center}} .u1fa-final-machine::before{{content:'';position:absolute;width:92%;height:82%;border-radius:50%;background:radial-gradient(circle,rgba(44,188,255,.20) 0%,rgba(62,112,255,.09) 42%,transparent 72%);filter:blur(13px)}} .u1fa-final-machine::after{{content:'';position:absolute;width:72%;height:18px;bottom:22px;border-radius:50%;background:rgba(0,0,0,.42);filter:blur(11px)}} .u1fa-final-machine img{{position:relative;z-index:2;display:block;width:100%;height:282px;object-fit:contain;filter:drop-shadow(0 22px 22px rgba(0,0,0,.58)) drop-shadow(0 0 17px rgba(43,188,255,.17));transition:transform .25s ease,filter .25s ease}} #{_HERO_ID}:hover .u1fa-final-machine img{{transform:translateY(-3px) scale(1.012);filter:drop-shadow(0 24px 26px rgba(0,0,0,.62)) drop-shadow(0 0 24px rgba(43,188,255,.22))}}
#{_DASHBOARD_ID}{{background:linear-gradient(145deg,#101a25,#0c141d)!important;border-color:#293e54!important;border-radius:19px!important;padding:18px!important;box-shadow:0 15px 38px rgba(0,0,0,.16)!important;margin:0 0 13px!important}} #{_DASHBOARD_ID} .u1fa-status-card{{position:relative;padding-left:54px!important;background:linear-gradient(145deg,#14202c,#0f1821)!important;border-color:#2b4055!important;border-radius:14px!important;transition:.17s ease}} #{_DASHBOARD_ID} .u1fa-status-card:hover{{transform:translateY(-2px);border-color:#44719a!important}} .u1fa-final-status-icon{{position:absolute;left:13px;top:15px;width:30px;height:30px;border-radius:9px;display:flex;align-items:center;justify-content:center;background:#142c40;color:#4fc1ff}} .u1fa-final-status-icon svg{{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round}} #{_DASHBOARD_ID} .u1fa-status-card:nth-child(2) .u1fa-final-status-icon{{color:#45e0aa;background:#123329}} #{_DASHBOARD_ID} .u1fa-status-card:nth-child(3) .u1fa-final-status-icon{{color:#b18cff;background:#251d3b}} #{_DASHBOARD_ID} .u1fa-status-card:nth-child(4) .u1fa-final-status-icon{{color:#ff7184;background:#351b24}} #{_DASHBOARD_ID} .u1fa-dot.ok{{box-shadow:0 0 11px rgba(85,217,141,.46);animation:u1faFinalPulse 2.8s ease-in-out infinite}}
#{_SETUP_ID}{{display:grid!important;grid-template-columns:minmax(0,1fr) auto;gap:15px;align-items:center;background:linear-gradient(135deg,#2b2513,#18160f)!important;border-color:#745d18!important;border-radius:15px!important;padding:14px 16px!important;margin:0 0 16px!important}} #{_SETUP_ID} strong,#{_SETUP_ID} p{{grid-column:1}} #{_SETUP_ID} p{{font-size:11px!important;margin:3px 0!important}} #{_SETUP_ID} a{{grid-column:2;grid-row:1 / span 2;white-space:nowrap}}
#u1fa-quick-zone{{margin:0 0 14px}} .u1fa-final-section-head{{display:flex;align-items:center;gap:10px;margin:0 0 11px 3px}} .u1fa-final-section-head b{{font-size:18px}} .u1fa-final-section-head small{{display:block;color:#90a4b9;font-size:12px;margin-top:2px}} #u1fa-quick-zone .u1fa-quick-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:11px;margin:0!important}} #u1fa-quick-zone .u1fa-quick-card{{position:relative;min-height:142px;padding:17px!important;border-radius:17px!important;transition:.18s ease;overflow:hidden}} #u1fa-quick-zone .u1fa-quick-card:hover{{transform:translateY(-3px);box-shadow:0 14px 30px rgba(0,0,0,.24)}} .u1fa-final-quick-icon{{width:45px;height:45px;display:flex;align-items:center;justify-content:center;border-radius:50%;margin-bottom:14px;background:#39aef5;color:#07141e}} .u1fa-final-quick-icon svg{{width:25px;height:25px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}} #u1fa-quick-zone .u1fa-quick-card:nth-child(1){{border-color:#197a5c!important;background:linear-gradient(145deg,#0d322b,#0c1d1c)!important}} #u1fa-quick-zone .u1fa-quick-card:nth-child(1) .u1fa-final-quick-icon{{background:#1f9f78}} #u1fa-quick-zone .u1fa-quick-card:nth-child(3){{border-color:#8a631b!important;background:linear-gradient(145deg,#302617,#1a1712)!important}} #u1fa-quick-zone .u1fa-quick-card:nth-child(3) .u1fa-final-quick-icon{{background:#ffb83d}} #u1fa-quick-zone .u1fa-quick-card:nth-child(4){{border-color:#5b458e!important;background:linear-gradient(145deg,#211b35,#151421)!important}} #u1fa-quick-zone .u1fa-quick-card:nth-child(4) .u1fa-final-quick-icon{{background:#8f67ea}}
#{_COMMUNITY_ID}{{position:relative;overflow:hidden;display:grid!important;grid-template-columns:minmax(0,1fr) auto;gap:18px;align-items:center;margin:0 0 16px!important;padding:17px 18px!important;border:1px solid #33475f!important;border-radius:17px!important;background:linear-gradient(135deg,#15273a,#0f1a27 62%,#1b1430)!important;box-shadow:0 14px 32px rgba(0,0,0,.17)!important}} #{_COMMUNITY_ID} .u1fa-coffee-cta{{border-color:#b68113!important;background:linear-gradient(135deg,#ffd84f,#ffb52d)!important;color:#171109!important;animation:u1faFinalCoffee 5.2s ease-in-out infinite}} #{_COMMUNITY_ID} .u1fa-social-btn{{min-height:40px!important;border-radius:11px!important}}
.u1fa-home-group{{border-color:#293d51!important;background:linear-gradient(180deg,#101923,#0c141c)!important;border-radius:16px!important;margin:11px 0!important;box-shadow:0 10px 26px rgba(0,0,0,.12)!important}} .u1fa-home-group>summary{{padding:16px 18px!important;font-size:16px!important}} .u1fa-home-group[open]>summary{{border-bottom:1px solid #243244}} .u1fa-home-group-body{{padding:13px 15px 15px!important}}
@keyframes u1faFinalSweep{{0%,18%{{transform:translateX(-31%)}}50%,70%{{transform:translateX(30%)}}100%{{transform:translateX(-31%)}}}} @keyframes u1faFinalPulse{{0%,100%{{opacity:.72;transform:scale(.92)}}50%{{opacity:1;transform:scale(1.08)}}}} @keyframes u1faFinalCoffee{{0%,76%,100%{{box-shadow:0 0 0 0 rgba(255,196,52,0)}}86%{{box-shadow:0 0 25px 3px rgba(255,196,52,.20)}}94%{{box-shadow:0 0 10px 1px rgba(255,196,52,.09)}}}}
@media(max-width:1100px){{body{{padding-left:0}} #{_SIDEBAR_ID}{{position:relative;inset:auto;width:auto;min-height:0;display:grid;grid-template-columns:auto 1fr auto;align-items:center;padding:10px 16px;border-right:0;border-bottom:1px solid #1e3144}} .u1fa-side-brand{{display:flex;align-items:center;gap:10px;text-align:left;padding:0;border:0}} .u1fa-side-brand img{{width:48px;height:48px}} .u1fa-side-brand strong{{margin:0}} .u1fa-side-brand small,.u1fa-side-version,.u1fa-side-foot{{display:none}} .u1fa-side-nav{{flex-direction:row;justify-content:center;flex-wrap:wrap;padding:0 12px}} .u1fa-side-nav a{{min-height:36px;padding:0 9px;font-size:11px}} .u1fa-side-language{{margin:0;padding:0}} main{{padding-top:18px!important}}}}
@media(max-width:900px){{#{_HERO_ID}{{grid-template-columns:1fr;min-height:0}} .u1fa-final-machine{{min-height:190px}} #u1fa-quick-zone .u1fa-quick-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}} #{_COMMUNITY_ID}{{grid-template-columns:1fr}}}}
@media(max-width:680px){{.u1fa-side-nav{{display:none}} #{_SIDEBAR_ID}{{grid-template-columns:1fr auto}} #{_HERO_ID}{{padding:22px 18px}} .u1fa-final-title{{font-size:34px}} #u1fa-quick-zone .u1fa-quick-grid{{grid-template-columns:1fr}} #{_SETUP_ID}{{grid-template-columns:1fr}} #{_SETUP_ID} a{{grid-column:1;grid-row:auto;width:max-content}}}}
@media(prefers-reduced-motion:reduce){{#{_HERO_ID}::before,#{_DASHBOARD_ID} .u1fa-dot.ok,#{_COMMUNITY_ID} .u1fa-coffee-cta{{animation:none!important}} .u1fa-quick-card,.u1fa-final-machine img{{transition:none!important}}}}
</style>'''


def _sidebar(language: str) -> str:
    it_active = 'active' if language != 'en' else ''
    en_active = 'active' if language == 'en' else ''
    if language == 'en':
        labels = ('Home', 'Filaments', 'Calibration', 'System', 'Connections', 'Updates')
    else:
        labels = ('Home', 'Filamenti', 'Calibrazione', 'Sistema', 'Connessioni', 'Aggiornamenti')
    return (
        f'<aside id=\"{_SIDEBAR_ID}\"><div class=\"u1fa-side-brand\">'
        '<img src=\"/assets/u1fa-logo.png\" alt=\"U1FA\"><strong>U1 Filament Automation</strong>'
        '<small>by Bottega3DLab</small><span class=\"u1fa-side-version\">v1.8.2</span></div>'
        '<nav class=\"u1fa-side-nav\">'
        f'<a class=\"active\" href=\"/\">{_svg("home")}<span>{labels[0]}</span></a>'
        f'<a href=\"#u1fa-quick-zone\">{_svg("spool")}<span>{labels[1]}</span></a>'
        f'<a href=\"#u1fa-calibration-card\" onclick=\"var d=document.getElementById(\\\'{_FILAMENT_ID}\\\');if(d)d.open=true\">{_svg("target")}<span>{labels[2]}</span></a>'
        f'<a href=\"#{_DASHBOARD_ID}\">{_svg("printer")}<span>{labels[3]}</span></a>'
        f'<a href=\"/connections\">{_svg("settings")}<span>{labels[4]}</span></a>'
        f'<a href=\"/updates\">{_svg("update")}<span>{labels[5]}</span></a>'
        '</nav><div class=\"u1fa-side-language\">'
        f'<a class=\"{it_active}\" href=\"/language?lang=it\">IT</a><a class=\"{en_active}\" href=\"/language?lang=en\">EN</a>'
        '</div><div class=\"u1fa-side-foot\">Bottega3DLab<br>Print smarter · Live better</div></aside>'
    )


def _hero(language: str) -> str:
    subtitle = (
        'Spoolman inventory, Snapmaker Orca profiles and Adaptive PA in one controlled workflow.'
        if language == 'en'
        else 'Inventario Spoolman, profili Snapmaker Orca e Adaptive PA in un unico flusso controllato.'
    )
    return (
        f'<section id=\"{_HERO_ID}\"><div class=\"u1fa-final-hero-copy\">'
        '<div class=\"u1fa-final-kicker\">BOTTEGA3DLAB · U1FA 1.8.2</div>'
        '<div class=\"u1fa-final-title\">U1 Filament <span>Automation</span></div>'
        f'<p class=\"u1fa-final-sub\">{subtitle}</p><div class=\"u1fa-final-chips\">'
        '<span class=\"u1fa-final-chip\"><span class=\"u1fa-badge-icon spool\">◎</span>Spoolman</span>'
        '<span class=\"u1fa-final-chip\"><span class=\"u1fa-badge-icon\">◈</span>Snapmaker Orca</span>'
        '<span class=\"u1fa-final-chip\"><span class=\"u1fa-badge-icon klipper\">V</span>Klipper</span>'
        '<span class=\"u1fa-final-chip\"><span class=\"u1fa-badge-icon paxx\">P</span>PAXX</span>'
        '<span class=\"u1fa-final-chip\"><span class=\"u1fa-badge-icon\">⚡</span>Adaptive PA</span>'
        '</div></div><div class=\"u1fa-final-machine\">'
        '<img src=\"/u1-product-image\" alt=\"Snapmaker U1\" loading=\"eager\"></div></section>'
    )


def _extract(page: str, regex: re.Pattern[str]) -> tuple[str, str]:
    match = regex.search(page)
    if not match:
        return page, ''
    return page[: match.start()] + page[match.end() :], match.group(0)


def _decorate_quick_grid(grid: str, language: str) -> str:
    if not grid:
        return ''
    icons = ('spool', 'target', 'trash')
    for index, icon in enumerate(icons, 1):
        grid = grid.replace(
            f'<span class=\"u1fa-quick-index\">0{index}</span>',
            f'<span class=\"u1fa-final-quick-icon\">{_svg(icon)}</span>',
            1,
        )
    grid = grid.replace(
        'href=\"#u1fa-calibration-card\"',
        f'href=\"#u1fa-calibration-card\" onclick=\"var d=document.getElementById(\\\'{_FILAMENT_ID}\\\');if(d)d.open=true\"',
        1,
    )
    title = 'System status' if language == 'en' else 'Stato sistema'
    text = 'Services, connections and automation status' if language == 'en' else 'Servizi, connessioni e stato automazione'
    extra = (
        f'<a class=\"u1fa-quick-card\" href=\"#{_DASHBOARD_ID}\">'
        f'<span class=\"u1fa-final-quick-icon\">{_svg("pulse")}</span><strong>{title}</strong><small>{text}</small></a>'
    )
    stripped = grid.rstrip()
    if stripped.endswith('</div>'):
        grid = stripped[:-6] + extra + '</div>'
    else:
        grid += extra
    heading = 'Quick actions' if language == 'en' else 'Azioni rapide'
    sub = 'Everything you need most, immediately.' if language == 'en' else 'Tutto quello che ti serve più spesso, subito.'
    return (
        '<section id=\"u1fa-quick-zone\"><div class=\"u1fa-final-section-head\"><span style=\"font-size:25px;color:#2cb8ff\">⚡</span>'
        f'<div><b>{heading}</b><small>{sub}</small></div></div>{grid}</section>'
    )


def _decorate_status_cards(page: str) -> str:
    for icon in ('printer', 'database', 'orca', 'pulse'):
        if _STATUS_CARD not in page:
            break
        page = page.replace(
            _STATUS_CARD,
            _STATUS_CARD + f'<span class=\"u1fa-final-status-icon\">{_svg(icon)}</span>',
            1,
        )
    return page


def finalize_home(page: str, language: str = 'it') -> str:
    if f'id=\"{_STYLE_ID}\"' not in page:
        page = page.replace('</head>', _CSS + '</head>', 1)
    if f'id=\"{_SIDEBAR_ID}\"' not in page:
        page = page.replace('<body>', '<body>' + _sidebar(language), 1)

    page = _HERO_RE.sub(_hero(language), page, count=1)
    page = _decorate_status_cards(page)
    page, setup = _extract(page, _SETUP_RE)
    page, community = _extract(page, _COMMUNITY_RE)
    page, quick_grid = _extract(page, _QUICK_RE)
    quick = _decorate_quick_grid(quick_grid, language)

    page = re.sub(
        rf'(<details[^>]*id=\"{_FILAMENT_ID}\"[^>]*?)\\sopen(?=[\\s>])',
        r'\\1',
        page,
        count=1,
    )

    insert = setup + quick + community
    dash_start = page.find(f'id=\"{_DASHBOARD_ID}\"')
    if dash_start >= 0:
        dash_end = page.find('</section>', dash_start)
        if dash_end >= 0:
            at = dash_end + len('</section>')
            page = page[:at] + insert + page[at:]
        else:
            page = page.replace('</main>', insert + '</main>', 1)
    else:
        page = page.replace('</main>', insert + '</main>', 1)
    return page


def install_182_final_ui(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._home
    if getattr(current, '_u1fa_182_final_ui', False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = '',
        language: str = 'it',
    ) -> str:
        page = current(controller, token, error=error, language=language)
        return finalize_home(page, language)

    setattr(patched, '_u1fa_182_final_ui', True)
    gui_module._home = patched
