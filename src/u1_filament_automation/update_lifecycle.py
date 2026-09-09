"""Desktop update lifecycle helpers.

The update package is still opened only after the existing explicit confirmation
and SHA-256 verification.  Once the verified installer/DMG has been opened, the
local U1FA service can stop itself so macOS/Windows can replace the running app.
A running calibration always blocks this automatic close.
"""

from __future__ import annotations

import secrets
import threading
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


AUTO_CLOSE_DELAY_SECONDS = 1.0


def installer_open_allowed(job_state: str, active_states: set[str] | frozenset[str]) -> bool:
    """Return False when closing U1FA could interrupt an active calibration."""
    return job_state not in active_states


def _opened_page(gui_module: Any, path: Path, language: str) -> str:
    if language == "en":
        title = "Installer opened"
        message = (
            "The verified installer has been opened. U1FA will now close "
            "automatically so the installed application can be replaced safely."
        )
        detail = "No command is sent to the Snapmaker U1."
    else:
        title = "Installer aperto"
        message = (
            "Il pacchetto verificato è stato aperto. U1FA ora si chiuderà "
            "automaticamente così potrai sostituire l'applicazione senza l'errore «in uso»."
        )
        detail = "Nessun comando viene inviato alla Snapmaker U1."
    body = (
        f"<h1>{title}</h1><div class=\"card\">"
        f"<p class=\"ok\"><strong>{message}</strong></p>"
        f"<p><code>{path}</code></p>"
        f"<p class=\"muted\">{detail}</p></div>"
    )
    return gui_module._page(title, body, language=language)


def _schedule_server_shutdown(server: Any, delay: float = AUTO_CLOSE_DELAY_SECONDS) -> threading.Thread:
    """Stop the local HTTP service shortly after the success page is sent."""
    def worker() -> None:
        time.sleep(max(0.0, delay))
        server.shutdown()

    thread = threading.Thread(
        target=worker,
        name="u1fa-update-auto-close",
        daemon=True,
    )
    thread.start()
    return thread


def install_update_lifecycle_patch(gui_module: Any) -> None:
    """Patch only the verified-installer POST route used by the desktop app."""
    current_factory = gui_module._handler
    if getattr(current_factory, "_u1fa_update_lifecycle_patch", False):
        return

    def patched_handler(controller: Any, token: str):
        BaseHandler = current_factory(controller, token)

        class Handler(BaseHandler):
            def do_POST(self) -> None:  # noqa: N802
                path = urlsplit(self.path).path
                if path != "/updates/open":
                    return super().do_POST()

                language = controller.language()
                try:
                    values = gui_module._form(self)
                    if not secrets.compare_digest(values.get("token", ""), token):
                        raise gui_module.GUIError(
                            gui_module._tr(
                                language,
                                "Sessione non valida: operazione bloccata",
                                "Invalid session: operation blocked",
                            )
                        )
                    if values.get("confirm") != "yes":
                        raise gui_module.GUIError(
                            gui_module._tr(
                                language,
                                "Conferma installazione mancante",
                                "Installation confirmation is missing",
                            )
                        )
                    state = controller.snapshot().state
                    if not installer_open_allowed(state, gui_module.ACTIVE_CALIBRATION_STATES):
                        raise gui_module.GUIError(
                            gui_module._tr(
                                language,
                                "Aggiornamento bloccato durante la calibrazione: attendi il completamento prima di aprire l'installer.",
                                "Update blocked during calibration: wait for completion before opening the installer.",
                            )
                        )

                    opened = controller.open_downloaded_update()
                    self._send(_opened_page(gui_module, opened, language))
                    _schedule_server_shutdown(self.server)
                    return
                except (ValueError, UnicodeError, gui_module.GUIError) as exc:
                    self._send(
                        gui_module._updates_page(
                            controller,
                            token,
                            str(exc),
                            language,
                        ),
                        400,
                    )

        return Handler

    setattr(patched_handler, "_u1fa_update_lifecycle_patch", True)
    gui_module._handler = patched_handler
