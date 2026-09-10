from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class ConnectionConfig:
    moonraker_url: str
    spoolman_url: str

    def to_dict(self) -> dict[str, str]:
        return {
            "moonraker_url": self.moonraker_url,
            "spoolman_url": self.spoolman_url,
        }


def default_connection_config_path() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        root = home / "Library" / "Application Support"
    elif os.name == "nt":
        root = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config"))
    return root / "U1 Filament Automation" / "connections.json"


def normalize_service_url(value: str, label: str) -> str:
    raw = value.strip()
    if not raw:
        raise ConfigError(f"{label}: indirizzo mancante / address required")
    if "://" not in raw:
        raw = "http://" + raw
    parsed = urlsplit(raw)
    if parsed.scheme not in {"http", "https"}:
        raise ConfigError(f"{label}: usare http:// oppure https:// / use http:// or https://")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ConfigError(f"{label}: host non valido / invalid host")
    try:
        parsed.port
    except ValueError as exc:
        raise ConfigError(f"{label}: porta non valida / invalid port") from exc
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ConfigError(f"{label}: inserire solo IP/host e porta / enter only IP/host and port")
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


def load_connection_config(path: Path | None = None) -> ConnectionConfig | None:
    target = default_connection_config_path() if path is None else path.expanduser()
    if not target.exists():
        return None
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise TypeError("root is not an object")
        moonraker = normalize_service_url(str(payload.get("moonraker_url", "")), "Moonraker")
        spoolman = normalize_service_url(str(payload.get("spoolman_url", "")), "Spoolman")
    except (OSError, json.JSONDecodeError, TypeError, ConfigError) as exc:
        raise ConfigError(f"Configurazione connessioni non valida: {exc}") from exc
    return ConnectionConfig(moonraker, spoolman)


def save_connection_config(
    config: ConnectionConfig,
    path: Path | None = None,
) -> Path:
    target = default_connection_config_path() if path is None else path.expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    try:
        temporary.write_text(
            json.dumps(config.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        try:
            temporary.chmod(0o600)
        except OSError:
            pass
        temporary.replace(target)
    except OSError as exc:
        raise ConfigError(f"Impossibile salvare la configurazione: {exc}") from exc
    return target
