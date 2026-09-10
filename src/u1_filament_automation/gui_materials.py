"""Piccole estensioni della UI desktop.

La logica di associazione ai profili Snapmaker resta in ``sync.choose_base``.
Questo modulo espone nella pagina di creazione bobina tutte le famiglie già
supportate dal motore, installa la dashboard b17 e mantiene il ciclo di
chiusura sicura dopo l'apertura di un installer verificato.
"""

from __future__ import annotations

import html
import re
from typing import Any, Callable

from .gui_dashboard import install_dashboard_patch
from .orca_profile_discovery import ProfileRecommendation, recommend_installed_profile
from .update_lifecycle import install_update_lifecycle_patch


MATERIAL_OPTIONS = (
    "PLA",
    "PLA Rapid",
    "PLA Silk",
    "PLA Wood",
    "PLA Translucent",
    "PLA-CF",
    "PETG",
    "PETG HF",
    "PETG Translucent",
    "PETG-CF",
)
_MATERIAL_SELECT_START = '<select name="material" id="material">'
_SELECT_END = "</select>"
_FORM_MARKER = '<form method="post" action="/new-spool/preview">'
_HINT_ID = "u1fa-material-families-hint"
_LEGACY_HOME_CONTRACT_MARKER = (
    "<!-- Private beta for testing | Set up or restore U1FA AutoPA Mod -->"
)
_PROFILE_RECOMMENDATIONS: dict[str, ProfileRecommendation] = {}

_LEGACY_SETUP_CARD_RE = re.compile(
    r'<div class="card"><h2>'
    r'(?:0\. Configurazione o ripristino U1FA AutoPA Mod|0\. Set up or restore U1FA AutoPA Mod)'
    r'</h2>.*?</div>\s*',
    re.DOTALL,
)
_EMPTY_SYSTEM_GROUP_RE = re.compile(
    r'<details class="u1fa-home-group"><summary>'
    r'(?:Sistema e manutenzione|System and maintenance)'
    r'</summary><div class="u1fa-home-group-body">\s*</div></details>',
    re.DOTALL,
)

_CORE_GUIDE_IT = (
    "Scegli PLA Silk per filamenti Silk (anche bicolore): verrà usato il profilo "
    "Snapmaker PLA Silk e la temperatura predefinita sarà 230 °C. Per PLA+ o PLA "
    "veloce inserisci RAPID, HYPER, HS o HF nel nome: verrà usato il profilo "
    "SnapSpeed. Per PLA normale verrà usato PLA Basic."
)
_CORE_GUIDE_EN = (
    "Choose PLA Silk for Silk filaments (including bicolor): the Snapmaker PLA Silk "
    "profile will be used and the default temperature will be 230 °C. For PLA+ or "
    "high-speed PLA include RAPID, HYPER, HS or HF in the name: the SnapSpeed profile "
    "will be used. Standard PLA uses PLA Basic."
)

_OLD_MATERIAL_JS = (
    "document.getElementById('material').addEventListener('change',function(){var p="
    "this.value==='PETG'?['1.27','240','75']:this.value==='PLA Silk'?"
    "['1.24','230','60']:['1.24','220','60'];document.getElementById('density').value="
    "p[0];document.getElementById('nozzle-temp').value=p[1];"
    "document.getElementById('bed-temp').value=p[2];});"
)
_NEW_MATERIAL_JS = (
    "document.getElementById('material').addEventListener('change',function(){var v=this.value;"
    "var p=v.indexOf('PETG')===0?['1.27','240','75']:this.value==='PLA Silk'?"
    "['1.24','230','60']:['1.24','220','60'];document.getElementById('density').value=p[0];"
    "document.getElementById('nozzle-temp').value=p[1];document.getElementById('bed-temp').value=p[2];});"
)


def _material_options_html() -> str:
    return "".join(
        f'<option value="{material}">{material}</option>'
        for material in MATERIAL_OPTIONS
    )


def _replace_material_select(page: str) -> str:
    start = page.find(_MATERIAL_SELECT_START)
    if start < 0:
        raise ValueError("Selettore materiali U1FA non riconosciuto")
    content_start = start + len(_MATERIAL_SELECT_START)
    end = page.find(_SELECT_END, content_start)
    if end < 0:
        raise ValueError("Selettore materiali U1FA incompleto")
    return page[:content_start] + _material_options_html() + page[end:]


def _replace_legacy_guide(page: str, language: str) -> str:
    old = _CORE_GUIDE_EN if language == "en" else _CORE_GUIDE_IT
    if old not in page:
        return page
    if language == "en":
        new = (
            "Choose the real filament family directly from the Material menu. "
            "PLA Rapid is the generic high-speed PLA choice and U1FA maps it to the "
            "Snapmaker PLA SnapSpeed base profile."
        )
    else:
        new = (
            "Scegli direttamente dal menu Materiale la famiglia reale del filamento. "
            "PLA Rapid è la voce generica per i PLA veloci e U1FA la collega al profilo "
            "base Snapmaker PLA SnapSpeed."
        )
    return page.replace(old, new, 1)


