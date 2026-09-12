"""U1 Filament Automation for Spoolman and Snapmaker Orca."""

__version__ = "1.8.1"

# Install the small metadata bridge before callers import sync_profiles from
# the sync module. This keeps CLI and desktop builds on the same behaviour.
from . import sync as _sync_module
from .profile_density import install_sync_density_patch

install_sync_density_patch(_sync_module)
