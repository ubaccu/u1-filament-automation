from __future__ import annotations

import html
import re
from typing import Any, Callable


_HEX_RE = re.compile(r"^[0-9A-Fa-f]{6}$")
_SELECT_RE = re.compile(
    r'<select name="(?P<name>profile_name(?:_\d+)?)"(?P<attrs>[^>]*)>(?P<body>.*?)</select>',
    re.DOTALL,
)
_EMPTY_OPTION_RE = re.compile(r'<option value="">.*?</option>', re.DOTALL)
_ASSET_MARKER = "u1fa-profile-picker-205"


def _normalize_hex(value: Any) -> str:
    text = str(value or "").strip().lstrip("#")
    return text.upper() if _HEX_RE.fullmatch(text) else ""


def _filament_for_spool(inventory: Any, spool: dict[str, Any]) -> dict[str, Any]:
    nested = spool.get("filament")
    if isinstance(nested, dict):
        if _normalize_hex(nested.get("color_hex")) or nested.get("multi_color_hexes"):
            return nested
        nested_id = nested.get("id")
    else:
        nested_id = None
    filament_id = nested_id if nested_id is not None else spool.get("filament_id")
    for filament in getattr(inventory, "filaments", ()):
        if str(filament.get("id")) == str(filament_id):
            return filament
    return nested if isinstance(nested, dict) else {}


def _filament_colors(filament: dict[str, Any]) -> tuple[str, ...]:
    colors: list[str] = []
    raw_multi = filament.get("multi_color_hexes")
    if isinstance(raw_multi, str):
        candidates = re.split(r"[,;\s]+", raw_multi.strip())
    elif isinstance(raw_multi, (list, tuple)):
        candidates = [str(item) for item in raw_multi]
    else:
        candidates = []
    for candidate in candidates:
        value = _normalize_hex(candidate)
        if value and value not in colors:
            colors.append(value)
    if colors:
        return tuple(colors)
    single = _normalize_hex(filament.get("color_hex"))
    return (single,) if single else ()


def _colors_for_profile(controller: Any, profile: Any) -> tuple[str, ...]:
    inventory = getattr(controller, "_inventory", None)
    if inventory is None:
        return ()
    spool_ids = {str(item) for item in getattr(profile, "spool_ids", ())}
    if not spool_ids:
        return ()
    for spool in getattr(inventory, "spools", ()):
        if str(spool.get("id")) not in spool_ids:
            continue
        colors = _filament_colors(_filament_for_spool(inventory, spool))
        if colors:
            return colors
    return ()


def _sorted_profiles(controller: Any) -> tuple[Any, ...]:
    return tuple(
        sorted(
            controller.profiles(),
            key=lambda item: (
                str(getattr(item, "profile_name", "")).casefold(),
                str(getattr(item, "profile_name", "")),
            ),
        )
    )


def _option_html(controller: Any, profile: Any, language: str) -> str:
    profile_name = str(profile.profile_name)
    spool_ids = list(getattr(profile, "spool_ids", ()))
    colors = _colors_for_profile(controller, profile)
    spool_word = "spools" if language == "en" else "bobine"
    color_text = "" if not colors else " — " + " / ".join(f"#{value}" for value in colors)
    color_attr = ",".join(f"#{value}" for value in colors)
    return (
        f'<option value="{html.escape(profile_name, quote=True)}" '
        f'data-u1fa-colors="{html.escape(color_attr, quote=True)}">'
        f'{html.escape(profile_name)} — {spool_word} {html.escape(str(spool_ids))}'
        f'{html.escape(color_text)}</option>'
    )


def _picker_assets(language: str) -> str:
    color_label = "Color" if language == "en" else "Colore"
    return f"""
<!-- {_ASSET_MARKER} -->
<style>
.u1fa-profile-color-preview{{display:flex;align-items:center;gap:7px;margin-top:7px;font-size:.9em;opacity:.88}}
.u1fa-profile-color-swatch{{display:inline-block;width:17px;height:17px;border-radius:4px;border:1px solid rgba(127,127,127,.55);box-shadow:inset 0 0 0 1px rgba(255,255,255,.18)}}
.u1fa-profile-color-code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}
</style>
<script>
(function(){{
  function update(select){{
    var preview = select.nextElementSibling;
    if (!preview || !preview.classList.contains('u1fa-profile-color-preview')) {{
      preview = document.createElement('div');
      preview.className = 'u1fa-profile-color-preview';
      select.insertAdjacentElement('afterend', preview);
    }}
    var option = select.options[select.selectedIndex];
    var raw = option ? (option.getAttribute('data-u1fa-colors') || '') : '';
    var colors = raw.split(',').filter(Boolean);
    preview.replaceChildren();
    if (!colors.length) {{ preview.hidden = true; return; }}
    preview.hidden = false;
    var label = document.createElement('span');
    label.textContent = '{color_label}:';
    preview.appendChild(label);
    colors.forEach(function(color){{
      var swatch = document.createElement('span');
      swatch.className = 'u1fa-profile-color-swatch';
      swatch.style.backgroundColor = color;
      swatch.title = color;
      preview.appendChild(swatch);
    }});
    var code = document.createElement('span');
    code.className = 'u1fa-profile-color-code';
    code.textContent = colors.join(' / ');
    preview.appendChild(code);
  }}
  function setup(){{
    document.querySelectorAll('select[data-u1fa-profile-picker="1"]').forEach(function(select){{
      update(select);
      select.addEventListener('change', function(){{ update(select); }});
    }});
  }}
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', setup);
  else setup();
}})();
</script>
"""


def enhance_profile_picker_page(page: str, controller: Any, language: str = "it") -> str:
    profiles = _sorted_profiles(controller)
    if not profiles or 'name="profile_name' not in page:
        return page

    def replace_select(match: re.Match[str]) -> str:
        name = match.group("name")
        attrs = match.group("attrs")
        body = match.group("body")
        empty = ""
        empty_match = _EMPTY_OPTION_RE.search(body)
        if empty_match is not None:
            empty = empty_match.group(0)
        options = "".join(_option_html(controller, item, language) for item in profiles)
        return (
            f'<select name="{name}"{attrs} data-u1fa-profile-picker="1">'
            f'{empty}{options}</select>'
        )

    updated = _SELECT_RE.sub(replace_select, page)
    if updated == page or _ASSET_MARKER in updated:
        return updated
    assets = _picker_assets(language)
    if "</body>" in updated:
        return updated.replace("</body>", assets + "</body>", 1)
    return updated + assets


def install_profile_picker_patch(gui_module: Any) -> None:
    """Sort calibration profiles A-Z and show their Spoolman colour in the GUI."""
    for name in ("_home", "_batch_form"):
        current: Callable[..., str] | None = getattr(gui_module, name, None)
        if not callable(current) or getattr(current, "_u1fa_profile_picker_205", False):
            continue

        def make_wrapper(renderer: Callable[..., str]) -> Callable[..., str]:
            def patched(
                controller: Any,
                token: str,
                error: str = "",
                language: str = "it",
            ) -> str:
                page = renderer(controller, token, error=error, language=language)
                return enhance_profile_picker_page(page, controller, language)

            setattr(patched, "_u1fa_profile_picker_205", True)
            return patched

        setattr(gui_module, name, make_wrapper(current))
