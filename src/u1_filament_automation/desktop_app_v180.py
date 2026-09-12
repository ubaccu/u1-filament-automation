"""Desktop entrypoint for the final U1FA 1.8.x release line."""

from __future__ import annotations

from . import gui as gui_module
from .desktop_app import main as _desktop_main
from .gui_b23 import install_b23_patch
from .gui_b24 import install_b24_patch
from .gui_v180 import install_v180_patch
from .gui_182_layout import install_182_layout_patch
from .gui_182_polish import install_182_home_polish
from .gui_182_final_ui_fixed import install_182_final_ui_fixed
from .gui_182_interactions import install_182_interaction_fix
from .gui_182_final_touch import install_182_final_touch
from .gui_182_nav_repair import install_182_nav_repair


# Apply compatibility and release UI patches in order. These imports only patch
# local application behaviour; they do not connect to or write to the printer,
# Spoolman or Snapmaker Orca.
install_b23_patch(gui_module)
install_b24_patch(gui_module)
install_v180_patch(gui_module)
install_182_layout_patch(gui_module)
install_182_home_polish(gui_module)
install_182_final_ui_fixed(gui_module)
install_182_interaction_fix(gui_module)
install_182_final_touch(gui_module)
install_182_nav_repair(gui_module)


def main() -> int:
    return _desktop_main()


if __name__ == "__main__":
    raise SystemExit(main())