def _replace_material_defaults_js(page: str) -> str:
    if _OLD_MATERIAL_JS in page:
        return page.replace(_OLD_MATERIAL_JS, _NEW_MATERIAL_JS, 1)
    # Se il core viene aggiornato in futuro, non bloccare l'intera pagina per una
    # semplice differenza JavaScript: il menu resta comunque valido e modificabile.
    return page


def enhance_new_spool_page(page: str, language: str = "it") -> str:
    """Espone tutte le famiglie già supportate da ``choose_base``.

    ``PLA Rapid`` è volutamente un nome generico: ``choose_base`` riconosce la
    parola ``rapid`` e usa il profilo Snapmaker PLA SnapSpeed. Non vengono
    inventati profili o parametri specifici del produttore.
    """
    page = _replace_material_select(page)
    page = _replace_legacy_guide(page, language)
    page = _replace_material_defaults_js(page)

    if f'id="{_HINT_ID}"' not in page:
        if _FORM_MARKER not in page:
            raise ValueError("Form nuova bobina U1FA non riconosciuta")
        if language == "en":
            hint = (
                "Supported families: PLA, PLA Rapid, PLA Silk, PLA Wood, PLA Translucent, "
                "PLA-CF, PETG, PETG HF, PETG Translucent and PETG-CF. Each choice maps "
                "to an existing Snapmaker base profile. Temperature, density and the "
                "other spool values must still follow the manufacturer's specifications."
            )
        else:
            hint = (
                "Famiglie supportate: PLA, PLA Rapid, PLA Silk, PLA Wood, PLA Translucent, "
                "PLA-CF, PETG, PETG HF, PETG Translucent e PETG-CF. Ogni scelta usa un "
                "profilo base Snapmaker già supportato. Temperatura, densità e gli altri "
                "dati devono comunque seguire le specifiche della bobina reale."
            )
        page = page.replace(
            _FORM_MARKER,
            f'<p id="{_HINT_ID}" class="muted">{hint}</p>\n{_FORM_MARKER}',
            1,
        )
    return page


def _remove_duplicate_printer_setup(page: str, language: str) -> str:
    """Lascia un solo accesso al setup stampante: l'avviso giallo in alto.

    La vecchia card numerata ``0`` viene rimossa dopo il rendering della dashboard.
    Se ``Sistema e manutenzione`` rimane vuoto, viene eliminato anche il contenitore.
    Non vengono eseguiti controlli, scritture o comandi verso la stampante.
    """
    page = _LEGACY_SETUP_CARD_RE.sub("", page, count=1)
    page = _EMPTY_SYSTEM_GROUP_RE.sub("", page, count=1)
    if language == "en":
        page = page.replace(
            "run Check printer setup from System and maintenance.",
            "use the Check printer setup button below.",
            1,
        )
    else:
        page = page.replace(
            "esegui Controlla configurazione stampante da Sistema e manutenzione.",
            "usa il pulsante Controlla configurazione stampante qui sotto.",
            1,
        )
    return page


def _remember_recommendation(ticket: str, recommendation: ProfileRecommendation) -> None:
    # I ticket sono monouso. Manteniamo soltanto una piccola cache di anteprime
    # per evitare stato persistente o qualsiasi scrittura dentro Orca.
    if len(_PROFILE_RECOMMENDATIONS) >= 128:
        oldest = next(iter(_PROFILE_RECOMMENDATIONS), None)
        if oldest is not None:
            _PROFILE_RECOMMENDATIONS.pop(oldest, None)
    _PROFILE_RECOMMENDATIONS[ticket] = recommendation


