"""Controllo e download sicuro degli aggiornamenti desktop U1FA."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import ssl
import subprocess
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

import certifi


DEFAULT_GITHUB_REPOSITORY = "ubaccu/u1-filament-automation"
GITHUB_API_VERSION = "2026-03-10"
MAX_RELEASE_RESPONSE = 2 * 1024 * 1024
MAX_UPDATE_SIZE = 500 * 1024 * 1024
DEFAULT_UPDATE_TIMEOUT = 15.0
_VERSION_RE = re.compile(
    r"^v?(\d+)\.(\d+)\.(\d+)(?:[-.]?(alpha|beta|rc|a|b)[.-]?(\d+))?$",
    re.IGNORECASE,
)
_SAFE_ASSET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,199}$")


class UpdateError(RuntimeError):
    pass


def github_ssl_context() -> ssl.SSLContext:
    """Trust both the operating system and U1FA's bundled CA store."""
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=certifi.where())
    return context


def _open_https(
    request: urllib.request.Request,
    timeout: float,
    opener: Callable[..., Any] | None,
):
    if opener is not None:
        return opener(request, timeout=timeout)
    return urllib.request.urlopen(
        request,
        timeout=timeout,
        context=github_ssl_context(),
    )


@dataclass(frozen=True)
class UpdateAsset:
    name: str
    download_url: str
    size: int
    sha256: str


@dataclass(frozen=True)
class UpdateInfo:
    version: str
    tag: str
    title: str
    notes: str
    release_url: str
    prerelease: bool
    asset: UpdateAsset


def _version_key(value: str) -> tuple[int, int, int, int, int]:
    match = _VERSION_RE.fullmatch(value.strip())
    if match is None:
        raise UpdateError(f"Versione aggiornamento non valida / Invalid update version: {value}")
    major, minor, patch = (int(match.group(index)) for index in (1, 2, 3))
    stage = (match.group(4) or "").casefold()
    stage_number = int(match.group(5) or 0)
    rank = {"a": 0, "alpha": 0, "b": 1, "beta": 1, "rc": 2, "": 3}[stage]
    return major, minor, patch, rank, stage_number


def is_newer_version(candidate: str, current: str) -> bool:
    return _version_key(candidate) > _version_key(current)


def update_channel_for_version(current: str) -> str:
    key = _version_key(current)
    return "stable" if key[3] == 3 else "beta"


def _normalized_machine(machine: str) -> str:
    value = machine.casefold()
    if value in {"amd64", "x64", "x86_64"}:
        return "x86_64"
    if value in {"arm64", "aarch64"}:
        return "arm64"
    return value


def asset_marker(system: str | None = None, machine: str | None = None) -> str:
    current_system = platform.system() if system is None else system
    current_machine = _normalized_machine(
        platform.machine() if machine is None else machine
    )
    if current_system == "Darwin" and current_machine in {"x86_64", "arm64"}:
        return f"macOS-{current_machine}.dmg"
    if current_system == "Windows" and current_machine == "x86_64":
        return "Windows-x64-Setup.exe"
    if current_system == "Linux" and current_machine == "x86_64":
        return "Linux-x86_64.AppImage"
    raise UpdateError(
        f"Piattaforma non supportata / Unsupported platform: "
        f"{current_system} {current_machine}"
    )


