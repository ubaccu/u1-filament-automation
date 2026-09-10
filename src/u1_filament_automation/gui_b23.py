from __future__ import annotations

import html
import ipaddress
import json
import re
import secrets
from typing import Any, Callable
from urllib.parse import urlsplit

from .network_discovery import MoonrakerCandidate, discover_moonraker_candidates


_LOCATION_LABEL_IT = "Posizione bobina / stoccaggio (facoltativa)"
_LOCATION_LABEL_EN = "Spool location / storage (optional)"


def _markdown_inline(value: str) -> str:
    escaped = html.escape(value)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    return escaped


def render_release_notes(markdown: str) -> str:
    """Render the small Markdown subset used by U1FA release notes safely."""
    lines = markdown.splitlines()
    parts: list[str] = []
    bullets: list[str] = []

    def flush_bullets() -> None:
        nonlocal bullets
        if bullets:
            parts.append("<ul>" + "".join(f"<li>{item}</li>" for item in bullets) + "</ul>")
            bullets = []

    for raw in lines:
        line = raw.strip()
        if not line:
            flush_bullets()
            continue
        if line == "---":
            flush_bullets()
            parts.append("<hr>")
        elif line.startswith("### "):
            flush_bullets()
            parts.append(f"<h4>{_markdown_inline(line[4:])}</h4>")
        elif line.startswith("## "):
            flush_bullets()
            parts.append(f"<h3>{_markdown_inline(line[3:])}</h3>")
        elif line.startswith("# "):
            flush_bullets()
            parts.append(f"<h3>{_markdown_inline(line[2:])}</h3>")
        elif line.startswith(("- ", "* ")):
            bullets.append(_markdown_inline(line[2:]))
        else:
            flush_bullets()
            parts.append(f"<p>{_markdown_inline(line)}</p>")
    flush_bullets()
    return "".join(parts)