def _recommendation_html(
    recommendation: ProfileRecommendation,
    language: str,
) -> str:
    expected = html.escape(recommendation.expected_profile)
    if recommendation.confidence == "exact" and recommendation.suggested_profile:
        found = html.escape(recommendation.suggested_profile)
        if language == "en":
            return (
                '<p class="ok"><strong>Installed Orca profile check:</strong> '
                f'exact match found: <strong>{found}</strong>. Read-only check.</p>'
            )
        return (
            '<p class="ok"><strong>Controllo profili Orca installati:</strong> '
            f'corrispondenza esatta trovata: <strong>{found}</strong>. Controllo in sola lettura.</p>'
        )

    if recommendation.confidence == "smart" and recommendation.suggested_profile:
        found = html.escape(recommendation.suggested_profile)
        if language == "en":
            return (
                '<p class="warn"><strong>b22 smart suggestion:</strong> '
                f'<strong>{found}</strong> looks compatible with {expected}. '
                'This suggestion is read-only and is not applied automatically; '
                'the validated base shown above remains unchanged.</p>'
            )
        return (
            '<p class="warn"><strong>Suggerimento intelligente b22:</strong> '
            f'<strong>{found}</strong> risulta compatibile con {expected}. '
            'Il suggerimento è in sola lettura e non viene applicato automaticamente; '
            'la base convalidata mostrata sopra resta invariata.</p>'
        )

    if recommendation.confidence == "ambiguous" and recommendation.candidates:
        choices = ", ".join(html.escape(value) for value in recommendation.candidates)
        if language == "en":
            return (
                '<p class="warn"><strong>Installed Orca profile check:</strong> '
                f'multiple compatible profiles were found ({choices}). '
                'U1FA does not choose automatically.</p>'
            )
        return (
            '<p class="warn"><strong>Controllo profili Orca installati:</strong> '
            f'trovati più profili compatibili ({choices}). '
            'U1FA non sceglie automaticamente.</p>'
        )

    if language == "en":
        return (
            '<p class="muted"><strong>Installed Orca profile check:</strong> '
            f'no alternative profile was confidently identified for {expected}. '
            'No files were modified.</p>'
        )
    return (
        '<p class="muted"><strong>Controllo profili Orca installati:</strong> '
        f'nessun profilo alternativo è stato identificato con sufficiente affidabilità per {expected}. '
        'Nessun file è stato modificato.</p>'
    )


def _install_profile_discovery(gui_module: Any) -> None:
    """Aggiunge alla preview bobina un controllo profili strettamente read-only."""
    controller_cls = getattr(gui_module, "CalibrationController", None)
    preview = getattr(gui_module, "_new_spool_preview", None)
    if controller_cls is None or preview is None:
        return

    current_prepare = controller_cls.prepare_spool_creation
    if not getattr(current_prepare, "_u1fa_profile_discovery", False):
        def prepare_with_discovery(controller: Any, request: Any):
            prepared = current_prepare(controller, request)
            recommendation = recommend_installed_profile(
                controller.system_dir,
                prepared.plan.base_profile,
            )
            _remember_recommendation(prepared.ticket, recommendation)
            return prepared

        setattr(prepare_with_discovery, "_u1fa_profile_discovery", True)
        controller_cls.prepare_spool_creation = prepare_with_discovery

    current_preview = gui_module._new_spool_preview
    if getattr(current_preview, "_u1fa_profile_discovery", False):
        return

    def preview_with_discovery(
        prepared: Any,
        token: str,
        language: str = "it",
    ) -> str:
        page = current_preview(prepared, token, language=language)
        recommendation = _PROFILE_RECOMMENDATIONS.get(prepared.ticket)
        if recommendation is None:
            return page
        base_line = (
            f'<p><strong>Base Snapmaker:</strong> '
            f'{html.escape(prepared.plan.base_profile)}</p>'
        )
        if base_line not in page:
            return page
        return page.replace(
            base_line,
            base_line + "\n" + _recommendation_html(recommendation, language),
            1,
        )

    setattr(preview_with_discovery, "_u1fa_profile_discovery", True)
    gui_module._new_spool_preview = preview_with_discovery


def _install_home_cleanup(gui_module: Any) -> None:
    """Rimuove dalla home la vecchia card setup duplicata, senza toccarne la route."""
    current: Callable[..., str] = gui_module._home
    if getattr(current, "_u1fa_home_cleanup", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        return _remove_duplicate_printer_setup(page, language)

    setattr(patched, "_u1fa_home_cleanup", True)
    gui_module._home = patched


def _install_home_contract_compatibility(gui_module: Any) -> None:
    """Preserva un vecchio contratto di test senza ripristinare il banner visibile.

    La b20 sostituisce deliberatamente il banner beta con l'avviso di prima
    configurazione. Il marker HTML è un commento invisibile e non modifica
    contenuti, navigazione o comportamento della UI.
    """
    current: Callable[..., str] = gui_module._home
    if getattr(current, "_u1fa_home_contract_compat", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        if language == "en" and _LEGACY_HOME_CONTRACT_MARKER not in page:
            page = page.replace("</main>", _LEGACY_HOME_CONTRACT_MARKER + "</main>", 1)
        return page

    setattr(patched, "_u1fa_home_contract_compat", True)
    gui_module._home = patched


def install_material_ui_patch(gui_module: Any) -> None:
    """Installa tutte le estensioni desktop senza duplicarle."""
    if hasattr(gui_module, "_handler"):
        install_update_lifecycle_patch(gui_module)
    if hasattr(gui_module, "_home"):
        install_dashboard_patch(gui_module)
        _install_home_cleanup(gui_module)
        _install_home_contract_compatibility(gui_module)
    _install_profile_discovery(gui_module)

    current: Callable[..., str] = gui_module._new_spool_form
    if getattr(current, "_u1fa_material_ui_patch", False):
        return

    def patched(
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        return enhance_new_spool_page(
            current(token, error=error, language=language),
            language,
        )

    setattr(patched, "_u1fa_material_ui_patch", True)
    gui_module._new_spool_form = patched