def _github_https_url(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise UpdateError(f"{label} mancante / missing")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
        raise UpdateError(f"{label} non attendibile / untrusted")
    return value


def _release_asset(
    release: dict[str, Any],
    marker: str,
) -> UpdateAsset | None:
    for raw_asset in release.get("assets") or []:
        if not isinstance(raw_asset, dict):
            continue
        name = raw_asset.get("name")
        if not isinstance(name, str) or not name.endswith(marker):
            continue
        if not _SAFE_ASSET_RE.fullmatch(name) or Path(name).name != name:
            raise UpdateError("Nome del pacchetto non valido / Invalid package name")
        digest = raw_asset.get("digest")
        if not isinstance(digest, str) or not digest.startswith("sha256:"):
            raise UpdateError(
                "Pacchetto senza SHA-256 verificabile / Package has no verifiable SHA-256"
            )
        sha256 = digest.removeprefix("sha256:").casefold()
        if not re.fullmatch(r"[0-9a-f]{64}", sha256):
            raise UpdateError("SHA-256 aggiornamento non valido / Invalid update SHA-256")
        try:
            size = int(raw_asset.get("size", 0))
        except (TypeError, ValueError) as exc:
            raise UpdateError("Dimensione aggiornamento non valida / Invalid update size") from exc
        if size < 1 or size > MAX_UPDATE_SIZE:
            raise UpdateError("Dimensione aggiornamento non consentita / Update size not allowed")
        return UpdateAsset(
            name=name,
            download_url=_github_https_url(
                raw_asset.get("browser_download_url"),
                "URL download",
            ),
            size=size,
            sha256=sha256,
        )
    return None


def select_update(
    releases: Any,
    current_version: str,
    channel: str,
    system: str | None = None,
    machine: str | None = None,
) -> UpdateInfo | None:
    if channel not in {"stable", "beta"}:
        raise UpdateError("Canale aggiornamenti non valido / Invalid update channel")
    if not isinstance(releases, list):
        raise UpdateError("Risposta aggiornamenti non valida / Invalid update response")
    marker = asset_marker(system, machine)
    candidates: list[tuple[tuple[int, int, int, int, int], UpdateInfo]] = []
    for release in releases:
        if not isinstance(release, dict) or release.get("draft") is True:
            continue
        prerelease = release.get("prerelease") is True
        if channel == "stable" and prerelease:
            continue
        tag = release.get("tag_name")
        if not isinstance(tag, str):
            continue
        try:
            if not is_newer_version(tag, current_version):
                continue
            key = _version_key(tag)
        except UpdateError:
            continue
        asset = _release_asset(release, marker)
        if asset is None:
            continue
        title = release.get("name")
        notes = release.get("body")
        candidates.append((
            key,
            UpdateInfo(
                version=tag.removeprefix("v"),
                tag=tag,
                title=title.strip()[:200] if isinstance(title, str) else tag,
                notes=notes.strip()[:12000] if isinstance(notes, str) else "",
                release_url=_github_https_url(release.get("html_url"), "URL release"),
                prerelease=prerelease,
                asset=asset,
            ),
        ))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def check_for_update(
    current_version: str,
    repository: str = DEFAULT_GITHUB_REPOSITORY,
    channel: str | None = None,
    timeout: float = DEFAULT_UPDATE_TIMEOUT,
    system: str | None = None,
    machine: str | None = None,
    opener: Callable[..., Any] | None = None,
) -> UpdateInfo | None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise UpdateError("Repository aggiornamenti non valido / Invalid update repository")
    selected_channel = channel or update_channel_for_version(current_version)
    url = f"https://api.github.com/repos/{repository}/releases?per_page=10"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "User-Agent": f"U1-Filament-Automation/{current_version}",
        },
    )
    try:
        with _open_https(request, timeout, opener) as response:
            data = response.read(MAX_RELEASE_RESPONSE + 1)
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(exc, urllib.error.HTTPError):
            detail = f"HTTP {exc.code}"
        elif isinstance(reason, TimeoutError) or "timed out" in str(reason).casefold():
            detail = f"GitHub: timeout dopo {timeout:g} s / timeout after {timeout:g} s"
        else:
            detail = f"GitHub: {type(reason).__name__}"
        raise UpdateError(detail) from exc
    if len(data) > MAX_RELEASE_RESPONSE:
        raise UpdateError("Risposta aggiornamenti troppo grande / Update response too large")
    try:
        payload = json.loads(data.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise UpdateError("Risposta aggiornamenti illeggibile / Invalid update response") from exc
    return select_update(
        payload,
        current_version,
        selected_channel,
        system,
        machine,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_update(
    info: UpdateInfo,
    destination_dir: Path,
    timeout: float = 30.0,
    opener: Callable[..., Any] | None = None,
) -> Path:
    destination = destination_dir.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / info.asset.name
    if target.exists() and target.is_file() and _sha256(target) == info.asset.sha256:
        return target
    request = urllib.request.Request(
        info.asset.download_url,
        headers={"User-Agent": f"U1-Filament-Automation/{info.version}"},
    )
    temporary_path: Path | None = None
    try:
        with _open_https(request, timeout, opener) as response, tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=".u1fa-update-",
            suffix=".part",
            dir=destination,
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            digest = hashlib.sha256()
            received = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                received += len(chunk)
                if received > info.asset.size or received > MAX_UPDATE_SIZE:
                    raise UpdateError(
                        "Download più grande del previsto / Download exceeds expected size"
                    )
                digest.update(chunk)
                output.write(chunk)
        if received != info.asset.size:
            raise UpdateError("Download incompleto / Incomplete download")
        if digest.hexdigest() != info.asset.sha256:
            raise UpdateError("SHA-256 non corrispondente: file eliminato / SHA-256 mismatch: file removed")
        os.replace(temporary_path, target)
        temporary_path = None
        if target.suffix.casefold() == ".appimage":
            target.chmod(0o755)
        return target
    except UpdateError:
        raise
    except (OSError, urllib.error.URLError, TimeoutError) as exc:
        raise UpdateError("Download aggiornamento non riuscito / Update download failed") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def open_update_package(path: Path, system: str | None = None) -> None:
    target = path.expanduser().resolve()
    if not target.is_file():
        raise UpdateError("Pacchetto aggiornamento non trovato / Update package not found")
    current_system = platform.system() if system is None else system
    try:
        if current_system == "Darwin" and target.suffix.casefold() == ".dmg":
            subprocess.Popen(["/usr/bin/open", str(target)])
        elif current_system == "Windows" and target.suffix.casefold() == ".exe":
            os.startfile(str(target))  # type: ignore[attr-defined]
        elif current_system == "Linux" and target.suffix.casefold() == ".appimage":
            subprocess.Popen(["xdg-open", str(target.parent)])
        else:
            raise UpdateError("Formato aggiornamento non supportato / Unsupported update format")
    except UpdateError:
        raise
    except OSError as exc:
        raise UpdateError("Impossibile aprire l'aggiornamento / Cannot open update") from exc
