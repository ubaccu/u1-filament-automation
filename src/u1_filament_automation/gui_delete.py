from __future__ import annotations

import html
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlsplit

from .filament_delete import (
    FilamentDeletionError,
    FilamentDeletionPlan,
    FilamentDeletionResult,
    deletion_candidates,
    execute_filament_deletion,
    inventory_with_archived_spools,
    plan_filament_deletion,
)
from .spoolman import ServiceError


_HOME_MARKER = "<!-- u1fa-filament-delete -->"


@dataclass(frozen=True)
class PreparedFilamentDeletion:
    ticket: str
    plan: FilamentDeletionPlan


@dataclass(frozen=True)
class FilamentDeletionReceipt:
    result: FilamentDeletionResult


def _install_controller_patch(gui_module: Any) -> None:
    controller_cls = getattr(gui_module, "CalibrationController", None)
    if controller_cls is None:
        return

    current_init = controller_cls.__init__
    if getattr(current_init, "_u1fa_filament_delete", False):
        return

    def patched_init(controller: Any, *args: Any, **kwargs: Any) -> None:
        current_init(controller, *args, **kwargs)
        controller._deletion_lock = threading.Lock()
        controller._pending_deletion = None
        controller._last_deletion = None

    setattr(patched_init, "_u1fa_filament_delete", True)
    controller_cls.__init__ = patched_init

    def prepare_filament_deletion(
        controller: Any,
        filament_id: int | str,
        *,
        delete_orca_profile: bool = True,
    ) -> PreparedFilamentDeletion:
        with controller._lock:
            if controller._job.state in gui_module.ACTIVE_CALIBRATION_STATES:
                raise gui_module.GUIError(
                    "Attendere la fine della calibrazione in corso / "
                    "Wait for the current calibration to finish"
                )
        if controller.real_orca_dir is None:
            raise gui_module.GUIError(
                "Cartella reale di Snapmaker Orca non configurata / "
                "Real Snapmaker Orca folder is not configured"
            )
        client = controller._spoolman_client()
        try:
            inventory = inventory_with_archived_spools(client)
            plan = plan_filament_deletion(
                inventory,
                filament_id,
                controller._managed_profiles,
                delete_orca_profile=delete_orca_profile,
            )
        except (ServiceError, ValueError) as exc:
            raise gui_module.GUIError(str(exc)) from exc
        prepared = PreparedFilamentDeletion(
            ticket=secrets.token_urlsafe(32),
            plan=plan,
        )
        with controller._lock:
            controller._pending_deletion = prepared
        return prepared

    def delete_prepared_filament(
        controller: Any,
        ticket: str,
    ) -> FilamentDeletionReceipt:
        with controller._deletion_lock:
            with controller._lock:
                prepared = controller._pending_deletion
                if prepared is None or not secrets.compare_digest(prepared.ticket, ticket):
                    raise gui_module.GUIError(
                        "Conferma cancellazione scaduta o già usata / "
                        "Deletion confirmation expired or was already used"
                    )
                controller._pending_deletion = None
                if controller._job.state in gui_module.ACTIVE_CALIBRATION_STATES:
                    raise gui_module.GUIError(
                        "Attendere la fine della calibrazione in corso / "
                        "Wait for the current calibration to finish"
                    )
            if controller.real_orca_dir is None:
                raise gui_module.GUIError(
                    "Cartella reale di Snapmaker Orca non configurata / "
                    "Real Snapmaker Orca folder is not configured"
                )
            client = controller._spoolman_client()
            try:
                result = execute_filament_deletion(
                    client,
                    prepared.plan,
                    real_orca_dir=controller.real_orca_dir,
                    watch_state_path=controller._monitor_state_path,
                    managed_profiles=controller._managed_profiles,
                )
            except FilamentDeletionError as exc:
                detail = ""
                if exc.deleted_spool_ids:
                    detail = (
                        " Bobine già eliminate / Spools already deleted: "
                        + ", ".join(str(item) for item in exc.deleted_spool_ids)
                        + "."
                    )
                raise gui_module.GUIError(str(exc) + detail) from exc
            controller._managed_profiles = set(result.managed_profiles_after)
            try:
                controller._accept_inventory(client.inventory())
            except (ServiceError, ValueError):
                pass
            now = time.strftime("%H:%M:%S")
            controller._set_monitor(gui_module.ProfileMonitorSnapshot(
                "ready",
                "Filamento eliminato; Spoolman e stato U1FA aggiornati",
                "Filament deleted; Spoolman and U1FA state updated",
                (),
                now,
            ))
            receipt = FilamentDeletionReceipt(result=result)
            with controller._lock:
                controller._last_deletion = receipt
            return receipt

    def last_deletion(controller: Any) -> FilamentDeletionReceipt | None:
        with controller._lock:
            return controller._last_deletion

    controller_cls.prepare_filament_deletion = prepare_filament_deletion
    controller_cls.delete_prepared_filament = delete_prepared_filament
    controller_cls.last_deletion = last_deletion


