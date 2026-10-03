from __future__ import annotations

import html
import re
from typing import Any, Callable

from . import gui_delete as gui_delete_module
from . import gui_language as language_module


_EXACT_EN_EXTRA = {
    "Materiale non ancora associato a un profilo base Snapmaker; creazione bloccata": "Material is not yet associated with a Snapmaker base profile; creation blocked",
    "Il profilo Orca non appartiene a una cartella autorizzata": "The Orca profile is outside an authorized folder",
    "Ciclo rilevato nell'ereditarietà dei profili Orca": "A loop was detected in Orca profile inheritance",
    "Catena di ereditarietà Orca troppo lunga": "The Orca inheritance chain is too long",
    "Il flusso volumetrico massimo deve essere tra 0 e 100 mm3/s": "Maximum volumetric flow must be between 0 and 100 mm3/s",
    "La velocità minima del produttore deve essere inferiore alla massima": "The manufacturer minimum speed must be lower than the maximum speed",
    "I limiti scelti non lasciano spazio per tre velocità di calibrazione distinte": "The selected limits do not allow three distinct calibration speeds",
    "Impossibile costruire un envelope crescente dai limiti scelti": "Cannot build an increasing envelope from the selected limits",
    "Il log non contiene né un ID bobina Spoolman né un nome filamento": "The log contains neither a Spoolman spool ID nor a filament name",
    "La cartella backup contiene un link simbolico: scrittura bloccata": "The backup folder contains a symbolic link: write blocked",
    "Il profilo risolto esce dalla cartella autorizzata: scrittura bloccata": "The resolved profile is outside the authorized folder: write blocked",
    "Versione del calibratore non riconosciuta: configurazione bloccata": "Unrecognized calibrator version: setup blocked",
    "Macro Adaptive PA già presente ma non riconosciuta: nessuna sovrascrittura": "An Adaptive PA macro is already present but is not recognized: nothing will be overwritten",
    "Macro Adaptive PA riconosciuta ma appartenente a un'altra linea firmware": "The Adaptive PA macro is recognized but belongs to a different firmware line",
    "printer.cfg non è UTF-8: modifica bloccata": "printer.cfg is not UTF-8: modification blocked",
    "Verifica finale calibratore AutoPA fallita": "Final AutoPA calibrator verification failed",
    "Verifica finale macro Adaptive PA fallita": "Final Adaptive PA macro verification failed",
    "Destinazione SSH non valida": "Invalid SSH destination",
    "Il file è cambiato dopo il controllo; installazione annullata": "The file changed after verification; installation cancelled",
    "Backup non appartenente al calibratore U1FA": "The backup does not belong to the U1FA calibrator",
    "Filamento Spoolman non trovato o ID ambiguo": "Spoolman filament not found or ID is ambiguous",
    "Il filamento Spoolman selezionato non ha un ID valido": "The selected Spoolman filament does not have a valid ID",
    "Spoolman è cambiato dopo l'anteprima: cancellazione annullata prima di qualsiasi modifica": "Spoolman changed after the preview: deletion cancelled before any modification",
}


