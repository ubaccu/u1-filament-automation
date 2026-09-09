"""Piccole estensioni della UI desktop.

La logica di associazione ai profili Snapmaker resta in ``sync.choose_base``.
Questo modulo aggiunge opzioni guidate alla pagina di creazione bobina e installa
il ciclo di chiusura sicura dopo l'apertura di un installer verificato.
"""

from __future__ import annotations

from typing import Any, Callable

from .update_lifecycle import install_update_lifecycle_patch


PLA_WOOD_OPTION = '<option value="PLA Wood">PLA Wood</option>'
_PLA_SILK_OPTION = '<option value="PLA Silk">PLA Silk</option>'
_FORM_MARKER = '<form method="post" action="/new-spool/preview">'
_HINT_ID = "u1fa-pla-wood-hint"


def enhance_new_spool_page(page: str, language: str = "it") -> str:
    """Aggiunge PLA Wood alla form esistente in modo idempotente.

    I valori iniziali di temperatura/densità restano quelli PLA standard: U1FA
    non inventa parametri specifici del produttore. L'utente può correggerli
    prima dell'anteprima, mentre ``choose_base`` seleziona il profilo Snapmaker
    PLA Wood già supportato dal motore di sincronizzazione.
    """
    if PLA_WOOD_OPTION not in page:
        if _PLA_SILK_OPTION not in page:
            raise ValueError("Selettore materiali U1FA non riconosciuto")
        page = page.replace(
            _PLA_SILK_OPTION,
            _PLA_SILK_OPTION + PLA_WOOD_OPTION,
            1,
        )

    if f'id="{_HINT_ID}"' not in page:
        if _FORM_MARKER not in page:
            raise ValueError("Form nuova bobina U1FA non riconosciuta")
        if language == "en":
            hint = (
                "Choose PLA Wood for wood-filled PLA: U1FA will use the "
                "Snapmaker PLA Wood base profile. Initial temperature and density "
                "remain standard PLA values; adjust them to the spool manufacturer's "
                "specifications before previewing."
            )
        else:
            hint = (
                "Scegli PLA Wood per i PLA caricati legno: U1FA userà il profilo base "
                "Snapmaker PLA Wood. Temperatura e densità iniziali restano quelle del "
                "PLA standard; correggile secondo i dati del produttore prima "
                "dell'anteprima."
            )
        page = page.replace(
            _FORM_MARKER,
            f'<p id="{_HINT_ID}" class="muted">{hint}</p>\n{_FORM_MARKER}',
            1,
        )
    return page


def install_material_ui_patch(gui_module: Any) -> None:
    """Installa le estensioni desktop senza duplicarle."""
    if hasattr(gui_module, "_handler"):
        install_update_lifecycle_patch(gui_module)

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