def _candidate_label(candidate: Any, language: str) -> str:
    total = len(candidate.spool_ids)
    archived = len(candidate.archived_spool_ids)
    if language == "en":
        suffix = f"{total} linked spool(s)"
        if archived:
            suffix += f", {archived} archived"
    else:
        suffix = f"{total} bobina/e collegata/e"
        if archived:
            suffix += f", {archived} archiviata/e"
    return f"[ID {candidate.filament_id}] {candidate.display_name} — {suffix}"


def _delete_form(
    gui_module: Any,
    controller: Any,
    token: str,
    error: str = "",
    language: str = "it",
) -> str:
    error_box = "" if not error else f'<p class="warn">{html.escape(error)}</p>'
    try:
        inventory = inventory_with_archived_spools(controller._spoolman_client())
        candidates = deletion_candidates(inventory)
        options = "".join(
            f'<option value="{html.escape(str(item.filament_id))}">{html.escape(_candidate_label(item, language))}</option>'
            for item in candidates
        )
        if not options:
            options = f'<option value="">{gui_module._tr(language, "Nessun filamento disponibile", "No filament available")}</option>'
    except (ServiceError, ValueError) as exc:
        options = f'<option value="">{gui_module._tr(language, "Spoolman non disponibile", "Spoolman unavailable")}</option>'
        error_box += f'<p class="warn">{html.escape(str(exc))}</p>'

    body = f"""
<h1>{gui_module._tr(language, 'Elimina filamento', 'Delete filament')}</h1>
<div class="card">{error_box}
<p>{gui_module._tr(language, 'Questa procedura elimina prima tutte le bobine collegate al filamento, comprese quelle archiviate, e poi elimina il filamento da Spoolman.', 'This procedure first deletes every spool linked to the filament, including archived spools, and then deletes the filament from Spoolman.')}</p>
<p class="warn"><strong>{gui_module._tr(language, 'Operazione irreversibile.', 'Irreversible operation.')}</strong> {gui_module._tr(language, 'Il vendor non viene eliminato e non viene inviato alcun comando alla U1.', 'The vendor is not deleted and no command is sent to the U1.')}</p>
<form method="post" action="/delete-filament/preview">
<input type="hidden" name="token" value="{token}">
<label>{gui_module._tr(language, 'Filamento Spoolman', 'Spoolman filament')}</label>
<select name="filament_id" required>{options}</select>
<label><input style="width:auto" type="checkbox" name="delete_orca_profile" value="yes" checked> {gui_module._tr(language, 'Elimina anche il profilo Orca se è gestito da U1FA', 'Also delete the Orca profile if it is managed by U1FA')}</label>
<p class="muted">{gui_module._tr(language, 'Un profilo Orca non gestito da U1FA non verrà mai cancellato automaticamente.', 'An Orca profile not managed by U1FA is never deleted automatically.')}</p>
<p><button class="danger" type="submit">{gui_module._tr(language, 'Mostra cosa verrà eliminato', 'Preview what will be deleted')}</button> <a class="button secondary" href="/">{gui_module._tr(language, 'Annulla', 'Cancel')}</a></p>
</form></div>
"""
    return gui_module._page(
        gui_module._tr(language, "Elimina filamento", "Delete filament"),
        body,
        language=language,
    )