_PATTERNS_EXTRA: tuple[tuple[str, str], ...] = (
    (r"^Profilo Orca non leggibile: (.+)$", r"Orca profile is not readable: \1"),
    (r"^Profilo Orca non valido: (.+)$", r"Invalid Orca profile: \1"),
    (r"^La velocità (minima|massima) del produttore deve essere tra 0 e 1000 mm/s$", r"The manufacturer \1 speed must be between 0 and 1000 mm/s"),
    (r"^La bobina Spoolman ID (\d+) non è presente nell'inventario$", r"Spoolman spool ID \1 is not present in the inventory"),
    (r"^La bobina Spoolman ID (\d+) corrisponde a più profili$", r"Spoolman spool ID \1 matches multiple profiles"),
    (r"^Nessun profilo Spoolman corrisponde al filamento del log: (.+)$", r"No Spoolman profile matches the filament in the log: \1"),
    (r"^Nome filamento ambiguo \((.+)\); profili possibili: (.+)$", r"Ambiguous filament name (\1); possible profiles: \2"),
    (r"^Impossibile leggere la cartella profili: (.+)$", r"Cannot read the profile folder: \1"),
    (r"^Il profilo (.+) è un link simbolico: scrittura bloccata$", r"Profile \1 is a symbolic link: write blocked"),
    (r"^Profilo Orca non trovato: (.+)\. Crearlo prima con sync/watch nella stessa cartella\.$", r"Orca profile not found: \1. Create it first with sync/watch in the same folder."),
    (r"^Più JSON Orca corrispondono a (.+); nessuna modifica eseguita$", r"Multiple Orca JSON files match \1; no changes were made"),
    (r"^JSON Orca non valido \((.+)\): (.+)$", r"Invalid Orca JSON (\1): \2"),
    (r"^Creazione del backup fallita: (.+)$", r"Backup creation failed: \1"),
    (r"^Scrittura atomica fallita: (.+)$", r"Atomic write failed: \1"),
    (r"^Asset incorporato non leggibile: (.+)$", r"Bundled asset is not readable: \1"),
    (r"^Asset incorporato non valido: atteso (.+), trovato (.+)$", r"Invalid bundled asset: expected \1, found \2"),
    (r"^Controllo sintattico Python fallito: (.+)$", r"Python syntax validation failed: \1"),
    (r"^Impossibile leggere (.+): (.+)$", r"Cannot read \1: \2"),
    (r"^Configurazione principale U1 non trovata: (.+)$", r"Main U1 configuration not found: \1"),
    (r"^Installazione annullata: (.+)$", r"Installation cancelled: \1"),
    (r"^Verifica SHA-256 dopo la sostituzione fallita$", r"SHA-256 verification after replacement failed"),
    (r"^Risposta inattesa dall'endpoint (.+)$", r"Unexpected response from endpoint \1"),
    (r"^Cartella profili Orca non leggibile: (.+)$", r"Orca profile folder is not readable: \1"),
    (r"^Cancellazione interrotta eliminando la bobina Spoolman ID (.+): (.+)$", r"Deletion stopped while removing Spoolman spool ID \1: \2"),
    (r"^Le bobine collegate sono state eliminate, ma il filamento Spoolman ID (.+) non è stato cancellato: (.+)$", r"The linked spools were deleted, but Spoolman filament ID \1 was not deleted: \2"),
    (r"^Profilo Orca non eliminato \((.+)\): (.+)$", r"Orca profile was not deleted (\1): \2"),
    (r"^Stato monitor non aggiornato: (.+)$", r"Monitor state was not updated: \1"),
    (r"^Più profili Snapmaker Orca equivalenti corrispondono al filamento: creazione bloccata prima di qualsiasi scrittura in Spoolman\.$", r"Multiple equivalent Snapmaker Orca profiles match the filament: creation blocked before any Spoolman write."),
)


def _translate_firmware_detail(detail: str) -> str:
    translated = detail
    replacements = (
        ("baseline 1.5.2/PAXX non corrisponde agli hash convalidati", "the 1.5.2/PAXX baseline does not match the validated hashes"),
        ("file mancanti=", "missing files="),
        ("trovato=", "found="),
        ("atteso=", "expected="),
        ("<vuoto>", "<empty>"),
        ("<mancante>", "<missing>"),
    )
    for old, new in replacements:
        translated = translated.replace(old, new)
    return translated


