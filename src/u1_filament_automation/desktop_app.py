"""Entrypoint condiviso delle applicazioni desktop compilate."""

from __future__ import annotations

import ctypes
import os
import platform
import subprocess
import sys
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Mapping, TextIO

from .cli import main as cli_main


APP_NAME = "U1 Filament Automation"
APP_URL = "http://127.0.0.1:8765/"
ASKPASS_MODE_ENV = "U1FA_ASKPASS_MODE"
ASKPASS_PASSWORD_ENV = "U1FA_SSH_PASSWORD"


def application_data_dir(
    home: Path | None = None,
    system: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    """Restituisce una cartella dati personale, mai legata all'utente di build."""
    base = Path.home() if home is None else home
    current_system = platform.system() if system is None else system
    env = os.environ if environ is None else environ
    if current_system == "Darwin":
        return base / "Library" / "Application Support" / APP_NAME
    if current_system == "Windows":
        local_appdata = env.get("LOCALAPPDATA") or env.get("APPDATA")
        root = Path(local_appdata) if local_appdata else base / "AppData" / "Local"
        return root / APP_NAME
    xdg_data = env.get("XDG_DATA_HOME")
    root = Path(xdg_data) if xdg_data else base / ".local" / "share"
    return root / APP_NAME


def desktop_log_path(
    home: Path | None = None,
    system: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> Path:
    base = Path.home() if home is None else home
    current_system = platform.system() if system is None else system
    env = os.environ if environ is None else environ
    if current_system == "Darwin":
        return base / "Library" / "Logs" / APP_NAME / "app.log"
    if current_system == "Windows":
        return application_data_dir(base, current_system, env) / "logs" / "app.log"
    xdg_state = env.get("XDG_STATE_HOME")
    root = Path(xdg_state) if xdg_state else base / ".local" / "state"
    return root / APP_NAME / "app.log"


def server_is_running(url: str = APP_URL) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1.0) as response:
            body = response.read(8192)
            return 200 <= response.status < 500 and b"U1 Filament Automation" in body
    except (OSError, urllib.error.URLError, ValueError):
        return False


def _write_windows_stdout(data: bytes) -> bool:
    """Scrive sull'handle ereditato anche in un eseguibile Windows senza console."""
    try:
        stdout_handle = ctypes.windll.kernel32.GetStdHandle(-11)  # type: ignore[attr-defined]
        if not stdout_handle or stdout_handle == -1:
            return False
        written = ctypes.c_ulong(0)
        buffer = ctypes.create_string_buffer(data)
        result = ctypes.windll.kernel32.WriteFile(  # type: ignore[attr-defined]
            stdout_handle,
            buffer,
            len(data),
            ctypes.byref(written),
            None,
        )
        return bool(result) and written.value == len(data)
    except (AttributeError, OSError, ValueError):
        return False


def emit_askpass_password(
    environ: Mapping[str, str] | None = None,
    system: str | None = None,
) -> int:
    """Modalità interna usata da OpenSSH; non salva né mostra la password."""
    env = os.environ if environ is None else environ
    password = env.get(ASKPASS_PASSWORD_ENV, "")
    if not password or "\n" in password or "\r" in password:
        return 1
    payload = (password + "\n").encode("utf-8")
    current_system = platform.system() if system is None else system
    if current_system == "Windows" and _write_windows_stdout(payload):
        return 0
    try:
        os.write(1, payload)
    except OSError:
        return 1
    return 0


def show_error(message: str, system: str | None = None) -> None:
    current_system = platform.system() if system is None else system
    try:
        if current_system == "Darwin":
            script = (
                'on run argv\n'
                'display alert "U1 Filament Automation" message (item 1 of argv) as critical\n'
                'end run'
            )
            subprocess.run(
                ["/usr/bin/osascript", "-e", script, message],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        elif current_system == "Windows":
            ctypes.windll.user32.MessageBoxW(  # type: ignore[attr-defined]
                None, message, APP_NAME, 0x10
            )
        else:
            subprocess.run(
                ["zenity", "--error", f"--title={APP_NAME}", f"--text={message}"],
                check=False,
                capture_output=True,
                timeout=10,
            )
    except (AttributeError, OSError, subprocess.SubprocessError):
        return


def _open_log() -> TextIO:
    target = desktop_log_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    return target.open("a", encoding="utf-8", buffering=1)


def main() -> int:
    if os.environ.get(ASKPASS_MODE_ENV) == "1":
        return emit_askpass_password()
    if server_is_running():
        webbrowser.open(APP_URL)
        return 0

    output = _open_log()
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = output
    sys.stderr = output
    try:
        data_dir = application_data_dir()
        sandbox_dir = data_dir / "sandbox"
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        result = cli_main(["gui", "--sandbox-dir", str(sandbox_dir)])
        if result != 0:
            show_error(
                "U1 Filament Automation non è stata avviata / did not start. "
                f"Log: {desktop_log_path()}"
            )
        return result
    except Exception as exc:  # pragma: no cover - ultima protezione desktop
        print(f"Avvio non riuscito / startup failed: {exc!r}")
        show_error(
            "Avvio non riuscito / startup failed. "
            f"Log: {desktop_log_path()}"
        )
        return 1
    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        output.close()


if __name__ == "__main__":
    raise SystemExit(main())
