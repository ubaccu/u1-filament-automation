"""Compatibilità con l'entrypoint macOS introdotto nella v1.6."""

from __future__ import annotations

from pathlib import Path

from .desktop_app import APP_NAME, APP_URL, desktop_log_path, main


def application_support_dir(home: Path | None = None) -> Path:
    from .desktop_app import application_data_dir

    return application_data_dir(home=home, system="Darwin", environ={})


def log_path(home: Path | None = None) -> Path:
    return desktop_log_path(home=home, system="Darwin", environ={})


if __name__ == "__main__":
    raise SystemExit(main())
