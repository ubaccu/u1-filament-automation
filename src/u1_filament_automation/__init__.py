"""U1 Filament Automation for Spoolman and Snapmaker Orca."""

__version__ = "1.8.2"

# Install the small metadata bridge before callers import sync_profiles from
# the sync module. This keeps CLI and desktop builds on the same behaviour.
from . import sync as _sync_module
from .profile_density import install_sync_density_patch

install_sync_density_patch(_sync_module)

# U1FA 1.8.2 adds a guarded desktop extension for deleting a filament together
# with every linked Spoolman spool (including archived spools). The extension
# never writes to the printer and only removes Orca profiles already managed by
# U1FA after an explicit preview + confirmation.
from . import gui as _gui_module
from .gui_delete import install_filament_delete_ui_patch
from .gui_post_creation import install_post_creation_ui_patch

install_filament_delete_ui_patch(_gui_module)
install_post_creation_ui_patch(_gui_module)
