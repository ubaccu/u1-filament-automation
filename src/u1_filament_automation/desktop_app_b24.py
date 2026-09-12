"""Desktop entrypoint for U1FA b24 profile de-duplication improvements."""

from __future__ import annotations

from . import gui as gui_module
from .desktop_app import main as _desktop_main
from .gui_b23 import install_b23_patch
from .gui_b24 import install_b24_patch


# desktop_app installs the established material/dashboard patches on import.
# Apply b23 first, then b24 so b24 wraps the final spool workflow safely.
install_b23_patch(gui_module)
install_b24_patch(gui_module)


def main() -> int:
    return _desktop_main()


if __name__ == "__main__":
    raise SystemExit(main())
