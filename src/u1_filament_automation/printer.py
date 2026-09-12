from __future__ import annotations

import base64
import fnmatch
import getpass
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Protocol


STOCK_SHA256 = "dcbc26d5c726eb464b8e2a31d2856a816f3170bbda1ed5facb57fb19a816e894"
V6_SHA256 = "74ff744304657547e513fe74c3d42beb55f35eebd4d8f3e0749f0c7febc089ce"
ADAPTIVE_PA_MACRO_SHA256 = (
    "db181aa5ee12b93886230a6b71cfd105c92a56cf4651e5e5dca7788aac7daeb4"
)
FLOW_CALIBRATOR_PATH = PurePosixPath(
    "/home/lava/klipper/klippy/extras/flow_calibrator.py"
)
ADAPTIVE_PA_MACRO_PATH = PurePosixPath(
    "/home/lava/printer_data/config/adaptive_pa_macro.cfg"
)
PRINTER_CFG_PATH = PurePosixPath(
    "/home/lava/printer_data/config/printer.cfg"
)
PRINTER_CFG_INCLUDE = "[include adaptive_pa_macro.cfg]"
LEGACY_BACKUP_PATH = PurePosixPath(
    "/home/lava/klipper/klippy/extras/"
    "flow_calibrator.py.BACKUP_ORIGINALE_20260824"
)
SAFE_PRINT_STATES = frozenset({"standby", "complete", "cancelled", "error"})
SAFE_MACHINE_STATES = frozenset({"idle", "0"})
BACKUP_PREFIX = "flow_calibrator.py.U1FA_BACKUP_"


class PrinterInstallError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bundled_asset(name: str) -> Path:
    return Path(__file__).resolve().parent / "assets" / name


def validated_asset(name: str, expected_sha256: str) -> bytes:
    path = bundled_asset(name)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise PrinterInstallError(f"Asset incorporato non leggibile: {path}") from exc
    actual = sha256_bytes(data)
    if actual != expected_sha256:
        raise PrinterInstallError(
            f"Asset incorporato non valido: atteso {expected_sha256}, trovato {actual}"
        )
    return data


def validate_python_source(data: bytes, filename: str) -> None:
    try:
        source = data.decode("utf-8")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            compile(source, filename, "exec")
    except (UnicodeDecodeError, SyntaxError) as exc:
        raise PrinterInstallError(f"Controllo sintattico Python fallito: {exc}") from exc


@dataclass(frozen=True)
class CalibratorStatus:
    path: str
    sha256: str
    state: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class AdaptivePAMacroStatus:
    path: str
    sha256: str | None
    state: str
    loaded_by_klipper: bool | None

    @property
    def complete(self) -> bool:
        return self.state == "v6-installed" and self.loaded_by_klipper is True

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "complete": self.complete}


@dataclass(frozen=True)
class PrinterSafetyStatus:
    klippy_state: str
    print_state: str
    virtual_sd_active: bool
    idle_state: str
    machine_state: str | None = None

    @property
    def safe_to_modify(self) -> bool:
        return (
            self.klippy_state.casefold() == "ready"
            and self.print_state.casefold() in SAFE_PRINT_STATES
            and not self.virtual_sd_active
            and self.idle_state.casefold() in {"ready", "idle"}
            and (
                self.machine_state is None
                # Snapmaker serializza MachineMainState.IDLE come intero 0.
                # Alcune versioni/fixture restituiscono invece il nome IDLE.
                or self.machine_state.strip().casefold() in SAFE_MACHINE_STATES
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "safe_to_modify": self.safe_to_modify}


@dataclass(frozen=True)
class FileWriteResult:
    action: str
    path: str
    backup_path: str
    sha256_before: str
    sha256_after: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class PrinterSetupResult:
    calibrator: CalibratorStatus
    macro: AdaptivePAMacroStatus
    writes: tuple[FileWriteResult, ...]
    include_already_present: bool
    power_cycle_required: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "calibrator": self.calibrator.to_dict(),
            "adaptive_pa_macro": self.macro.to_dict(),
            "writes": [item.to_dict() for item in self.writes],
            "include_already_present": self.include_already_present,
            "power_cycle_required": self.power_cycle_required,
        }


@dataclass(frozen=True)
class PrinterSetupPlan:
    calibrator: CalibratorStatus
    macro: AdaptivePAMacroStatus
    install_calibrator: bool
    create_macro: bool
    update_printer_cfg: bool
    include_already_present: bool

    @property
    def changes_required(self) -> bool:
        return self.install_calibrator or self.create_macro or self.update_printer_cfg

    def to_dict(self) -> dict[str, Any]:
        return {
            "calibrator": self.calibrator.to_dict(),
            "adaptive_pa_macro": self.macro.to_dict(),
            "install_calibrator": self.install_calibrator,
            "create_macro": self.create_macro,
            "update_printer_cfg": self.update_printer_cfg,
            "include_already_present": self.include_already_present,
            "changes_required": self.changes_required,
        }


class PrinterFileTarget(Protocol):
    display_path: str

    def read_bytes(self) -> bytes: ...

    def read_path_bytes(self, remote_path: PurePosixPath) -> bytes: ...

    def display_path_for(self, remote_path: PurePosixPath) -> str: ...

    def install_atomic(self, expected_sha256: str, new_data: bytes) -> FileWriteResult: ...

    def restore_atomic(
        self, backup_path: str, expected_current_sha256: str
    ) -> FileWriteResult: ...

    def write_path_atomic(
        self,
        remote_path: PurePosixPath,
        expected_current_sha256: str | None,
        new_data: bytes,
        expected_new_sha256: str,
    ) -> FileWriteResult: ...

    def restore_path_atomic(
        self,
        remote_path: PurePosixPath,
        backup_path: str,
        expected_current_sha256: str,
        expected_backup_sha256: str,
    ) -> FileWriteResult: ...

    def delete_path_if_sha(
        self, remote_path: PurePosixPath, expected_current_sha256: str
    ) -> None: ...