def _delete_preview(
    gui_module: Any,
    prepared: PreparedFilamentDeletion,
    token: str,
    language: str,
) -> str:
    plan = prepared.plan
    if plan.spool_ids:
        spool_items = "".join(
            f"<li>ID {html.escape(str(item))}{' — ' + gui_module._tr(language, 'archiviata', 'archived') if item in plan.archived_spool_ids else ''}</li>"
            for item in plan.spool_ids
        )
    else:
        spool_items = f"<li>{gui_module._tr(language, 'Nessuna bobina collegata', 'No linked spools')}</li>"

    if plan.profile_managed and plan.delete_orca_profile:
        orca_text = gui_module._tr(
            language,
            f"Il profilo Orca gestito da U1FA “{plan.profile_name}” verrà eliminato insieme ai relativi file U1FA.",
            f"The U1FA-managed Orca profile “{plan.profile_name}” will be deleted together with its U1FA files.",
        )
    elif plan.profile_managed:
        orca_text = gui_module._tr(
            language,
            f"Il profilo Orca “{plan.profile_name}” verrà mantenuto, ma non sarà più marcato come gestito da U1FA.",
            f"The Orca profile “{plan.profile_name}” will be kept, but it will no longer be marked as managed by U1FA.",
        )
    else:
        orca_text = gui_module._tr(
            language,
            "Il profilo Orca corrispondente non risulta gestito da U1FA e non verrà toccato.",
            "The matching Orca profile is not managed by U1FA and will not be touched.",
        )

    body = f"""
<h1>{gui_module._tr(language, 'Conferma cancellazione', 'Confirm deletion')}</h1>
<div class="card">
<p><strong>{gui_module._tr(language, 'Filamento', 'Filament')}:</strong> {html.escape(plan.display_name)} (ID {html.escape(str(plan.filament_id))})</p>
<p><strong>{gui_module._tr(language, 'Bobine che verranno eliminate prima', 'Spools that will be deleted first')}:</strong></p><ul>{spool_items}</ul>
<p>{html.escape(orca_text)}</p>
<p class="warn"><strong>{gui_module._tr(language, 'Dopo la conferma non è possibile annullare.', 'After confirmation this cannot be undone.')}</strong></p>
<form method="post" action="/delete-filament/apply">
<input type="hidden" name="token" value="{token}">
<input type="hidden" name="ticket" value="{prepared.ticket}">
<label><input style="width:auto" type="checkbox" name="confirm" value="yes" required> {gui_module._tr(language, 'Confermo di voler eliminare le bobine elencate e il filamento', 'I confirm that I want to delete the listed spools and the filament')}</label>
<p><button class="danger" type="submit">{gui_module._tr(language, 'Elimina definitivamente', 'Delete permanently')}</button> <a class="button secondary" href="/delete-filament">{gui_module._tr(language, 'Annulla', 'Cancel')}</a></p>
</form></div>
"""
    return gui_module._page(
        gui_module._tr(language, "Conferma cancellazione", "Confirm deletion"),
        body,
        language=language,
    )


def _delete_result(
    gui_module: Any,
    receipt: FilamentDeletionReceipt,
    language: str,
) -> str:
    result = receipt.result
    spool_ids = ", ".join(str(item) for item in result.deleted_spool_ids) or gui_module._tr(language, "nessuna", "none")
    if result.orca_files_deleted:
        orca = "<ul>" + "".join(
            f"<li>{html.escape(item)}</li>" for item in result.orca_files_deleted
        ) + "</ul>"
    elif result.plan.profile_managed and not result.plan.delete_orca_profile:
        orca = f'<p>{gui_module._tr(language, "Profilo Orca mantenuto come richiesto.", "Orca profile kept as requested.")}</p>'
    else:
        orca = f'<p class="muted">{gui_module._tr(language, "Nessun file Orca eliminato.", "No Orca files deleted.")}</p>'
    warnings = "" if not result.warnings else (
        '<div class="warn"><strong>'
        + gui_module._tr(language, "Avvisi", "Warnings")
        + ":</strong><ul>"
        + "".join(f"<li>{html.escape(item)}</li>" for item in result.warnings)
        + "</ul></div>"
    )
    body = f"""
<h1>{gui_module._tr(language, 'Filamento eliminato', 'Filament deleted')}</h1>
<div class="card">
<p class="ok"><strong>{html.escape(result.plan.display_name)}</strong> — {gui_module._tr(language, 'eliminazione Spoolman completata', 'Spoolman deletion completed')}.</p>
<p><strong>{gui_module._tr(language, 'Bobine eliminate', 'Deleted spools')}:</strong> {html.escape(spool_ids)}</p>
<p><strong>{gui_module._tr(language, 'Filamento eliminato', 'Deleted filament')}:</strong> ID {html.escape(str(result.plan.filament_id))}</p>
<p><strong>{gui_module._tr(language, 'Pulizia Orca / U1FA', 'Orca / U1FA cleanup')}:</strong></p>{orca}{warnings}
<p><a class="button" href="/">{gui_module._tr(language, 'Torna alla schermata iniziale', 'Return to home')}</a> <a class="button secondary" href="/delete-filament">{gui_module._tr(language, 'Elimina un altro filamento', 'Delete another filament')}</a></p>
</div>
"""
    return gui_module._page(
        gui_module._tr(language, "Filamento eliminato", "Filament deleted"),
        body,
        language=language,
    )