def translate_error_en(message: str) -> str:
    text = str(message)
    if not text:
        return text

    current = language_module._translate_error_en_base(text)
    if current != text:
        return current

    if text in _EXACT_EN_EXTRA:
        return _EXACT_EN_EXTRA[text]

    if text.startswith("Client OpenSSH non trovato / OpenSSH Client not found."):
        return (
            "OpenSSH Client not found. On Windows enable it in Settings > System > "
            "Optional features; on Linux install openssh-client."
        )

    firmware_match = re.match(
        r"^Firmware/componenti non convalidati: (.+) / Firmware or components not validated\.$",
        text,
    )
    if firmware_match:
        return "Firmware or components not validated: " + _translate_firmware_detail(
            firmware_match.group(1)
        )

    # Deletion errors can append a bilingual partial-state suffix. Handle this
    # before the broader deletion patterns so no Italian fragment survives.
    suffix_match = re.match(
        r"^(.*) Bobine già eliminate / Spools already deleted: ([0-9, ]+)\.$",
        text,
    )
    if suffix_match:
        base = translate_error_en(suffix_match.group(1))
        return f"{base} Spools already deleted: {suffix_match.group(2)}."

    for pattern, replacement in _PATTERNS_EXTRA:
        if re.match(pattern, text):
            translated = re.sub(pattern, replacement, text)
            # Nested service errors can themselves be localized.
            for prefix in (
                "Deletion stopped while removing Spoolman spool ID ",
                "The linked spools were deleted, but Spoolman filament ID ",
                "Installation cancelled: ",
            ):
                if translated.startswith(prefix) and ": " in translated:
                    head, tail = translated.rsplit(": ", 1)
                    nested = translate_error_en(tail)
                    if nested != tail:
                        translated = head + ": " + nested
            return translated

    return text


def _translate_warn_paragraphs(page: str) -> str:
    pattern = re.compile(r'<p class="warn">(.*?)</p>')

    def repl(match: re.Match[str]) -> str:
        raw = html.unescape(re.sub(r"<[^>]+>", "", match.group(1)))
        translated = translate_error_en(raw)
        if translated == raw:
            return match.group(0)
        return f'<p class="warn">{html.escape(translated)}</p>'

    return pattern.sub(repl, page)


def _translate_warning_items(page: str) -> str:
    marker = '<div class="warn"><strong>Warnings:</strong><ul>'
    if marker not in page:
        return page
    head, tail = page.split(marker, 1)
    items, remainder = tail.split("</ul></div>", 1)

    def repl(match: re.Match[str]) -> str:
        raw = html.unescape(match.group(1))
        return f"<li>{html.escape(translate_error_en(raw))}</li>"

    items = re.sub(r"<li>(.*?)</li>", repl, items)
    return head + marker + items + "</ul></div>" + remainder


def _install_delete_rendering_cleanup() -> None:
    current_form: Callable[..., str] = gui_delete_module._delete_form
    if not getattr(current_form, "_u1fa_language_extra", False):
        def patched_form(*args: Any, **kwargs: Any) -> str:
            language = str(kwargs.get("language", ""))
            if not language and len(args) >= 5:
                language = str(args[4])
            mutable = list(args)
            if language == "en":
                if "error" in kwargs:
                    kwargs = dict(kwargs)
                    kwargs["error"] = translate_error_en(str(kwargs.get("error", "")))
                elif len(mutable) >= 4:
                    mutable[3] = translate_error_en(str(mutable[3]))
            page = current_form(*mutable, **kwargs)
            if language != "en":
                return page
            return _translate_warn_paragraphs(page).replace(">Filamento ", ">Filament ")

        setattr(patched_form, "_u1fa_language_extra", True)
        gui_delete_module._delete_form = patched_form

    current_result: Callable[..., str] = gui_delete_module._delete_result
    if not getattr(current_result, "_u1fa_language_extra", False):
        def patched_result(*args: Any, **kwargs: Any) -> str:
            language = str(kwargs.get("language", ""))
            if not language and len(args) >= 3:
                language = str(args[2])
            page = current_result(*args, **kwargs)
            return _translate_warning_items(page) if language == "en" else page

        setattr(patched_result, "_u1fa_language_extra", True)
        gui_delete_module._delete_result = patched_result


def install_language_extra(gui_module: Any) -> None:
    """Complete EN cleanup for technical GUI error paths without changing core logic."""
    if not hasattr(language_module, "_translate_error_en_base"):
        language_module._translate_error_en_base = language_module._translate_error_en
    language_module._translate_error_en = translate_error_en
    gui_module._u1fa_translate_error_en = translate_error_en
    _install_delete_rendering_cleanup()