def classify_calibrator(data: bytes, path: str) -> CalibratorStatus:
    digest = sha256_bytes(data)
    if digest == STOCK_SHA256:
        state = "stock-compatible"
    elif digest == V6_SHA256:
        state = "v6-installed"
    else:
        state = "unknown-blocked"
    return CalibratorStatus(path=path, sha256=digest, state=state)


def inspect_calibrator(target: PrinterFileTarget) -> CalibratorStatus:
    try:
        data = target.read_bytes()
    except (OSError, subprocess.SubprocessError) as exc:
        raise PrinterInstallError(
            f"Impossibile leggere {target.display_path}: {exc}"
        ) from exc
    return classify_calibrator(data, target.display_path)


def inspect_adaptive_pa_macro(
    target: PrinterFileTarget,
    loaded_by_klipper: bool | None = None,
) -> AdaptivePAMacroStatus:
    path = target.display_path_for(ADAPTIVE_PA_MACRO_PATH)
    try:
        data = target.read_path_bytes(ADAPTIVE_PA_MACRO_PATH)
    except FileNotFoundError:
        return AdaptivePAMacroStatus(
            path=path,
            sha256=None,
            state="missing",
            loaded_by_klipper=loaded_by_klipper,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PrinterInstallError(f"Impossibile leggere {path}: {exc}") from exc
    digest = sha256_bytes(data)
    state = "v6-installed" if digest == ADAPTIVE_PA_MACRO_SHA256 else "unknown-blocked"
    return AdaptivePAMacroStatus(
        path=path,
        sha256=digest,
        state=state,
        loaded_by_klipper=loaded_by_klipper,
    )


_INCLUDE_RE = re.compile(
    rb"(?im)^\s*\[include\s+([^\]\r\n]+)\]\s*(?:#.*)?$"
)


def printer_cfg_includes_macro(data: bytes) -> bool:
    """Riconosce sia l'include esatto sia un glob che copre la macro."""
    for match in _INCLUDE_RE.finditer(data):
        try:
            pattern = match.group(1).decode("utf-8").strip()
        except UnicodeDecodeError:
            continue
        if fnmatch.fnmatchcase(ADAPTIVE_PA_MACRO_PATH.name, pattern):
            return True
    return False


def plan_printer_setup(
    target: PrinterFileTarget,
    loaded_by_klipper: bool | None = None,
) -> PrinterSetupPlan:
    calibrator = inspect_calibrator(target)
    if calibrator.state == "unknown-blocked":
        raise PrinterInstallError(
            "Versione del calibratore non riconosciuta: configurazione bloccata"
        )
    macro = inspect_adaptive_pa_macro(target, loaded_by_klipper=loaded_by_klipper)
    if macro.state == "unknown-blocked":
        raise PrinterInstallError(
            "Macro Adaptive PA già presente ma non riconosciuta: nessuna sovrascrittura"
        )

    include_present = loaded_by_klipper is True
    update_printer_cfg = False
    if not include_present:
        try:
            printer_cfg = target.read_path_bytes(PRINTER_CFG_PATH)
        except FileNotFoundError as exc:
            raise PrinterInstallError(
                f"Configurazione principale U1 non trovata: {target.display_path_for(PRINTER_CFG_PATH)}"
            ) from exc
        include_present = printer_cfg_includes_macro(printer_cfg)
        update_printer_cfg = not include_present

    return PrinterSetupPlan(
        calibrator=calibrator,
        macro=macro,
        install_calibrator=calibrator.state == "stock-compatible",
        create_macro=macro.state == "missing",
        update_printer_cfg=update_printer_cfg,
        include_already_present=include_present,
    )


def _printer_cfg_with_include(data: bytes) -> bytes:
    if printer_cfg_includes_macro(data):
        return data
    try:
        data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PrinterInstallError("printer.cfg non è UTF-8: modifica bloccata") from exc
    separator = b"" if not data or data.endswith(b"\n") else b"\n"
    return (
        data
        + separator
        + b"\n# U1 Filament Automation - Adaptive PA v6\n"
        + PRINTER_CFG_INCLUDE.encode("utf-8")
        + b"\n"
    )


def install_printer_setup(
    target: PrinterFileTarget,
    loaded_by_klipper: bool | None = None,
    power_cycle_required: bool = True,
) -> PrinterSetupResult:
    """Installa calibratore, macro e include con rollback automatico."""
    plan = plan_printer_setup(target, loaded_by_klipper=loaded_by_klipper)
    macro_data = validated_asset("adaptive_pa_macro.cfg", ADAPTIVE_PA_MACRO_SHA256)
    v6_data = validated_asset("flow_calibrator_v6.py", V6_SHA256)
    validate_python_source(v6_data, str(FLOW_CALIBRATOR_PATH))

    writes: list[FileWriteResult] = []
    macro_write: FileWriteResult | None = None
    cfg_write: FileWriteResult | None = None
    flow_write: FileWriteResult | None = None
    cfg_before_sha: str | None = None
    try:
        if plan.create_macro:
            macro_write = target.write_path_atomic(
                ADAPTIVE_PA_MACRO_PATH,
                None,
                macro_data,
                ADAPTIVE_PA_MACRO_SHA256,
            )
            writes.append(macro_write)

        if plan.update_printer_cfg:
            cfg_before = target.read_path_bytes(PRINTER_CFG_PATH)
            cfg_before_sha = sha256_bytes(cfg_before)
            cfg_after = _printer_cfg_with_include(cfg_before)
            cfg_write = target.write_path_atomic(
                PRINTER_CFG_PATH,
                cfg_before_sha,
                cfg_after,
                sha256_bytes(cfg_after),
            )
            writes.append(cfg_write)

        if plan.install_calibrator:
            flow_write = target.install_atomic(STOCK_SHA256, v6_data)
            writes.append(flow_write)
    except Exception as exc:
        rollback_errors: list[str] = []
        if flow_write is not None:
            try:
                target.restore_atomic(flow_write.backup_path, V6_SHA256)
            except Exception as rollback_exc:
                rollback_errors.append(f"calibratore: {rollback_exc}")
        if cfg_write is not None and cfg_before_sha is not None:
            try:
                target.restore_path_atomic(
                    PRINTER_CFG_PATH,
                    cfg_write.backup_path,
                    cfg_write.sha256_after,
                    cfg_before_sha,
                )
            except Exception as rollback_exc:
                rollback_errors.append(f"printer.cfg: {rollback_exc}")
        if macro_write is not None:
            try:
                target.delete_path_if_sha(
                    ADAPTIVE_PA_MACRO_PATH, ADAPTIVE_PA_MACRO_SHA256
                )
            except Exception as rollback_exc:
                rollback_errors.append(f"macro: {rollback_exc}")
        detail = "" if not rollback_errors else "; rollback incompleto: " + "; ".join(rollback_errors)
        raise PrinterInstallError(f"Installazione annullata: {exc}{detail}") from exc

    installed_calibrator = inspect_calibrator(target)
    installed_macro = inspect_adaptive_pa_macro(
        target, loaded_by_klipper=loaded_by_klipper
    )
    if installed_calibrator.state != "v6-installed":
        raise PrinterInstallError("Verifica finale calibratore v6 fallita")
    if installed_macro.state != "v6-installed":
        raise PrinterInstallError("Verifica finale macro Adaptive PA fallita")
    return PrinterSetupResult(
        calibrator=installed_calibrator,
        macro=installed_macro,
        writes=tuple(writes),
        include_already_present=(
            plan.include_already_present or cfg_write is not None
        ),
        power_cycle_required=power_cycle_required and bool(writes),
    )


def _new_backup_path(target: Path) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    return target.with_name(f"{BACKUP_PREFIX}{stamp}_{uuid.uuid4().hex[:8]}")


def _new_generic_backup_path(target: Path) -> Path:
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    return target.with_name(
        f"{target.name}.U1FA_BACKUP_{stamp}_{uuid.uuid4().hex[:8]}"
    )


def _write_exclusive(path: Path, data: bytes, mode: int, uid: int, gid: int) -> None:
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(path, mode)
    try:
        os.chown(path, uid, gid)
    except (AttributeError, PermissionError):
        pass


def _replace_and_verify(target: Path, data: bytes, mode: int, uid: int, gid: int) -> None:
    temporary = target.with_name(f".{target.name}.u1fa-{uuid.uuid4().hex}.tmp")
    try:
        _write_exclusive(temporary, data, mode, uid, gid)
        os.replace(temporary, target)
        if sha256_bytes(target.read_bytes()) != sha256_bytes(data):
            raise PrinterInstallError("Verifica SHA-256 dopo la sostituzione fallita")
    finally:
        temporary.unlink(missing_ok=True)


class LocalPrinterTarget:
    """Replica il percorso assoluto U1 dentro una cartella sandbox locale."""

    def __init__(
        self,
        root: Path,
        remote_path: PurePosixPath = FLOW_CALIBRATOR_PATH,
    ) -> None:
        self.root = root.expanduser().resolve()
        self.remote_path = remote_path
        self.path = self.root.joinpath(*remote_path.parts[1:])
        self.display_path = str(self.path)

    def seed_stock_if_missing(self) -> bool:
        if self.path.exists():
            return False
        data = validated_asset("flow_calibrator_stock.py", STOCK_SHA256)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        uid = getattr(os, "getuid", lambda: 0)()
        gid = getattr(os, "getgid", lambda: 0)()
        _write_exclusive(self.path, data, 0o644, uid, gid)
        return True

    def seed_config_if_missing(self) -> bool:
        path = self.path_for(PRINTER_CFG_PATH)
        if path.exists():
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        uid = getattr(os, "getuid", lambda: 0)()
        gid = getattr(os, "getgid", lambda: 0)()
        _write_exclusive(path, (PRINTER_CFG_INCLUDE + "\n").encode(), 0o644, uid, gid)
        return True

    def read_bytes(self) -> bytes:
        return self.path.read_bytes()

    def path_for(self, remote_path: PurePosixPath) -> Path:
        return self.root.joinpath(*remote_path.parts[1:])

    def display_path_for(self, remote_path: PurePosixPath) -> str:
        return str(self.path_for(remote_path))

    def read_path_bytes(self, remote_path: PurePosixPath) -> bytes:
        return self.path_for(remote_path).read_bytes()

    def _resolve_backup(self, backup_path: str) -> Path:
        candidate = Path(backup_path).expanduser().resolve()
        legacy_local = self.root.joinpath(*LEGACY_BACKUP_PATH.parts[1:])
        trusted = candidate.name.startswith(BACKUP_PREFIX) or candidate == legacy_local
        if candidate.parent != self.path.parent or not trusted:
            raise PrinterInstallError("Backup non appartenente al calibratore U1FA")
        return candidate

    def install_atomic(self, expected_sha256: str, new_data: bytes) -> FileWriteResult:
        validate_python_source(new_data, str(self.path))
        current = self.path.read_bytes()
        before = sha256_bytes(current)
        if before != expected_sha256:
            raise PrinterInstallError(
                "Il file è cambiato dopo il controllo; installazione annullata"
            )
        metadata = self.path.stat()
        backup = _new_backup_path(self.path)
        _write_exclusive(
            backup,
            current,
            stat.S_IMODE(metadata.st_mode),
            metadata.st_uid,
            metadata.st_gid,
        )
        try:
            _replace_and_verify(
                self.path,
                new_data,
                stat.S_IMODE(metadata.st_mode),
                metadata.st_uid,
                metadata.st_gid,
            )
        except Exception:
            _replace_and_verify(
                self.path,
                current,
                stat.S_IMODE(metadata.st_mode),
                metadata.st_uid,
                metadata.st_gid,
            )
            raise
        return FileWriteResult(
            action="installed",
            path=str(self.path),
            backup_path=str(backup),
            sha256_before=before,
            sha256_after=sha256_bytes(self.path.read_bytes()),
        )

    def restore_atomic(
        self, backup_path: str, expected_current_sha256: str
    ) -> FileWriteResult:
        backup = self._resolve_backup(backup_path)
        backup_data = backup.read_bytes()
        if sha256_bytes(backup_data) != STOCK_SHA256:
            raise PrinterInstallError("Il backup non corrisponde all'originale validato")
        validate_python_source(backup_data, str(self.path))
        current = self.path.read_bytes()
        before = sha256_bytes(current)
        if before != expected_current_sha256:
            raise PrinterInstallError(
                "Il file corrente è cambiato; ripristino automatico annullato"
            )
        metadata = self.path.stat()
        rollback = _new_backup_path(self.path)
        _write_exclusive(
            rollback,
            current,
            stat.S_IMODE(metadata.st_mode),
            metadata.st_uid,
            metadata.st_gid,
        )
        _replace_and_verify(
            self.path,
            backup_data,
            stat.S_IMODE(metadata.st_mode),
            metadata.st_uid,
            metadata.st_gid,
        )
        return FileWriteResult(
            action="restored",
            path=str(self.path),
            backup_path=str(rollback),
            sha256_before=before,
            sha256_after=sha256_bytes(self.path.read_bytes()),
        )

    def write_path_atomic(
        self,
        remote_path: PurePosixPath,
        expected_current_sha256: str | None,
        new_data: bytes,
        expected_new_sha256: str,
    ) -> FileWriteResult:
        if sha256_bytes(new_data) != expected_new_sha256:
            raise PrinterInstallError("Asset da scrivere con SHA-256 non valido")
        target = self.path_for(remote_path)
        if target.is_symlink():
            raise PrinterInstallError("Percorso di configurazione simbolico: operazione bloccata")
        if not target.parent.is_dir():
            raise PrinterInstallError("Cartella di configurazione U1 non trovata")

        if expected_current_sha256 is None:
            if target.exists():
                raise PrinterInstallError("Il file è comparso dopo il controllo; operazione annullata")
            parent_metadata = target.parent.stat()
            temporary = target.with_name(f".{target.name}.u1fa-{uuid.uuid4().hex}.tmp")
            try:
                _write_exclusive(
                    temporary,
                    new_data,
                    0o644,
                    parent_metadata.st_uid,
                    parent_metadata.st_gid,
                )
                os.link(temporary, target)
                if sha256_bytes(target.read_bytes()) != expected_new_sha256:
                    target.unlink(missing_ok=True)
                    raise PrinterInstallError("Verifica SHA-256 dopo la creazione fallita")
            finally:
                temporary.unlink(missing_ok=True)
            return FileWriteResult(
                action="created",
                path=str(target),
                backup_path="",
                sha256_before="",
                sha256_after=expected_new_sha256,
            )

        current = target.read_bytes()
        before = sha256_bytes(current)
        if before != expected_current_sha256:
            raise PrinterInstallError("Il file è cambiato dopo il controllo; operazione annullata")
        metadata = target.stat()
        backup = _new_generic_backup_path(target)
        _write_exclusive(
            backup,
            current,
            stat.S_IMODE(metadata.st_mode),
            metadata.st_uid,
            metadata.st_gid,
        )
        try:
            _replace_and_verify(
                target,
                new_data,
                stat.S_IMODE(metadata.st_mode),
                metadata.st_uid,
                metadata.st_gid,
            )
        except Exception:
            _replace_and_verify(
                target,
                current,
                stat.S_IMODE(metadata.st_mode),
                metadata.st_uid,
                metadata.st_gid,
            )
            raise
        return FileWriteResult(
            action="updated",
            path=str(target),
            backup_path=str(backup),
            sha256_before=before,
            sha256_after=sha256_bytes(target.read_bytes()),
        )

    def restore_path_atomic(
        self,
        remote_path: PurePosixPath,
        backup_path: str,
        expected_current_sha256: str,
        expected_backup_sha256: str,
    ) -> FileWriteResult:
        target = self.path_for(remote_path)
        backup = Path(backup_path).expanduser().resolve()
        trusted_prefix = f"{target.name}.U1FA_BACKUP_"
        if backup.parent != target.parent or not backup.name.startswith(trusted_prefix):
            raise PrinterInstallError("Backup U1FA non appartenente al file indicato")
        backup_data = backup.read_bytes()
        if sha256_bytes(backup_data) != expected_backup_sha256:
            raise PrinterInstallError("SHA-256 del backup U1FA non valido")
        current = target.read_bytes()
        before = sha256_bytes(current)
        if before != expected_current_sha256:
            raise PrinterInstallError("File cambiato: rollback automatico annullato")
        metadata = target.stat()
        rollback = _new_generic_backup_path(target)
        _write_exclusive(
            rollback, current, stat.S_IMODE(metadata.st_mode), metadata.st_uid, metadata.st_gid
        )
        _replace_and_verify(
            target, backup_data, stat.S_IMODE(metadata.st_mode), metadata.st_uid, metadata.st_gid
        )
        return FileWriteResult(
            action="restored",
            path=str(target),
            backup_path=str(rollback),
            sha256_before=before,
            sha256_after=expected_backup_sha256,
        )

    def delete_path_if_sha(
        self, remote_path: PurePosixPath, expected_current_sha256: str
    ) -> None:
        target = self.path_for(remote_path)
        if target.is_symlink() or sha256_bytes(target.read_bytes()) != expected_current_sha256:
            raise PrinterInstallError("File cambiato: rimozione di rollback annullata")
        target.unlink()


_SSH_TARGET_RE = re.compile(r"^[A-Za-z0-9_.%+@:-]+$")


class SSHPrinterTarget:
    def __init__(
        self,
        ssh_target: str,
        port: int = 22,
        identity_file: str | None = None,
        ask_password: bool = False,
        password_provider: Callable[[], str] | None = None,
        timeout: float = 5.0,
        remote_path: PurePosixPath = FLOW_CALIBRATOR_PATH,
    ) -> None:
        if not _SSH_TARGET_RE.fullmatch(ssh_target) or ssh_target.startswith("-"):
            raise PrinterInstallError("Destinazione SSH non valida")
        if not 1 <= port <= 65535:
            raise PrinterInstallError("Porta SSH non valida")
        self.ssh_target = ssh_target
        self.port = port
        self.identity_file = identity_file
        self.ask_password = ask_password
        self.password_provider = password_provider or (
            lambda: getpass.getpass("Password SSH U1 (non verrà mostrata): ")
        )
        self._password: str | None = None
        self.timeout = timeout
        self.remote_path = remote_path
        self.display_path = f"{ssh_target}:{remote_path}"

    def _command(self) -> list[str]:
        batch_mode = "no" if self.ask_password else "yes"
        command = [
            "ssh",
            "-o",
            f"BatchMode={batch_mode}",
            "-o",
            f"ConnectTimeout={max(1, int(self.timeout))}",
            "-p",
            str(self.port),
        ]
        if self.ask_password:
            command.extend(
                [
                    "-o",
                    "PreferredAuthentications=password,keyboard-interactive",
                    "-o",
                    "PubkeyAuthentication=no",
                    "-o",
                    "NumberOfPasswordPrompts=1",
                ]
            )
        if self.identity_file:
            command.extend(["-i", str(Path(self.identity_file).expanduser())])
        command.extend([self.ssh_target, "python3", "-"])
        return command

    def _password_value(self) -> str:
        if self._password is None:
            try:
                password = self.password_provider()
            except (EOFError, KeyboardInterrupt) as exc:
                raise PrinterInstallError("Inserimento password SSH annullato") from exc
            if not password or "\n" in password or "\r" in password:
                raise PrinterInstallError("Password SSH non valida")
            self._password = password
        return self._password

    def _run_script(self, script: str) -> dict[str, Any]:
        if shutil.which("ssh") is None:
            raise PrinterInstallError(
                "Client OpenSSH non trovato / OpenSSH Client not found. "
                "Su Windows abilitarlo da Impostazioni > Sistema > Funzionalità "
                "facoltative; su Linux installare openssh-client."
            )
        askpass_dir: tempfile.TemporaryDirectory[str] | None = None
        environment = None
        start_new_session = False
        if self.ask_password:
            password = self._password_value()
            askpass_dir = tempfile.TemporaryDirectory(prefix="u1fa-askpass-")
            if os.name == "nt" and getattr(sys, "frozen", False):
                # L'eseguibile PyInstaller riconosce U1FA_ASKPASS_MODE e scrive
                # la password sull'handle ereditato, senza mostrarla né salvarla.
                askpass = Path(sys.executable)
            elif os.name == "nt":
                # Fallback per l'esecuzione del sorgente su Windows. La build
                # distribuita usa sempre il ramo PyInstaller qui sopra.
                askpass = Path(askpass_dir.name) / "askpass.cmd"
                askpass.write_text(
                    "@echo off\r\n"
                    "powershell.exe -NoProfile -NonInteractive -Command "
                    '"[Console]::Out.WriteLine($env:U1FA_SSH_PASSWORD)"\r\n',
                    encoding="utf-8",
                )
            else:
                askpass = Path(askpass_dir.name) / "askpass.sh"
                askpass.write_text(
                    '#!/bin/sh\nprintf "%s\\n" "$U1FA_SSH_PASSWORD"\n',
                    encoding="utf-8",
                )
                os.chmod(askpass, 0o700)
            environment = os.environ.copy()
            environment.update(
                {
                    "SSH_ASKPASS": str(askpass),
                    "SSH_ASKPASS_REQUIRE": "force",
                    "DISPLAY": environment.get("DISPLAY") or ":u1fa",
                    "U1FA_SSH_PASSWORD": password,
                    "U1FA_ASKPASS_MODE": "1",
                }
            )
            start_new_session = True
        try:
            result = subprocess.run(
                self._command(),
                input=script,
                text=True,
                capture_output=True,
                timeout=max(2.0, self.timeout + 2.0),
                check=False,
                env=environment,
                start_new_session=start_new_session,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise PrinterInstallError(f"Connessione SSH fallita: {exc}") from exc
        finally:
            if askpass_dir is not None:
                askpass_dir.cleanup()
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "errore remoto"
            raise PrinterInstallError(f"Comando SSH fallito: {detail}")
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        if not lines:
            raise PrinterInstallError("La U1 non ha restituito alcun risultato")
        try:
            payload = json.loads(lines[-1])
        except json.JSONDecodeError as exc:
            raise PrinterInstallError("Risposta SSH non riconosciuta") from exc
        if not isinstance(payload, dict) or not payload.get("ok"):
            raise PrinterInstallError(str(payload.get("error", "operazione remota fallita")))
        return payload

    def read_bytes(self) -> bytes:
        return self.read_path_bytes(self.remote_path)

    def display_path_for(self, remote_path: PurePosixPath) -> str:
        return f"{self.ssh_target}:{remote_path}"

    def read_path_bytes(self, remote_path: PurePosixPath) -> bytes:
        script = f"""\
import base64, json
from pathlib import Path
try:
    path = Path({str(remote_path)!r})
    if not path.is_file():
        print(json.dumps({{"ok": True, "exists": False}}))
        raise SystemExit(0)
    data = path.read_bytes()
    print(json.dumps({{"ok": True, "data": base64.b64encode(data).decode("ascii")}}))
except Exception as exc:
    print(json.dumps({{"ok": False, "error": str(exc)}}))
"""
        payload = self._run_script(script)
        if payload.get("exists") is False:
            raise FileNotFoundError(self.display_path_for(remote_path))
        try:
            return base64.b64decode(str(payload["data"]), validate=True)
        except (KeyError, ValueError) as exc:
            raise PrinterInstallError("Contenuto remoto non valido") from exc

    def install_atomic(self, expected_sha256: str, new_data: bytes) -> FileWriteResult:
        encoded = base64.b64encode(new_data).decode("ascii")
        script = _remote_install_script(
            str(self.remote_path), expected_sha256, V6_SHA256, encoded
        )
        return _write_result(self._run_script(script))

    def write_path_atomic(
        self,
        remote_path: PurePosixPath,
        expected_current_sha256: str | None,
        new_data: bytes,
        expected_new_sha256: str,
    ) -> FileWriteResult:
        script = _remote_write_path_script(
            str(remote_path),
            expected_current_sha256,
            expected_new_sha256,
            base64.b64encode(new_data).decode("ascii"),
        )
        return _write_result(self._run_script(script))

    def restore_path_atomic(
        self,
        remote_path: PurePosixPath,
        backup_path: str,
        expected_current_sha256: str,
        expected_backup_sha256: str,
    ) -> FileWriteResult:
        backup = PurePosixPath(backup_path)
        if (
            backup.parent != remote_path.parent
            or not backup.name.startswith(f"{remote_path.name}.U1FA_BACKUP_")
        ):
            raise PrinterInstallError("Backup remoto U1FA non appartenente al file")
        return _write_result(
            self._run_script(
                _remote_restore_path_script(
                    str(remote_path),
                    str(backup),
                    expected_current_sha256,
                    expected_backup_sha256,
                )
            )
        )

    def delete_path_if_sha(
        self, remote_path: PurePosixPath, expected_current_sha256: str
    ) -> None:
        self._run_script(
            _remote_delete_path_script(str(remote_path), expected_current_sha256)
        )

    def restore_atomic(
        self, backup_path: str, expected_current_sha256: str
    ) -> FileWriteResult:
        backup = PurePosixPath(backup_path)
        trusted = backup.name.startswith(BACKUP_PREFIX) or backup == LEGACY_BACKUP_PATH
        if backup.parent != self.remote_path.parent or not trusted:
            raise PrinterInstallError("Backup remoto non appartenente al calibratore U1FA")
        script = _remote_restore_script(
            str(self.remote_path), str(backup), expected_current_sha256, STOCK_SHA256
        )
        return _write_result(self._run_script(script))


def _write_result(payload: dict[str, Any]) -> FileWriteResult:
    try:
        return FileWriteResult(
            action=str(payload["action"]),
            path=str(payload["path"]),
            backup_path=str(payload["backup_path"]),
            sha256_before=str(payload["sha256_before"]),
            sha256_after=str(payload["sha256_after"]),
        )
    except KeyError as exc:
        raise PrinterInstallError("Risultato remoto incompleto") from exc


def _remote_install_script(
    target: str, expected_sha256: str, new_sha256: str, encoded_data: str
) -> str:
    return f"""\
import base64, hashlib, json, os, stat, time, uuid, warnings
from pathlib import Path
target = Path({target!r})
expected = {expected_sha256!r}
expected_new = {new_sha256!r}
new_data = base64.b64decode({encoded_data!r})
temporary = None
replaced = False
current = None
metadata = None
try:
    current = target.read_bytes()
    before = hashlib.sha256(current).hexdigest()
    if before != expected:
        raise RuntimeError("file cambiato dopo il controllo; operazione annullata")
    if hashlib.sha256(new_data).hexdigest() != expected_new:
        raise RuntimeError("asset v6 non valido")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        compile(new_data.decode("utf-8"), str(target), "exec")
    metadata = target.stat()
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    backup = target.with_name("{BACKUP_PREFIX}" + stamp + "_" + uuid.uuid4().hex[:8])
    with backup.open("xb") as handle:
        handle.write(current)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(backup, stat.S_IMODE(metadata.st_mode))
    os.chown(backup, metadata.st_uid, metadata.st_gid)
    temporary = target.with_name("." + target.name + ".u1fa-" + uuid.uuid4().hex + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(new_data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, stat.S_IMODE(metadata.st_mode))
    os.chown(temporary, metadata.st_uid, metadata.st_gid)
    os.replace(temporary, target)
    temporary = None
    replaced = True
    after = hashlib.sha256(target.read_bytes()).hexdigest()
    if after != expected_new:
        raise RuntimeError("verifica SHA-256 dopo la sostituzione fallita")
    print(json.dumps({{"ok": True, "action": "installed", "path": str(target), "backup_path": str(backup), "sha256_before": before, "sha256_after": after}}))
except Exception as exc:
    if temporary is not None:
        try:
            temporary.unlink()
        except Exception:
            pass
    if replaced and current is not None and metadata is not None:
        try:
            rollback_tmp = target.with_name("." + target.name + ".u1fa-rollback-" + uuid.uuid4().hex + ".tmp")
            with rollback_tmp.open("xb") as handle:
                handle.write(current)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(rollback_tmp, stat.S_IMODE(metadata.st_mode))
            os.chown(rollback_tmp, metadata.st_uid, metadata.st_gid)
            os.replace(rollback_tmp, target)
        except Exception as rollback_exc:
            print(json.dumps({{"ok": False, "error": str(exc) + "; rollback fallito: " + str(rollback_exc)}}))
            raise SystemExit(0)
    print(json.dumps({{"ok": False, "error": str(exc)}}))
"""


def _remote_restore_script(
    target: str,
    backup_path: str,
    expected_current_sha256: str,
    expected_backup_sha256: str,
) -> str:
    return f"""\
import hashlib, json, os, stat, time, uuid, warnings
from pathlib import Path
target = Path({target!r})
backup = Path({backup_path!r})
temporary = None
replaced = False
current = None
metadata = None
try:
    current = target.read_bytes()
    before = hashlib.sha256(current).hexdigest()
    if before != {expected_current_sha256!r}:
        raise RuntimeError("file corrente cambiato; ripristino annullato")
    backup_data = backup.read_bytes()
    if hashlib.sha256(backup_data).hexdigest() != {expected_backup_sha256!r}:
        raise RuntimeError("backup non corrispondente all'originale validato")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        compile(backup_data.decode("utf-8"), str(target), "exec")
    metadata = target.stat()
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    rollback = target.with_name("{BACKUP_PREFIX}" + stamp + "_" + uuid.uuid4().hex[:8])
    with rollback.open("xb") as handle:
        handle.write(current)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(rollback, stat.S_IMODE(metadata.st_mode))
    os.chown(rollback, metadata.st_uid, metadata.st_gid)
    temporary = target.with_name("." + target.name + ".u1fa-" + uuid.uuid4().hex + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(backup_data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, stat.S_IMODE(metadata.st_mode))
    os.chown(temporary, metadata.st_uid, metadata.st_gid)
    os.replace(temporary, target)
    temporary = None
    replaced = True
    after = hashlib.sha256(target.read_bytes()).hexdigest()
    if after != {expected_backup_sha256!r}:
        raise RuntimeError("verifica SHA-256 del ripristino fallita")
    print(json.dumps({{"ok": True, "action": "restored", "path": str(target), "backup_path": str(rollback), "sha256_before": before, "sha256_after": after}}))
except Exception as exc:
    if temporary is not None:
        try:
            temporary.unlink()
        except Exception:
            pass
    if replaced and current is not None and metadata is not None:
        try:
            recovery_tmp = target.with_name("." + target.name + ".u1fa-recovery-" + uuid.uuid4().hex + ".tmp")
            with recovery_tmp.open("xb") as handle:
                handle.write(current)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(recovery_tmp, stat.S_IMODE(metadata.st_mode))
            os.chown(recovery_tmp, metadata.st_uid, metadata.st_gid)
            os.replace(recovery_tmp, target)
        except Exception as recovery_exc:
            print(json.dumps({{"ok": False, "error": str(exc) + "; recovery fallita: " + str(recovery_exc)}}))
            raise SystemExit(0)
    print(json.dumps({{"ok": False, "error": str(exc)}}))
"""


def _remote_write_path_script(
    target: str,
    expected_current_sha256: str | None,
    expected_new_sha256: str,
    encoded_data: str,
) -> str:
    return f"""\
import base64, hashlib, json, os, stat, time, uuid
from pathlib import Path
target = Path({target!r})
expected_current = {expected_current_sha256!r}
expected_new = {expected_new_sha256!r}
new_data = base64.b64decode({encoded_data!r})
temporary = None
replaced = False
current = None
metadata = None
try:
    if hashlib.sha256(new_data).hexdigest() != expected_new:
        raise RuntimeError("asset da scrivere con SHA-256 non valido")
    if target.is_symlink():
        raise RuntimeError("percorso simbolico: operazione bloccata")
    if not target.parent.is_dir():
        raise RuntimeError("cartella di configurazione U1 non trovata")
    if expected_current is None:
        if target.exists():
            raise RuntimeError("file comparso dopo il controllo; operazione annullata")
        parent_meta = target.parent.stat()
        temporary = target.with_name("." + target.name + ".u1fa-" + uuid.uuid4().hex + ".tmp")
        with temporary.open("xb") as handle:
            handle.write(new_data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.chown(temporary, parent_meta.st_uid, parent_meta.st_gid)
        os.link(temporary, target)
        temporary.unlink()
        temporary = None
        after = hashlib.sha256(target.read_bytes()).hexdigest()
        if after != expected_new:
            target.unlink()
            raise RuntimeError("verifica SHA-256 dopo la creazione fallita")
        print(json.dumps({{"ok": True, "action": "created", "path": str(target), "backup_path": "", "sha256_before": "", "sha256_after": after}}))
    else:
        current = target.read_bytes()
        before = hashlib.sha256(current).hexdigest()
        if before != expected_current:
            raise RuntimeError("file cambiato dopo il controllo; operazione annullata")
        metadata = target.stat()
        stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        backup = target.with_name(target.name + ".U1FA_BACKUP_" + stamp + "_" + uuid.uuid4().hex[:8])
        with backup.open("xb") as handle:
            handle.write(current)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(backup, stat.S_IMODE(metadata.st_mode))
        os.chown(backup, metadata.st_uid, metadata.st_gid)
        temporary = target.with_name("." + target.name + ".u1fa-" + uuid.uuid4().hex + ".tmp")
        with temporary.open("xb") as handle:
            handle.write(new_data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, stat.S_IMODE(metadata.st_mode))
        os.chown(temporary, metadata.st_uid, metadata.st_gid)
        os.replace(temporary, target)
        temporary = None
        replaced = True
        after = hashlib.sha256(target.read_bytes()).hexdigest()
        if after != expected_new:
            raise RuntimeError("verifica SHA-256 dopo la sostituzione fallita")
        print(json.dumps({{"ok": True, "action": "updated", "path": str(target), "backup_path": str(backup), "sha256_before": before, "sha256_after": after}}))
except Exception as exc:
    if temporary is not None:
        try:
            temporary.unlink()
        except Exception:
            pass
    if replaced and current is not None and metadata is not None:
        try:
            rollback = target.with_name("." + target.name + ".u1fa-rollback-" + uuid.uuid4().hex + ".tmp")
            with rollback.open("xb") as handle:
                handle.write(current)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(rollback, stat.S_IMODE(metadata.st_mode))
            os.chown(rollback, metadata.st_uid, metadata.st_gid)
            os.replace(rollback, target)
        except Exception as rollback_exc:
            print(json.dumps({{"ok": False, "error": str(exc) + "; rollback fallito: " + str(rollback_exc)}}))
            raise SystemExit(0)
    print(json.dumps({{"ok": False, "error": str(exc)}}))
"""


def _remote_restore_path_script(
    target: str,
    backup_path: str,
    expected_current_sha256: str,
    expected_backup_sha256: str,
) -> str:
    return f"""\
import hashlib, json, os, stat, time, uuid
from pathlib import Path
target = Path({target!r})
backup = Path({backup_path!r})
temporary = None
try:
    current = target.read_bytes()
    before = hashlib.sha256(current).hexdigest()
    if before != {expected_current_sha256!r}:
        raise RuntimeError("file cambiato: rollback annullato")
    backup_data = backup.read_bytes()
    if hashlib.sha256(backup_data).hexdigest() != {expected_backup_sha256!r}:
        raise RuntimeError("SHA-256 backup non valido")
    metadata = target.stat()
    stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    rollback = target.with_name(target.name + ".U1FA_BACKUP_" + stamp + "_" + uuid.uuid4().hex[:8])
    with rollback.open("xb") as handle:
        handle.write(current)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(rollback, stat.S_IMODE(metadata.st_mode))
    os.chown(rollback, metadata.st_uid, metadata.st_gid)
    temporary = target.with_name("." + target.name + ".u1fa-" + uuid.uuid4().hex + ".tmp")
    with temporary.open("xb") as handle:
        handle.write(backup_data)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, stat.S_IMODE(metadata.st_mode))
    os.chown(temporary, metadata.st_uid, metadata.st_gid)
    os.replace(temporary, target)
    temporary = None
    after = hashlib.sha256(target.read_bytes()).hexdigest()
    if after != {expected_backup_sha256!r}:
        raise RuntimeError("verifica SHA-256 rollback fallita")
    print(json.dumps({{"ok": True, "action": "restored", "path": str(target), "backup_path": str(rollback), "sha256_before": before, "sha256_after": after}}))
except Exception as exc:
    if temporary is not None:
        try:
            temporary.unlink()
        except Exception:
            pass
    print(json.dumps({{"ok": False, "error": str(exc)}}))
"""


def _remote_delete_path_script(target: str, expected_current_sha256: str) -> str:
    return f"""\
import hashlib, json
from pathlib import Path
target = Path({target!r})
try:
    if target.is_symlink():
        raise RuntimeError("percorso simbolico: rimozione bloccata")
    if hashlib.sha256(target.read_bytes()).hexdigest() != {expected_current_sha256!r}:
        raise RuntimeError("file cambiato: rimozione di rollback annullata")
    target.unlink()
    print(json.dumps({{"ok": True, "action": "deleted"}}))
except Exception as exc:
    print(json.dumps({{"ok": False, "error": str(exc)}}))
"""


class MoonrakerClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 5.0,
        api_key: str | None = None,
        opener: Any | None = None,
    ) -> None:
        if not base_url.startswith(("http://", "https://")):
            raise PrinterInstallError("URL Moonraker non valido")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key
        self.opener = urllib.request.urlopen if opener is None else opener

    def _request(
        self, method: str, path: str, body: dict[str, Any] | None = None
    ) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        request = urllib.request.Request(
            self.base_url + path,
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with self.opener(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            raise PrinterInstallError(f"Moonraker non raggiungibile: {exc}") from exc
        if isinstance(payload, dict) and "result" in payload:
            return payload["result"]
        return payload

    def safety_status(self) -> PrinterSafetyStatus:
        info = self._request("GET", "/printer/info")
        query = self._request(
            "POST",
            "/printer/objects/query",
            {
                "objects": {
                    "print_stats": ["state"],
                    "virtual_sdcard": ["is_active"],
                    "idle_timeout": ["state"],
                    "machine_state_manager": None,
                }
            },
        )
        if not isinstance(info, dict) or not isinstance(query, dict):
            raise PrinterInstallError("Risposta Moonraker incompleta")
        status = query.get("status")
        if not isinstance(status, dict):
            raise PrinterInstallError("Stato stampante non disponibile")
        print_stats = status.get("print_stats")
        virtual_sdcard = status.get("virtual_sdcard")
        idle_timeout = status.get("idle_timeout")
        if (
            not isinstance(print_stats, dict)
            or not isinstance(virtual_sdcard, dict)
            or not isinstance(idle_timeout, dict)
        ):
            raise PrinterInstallError("Oggetti di sicurezza Moonraker mancanti")
        machine = status.get("machine_state_manager")
        machine_state = None
        if isinstance(machine, dict) and machine.get("main_state") is not None:
            machine_state = str(machine["main_state"])
        return PrinterSafetyStatus(
            klippy_state=str(info.get("state", "unknown")),
            print_state=str(print_stats.get("state", "unknown")),
            virtual_sd_active=bool(virtual_sdcard.get("is_active", True)),
            idle_state=str(idle_timeout.get("state", "unknown")),
            machine_state=machine_state,
        )

    def gcode_store(self, count: int = 1000) -> list[dict[str, Any]]:
        if count < 1 or count > 10000:
            raise PrinterInstallError(
                "Il numero di risposte G-code richiesto deve essere tra 1 e 10000"
            )
        payload = self._request("GET", f"/server/gcode_store?count={count}")
        if not isinstance(payload, dict):
            raise PrinterInstallError("Risposta gcode_store Moonraker non valida")
        items = payload.get("gcode_store")
        if not isinstance(items, list):
            raise PrinterInstallError("Elenco gcode_store Moonraker mancante")
        return items

    def run_gcode(self, script: str) -> None:
        if not isinstance(script, str) or not script.strip():
            raise PrinterInstallError("Comando G-code vuoto: invio bloccato")
        if "\x00" in script or len(script) > 4096:
            raise PrinterInstallError("Comando G-code non valido: invio bloccato")
        result = self._request(
            "POST",
            "/printer/gcode/script",
            {"script": script.strip()},
        )
        if result != "ok":
            raise PrinterInstallError(
                f"Moonraker non ha confermato il comando G-code: {result!r}"
            )

    def object_names(self) -> frozenset[str]:
        result = self._request("GET", "/printer/objects/list")
        if not isinstance(result, dict) or not isinstance(result.get("objects"), list):
            raise PrinterInstallError("Elenco oggetti Klipper non disponibile")
        return frozenset(str(item) for item in result["objects"])

    def has_gcode_macro(self, name: str) -> bool:
        expected = f"gcode_macro {name}".casefold()
        return any(item.casefold() == expected for item in self.object_names())

def require_safe_printer(client: MoonrakerClient) -> PrinterSafetyStatus:
    status = client.safety_status()
    if not status.safe_to_modify:
        raise PrinterInstallError(
            "Stampante non inattiva: "
            f"Klipper={status.klippy_state}, stampa={status.print_state}, "
            f"virtual_sd_active={status.virtual_sd_active}, "
            f"idle={status.idle_state}, machine={status.machine_state}. "
            "Nessuna modifica eseguita."
        )
    return status
