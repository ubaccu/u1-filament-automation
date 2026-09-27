"""Desktop entrypoint for U1FA b23 UX and discovery improvements."""

from __future__ import annotations

from . import gui as gui_module
from .desktop_app import main as _desktop_main
from .gui_b23 import install_b23_patch


# desktop_app installs the established material/dashboard patches on import.
# b23 is applied afterwards so it can safely wrap the final rendered routes.
install_b23_patch(gui_module)


def main() -> int:
    return _desktop_main()


if __name__ == "__main__":
    raise SystemExit(main())
