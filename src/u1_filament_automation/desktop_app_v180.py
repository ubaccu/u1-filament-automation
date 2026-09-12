"""Desktop entrypoint for the final U1FA 1.8.0 release."""

from __future__ import annotations

from . import gui as gui_module
from .desktop_app import main as _desktop_main
from .gui_b23 import install_b23_patch
from .gui_b24 import install_b24_patch
from .gui_v180 import install_v180_patch


# Apply the established compatibility patches in release order. These imports
# only patch local application behavior; they do not connect to or write to the
# printer, Spoolman or Snapmaker Orca.
install_b23_patch(gui_module)
install_b24_patch(gui_module)
install_v180_patch(gui_module)


def main() -> int:
    return _desktop_main()


if __name__ == "__main__":
    raise SystemExit(main())
