"""Premium visual shell for the U1FA 1.8.2 home page.

This patch rearranges and styles already-rendered home controls and adds a local
route for the official Snapmaker U1 product image. Business logic, printer
commands, Spoolman operations, Orca profile handling and calibration behaviour
remain owned by the existing modules.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit


_STYLE_ID = "u1fa-home-premium-182"
_HERO_ID = "u1fa-hero-182"
_COMMUNITY_ID = "u1fa-community-182"
_SETUP_ID = "u1fa-first-setup-v20"
_DASHBOARD_ID = "u1fa-dashboard-v20"
_SUPPORT_ID = "u1fa-support-v20"
_PRODUCT_ROUTE = "/u1-product-image"
_PRODUCT_ASSET_NAME = "snapmaker_u1_official.webp"
_TIKTOK_URL = "https://www.tiktok.com/@bottega3dlab"
_GITHUB_URL = "https://github.com/ubaccu/u1-filament-automation"
_COFFEE_URL = "https://www.buymeacoffee.com/riccelliiv9"

_DELETE_CARD_RE = re.compile(
    r'<!-- u1fa-filament-delete --><div class="card"><h2>.*?</div>\s*',
    re.DOTALL,
)
_NEW_SPOOL_CARD_RE = re.compile(
    r'<div class="card"><h2>(?:1\. Nuova bobina|1\. New spool)</h2>.*?</div>\s*',
    re.DOTALL,
)
_DETAILS_RE = re.compile(
    r'<details[^>]*class="u1fa-home-group"[^>]*>.*?</details>',
    re.DOTALL,
)
_SETUP_RE = re.compile(
    rf'<section id="{_SETUP_ID}"[^>]*>.*?</section>\s*',
    re.DOTALL,
)
_SUPPORT_RE = re.compile(
    rf'<section id="{_SUPPORT_ID}"[^>]*>.*?</section>\s*',
    re.DOTALL,
)
_DASH_ACTIONS_RE = re.compile(
    r'<div class="u1fa-actions">.*?</div>',
    re.DOTALL,
)
_DASH_SUB_RE = re.compile(
    r'<div class="u1fa-dash-sub">.*?</div>',
    re.DOTALL,
)

_CSS = f"""
<style id="{_STYLE_ID}">
:root{{--u1fa-cyan:#28b8ff;--u1fa-blue:#2578ff;--u1fa-violet:#8f5cff;--u1fa-green:#56e39f;--u1fa-panel:#111923;--u1fa-panel2:#0b1118;--u1fa-line:#28384b;--u1fa-text:#f2f7ff;--u1fa-muted:#93a6bd;--u1fa-danger:#ff6576;}}
body{{background:radial-gradient(circle at 78% -15%,rgba(37,120,255,.12),transparent 34%),#0a0f15!important}}
main{{max-width:1120px!important}}
#{_HERO_ID}{{position:relative;overflow:hidden;display:grid;grid-template-columns:minmax(0,1.12fr) minmax(300px,.88fr);gap:28px;min-height:315px;margin:4px 0 18px;padding:30px 32px;border:1px solid #2e4661;border-radius:22px;background:linear-gradient(135deg,#14263a 0%,#101a27 46%,#0d131b 100%);box-shadow:0 24px 60px rgba(0,0,0,.28)}}
#{_HERO_ID}::before{{content:'';position:absolute;inset:-80% -35%;background:linear-gradient(110deg,transparent 41%,rgba(70,184,255,.10) 49%,rgba(124,92,255,.08) 52%,transparent 59%);transform:translateX(-28%);animation:u1faHeroSweep 10s ease-in-out infinite;pointer-events:none}}
.u1fa-hero-copy{{position:relative;z-index:2;align-self:center}}
.u1fa-hero-kicker{{font-size:12px;font-weight:900;letter-spacing:.16em;text-transform:uppercase;color:#67c8ff;margin-bottom:10px}}
.u1fa-hero-title{{font-size:42px;line-height:1.02;letter-spacing:-.035em;font-weight:900;margin:0;color:#f6fbff}}
.u1fa-hero-title span{{background:linear-gradient(90deg,#5fd1ff,#7c8cff 58%,#ad71ff);-webkit-background-clip:text;background-clip:text;color:transparent}}
.u1fa-hero-sub{{font-size:16px;line-height:1.55;color:#a8b8ca;margin:14px 0 18px;max-width:620px}}
.u1fa-hero-chips{{display:flex;flex-wrap:wrap;gap:8px}}
.u1fa-chip{{display:inline-flex;align-items:center;gap:7px;padding:8px 11px;border-radius:999px;border:1px solid #314860;background:rgba(11,18,27,.62);color:#c8d6e6;font-size:12px;font-weight:800}}
.u1fa-chip-dot{{width:7px;height:7px;border-radius:50%;background:var(--u1fa-green);box-shadow:0 0 12px rgba(86,227,159,.65);animation:u1faPulse 2.6s ease-in-out infinite}}
.u1fa-hero-machine{{position:relative;z-index:2;min-height:250px;display:flex;align-items:center;justify-content:center}}
.u1fa-hero-machine::after{{content:'';position:absolute;width:82%;height:24px;bottom:17px;border-radius:50%;background:rgba(0,0,0,.42);filter:blur(13px)}}
.u1fa-hero-machine img{{position:relative;z-index:1;display:block;width:min(100%,430px);max-height:278px;object-fit:contain;filter:drop-shadow(0 18px 28px rgba(0,0,0,.40));transition:transform .25s ease,filter .25s ease}}
#{_HERO_ID}:hover .u1fa-hero-machine img{{transform:translateY(-3px) scale(1.01);filter:drop-shadow(0 22px 34px rgba(0,0,0,.48))}}
.u1fa-hero-machine-label{{position:absolute;right:6px;bottom:2px;z-index:3;padding:7px 10px;border:1px solid #36506a;border-radius:10px;background:rgba(8,14,21,.78);backdrop-filter:blur(8px);color:#9db3ca;font-size:11px;font-weight:800}}
#{_DASHBOARD_ID}{{background:linear-gradient(145deg,#111a24 0%,#0d141d 72%)!important;border-color:#293b50!important;border-radius:19px!important;box-shadow:0 16px 38px rgba(0,0,0,.18)!important;padding:20px!important}}
#{_DASHBOARD_ID} .u1fa-dash-title{{font-size:20px!important}}
#{_DASHBOARD_ID} .u1fa-dash-sub{{font-size:13px!important}}
#{_DASHBOARD_ID} .u1fa-status-grid{{gap:10px!important}}
#{_DASHBOARD_ID} .u1fa-status-card{{background:linear-gradient(145deg,#151f2b,#0e151e)!important;border-color:#293b50!important;border-radius:14px!important;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}}
#{_DASHBOARD_ID} .u1fa-status-card:hover{{transform:translateY(-2px);border-color:#3c6588!important;box-shadow:0 10px 24px rgba(0,0,0,.16)}}
#{_DASHBOARD_ID} .u1fa-dot.ok{{box-shadow:0 0 10px rgba(85,217,141,.45);animation:u1faPulse 2.8s ease-in-out infinite}}
#{_DASHBOARD_ID} .u1fa-actions{{margin-top:13px!important;padding-top:13px;border-top:1px solid #243244}}
#{_DASHBOARD_ID} .u1fa-dash-foot{{margin-top:10px!important;font-size:11px!important}}
.u1fa-home-group{{border-color:#293a4e!important;background:linear-gradient(180deg,#111923,#0d141c)!important;border-radius:18px!important;box-shadow:0 13px 30px rgba(0,0,0,.14)!important}}
.u1fa-home-group>summary{{padding:18px 20px!important;font-size:18px!important;letter-spacing:-.01em}}
.u1fa-home-group[open]>summary{{border-bottom:1px solid #243244}}
.u1fa-home-group-body{{padding:15px 16px 17px!important}}
.u1fa-home-group-body>.card{{border-color:#27384b!important;background:linear-gradient(145deg,#121b25,#0d141c)!important;border-radius:15px!important}}
.u1fa-quick-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:0 0 14px}}
.u1fa-quick-card{{position:relative;overflow:hidden;display:flex;flex-direction:column;min-height:134px;padding:17px;border-radius:16px;border:1px solid #30465f;background:linear-gradient(145deg,#16283a,#101923);text-decoration:none!important;color:var(--u1fa-text)!important;transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease}}
.u1fa-quick-card::after{{content:'';position:absolute;inset:auto -30% -65% 35%;height:110px;background:radial-gradient(circle,rgba(40,184,255,.16),transparent 66%);pointer-events:none}}
.u1fa-quick-card:hover{{transform:translateY(-3px);border-color:#4d88b6;box-shadow:0 13px 29px rgba(0,0,0,.22)}}
.u1fa-quick-card.danger{{background:linear-gradient(145deg,#2a1c24,#15151c);border-color:#65404d}}
.u1fa-quick-card.danger::after{{background:radial-gradient(circle,rgba(255,101,118,.15),transparent 66%)}}
.u1fa-quick-card.danger:hover{{border-color:#a65c70}}
.u1fa-quick-index{{width:34px;height:34px;border-radius:11px;display:inline-flex;align-items:center;justify-content:center;background:#203d58;color:#77d0ff;font-size:12px;font-weight:900;letter-spacing:.04em;margin-bottom:15px;box-shadow:inset 0 0 0 1px rgba(117,204,255,.10)}}
.u1fa-quick-card.danger .u1fa-quick-index{{background:#482632;color:#ff9dac}}
.u1fa-quick-card strong{{font-size:17px;line-height:1.2;margin-bottom:7px}}
.u1fa-quick-card small{{color:#a4b5c8;font-size:12px;line-height:1.45}}
.u1fa-calibration-card{{margin-top:0!important}}
.u1fa-calibration-card>h2{{margin-top:0}}
#{_SETUP_ID}{{display:grid!important;grid-template-columns:minmax(0,1fr) auto;column-gap:18px;align-items:center;background:linear-gradient(135deg,#211e15,#17150f)!important;border-color:#5a4b22!important;border-radius:14px!important;padding:14px 16px!important;margin:0 0 12px!important}}
#{_SETUP_ID} strong,#{_SETUP_ID} p{{grid-column:1}}
#{_SETUP_ID} strong{{margin-bottom:2px!important}}
#{_SETUP_ID} p{{margin:3px 0!important;font-size:12px;color:#c8ced7!important}}
#{_SETUP_ID} a{{grid-column:2;grid-row:1 / span 2;white-space:nowrap}}
#{_COMMUNITY_ID}{{position:relative;overflow:hidden;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:16px;align-items:center;margin:16px 0 4px;padding:19px 20px;border:1px solid #2f455e;border-radius:18px;background:linear-gradient(135deg,#15263a,#101823 60%,#151229);box-shadow:0 16px 36px rgba(0,0,0,.17)}}
#{_COMMUNITY_ID}::after{{content:'';position:absolute;right:-90px;top:-120px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(132,88,255,.18),transparent 67%);pointer-events:none}}
.u1fa-community-copy{{position:relative;z-index:1}}
.u1fa-community-copy strong{{display:block;font-size:17px;margin-bottom:4px}}
.u1fa-community-copy p{{margin:0;color:#9fb0c3;font-size:13px}}
.u1fa-community-actions{{position:relative;z-index:1;display:flex;flex-wrap:wrap;justify-content:flex-end;gap:9px}}
.u1fa-social-btn{{display:inline-flex;align-items:center;justify-content:center;min-height:42px;padding:0 14px;border:1px solid #344961;border-radius:12px;background:#121c28;color:#d9e7f6!important;text-decoration:none!important;font-weight:800;font-size:13px;transition:transform .16s ease,border-color .16s ease,background .16s ease}}
.u1fa-social-btn:hover{{transform:translateY(-2px);border-color:#5282ad;background:#172536}}
.u1fa-coffee-cta{{border-color:#85691a!important;background:linear-gradient(135deg,#ffd84d,#ffb936)!important;color:#17130a!important;box-shadow:0 0 0 0 rgba(255,196,52,.0);animation:u1faCoffeeGlow 5s ease-in-out infinite}}
.u1fa-coffee-cta:hover{{border-color:#ffd45a!important;background:linear-gradient(135deg,#ffe06a,#ffc545)!important}}
@keyframes u1faHeroSweep{{0%,18%{{transform:translateX(-30%)}}50%,70%{{transform:translateX(30%)}}100%{{transform:translateX(-30%)}}}}
@keyframes u1faPulse{{0%,100%{{opacity:.72;transform:scale(.92)}}50%{{opacity:1;transform:scale(1.08)}}}}
@keyframes u1faCoffeeGlow{{0%,76%,100%{{box-shadow:0 0 0 0 rgba(255,196,52,0)}}84%{{box-shadow:0 0 24px 3px rgba(255,196,52,.18)}}92%{{box-shadow:0 0 11px 1px rgba(255,196,52,.10)}}}}
@media(max-width:900px){{#{_HERO_ID}{{grid-template-columns:1fr;min-height:0}}.u1fa-hero-machine{{min-height:210px}}#{_COMMUNITY_ID}{{grid-template-columns:1fr}}.u1fa-community-actions{{justify-content:flex-start}}}}
@media(max-width:720px){{#{_HERO_ID}{{padding:24px 20px}}.u1fa-hero-title{{font-size:34px}}.u1fa-quick-grid{{grid-template-columns:1fr}}.u1fa-quick-card{{min-height:0}}#{_SETUP_ID}{{grid-template-columns:1fr}}#{_SETUP_ID} a{{grid-column:1;grid-row:auto;margin-top:10px;width:max-content}}}}
@media(prefers-reduced-motion:reduce){{#{_HERO_ID}::before,.u1fa-chip-dot,#{_DASHBOARD_ID} .u1fa-dot.ok,.u1fa-coffee-cta{{animation:none!important}}.u1fa-quick-card,.u1fa-social-btn,.u1fa-status-card,.u1fa-hero-machine img{{transition:none!important}}}}
</style>
"""


def _summary_text(block: str) -> str:
    match = re.search(r'<summary>(.*?)</summary>', block, re.DOTALL)
    return "" if match is None else re.sub(r'<[^>]+>', "", match.group(1)).strip()


def _hero(language: str) -> str:
    if language == "en":
        subtitle = "Spoolman inventory, Snapmaker Orca profiles and Adaptive PA in one controlled workflow."
        official = "Official Snapmaker U1 product image"
        chip_a, chip_b, chip_c = "Snapmaker U1", "Spoolman + Orca", "Adaptive PA"
    else:
        subtitle = "Inventario Spoolman, profili Snapmaker Orca e Adaptive PA in un unico flusso controllato."
        official = "Immagine prodotto ufficiale Snapmaker U1"
        chip_a, chip_b, chip_c = "Snapmaker U1", "Spoolman + Orca", "Adaptive PA"
    return (
        f'<section id="{_HERO_ID}">'
        '<div class="u1fa-hero-copy">'
        '<div class="u1fa-hero-kicker">BOTTEGA3DLAB · U1FA 1.8.2</div>'
        '<div class="u1fa-hero-title">U1 Filament <span>Automation</span></div>'
        f'<p class="u1fa-hero-sub">{subtitle}</p>'
        '<div class="u1fa-hero-chips">'
        f'<span class="u1fa-chip"><span class="u1fa-chip-dot"></span>{chip_a}</span>'
        f'<span class="u1fa-chip">{chip_b}</span>'
        f'<span class="u1fa-chip">{chip_c}</span>'
        '</div></div>'
        '<div class="u1fa-hero-machine">'
        f'<img src="{_PRODUCT_ROUTE}" alt="Snapmaker U1" loading="eager">'
        f'<span class="u1fa-hero-machine-label">{official}</span>'
        '</div></section>'
    )


def _quick_actions(language: str) -> str:
    if language == "en":
        new_title, new_text = "New spool", "Create the Spoolman spool and its Snapmaker Orca profile"
        cal_title, cal_text = "Calibrate PA", "Run Adaptive PA on a spool already available in Spoolman"
        del_title, del_text = "Delete filament", "Guided cleanup of linked spools, managed Orca profile and U1FA state"
    else:
        new_title, new_text = "Nuova bobina", "Crea la bobina Spoolman e il relativo profilo Snapmaker Orca"
        cal_title, cal_text = "Calibra PA", "Avvia Adaptive PA su una bobina già presente in Spoolman"
        del_title, del_text = "Elimina filamento", "Pulizia guidata di bobine collegate, profilo Orca gestito e stato U1FA"
    return (
        '<div class="u1fa-quick-grid">'
        f'<a class="u1fa-quick-card" href="/new-spool"><span class="u1fa-quick-index">01</span><strong>{new_title}</strong><small>{new_text}</small></a>'
        f'<a class="u1fa-quick-card" href="#u1fa-calibration-card"><span class="u1fa-quick-index">02</span><strong>{cal_title}</strong><small>{cal_text}</small></a>'
        f'<a class="u1fa-quick-card danger" href="/delete-filament"><span class="u1fa-quick-index">03</span><strong>{del_title}</strong><small>{del_text}</small></a>'
        '</div>'
    )


def _dashboard_actions(language: str) -> str:
    if language == "en":
        connections, updates = "Connections", "U1FA updates"
    else:
        connections, updates = "Connessioni", "Aggiornamenti U1FA"
    return (
        '<div class="u1fa-actions">'
        f'<a class="button secondary" href="/connections">⚙ {connections}</a>'
        f'<a class="button secondary" href="/updates">↻ {updates}</a>'
        '</div>'
    )


def _community_card(language: str) -> str:
    if language == "en":
        title = "U1FA is built by Bottega3DLab"
        text = "Follow the project, open the source repository or support continued development."
        coffee = "☕ Buy me a coffee"
        tiktok = "TikTok · @bottega3dlab"
        github = "GitHub · U1FA"
    else:
        title = "U1FA è sviluppato da Bottega3DLab"
        text = "Segui il progetto, apri il repository oppure sostieni lo sviluppo delle prossime versioni."
        coffee = "☕ Offrimi un caffè"
        tiktok = "TikTok · @bottega3dlab"
        github = "GitHub · U1FA"
    return (
        f'<section id="{_COMMUNITY_ID}">'
        f'<div class="u1fa-community-copy"><strong>{title}</strong><p>{text}</p></div>'
        '<div class="u1fa-community-actions">'
        f'<a class="u1fa-social-btn u1fa-coffee-cta" href="{_COFFEE_URL}" target="_blank" rel="noopener noreferrer">{coffee}</a>'
        f'<a class="u1fa-social-btn" href="{_TIKTOK_URL}" target="_blank" rel="noopener noreferrer">{tiktok}</a>'
        f'<a class="u1fa-social-btn" href="{_GITHUB_URL}" target="_blank" rel="noopener noreferrer">{github}</a>'
        '</div></section>'
    )


def _polish_filament_block(block: str, language: str) -> str:
    block = _DELETE_CARD_RE.sub("", block, count=1)
    block = _NEW_SPOOL_CARD_RE.sub("", block, count=1)
    if language == "en":
        old_heading = '<div class="card"><h2>2. Calibrate an existing spool</h2>'
        new_heading = '<div id="u1fa-calibration-card" class="card u1fa-calibration-card"><h2>Adaptive PA calibration</h2>'
    else:
        old_heading = '<div class="card"><h2>2. Calibra una bobina già presente</h2>'
        new_heading = '<div id="u1fa-calibration-card" class="card u1fa-calibration-card"><h2>Calibrazione Adaptive PA</h2>'
    block = block.replace(old_heading, new_heading, 1)
    body_marker = '<div class="u1fa-home-group-body">'
    if body_marker in block:
        block = block.replace(body_marker, body_marker + _quick_actions(language), 1)
    return block


def _polish_dashboard(page: str, language: str) -> str:
    title = "System status" if language == "en" else "Stato sistema"
    subtitle = (
        "Local services and automation status."
        if language == "en"
        else "Servizi locali e stato dell'automazione."
    )
    page = page.replace(
        '<div class="u1fa-dash-title">U1FA Control Center</div>',
        f'<div class="u1fa-dash-title">{title}</div>',
        1,
    )
    page = _DASH_SUB_RE.sub(f'<div class="u1fa-dash-sub">{subtitle}</div>', page, count=1)
    page = _DASH_ACTIONS_RE.sub(_dashboard_actions(language), page, count=1)
    return page


def polish_home(page: str, language: str = "it") -> str:
    if f'id="{_STYLE_ID}"' not in page:
        page = page.replace("</head>", _CSS + "</head>", 1)

    page = _polish_dashboard(page, language)
    page = _SUPPORT_RE.sub(_community_card(language), page, count=1)

    setup_match = _SETUP_RE.search(page)
    setup = setup_match.group(0) if setup_match else ""
    if setup:
        page = page[: setup_match.start()] + page[setup_match.end() :]

    blocks = list(_DETAILS_RE.finditer(page))
    if blocks:
        extracted = [match.group(0) for match in blocks]
        for block in extracted:
            page = page.replace(block, "", 1)

        filament = system = safety = ""
        leftovers: list[str] = []
        for block in extracted:
            label = _summary_text(block).casefold()
            if label in {"gestione filamenti", "filament management"}:
                filament = _polish_filament_block(block, language)
            elif label in {"sistema e manutenzione", "system and maintenance"}:
                system = block
            elif label in {"sicurezza e applicazione", "safety and application"}:
                safety = block
            else:
                leftovers.append(block)

        if setup and system:
            body_marker = '<div class="u1fa-home-group-body">'
            system = system.replace(body_marker, body_marker + setup, 1)
            setup = ""

        ordered = "".join(item for item in (filament, system, safety, *leftovers) if item)
        dash_start = page.find(f'id="{_DASHBOARD_ID}"')
        if dash_start >= 0:
            dash_end = page.find("</section>", dash_start)
            if dash_end >= 0:
                insert_at = dash_end + len("</section>")
                page = page[:insert_at] + ordered + page[insert_at:]
            else:
                page = page.replace("</main>", ordered + "</main>", 1)
        else:
            page = page.replace("</main>", ordered + "</main>", 1)

    if setup:
        page = page.replace("</main>", setup + "</main>", 1)

    if f'id="{_COMMUNITY_ID}"' not in page:
        page = page.replace("</main>", _community_card(language) + "</main>", 1)

    if f'id="{_HERO_ID}"' not in page:
        dashboard_marker = f'<section id="{_DASHBOARD_ID}"'
        if dashboard_marker in page:
            page = page.replace(dashboard_marker, _hero(language) + dashboard_marker, 1)
        else:
            page = page.replace("<main>", "<main>" + _hero(language), 1)
    return page


def _fallback_product_svg() -> bytes:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="600" viewBox="0 0 900 600">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#17283a"/><stop offset="1" stop-color="#0d141c"/></linearGradient></defs>'
        '<rect width="900" height="600" rx="36" fill="url(#g)"/>'
        '<text x="450" y="275" text-anchor="middle" fill="#eaf5ff" font-family="Arial,sans-serif" font-size="62" font-weight="700">Snapmaker U1</text>'
        '<text x="450" y="335" text-anchor="middle" fill="#7fcfff" font-family="Arial,sans-serif" font-size="25">official product asset unavailable</text>'
        '</svg>'
    ).encode("utf-8")


def _install_product_asset_route(gui_module: Any) -> None:
    current_handler = gui_module._handler
    if getattr(current_handler, "_u1fa_182_product_asset", False):
        return
    asset_path = Path(gui_module.__file__).resolve().parent / "assets" / _PRODUCT_ASSET_NAME

    def patched_handler(controller: Any, token: str):
        base_handler = current_handler(controller, token)

        class Handler(base_handler):
            def do_GET(self) -> None:  # noqa: N802
                if urlsplit(self.path).path == _PRODUCT_ROUTE:
                    try:
                        data = asset_path.read_bytes()
                        content_type = "image/webp"
                    except OSError:
                        data = _fallback_product_svg()
                        content_type = "image/svg+xml; charset=utf-8"
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "public, max-age=3600")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    self.wfile.write(data)
                    return
                super().do_GET()

        return Handler

    setattr(patched_handler, "_u1fa_182_product_asset", True)
    gui_module._handler = patched_handler


def install_182_home_polish(gui_module: Any) -> None:
    """Install the visual home wrapper and the read-only product-image route."""
    current: Callable[..., str] = gui_module._home
    if not getattr(current, "_u1fa_182_home_polish", False):
        def patched(
            controller: Any,
            token: str,
            error: str = "",
            language: str = "it",
        ) -> str:
            page = current(controller, token, error=error, language=language)
            return polish_home(page, language)

        setattr(patched, "_u1fa_182_home_polish", True)
        gui_module._home = patched

    _install_product_asset_route(gui_module)