def _patch_new_spool_form(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._new_spool_form
    if getattr(current, "_u1fa_b23_spool_form", False):
        return

    def patched(token: str, error: str = "", language: str = "it") -> str:
        page = current(token, error=error, language=language)
        old_label = "Location (optional)" if language == "en" else "Posizione (facoltativa)"
        new_label = _LOCATION_LABEL_EN if language == "en" else _LOCATION_LABEL_IT
        page = page.replace(f"<label>{old_label}</label>", f"<label>{new_label}</label>", 1)
        marker = '<input name="location" maxlength="64">'
        if marker in page:
            hint = (
                "<p class=\"muted\">Example: Rack 3, PLA shelf, drawer 2. "
                "This is storage information, not U1 extruder 1–4.</p>"
                if language == "en"
                else "<p class=\"muted\">Esempio: Rack 3, scaffale PLA, cassetto 2. "
                "È una posizione di stoccaggio, non l’estrusore U1 1–4.</p>"
            )
            page = page.replace(marker, marker + hint, 1)
        return page

    setattr(patched, "_u1fa_b23_spool_form", True)
    gui_module._new_spool_form = patched


def _edit_values(item: Any) -> dict[str, str]:
    multicolor = bool(item.multi_color_hexes)
    return {
        "vendor": item.vendor,
        "material": item.material,
        "name": item.name,
        "color_hex": "#" + item.color_hex.lstrip("#"),
        "color_mode": "multi" if multicolor else "single",
        "multi_color_hexes": ",".join(
            "#" + value.lstrip("#") for value in item.multi_color_hexes
        ),
        "multi_color_direction": item.multi_color_direction or "coaxial",
        "nozzle_temperature": str(item.nozzle_temperature),
        "bed_temperature": str(item.bed_temperature),
        "density": f"{item.density:g}",
        "diameter": f"{item.diameter:g}",
        "filament_weight": f"{item.filament_weight:g}",
        "remaining_weight": f"{item.remaining_weight:g}",
        "empty_spool_weight": f"{item.empty_spool_weight:g}",
        "location": item.location,
        "lot_nr": item.lot_nr,
        "comment": item.comment,
    }


def _hidden_edit_fields(item: Any) -> str:
    return "".join(
        f'<input type="hidden" name="{html.escape(name, quote=True)}" value="{html.escape(value, quote=True)}">'
        for name, value in _edit_values(item).items()
    )


def _prefill_new_spool_form(page: str, item: Any) -> str:
    values = _edit_values(item)
    payload = json.dumps(values, ensure_ascii=True).replace("<", "\\u003c").replace(">", "\\u003e")
    multicolors = ["#" + value.lstrip("#") for value in item.multi_color_hexes]
    colors_payload = json.dumps(multicolors, ensure_ascii=True)
    script = f"""
<script>
(function(){{
  var data={payload};
  Object.keys(data).forEach(function(name){{
    var fields=document.getElementsByName(name);
    if(fields.length) fields[0].value=data[name];
  }});
  if(typeof showColor==='function') showColor(data.color_hex);
  if(typeof mode!=='undefined') mode.value=data.color_mode;
  if(data.color_mode==='multi' && typeof multiColors!=='undefined') multiColors={colors_payload};
  if(typeof updateColorMode==='function') updateColorMode();
  if(typeof multiField!=='undefined') multiField.value=data.multi_color_hexes;
  if(typeof multiColors!=='undefined' && data.color_mode==='multi' && typeof renderMulti==='function') renderMulti();
  var direction=document.getElementById('multi-color-direction');
  if(direction) direction.value=data.multi_color_direction;
}})();
</script>
"""
    return page.replace("</body>", script + "</body>", 1)


def _patch_new_spool_preview(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._new_spool_preview
    if getattr(current, "_u1fa_b23_spool_preview", False):
        return

    def patched(prepared: Any, token: str, language: str = "it") -> str:
        page = current(prepared, token, language=language)
        item = prepared.plan.request
        if item.location:
            label = "Spool location / storage" if language == "en" else "Posizione bobina / stoccaggio"
            row = f'<p><strong>{label}:</strong> {html.escape(item.location)}</p>'
            base_marker = '<p><strong>Base Snapmaker:</strong>'
            index = page.find(base_marker)
            if index >= 0:
                page = page[:index] + row + "\n" + page[index:]

        old = (
            '<a class="button secondary" href="/new-spool">Edit data</a>'
            if language == "en"
            else '<a class="button secondary" href="/new-spool">Modifica dati</a>'
        )
        label = "Edit data" if language == "en" else "Modifica dati"
        replacement = (
            f'<button class="secondary" type="submit" formnovalidate '
            f'formaction="/new-spool/edit" formmethod="post">{label}</button>'
        )
        page = page.replace(old, replacement, 1)
        ticket_marker = f'<input type="hidden" name="token" value="{token}"><input type="hidden" name="ticket" value="{prepared.ticket}">'
        if ticket_marker in page:
            page = page.replace(ticket_marker, ticket_marker + _hidden_edit_fields(item), 1)
        return page

    setattr(patched, "_u1fa_b23_spool_preview", True)
    gui_module._new_spool_preview = patched


def _patch_updates_page(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._updates_page
    if getattr(current, "_u1fa_b23_markdown", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        snapshot = controller.update_snapshot()
        if snapshot.info is None or not snapshot.info.notes:
            return page
        escaped = html.escape(snapshot.info.notes).replace("\n", "<br>")
        old_block = f'<p class="muted">{escaped}</p>'
        if old_block in page:
            rendered = render_release_notes(snapshot.info.notes)
            page = page.replace(
                old_block,
                f'<div class="muted release-notes">{rendered}</div>',
                1,
            )
        return page

    setattr(patched, "_u1fa_b23_markdown", True)
    gui_module._updates_page = patched


def _auto_discovery_form(token: str, language: str) -> str:
    label = "Detect U1 automatically" if language == "en" else "Rileva automaticamente la U1"
    note = (
        "U1FA scans only the local LAN with read-only Moonraker requests. "
        "It never sends G-code, starts prints or changes the printer."
        if language == "en"
        else "U1FA controlla solo la rete locale con richieste Moonraker in sola lettura. "
        "Non invia G-code, non avvia stampe e non modifica la stampante."
    )
    return (
        '<div class="card"><h2>'
        + ("Automatic detection" if language == "en" else "Rilevamento automatico")
        + "</h2>"
        + f"<p class=\"muted\">{note}</p>"
        + '<form method="post" action="/connections/discover">'
        + f'<input type="hidden" name="token" value="{html.escape(token, quote=True)}">'
        + f'<button type="submit">{label}</button></form></div>'
    )


def _patch_connections_form(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._connections_form
    if getattr(current, "_u1fa_b23_connection_form", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        heading = "<h1>U1 and Spoolman connections</h1>" if language == "en" else "<h1>Connessioni U1 e Spoolman</h1>"
        if heading in page and 'action="/connections/discover"' not in page:
            page = page.replace(heading, heading + _auto_discovery_form(token, language), 1)
        return page

    setattr(patched, "_u1fa_b23_connection_form", True)
    gui_module._connections_form = patched


def _patch_home(gui_module: Any) -> None:
    current: Callable[..., str] = gui_module._home
    if getattr(current, "_u1fa_b23_home_discovery", False):
        return

    def patched(
        controller: Any,
        token: str,
        error: str = "",
        language: str = "it",
    ) -> str:
        page = current(controller, token, error=error, language=language)
        if controller.connection_config() is not None:
            return page
        old = (
            '<p><a class="button danger" href="/connections">Configure U1 and Spoolman</a></p>'
            if language == "en"
            else '<p><a class="button danger" href="/connections">Configura U1 e Spoolman</a></p>'
        )
        if old in page:
            auto_label = "Detect automatically" if language == "en" else "Rileva automaticamente"
            manual_label = "Configure manually" if language == "en" else "Configura manualmente"
            replacement = (
                '<form method="post" action="/connections/discover">'
                f'<input type="hidden" name="token" value="{html.escape(token, quote=True)}">'
                f'<button class="danger" type="submit">{auto_label}</button> '
                f'<a class="button secondary" href="/connections">{manual_label}</a></form>'
            )
            page = page.replace(old, replacement, 1)
        return page

    setattr(patched, "_u1fa_b23_home_discovery", True)
    gui_module._home = patched


def _candidate_selection_page(
    gui_module: Any,
    candidates: tuple[MoonrakerCandidate, ...],
    token: str,
    language: str,
) -> str:
    title = "Confirm detected U1" if language == "en" else "Conferma la U1 rilevata"
    rows = []
    for index, candidate in enumerate(candidates):
        checked = " checked" if index == 0 else ""
        value = html.escape(candidate.url, quote=True)
        rows.append(
            f'<label><input style="width:auto" type="radio" name="moonraker_address" value="{value}"{checked}> '
            f'<code>{html.escape(candidate.url)}</code></label>'
        )
    if len(candidates) == 1:
        note = (
            "One compatible Snapmaker U1 was found. Confirm the address before U1FA saves the connections and performs the normal connection verification."
            if language == "en"
            else "È stata trovata una Snapmaker U1 compatibile. Conferma l’indirizzo prima che U1FA salvi le connessioni ed esegua la normale verifica di collegamento."
        )
    else:
        note = (
            "More than one compatible Snapmaker U1 was found. Select the correct printer; U1FA will verify it again before saving."
            if language == "en"
            else "È stata trovata più di una Snapmaker U1 compatibile. Seleziona la stampante corretta: U1FA la verificherà di nuovo prima di salvarla."
        )
    body = (
        f"<h1>{title}</h1><div class=\"card\"><p class=\"warn\">{note}</p>"
        '<form method="post" action="/connections/discover/select">'
        f'<input type="hidden" name="token" value="{html.escape(token, quote=True)}">'
        + "".join(rows)
        + f'<p><button type="submit">{("Verify and save" if language == "en" else "Verifica e salva")}</button> '
        f'<a class="button secondary" href="/connections">{("Cancel" if language == "en" else "Annulla")}</a></p></form></div>'
    )
    return gui_module._page(title, body, language=language)


def _private_lan_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        if parsed.scheme != "http" or parsed.port not in {None, 80}:
            return False
        address = ipaddress.ip_address(parsed.hostname or "")
        return bool(address.is_private and not address.is_loopback)
    except (ValueError, TypeError):
        return False


def _patch_handler(gui_module: Any) -> None:
    current = gui_module._handler
    if getattr(current, "_u1fa_b23_connection_discovery", False):
        return

    def patched(controller: Any, token: str):
        base_handler = current(controller, token)

        class B23Handler(base_handler):
            def do_POST(self) -> None:  # noqa: N802
                path = urlsplit(self.path).path
                if path not in {
                    "/connections/discover",
                    "/connections/discover/select",
                    "/new-spool/edit",
                }:
                    return super().do_POST()
                language = controller.language()
                try:
                    values = gui_module._form(self)
                    if not secrets.compare_digest(values.get("token", ""), token):
                        raise gui_module.GUIError(
                            "Invalid session: operation blocked"
                            if language == "en"
                            else "Sessione non valida: operazione bloccata"
                        )

                    if path == "/new-spool/edit":
                        item = gui_module._new_spool_request(values)
                        page = gui_module._new_spool_form(token, language=language)
                        self._send(_prefill_new_spool_form(page, item))
                        return

                    if path == "/connections/discover":
                        candidates = discover_moonraker_candidates()
                        if not candidates:
                            message = (
                                "No compatible Snapmaker U1 was found on the local LAN. Check that the U1 is on the same network or configure the address manually."
                                if language == "en"
                                else "Nessuna Snapmaker U1 compatibile trovata nella rete locale. Controlla che la U1 sia sulla stessa rete oppure configura l’indirizzo manualmente."
                            )
                            self._send(gui_module._connections_form(controller, token, message, language))
                            return
                        self._send(
                            _candidate_selection_page(gui_module, candidates, token, language)
                        )
                        return

                    selected = values.get("moonraker_address", "")
                    if not _private_lan_url(selected):
                        raise gui_module.GUIError(
                            "Detected address is not a valid private-LAN Moonraker URL"
                            if language == "en"
                            else "L’indirizzo selezionato non è un URL Moonraker valido della rete locale"
                        )
                    controller.configure_connections(selected, "auto")
                    self.send_response(303)
                    self.send_header("Location", "/")
                    self.end_headers()
                    return
                except gui_module.GUIError as exc:
                    self._send(gui_module._connections_form(controller, token, str(exc), language), 400)
                    return

        return B23Handler

    setattr(patched, "_u1fa_b23_connection_discovery", True)
    gui_module._handler = patched


def install_b23_patch(gui_module: Any) -> None:
    """Install b23 UI/discovery changes without touching printer configuration."""
    _patch_new_spool_form(gui_module)
    _patch_new_spool_preview(gui_module)
    _patch_updates_page(gui_module)
    _patch_connections_form(gui_module)
    _patch_home(gui_module)
    _patch_handler(gui_module)
