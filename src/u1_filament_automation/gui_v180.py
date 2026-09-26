"""Final 1.8.0 safety/clarity patch for the new-spool workflow.

This module adds a read-only Orca profile inspection to the confirmation page.
It never writes to Spoolman, Orca or the printer while preparing the preview.
"""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from . import sync as sync_module
from .profile_equivalence import equivalent_profile_paths


@dataclass(frozen=True)
class OrcaProfilePreview:
    status: str
    path: Path | None = None
    actual_name: str = ""
    adaptive_pa: str = "unknown"
    equivalent_count: int = 0


@dataclass(frozen=True)
class PreparedSpoolCreationV180:
    ticket: str
    plan: Any
    profile_preview: OrcaProfilePreview


def _truthy_setting(value: Any) -> bool:
    if isinstance(value, (list, tuple)):
        return any(_truthy_setting(item) for item in value)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "on"}
    return False


def _adaptive_pa_state(path: Path) -> tuple[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return "unknown", path.stem
    if not isinstance(payload, dict):
        return "unknown", path.stem
    raw_name = payload.get("name")
    actual_name = raw_name if isinstance(raw_name, str) and raw_name.strip() else path.stem
    model = payload.get("adaptive_pressure_advance_model")
    model_present = isinstance(model, (list, tuple)) and any(
        str(item).strip() for item in model
    )
    enabled = _truthy_setting(payload.get("adaptive_pressure_advance"))
    return ("present" if enabled or model_present else "absent"), actual_name


def inspect_orca_profile(user_dir: Path | None, profile_name: str) -> OrcaProfilePreview:
    """Inspect the target profile without modifying any file.

    Exact names win. If no exact profile exists, one conservative b24 legacy
    equivalent can be reused. More than one equivalent is treated as ambiguous
    and is blocked before any Spoolman write by the controller patch below.
    """
    if user_dir is None:
        return OrcaProfilePreview("unavailable")
    try:
        root = user_dir.expanduser().resolve()
        if not root.is_dir():
            return OrcaProfilePreview("unavailable")
        wanted = sync_module.safe_filename(profile_name).casefold()
        exact: list[Path] = []
        for path in root.glob("*.json"):
            if path.is_symlink() or not path.is_file():
                continue
            if path.stem.casefold() == wanted:
                exact.append(path.resolve())
    except OSError:
        return OrcaProfilePreview("unavailable")

    exact = list(dict.fromkeys(exact))
    if len(exact) > 1:
        return OrcaProfilePreview("ambiguous", equivalent_count=len(exact))
    if len(exact) == 1:
        state, actual_name = _adaptive_pa_state(exact[0])
        return OrcaProfilePreview("exact", exact[0], actual_name, state)

    equivalents = list(dict.fromkeys(equivalent_profile_paths(root, profile_name)))
    if len(equivalents) > 1:
        return OrcaProfilePreview(
            "ambiguous",
            equivalent_count=len(equivalents),
        )
    if len(equivalents) == 1:
        state, actual_name = _adaptive_pa_state(equivalents[0])
        return OrcaProfilePreview(
            "equivalent",
            equivalents[0],
            actual_name,
            state,
            equivalent_count=1,
        )
    return OrcaProfilePreview("new", adaptive_pa="absent")


def _patch_prepare_spool_creation(gui_module: Any) -> None:
    current = gui_module.CalibrationController.prepare_spool_creation
    if getattr(current, "_u1fa_v180_profile_preview", False):
        return

    def patched(controller: Any, request: Any) -> PreparedSpoolCreationV180:
        prepared = current(controller, request)
        preview = inspect_orca_profile(
            controller.real_orca_dir,
            prepared.plan.profile_name,
        )
        if preview.status == "ambiguous":
            # current() has only read Spoolman and prepared a pending ticket.
            # Clear that ticket and fail before create_prepared_spool can POST
            # anything to Spoolman or write an Orca profile.
            with controller._lock:
                controller._pending_creation = None
            raise gui_module.GUIError(
                "Più profili Snapmaker Orca equivalenti corrispondono al filamento: "
                "creazione bloccata prima di qualsiasi scrittura in Spoolman."
            )
        enriched = PreparedSpoolCreationV180(
            ticket=prepared.ticket,
            plan=prepared.plan,
            profile_preview=preview,
        )
        with controller._lock:
            controller._pending_creation = enriched
        return enriched

    setattr(patched, "_u1fa_v180_profile_preview", True)
    gui_module.CalibrationController.prepare_spool_creation = patched


def _profile_preview_html(prepared: Any, language: str) -> str:
    preview: OrcaProfilePreview | None = getattr(prepared, "profile_preview", None)
    if preview is None:
        return ""

    if language == "en":
        title = "Actions after confirmation"
        spoolman = (
            "Spoolman: vendor "
            + ("will be reused" if prepared.plan.vendor_action == "reuse" else "will be created")
            + "; filament "
            + ("will be reused" if prepared.plan.filament_action == "reuse" else "will be created")
            + "; a new physical spool will be created."
        )
        if preview.status == "exact":
            profile = "Orca profile: exact existing profile found — it will be reused, not recreated."
        elif preview.status == "equivalent":
            profile = (
                "Orca profile: one equivalent legacy profile was found and will be reused: "
                f"<strong>{html.escape(preview.actual_name)}</strong>. No duplicate will be created."
            )
        elif preview.status == "new":
            profile = "Orca profile: no existing match was found — one new profile will be created."
        else:
            profile = "Orca profile: status unavailable."
        if preview.adaptive_pa == "present":
            pa = "Adaptive PA: present — it will not be modified during spool/profile creation."
            pa_class = "ok"
        elif preview.adaptive_pa == "absent":
            pa = "Adaptive PA: not detected — this step does not add or change PA values."
            pa_class = "muted"
        else:
            pa = "Adaptive PA: status could not be read — no PA write is performed in this step."
            pa_class = "warn"
        foot = (
            "No printer command is sent. An exact managed profile may only receive the existing "
            "white/missing colour-swatch repair; PA fields are not changed by that repair."
        )
    else:
        title = "Azioni effettive dopo la conferma"
        spoolman = (
            "Spoolman: vendor "
            + ("verrà riutilizzato" if prepared.plan.vendor_action == "reuse" else "verrà creato")
            + "; filamento "
            + ("verrà riutilizzato" if prepared.plan.filament_action == "reuse" else "verrà creato")
            + "; verrà creata una nuova bobina fisica."
        )
        if preview.status == "exact":
            profile = "Profilo Orca: profilo esatto già esistente — verrà riutilizzato, non ricreato."
        elif preview.status == "equivalent":
            profile = (
                "Profilo Orca: trovato un unico profilo legacy equivalente, che verrà riutilizzato: "
                f"<strong>{html.escape(preview.actual_name)}</strong>. Nessun doppione verrà creato."
            )
        elif preview.status == "new":
            profile = "Profilo Orca: nessun profilo corrispondente trovato — verrà creato un nuovo profilo."
        else:
            profile = "Profilo Orca: stato non disponibile."
        if preview.adaptive_pa == "present":
            pa = "Adaptive PA: presente — non verrà modificato durante la creazione bobina/profilo."
            pa_class = "ok"
        elif preview.adaptive_pa == "absent":
            pa = "Adaptive PA: non rilevato — questa fase non aggiunge né modifica valori PA."
            pa_class = "muted"
        else:
            pa = "Adaptive PA: stato non leggibile — in questa fase non viene eseguita alcuna scrittura PA."
            pa_class = "warn"
        foot = (
            "Nessun comando viene inviato alla stampante. Su un profilo esatto gestito da U1FA può "
            "avvenire soltanto la correzione già prevista di un campione colore bianco/mancante; "
            "quella correzione non modifica i campi PA."
        )

    path_line = ""
    if preview.path is not None:
        path_line = f'<p class="muted">{html.escape(str(preview.path))}</p>'
    return (
        f'<hr><h3>{title}</h3>'
        f'<p>{spoolman}</p>'
        f'<p class="ok">{profile}</p>'
        f'<p class="{pa_class}">{pa}</p>'
        f'{path_line}'
        f'<p class="muted">{foot}</p>'
    )


def _patch_new_spool_preview(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._new_spool_preview
    if getattr(current, "_u1fa_v180_profile_preview", False):
        return

    def patched(prepared: Any, token: str, language: str = "it") -> str:
        page = current(prepared, token, language=language)
        details = _profile_preview_html(prepared, language)
        marker = '<form method="post" action="/new-spool/create">'
        if details and marker in page:
            page = page.replace(marker, details + marker, 1)

        preview: OrcaProfilePreview | None = getattr(prepared, "profile_preview", None)
        if preview is not None and preview.status in {"exact", "equivalent"}:
            if language == "en":
                page = page.replace(
                    "Create spool and Orca profile",
                    "Create spool and reuse Orca profile",
                    1,
                )
            else:
                page = page.replace(
                    "Crea bobina e profilo Orca",
                    "Crea bobina e riutilizza profilo Orca",
                    1,
                )
        return page

    setattr(patched, "_u1fa_v180_profile_preview", True)
    gui_module._new_spool_preview = patched


def install_v180_patch(gui_module: Any) -> None:
    """Install final preview safeguards without performing any external write."""
    _patch_prepare_spool_creation(gui_module)
    _patch_new_spool_preview(gui_module)