def _install_home_patch(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._home
    if getattr(current, "_u1fa_filament_delete", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        if _HOME_MARKER in page:
            return page
        card = f"""
{_HOME_MARKER}<div class="card"><h2>{gui_module._tr(language, 'Gestione filamenti', 'Filament management')}</h2>
<p>{gui_module._tr(language, 'Elimina in modo guidato un filamento Spoolman e tutte le bobine collegate, comprese quelle archiviate.', 'Safely delete a Spoolman filament and all linked spools, including archived ones.')}</p>
<p><a class="button danger" href="/delete-filament">{gui_module._tr(language, 'Elimina filamento', 'Delete filament')}</a></p></div>
"""
        return page.replace("</main>", card + "</main>", 1)

    setattr(patched, "_u1fa_filament_delete", True)
    gui_module._home = patched


def _install_handler_patch(gui_module: Any) -> None:
    current = gui_module._handler
    if getattr(current, "_u1fa_filament_delete", False):
        return

    def patched_handler(controller: Any, token: str):
        base_handler = current(controller, token)

        class Handler(base_handler):
            def do_GET(self) -> None:  # noqa: N802
                path = urlsplit(self.path).path
                language = controller.language()
                if path == "/delete-filament":
                    self._send(_delete_form(gui_module, controller, token, language=language))
                    return
                if path == "/filament-deleted":
                    receipt = controller.last_deletion()
                    if receipt is None:
                        self._send(
                            _delete_form(
                                gui_module,
                                controller,
                                token,
                                gui_module._tr(language, "Nessuna cancellazione appena eseguita", "No deletion was just completed"),
                                language,
                            ),
                            404,
                        )
                    else:
                        self._send(_delete_result(gui_module, receipt, language))
                    return
                super().do_GET()

            def do_POST(self) -> None:  # noqa: N802
                path = urlsplit(self.path).path
                if path not in {"/delete-filament/preview", "/delete-filament/apply"}:
                    super().do_POST()
                    return
                language = controller.language()
                try:
                    values = gui_module._form(self)
                    if not secrets.compare_digest(values.get("token", ""), token):
                        raise gui_module.GUIError(
                            gui_module._tr(language, "Sessione non valida: operazione bloccata", "Invalid session: operation blocked")
                        )
                    if path == "/delete-filament/preview":
                        filament_id = values.get("filament_id", "").strip()
                        if not filament_id:
                            raise gui_module.GUIError(
                                gui_module._tr(language, "Seleziona un filamento", "Select a filament")
                            )
                        prepared = controller.prepare_filament_deletion(
                            filament_id,
                            delete_orca_profile=values.get("delete_orca_profile") == "yes",
                        )
                        self._send(_delete_preview(gui_module, prepared, token, language))
                        return
                    if values.get("confirm") != "yes":
                        raise gui_module.GUIError(
                            gui_module._tr(language, "Conferma esplicita mancante: nessuna cancellazione eseguita", "Explicit confirmation missing: nothing was deleted")
                        )
                    controller.delete_prepared_filament(values.get("ticket", ""))
                    self.send_response(303)
                    self.send_header("Location", "/filament-deleted")
                    self.end_headers()
                except (ValueError, UnicodeError, ServiceError, gui_module.GUIError) as exc:
                    self._send(
                        _delete_form(gui_module, controller, token, str(exc), language),
                        400,
                    )

        return Handler

    setattr(patched_handler, "_u1fa_filament_delete", True)
    gui_module._handler = patched_handler


def install_filament_delete_ui_patch(gui_module: Any) -> None:
    """Installa la cancellazione guidata senza modificare la U1 o i profili non gestiti."""
    _install_controller_patch(gui_module)
    if hasattr(gui_module, "_home"):
        _install_home_patch(gui_module)
    if hasattr(gui_module, "_handler"):
        _install_handler_patch(gui_module)
