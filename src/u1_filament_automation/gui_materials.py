"""Piccole estensioni della UI desktop.

La logica di associazione ai profili Snapmaker resta in ``sync.choose_base``.
Questo modulo espone nella pagina di creazione bobina tutte le famiglie già
supportate dal motore, installa la dashboard b17 e mantiene il ciclo di
chiusura sicura dopo l'apertura di un installer verificato.
"""

from __future__ import annotations

from typing import Any, Callable

from .gui_dashboard import install_dashboard_patch
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


def install_material_ui_patch(gui_module: Any) -> None:
    """Installa tutte le estensioni desktop senza duplicarle."""
    if hasattr(gui_module, "_handler"):
        install_update_lifecycle_patch(gui_module)
    if hasattr(gui_module, "_home"):
        install_dashboard_patch(gui_module)

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
