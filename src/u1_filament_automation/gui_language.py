from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlsplit

from .config import default_connection_config_path


SUPPORTED_LANGUAGES = frozenset({"it", "en"})
PREFERENCES_FILENAME = "preferences.json"


class LanguagePreferenceError(RuntimeError):
    pass


def default_language_preferences_path() -> Path:
    return default_connection_config_path().with_name(PREFERENCES_FILENAME)


def load_language_preference(path: Path | None = None) -> str:
    target = default_language_preferences_path() if path is None else path.expanduser()
    if not target.exists():
        return "it"
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return "it"
        language = str(payload.get("language", "it")).strip().lower()
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return "it"
    return language if language in SUPPORTED_LANGUAGES else "it"


def save_language_preference(language: str, path: Path | None = None) -> Path:
    normalized = str(language).strip().lower()
    if normalized not in SUPPORTED_LANGUAGES:
        raise LanguagePreferenceError("Lingua non valida / Invalid language")
    target = default_language_preferences_path() if path is None else path.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    try:
        temporary.write_text(
            json.dumps({"language": normalized}, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        try:
            temporary.chmod(0o600)
        except OSError:
            pass
        temporary.replace(target)
    except OSError as exc:
        raise LanguagePreferenceError(
            f"Impossibile salvare la lingua / Could not save language preference: {exc}"
        ) from exc
    return target


_EXACT_EN = {
    "Pronto": "Ready",
    "Valori dell'envelope manuale non validi": "Invalid manual envelope values",
    "Lo slot fisico deve essere compreso tra 1 e 4": "Physical slot must be between 1 and 4",
    "La temperatura deve essere compresa tra 170 e 300 °C": "Temperature must be between 170 and 300 °C",
    "Envelope non valido: comando bloccato": "Invalid envelope: command blocked",
    "Envelope oltre il limite U1FA di 10000 mm/s²: comando bloccato": "Envelope exceeds the U1FA limit of 10000 mm/s²: command blocked",
    "Intervallo K incompleto: comando bloccato": "Incomplete K range: command blocked",
    "Intervallo K non valido: comando bloccato": "Invalid K range: command blocked",
    "Cartella reale di Snapmaker Orca non configurata": "Snapmaker Orca profile folder is not configured",
    "Orca Slicer standard non rilevato su questo computer": "Standard Orca Slicer was not detected on this computer",
    "Attendere la fine della calibrazione in corso": "Wait for the current calibration to finish",
    "Attendere l'operazione già in corso": "Wait for the current operation to finish",
    "Una calibrazione è già in corso": "A calibration is already running",
    "Coda calibrazione non valida": "Invalid calibration queue",
    "Nessuna calibrazione recente da recuperare": "There is no recent calibration to recover",
    "Destinazione SSH U1 non configurata": "U1 SSH destination is not configured",
    "Conferma installazione scaduta o già usata": "Setup confirmation expired or was already used",
    "Conferma scaduta o già usata: nessuna bobina creata": "Confirmation expired or was already used: no spool was created",
    "Profilo non presente nell'inventario Spoolman corrente": "Profile is not present in the current Spoolman inventory",
    "Modalità envelope non valida": "Invalid envelope mode",
    "Inserire tutti i valori dell'envelope manuale": "Enter all manual envelope values",
    "Macro APA_COIL_SET_ENVELOPE non caricata": "APA_COIL_SET_ENVELOPE macro is not loaded",
    "Macro APA_COIL_RUN_ULTRA non caricata": "APA_COIL_RUN_ULTRA macro is not loaded",
    "Tempo massimo superato senza una suite ULTRA completa": "Maximum wait time exceeded without a complete ULTRA suite",
    "Richiesta non valida": "Invalid request",
    "Dimensione richiesta non valida": "Invalid request size",
    "Per sicurezza l'interfaccia può ascoltare solo su localhost": "For safety, the interface can listen only on localhost",
    "La porta deve essere compresa tra 1024 e 65535": "Port must be between 1024 and 65535",
    "Cartella filamenti Snapmaker Orca non trovata": "Snapmaker Orca filament folder was not found",
    "Trovate più cartelle Orca: indicare --orca-dir": "Multiple Orca folders were found: specify --orca-dir",
    "La sandbox coincide o si sovrappone ai profili Orca reali": "The sandbox matches or overlaps the real Orca profiles",
    "Spoolman non raggiungibile": "Spoolman is unreachable",
}


def _translate_error_en(message: str) -> str:
    text = str(message)
    if not text:
        return text
    if text in _EXACT_EN:
        return _EXACT_EN[text]
    if " / " in text and any(
        marker in text
        for marker in (
            "Invalid ",
            "invalid ",
            "address required",
            "use http://",
            "Cannot ",
            "Could not ",
            "Minimum ",
            "No update ",
            "No verified ",
        )
    ):
        return text.split(" / ", 1)[1].strip()

    patterns: tuple[tuple[str, str], ...] = (
        (r"^Valore numerico non valido: (.+)$", r"Invalid numeric value: \1"),
        (r"^Valori non validi per la bobina (\d+)$", r"Invalid values for spool \1"),
        (r"^Envelope oltre il limite U1FA di (.+): comando bloccato$", r"Envelope exceeds the U1FA limit of \1: command blocked"),
        (r"^Profilo base Snapmaker non trovato: (.+)\. Nessun dato verrà scritto in Spoolman\.$", r"Snapmaker base profile not found: \1. No data will be written to Spoolman."),
        (r"^Profilo base Snapmaker non trovato: (.+)\. Nessun dato scritto in Spoolman\.$", r"Snapmaker base profile not found: \1. No data was written to Spoolman."),
        (r"^Compatibilità firmware non verificata in questa sessione: eseguire prima il controllo configurazione stampante$", r"Firmware compatibility has not been verified in this session: run the printer setup check first"),
        (r"^I file o lo stato U1 sono cambiati dopo l'anteprima: operazione annullata$", r"U1 files or state changed after the preview: operation cancelled"),
        (r"^Cartella reale di Snapmaker Orca non configurata: nessuna bobina verrà creata$", r"Snapmaker Orca profile folder is not configured: no spool will be created"),
        (r"^L'ultima suite completa è precedente alla calibrazione selezionata: recupero bloccato$", r"The latest complete suite predates the selected calibration: recovery blocked"),
        (r"^Profilo Snapmaker Orca aggiornato, ma mirror Orca Slicer fallito: (.+)$", r"Snapmaker Orca profile was updated, but the Orca Slicer mirror failed: \1"),
        (r"^Mirror Orca Slicer bloccato da profili esistenti o modificati: (.+)$", r"Orca Slicer mirror blocked by existing or modified profiles: \1"),
        (r"^La bobina Spoolman ID (\d+) è già stata creata, ma la creazione del profilo Orca non è stata completata: (.+)\. Non creare di nuovo la bobina; aggiornare la pagina iniziale e riprovare la sincronizzazione\.$", r"Spoolman spool ID \1 was already created, but Orca profile creation did not complete: \2. Do not create the spool again; refresh the home page and retry synchronization."),
        (r"^Max volumetric speed non trovato nel profilo Orca ereditato\. Inserirlo nel campo di correzione manuale\.$", r"Max volumetric speed was not found in the inherited Orca profile. Enter it in the manual override field."),
    )
    for pattern, replacement in patterns:
        if re.match(pattern, text):
            return re.sub(pattern, replacement, text)
    return text


def _translate_runtime_message_en(message: str) -> str:
    text = str(message)
    exact = {
        "Controllo stato stampante e macro…": "Checking printer state and macros…",
        "Calibrazione completata; profilo Snapmaker Orca aggiornato con backup.": "Calibration completed; the Snapmaker Orca profile was updated after creating a backup.",
        "Moonraker non ha confermato il comando entro il timeout; verifico la calibrazione già avviata senza reinviarla.": "Moonraker did not confirm the command before the timeout; checking the calibration already in progress without sending it again.",
        "Connessione Moonraker ripristinata; recupero dei risultati in corso.": "Moonraker connection restored; recovering calibration results.",
        "Recupero dell'ultima suite completa da Moonraker; nessun G-code inviato.": "Recovering the latest complete suite from Moonraker; no G-code is being sent.",
    }
    if text in exact:
        return exact[text]

    patterns: tuple[tuple[str, Callable[[re.Match[str]], str]], ...] = (
        (
            r"^Calibrazione avviata: slot fisico (\d+) → EXTRUDER=(\d+), (\d+) °C\. Stato iniziale: (.+)/(.+)\.$",
            lambda m: f"Calibration started: physical slot {m.group(1)} → EXTRUDER={m.group(2)}, {m.group(3)} °C. Initial state: {m.group(4)}/{m.group(5)}.",
        ),
        (
            r"^Preparazione coda calibrazione: (\d+) bobine$",
            lambda m: f"Preparing calibration queue: {m.group(1)} spools",
        ),
        (
            r"^Coda interrotta prima della bobina (\d+)/(\d+): (.+)$",
            lambda m: f"Queue stopped before spool {m.group(1)}/{m.group(2)}: {_translate_error_en(m.group(3))}",
        ),
        (
            r"^Calibrazione sequenziale (\d+)/(\d+): slot fisico (\d+) → EXTRUDER=(\d+), (\d+) °C\. Stato iniziale: (.+)/(.+)\.$",
            lambda m: f"Sequential calibration {m.group(1)}/{m.group(2)}: physical slot {m.group(3)} → EXTRUDER={m.group(4)}, {m.group(5)} °C. Initial state: {m.group(6)}/{m.group(7)}.",
        ),
        (
            r"^Moonraker non raggiungibile dopo (\d+) tentativi: (.+)$",
            lambda m: f"Moonraker is unreachable after {m.group(1)} attempts: {_translate_error_en(m.group(2))}",
        ),
        (
            r"^Connessione Moonraker temporaneamente interrotta; nuovo tentativo (\d+)/(\d+) tra ([0-9.]+) secondi\. La calibrazione non viene riavviata\.$",
            lambda m: f"Moonraker connection temporarily interrupted; retry {m.group(1)}/{m.group(2)} in {m.group(3)} seconds. The calibration will not be restarted.",
        ),
        (
            r"^Coda completata: (\d+)/(\d+) bobine calibrate; ultimo profilo Snapmaker Orca aggiornato con backup\.$",
            lambda m: f"Queue completed: {m.group(1)}/{m.group(2)} spools calibrated; the final Snapmaker Orca profile was updated after creating a backup.",
        ),
        (
            r"^Calibrazione (\d+)/(\d+) completata; profilo Snapmaker Orca aggiornato con backup\. Avvio della bobina successiva\.$",
            lambda m: f"Calibration {m.group(1)}/{m.group(2)} completed; the Snapmaker Orca profile was updated after creating a backup. Starting the next spool.",
        ),
        (
            r"^Recupero non ancora riuscito \((\d+)/(\d+)\); nuovo tentativo tra ([0-9.]+) secondi\. Nessun G-code inviato\.$",
            lambda m: f"Recovery has not succeeded yet ({m.group(1)}/{m.group(2)}); retrying in {m.group(3)} seconds. No G-code is being sent.",
        ),
        (
            r"^Recupero non riuscito: (.+)\. Nessun G-code inviato; la calibrazione non è stata ripetuta\.$",
            lambda m: f"Recovery failed: {_translate_error_en(m.group(1))}. No G-code was sent; the calibration was not repeated.",
        ),
    )
    for pattern, builder in patterns:
        match = re.match(pattern, text)
        if match:
            return builder(match)

    suffix = ". Controllare Fluidd: non viene inviato alcun riavvio automatico."
    if text.endswith(suffix):
        detail = text[: -len(suffix)]
        return (
            f"{_translate_error_en(detail)}. Check Fluidd: no automatic restart is sent."
        )
    return _translate_error_en(text)


def _install_controller_language_persistence(gui_module: Any, preference_path: Path) -> None:
    controller_cls = gui_module.CalibrationController
    current_init = controller_cls.__init__
    if getattr(current_init, "_u1fa_language_fix", False):
        return

    def patched_init(controller: Any, *args: Any, **kwargs: Any) -> None:
        current_init(controller, *args, **kwargs)
        controller._u1fa_language_preferences_path = preference_path
        language = load_language_preference(preference_path)
        with controller._lock:
            controller._language = language

    setattr(patched_init, "_u1fa_language_fix", True)
    controller_cls.__init__ = patched_init

    def set_language(controller: Any, language: str) -> None:
        normalized = str(language).strip().lower()
        if normalized not in SUPPORTED_LANGUAGES:
            raise gui_module.GUIError("Lingua non valida / Invalid language")
        target = getattr(controller, "_u1fa_language_preferences_path", preference_path)
        try:
            save_language_preference(normalized, target)
        except LanguagePreferenceError as exc:
            raise gui_module.GUIError(str(exc)) from exc
        with controller._lock:
            controller._language = normalized

    setattr(set_language, "_u1fa_language_fix", True)
    controller_cls.set_language = set_language


def _install_language_route(gui_module: Any) -> None:
    current_factory = gui_module._handler
    if getattr(current_factory, "_u1fa_language_fix", False):
        return

    def patched_handler(controller: Any, token: str):
        BaseHandler = current_factory(controller, token)

        class Handler(BaseHandler):
            def do_GET(self) -> None:  # noqa: N802
                request = urlsplit(self.path)
                if request.path != "/language":
                    return super().do_GET()
                requested = (parse_qs(request.query).get("lang") or [""])[-1]
                requested = str(requested).strip().lower()
                if requested in SUPPORTED_LANGUAGES:
                    try:
                        controller.set_language(requested)
                    except gui_module.GUIError as exc:
                        language = controller.language()
                        self._send(
                            gui_module._home(
                                controller,
                                token,
                                str(exc),
                                language,
                            ),
                            500,
                        )
                        return
                self.send_response(303)
                self.send_header("Location", "/")
                self.end_headers()

        return Handler

    setattr(patched_handler, "_u1fa_language_fix", True)
    gui_module._handler = patched_handler


def _install_error_rendering(gui_module: Any) -> None:
    specifications = (
        ("_home", 2, 3),
        ("_connections_form", 2, 3),
        ("_batch_form", 2, 3),
        ("_standard_orca_page", 2, 3),
        ("_new_spool_form", 1, 2),
        ("_printer_setup_form", 1, 2),
        ("_updates_page", 2, 3),
    )
    for name, error_index, language_index in specifications:
        current = getattr(gui_module, name, None)
        if not callable(current) or getattr(current, "_u1fa_language_error_fix", False):
            continue

        def make_wrapper(
            renderer: Callable[..., str],
            error_position: int,
            language_position: int,
        ) -> Callable[..., str]:
            def wrapped(*args: Any, **kwargs: Any) -> str:
                mutable = list(args)
                language = str(kwargs.get("language", ""))
                if not language and len(mutable) > language_position:
                    language = str(mutable[language_position])
                if not language:
                    language = "it"
                if language == "en":
                    if "error" in kwargs:
                        kwargs = dict(kwargs)
                        kwargs["error"] = _translate_error_en(str(kwargs.get("error", "")))
                    elif len(mutable) > error_position:
                        mutable[error_position] = _translate_error_en(str(mutable[error_position]))
                return renderer(*mutable, **kwargs)

            setattr(wrapped, "_u1fa_language_error_fix", True)
            return wrapped

        setattr(gui_module, name, make_wrapper(current, error_index, language_index))


def _install_preview_cleanup(gui_module: Any) -> None:
    current = gui_module._preview
    if getattr(current, "_u1fa_language_fix", False):
        return

    def patched(selection: Any, token: str, language: str = "it") -> str:
        page = current(selection, token, language)
        if language != "en":
            return page
        return (
            page.replace("correzione manuale", "manual override")
            .replace("ugello 0.4 mm", "0.4 mm nozzle")
            .replace("Automatico filamento", "Automatic filament")
        )

    setattr(patched, "_u1fa_language_fix", True)
    gui_module._preview = patched


def _rendered_status_message_en(job: Any) -> str:
    selection = getattr(job, "selection", None)
    if job.state == "idle":
        return "Ready"
    if job.state == "checking":
        return "Checking printer state and macros…"
    if job.state == "running" and selection is not None:
        return (
            f"Calibration started: physical slot {selection.physical_slot} → "
            f"EXTRUDER={selection.internal_extruder}, {selection.temperature} °C."
        )
    if job.state == "recovering":
        return "Recovering the completed calibration from Moonraker; no G-code is being sent."
    if job.state == "completed":
        return "Calibration completed; the Snapmaker Orca profile was updated after creating a backup."
    if job.state in {"blocked", "error"}:
        return f"Calibration blocked or failed. Technical detail: {job.message}"
    return str(job.message)


def _install_status_cleanup(gui_module: Any) -> None:
    current = gui_module._status
    if getattr(current, "_u1fa_language_fix", False):
        return

    def patched(controller: Any, language: str = "it", token: str = "") -> str:
        page = current(controller, language, token)
        if language != "en":
            return page
        job = controller.snapshot()
        old_message = _rendered_status_message_en(job)
        translated = _translate_runtime_message_en(job.message)
        if job.state in {"blocked", "error"}:
            translated = f"Calibration blocked or failed. Technical detail: {translated}"
        old_html = f"<p>{html.escape(old_message)}</p>"
        new_html = f"<p>{html.escape(translated)}</p>"
        if old_html in page:
            page = page.replace(old_html, new_html, 1)
        return page

    setattr(patched, "_u1fa_language_fix", True)
    gui_module._status = patched


def install_language_fix(
    gui_module: Any,
    preference_path: Path | None = None,
) -> None:
    """Install the 2.0.5 language fix without touching printer/profile logic."""
    target = (
        default_language_preferences_path()
        if preference_path is None
        else preference_path.expanduser()
    )
    _install_controller_language_persistence(gui_module, target)
    _install_error_rendering(gui_module)
    _install_preview_cleanup(gui_module)
    _install_status_cleanup(gui_module)
    _install_language_route(gui_module)
