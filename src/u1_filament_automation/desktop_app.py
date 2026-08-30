"""Entrypoint condiviso delle applicazioni desktop compilate."""

from __future__ import annotations

import ctypes
import os
import platform
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, TextIO
from urllib.parse import urlparse

from .config import (
    ConfigError,
    default_connection_config_path,
    load_connection_config,
    normalize_service_url,
)
from .gui import CalibrationController, GUIError, run_gui


APP_NAME = "U1 Filament Automation"
APP_URL = "http://127.0.0.1:8765/"
ASKPASS_MODE_ENV = "U1FA_ASKPASS_MODE"
ASKPASS_PASSWORD_ENV = "U1FA_SSH_PASSWORD"


@dataclass(frozen=True)
class DesktopRuntime:
    server: Any
    controller: CalibrationController
    url: str
    thread: threading.Thread


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


def _load_webview():
    try:
        import webview
    except ImportError as exc:  # pragma: no cover - dipendenza del pacchetto desktop
        raise RuntimeError(
            "Componente finestra desktop mancante / desktop window component missing"
        ) from exc
    return webview


def show_native_window(
    url: str,
    controller: CalibrationController | None = None,
) -> None:
    """Mostra U1FA in una finestra desktop, senza aprire il browser esterno."""
    webview = _load_webview()
    window = webview.create_window(
        APP_NAME,
        url,
        width=1280,
        height=860,
        min_size=(900, 650),
        resizable=True,
        confirm_close=True,
        background_color="#0b1015",
        text_select=True,
    )

    if controller is not None:
        def block_unsafe_close() -> bool:
            if controller.snapshot().state in {"checking", "running"}:
                show_error(
                    "Chiusura bloccata durante la calibrazione / "
                    "closing is blocked during calibration"
                )
                return False
            return True

        window.events.closing += block_unsafe_close

    stop_service_watch = threading.Event()

    def close_window_after_service_stops() -> None:
        """Chiude anche la finestra quando si usa ``Chiudi applicazione``."""
        consecutive_failures = 0
        while not stop_service_watch.wait(0.4):
            if server_is_running(url):
                consecutive_failures = 0
                continue
            consecutive_failures += 1
            if consecutive_failures < 3:
                continue
            try:
                window.destroy()
            except Exception:
                pass
            return

    service_watch = threading.Thread(
        target=close_window_after_service_stops,
        name="u1fa-window-lifecycle",
        daemon=True,
    )
    service_watch.start()

    gui_backend = "qt" if platform.system() == "Linux" else None
    try:
        webview.start(gui=gui_backend, debug=False)
    finally:
        stop_service_watch.set()
        service_watch.join(timeout=2.0)


def _run_desktop_server(
    data_dir: Path,
    ready: threading.Event,
    runtime_box: dict[str, Any],
    error_box: list[BaseException],
) -> None:
    def publish_runtime(server: Any, controller: CalibrationController, url: str) -> None:
        runtime_box.update(server=server, controller=controller, url=url)
        ready.set()

    try:
        config_path = default_connection_config_path()
        try:
            saved = load_connection_config(config_path)
        except ConfigError as exc:
            print(f"[AVVISO] {exc}")
            saved = None

        moonraker_url = "" if saved is None else saved.moonraker_url
        spoolman_url = (
            "http://127.0.0.1:7912" if saved is None else saved.spoolman_url
        )
        if moonraker_url:
            moonraker_url = normalize_service_url(moonraker_url, "U1/Moonraker")
        spoolman_url = normalize_service_url(spoolman_url, "Spoolman")
        parsed = urlparse(moonraker_url)
        ssh_target = f"root@{parsed.hostname}" if parsed.hostname else None

        run_gui(
            moonraker_url=moonraker_url,
            spoolman_url=spoolman_url,
            sandbox_dir=data_dir / "sandbox",
            open_browser=False,
            ssh_target=ssh_target,
            connection_config_path=config_path,
            ready_callback=publish_runtime,
        )
    except BaseException as exc:  # pragma: no cover - inoltrato alla GUI desktop
        error_box.append(exc)
        ready.set()


def start_desktop_runtime(data_dir: Path, timeout: float = 20.0) -> DesktopRuntime:
    ready = threading.Event()
    runtime_box: dict[str, Any] = {}
    error_box: list[BaseException] = []
    thread = threading.Thread(
        target=_run_desktop_server,
        args=(data_dir, ready, runtime_box, error_box),
        name="u1fa-local-service",
        daemon=True,
    )
    thread.start()
    if not ready.wait(timeout):
        raise RuntimeError("Avvio interfaccia scaduto / desktop startup timed out")
    if error_box:
        raise RuntimeError(str(error_box[0])) from error_box[0]
    if not {"server", "controller", "url"}.issubset(runtime_box):
        raise RuntimeError("Interfaccia locale non disponibile / local interface unavailable")
    return DesktopRuntime(
        runtime_box["server"],
        runtime_box["controller"],
        runtime_box["url"],
        thread,
    )


def main() -> int:
    if os.environ.get(ASKPASS_MODE_ENV) == "1":
        return emit_askpass_password()
    if server_is_running():
        show_native_window(APP_URL)
        return 0

    output = _open_log()
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = output
    sys.stderr = output
    try:
        data_dir = application_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        runtime = start_desktop_runtime(data_dir)
        try:
            show_native_window(runtime.url, runtime.controller)
        finally:
            runtime.controller.stop_profile_monitor()
            runtime.server.shutdown()
            runtime.thread.join(timeout=5.0)
        return 0
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
