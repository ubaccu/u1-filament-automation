from __future__ import annotations

import html
import secrets
import threading
import time
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs
from urllib.parse import urlsplit

from . import __version__
from .config import (
    ConfigError,
    ConnectionConfig,
    normalize_service_url,
    save_connection_config,
)
from .models import SpoolmanInventory
from .orca import discover_orca
from .pa import PAParseError, last_complete_suite_span
from .pa_capture import (
    PACaptureError,
    latest_cached_suite,
    new_gcode_entries,
    parse_gcode_store,
    response_text,
)
from .pa_profile import (
    CalibrationIdentity,
    PAProfileError,
    ProfileCandidate,
    find_profile_path,
    profile_candidates,
    update_pa_profile,
)
from .printer import (
    MoonrakerClient,
    PrinterInstallError,
    PrinterSetupPlan,
    PrinterSetupResult,
    SSHPrinterTarget,
    install_printer_setup,
    plan_printer_setup,
    require_safe_printer,
)
from .spoolman import (
    NewSpoolRequest,
    ServiceError,
    SpoolCreationPlan,
    SpoolCreationResult,
    SpoolmanClient,
    candidates_from_moonraker,
    create_spool_from_plan,
    explicit_candidates,
    first_working_inventory,
    plan_spool_creation,
)
from .sync import default_system_dir, sync_profiles
from .update import (
    UpdateError,
    UpdateInfo,
    check_for_update,
    download_update,
    open_update_package,
)
from .watch import (
    WatchStateError,
    default_watch_state_path,
    load_managed_profiles,
    managed_profiles_from_report,
    save_managed_profiles,
)


@dataclass(frozen=True)
class Envelope:
    name: str
    low_speed: int
    mid_speed: int
    high_speed: int
    low_accel: int
    mid_accel: int
    high_accel: int


VALIDATED_U1_ENVELOPE = Envelope(
    name="U1 convalidato",
    low_speed=100,
    mid_speed=218,
    high_speed=336,
    low_accel=2000,
    mid_accel=6000,
    high_accel=10000,
)
LOGO_ASSET = Path(__file__).resolve().parent / "assets" / "u1fa_logo.png"


class GUIError(RuntimeError):
    pass


def _tr(language: str, italian: str, english: str) -> str:
    return english if language == "en" else italian


@dataclass(frozen=True)
class CalibrationSelection:
    profile_name: str
    physical_slot: int
    internal_extruder: int
    temperature: int
    envelope: Envelope = VALIDATED_U1_ENVELOPE

    @property
    def commands(self) -> tuple[str, str]:
        return build_calibration_commands(
            self.physical_slot,
            self.temperature,
            self.envelope,
        )


@dataclass(frozen=True)
class JobSnapshot:
    state: str
    message: str
    selection: CalibrationSelection | None = None
    report: dict[str, Any] | None = None


@dataclass(frozen=True)
class PreparedSpoolCreation:
    ticket: str
    plan: SpoolCreationPlan


@dataclass(frozen=True)
class SpoolCreationReceipt:
    result: SpoolCreationResult
    sandbox_profile_path: Path
    real_profile_path: Path | None


@dataclass(frozen=True)
class PreparedPrinterSetup:
    ticket: str
    plan: PrinterSetupPlan


@dataclass(frozen=True)
class PrinterSetupReceipt:
    result: PrinterSetupResult


@dataclass(frozen=True)
class ProfileMonitorSnapshot:
    state: str
    message_it: str
    message_en: str
    created_profiles: tuple[str, ...] = ()
    checked_at: str = ""


@dataclass(frozen=True)
class UpdateSnapshot:
    state: str
    message_it: str
    message_en: str
    info: UpdateInfo | None = None
    local_path: Path | None = None


def physical_to_internal(physical_slot: int) -> int:
    if physical_slot not in {1, 2, 3, 4}:
        raise GUIError("Lo slot fisico deve essere compreso tra 1 e 4")
    return physical_slot - 1


def validate_temperature(value: int) -> int:
    if value < 170 or value > 300:
        raise GUIError("La temperatura deve essere compresa tra 170 e 300 °C")
    return value


def build_calibration_commands(
    physical_slot: int,
    temperature: int,
    envelope: Envelope = VALIDATED_U1_ENVELOPE,
) -> tuple[str, str]:
    extruder = physical_to_internal(physical_slot)
    temperature = validate_temperature(temperature)
    if not (
        0 < envelope.low_speed < envelope.mid_speed < envelope.high_speed
        and 0 < envelope.low_accel <= envelope.mid_accel <= envelope.high_accel
    ):
        raise GUIError("Envelope non valido: comando bloccato")
    envelope_command = (
        "APA_COIL_SET_ENVELOPE "
        f"LOW_SPEED={envelope.low_speed} "
        f"MID_SPEED={envelope.mid_speed} "
        f"HIGH_SPEED={envelope.high_speed} "
        f"LOW_ACCEL={envelope.low_accel} "
        f"MID_ACCEL={envelope.mid_accel} "
        f"HIGH_ACCEL={envelope.high_accel}"
    )
    run_command = (
        f"APA_COIL_RUN_ULTRA EXTRUDER={extruder} TEMP={temperature}"
    )
    return envelope_command, run_command


class CalibrationController:
    def __init__(
        self,
        moonraker_url: str,
        spoolman_url: str,
        sandbox_dir: Path,
        system_dir: Path,
        timeout: float = 5.0,
        poll_interval: float = 2.0,
        spoolman_client_factory: Callable[[], SpoolmanClient] | None = None,
        real_orca_dir: Path | None = None,
        ssh_target: str | None = None,
        ssh_port: int = 22,
        identity_file: str | None = None,
        monitor_interval: float = 10.0,
        connection_config_path: Path | None = None,
        update_checker: Callable[[], UpdateInfo | None] | None = None,
        update_dir: Path | None = None,
    ) -> None:
        self.moonraker_url = moonraker_url
        self.spoolman_url = spoolman_url
        self.sandbox_dir = sandbox_dir.expanduser().resolve()
        self.system_dir = system_dir.expanduser().resolve()
        self.real_orca_dir = (
            None if real_orca_dir is None else real_orca_dir.expanduser().resolve()
        )
        self.ssh_target = ssh_target
        self.ssh_port = ssh_port
        self.identity_file = identity_file
        self.monitor_interval = monitor_interval
        self.connection_config_path = connection_config_path
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._spoolman_client_factory = spoolman_client_factory
        self._lock = threading.Lock()
        self._creation_lock = threading.Lock()
        self._setup_lock = threading.Lock()
        self._job = JobSnapshot("idle", "Pronto")
        self._inventory = SpoolmanInventory(url=spoolman_url)
        self._profiles: tuple[ProfileCandidate, ...] = ()
        self._pending_creation: PreparedSpoolCreation | None = None
        self._last_creation: SpoolCreationReceipt | None = None
        self._pending_setup: PreparedPrinterSetup | None = None
        self._last_setup: PrinterSetupReceipt | None = None
        self._language = "it"
        self._monitor_lock = threading.Lock()
        self._monitor_stop = threading.Event()
        self._monitor_thread: threading.Thread | None = None
        self._monitor_state_path = (
            None
            if self.real_orca_dir is None
            else default_watch_state_path(self.real_orca_dir, sandbox=False)
        )
        self._managed_profiles: set[str] = set()
        self._monitor = ProfileMonitorSnapshot(
            "idle",
            "Monitor Spoolman pronto",
            "Spoolman monitor ready",
        )
        self._update_lock = threading.Lock()
        self._update_checker = update_checker or (
            lambda: check_for_update(__version__)
        )
        self._update_dir = (
            Path.home() / "Downloads" / "U1FA Updates"
            if update_dir is None
            else update_dir.expanduser()
        ).resolve()
        self._update = UpdateSnapshot(
            "idle",
            "Controllo aggiornamenti non ancora eseguito",
            "Update check has not run yet",
        )

    def language(self) -> str:
        with self._lock:
            return self._language

    def set_language(self, language: str) -> None:
        if language not in {"it", "en"}:
            raise GUIError("Lingua non valida / Invalid language")
        with self._lock:
            self._language = language

    def monitor_snapshot(self) -> ProfileMonitorSnapshot:
        with self._monitor_lock:
            return self._monitor

    def _set_monitor(self, snapshot: ProfileMonitorSnapshot) -> None:
        with self._monitor_lock:
            self._monitor = snapshot

    def update_snapshot(self) -> UpdateSnapshot:
        with self._update_lock:
            return self._update

    def _set_update(self, snapshot: UpdateSnapshot) -> None:
        with self._update_lock:
            self._update = snapshot

    def start_update_check(self) -> threading.Thread | None:
        with self._update_lock:
            if self._update.state in {"checking", "downloading"}:
                return None
            self._update = UpdateSnapshot(
                "checking",
                "Controllo aggiornamenti in corso…",
                "Checking for updates…",
            )

        def worker() -> None:
            try:
                info = self._update_checker()
                if info is None:
                    snapshot = UpdateSnapshot(
                        "current",
                        "U1FA è aggiornata",
                        "U1FA is up to date",
                    )
                else:
                    snapshot = UpdateSnapshot(
                        "available",
                        f"Nuova versione {info.version} disponibile",
                        f"Version {info.version} is available",
                        info=info,
                    )
            except (UpdateError, OSError, ValueError) as exc:
                snapshot = UpdateSnapshot(
                    "error",
                    f"Controllo aggiornamenti non disponibile: {exc}",
                    f"Update check unavailable: {exc}",
                )
            self._set_update(snapshot)

        thread = threading.Thread(
            target=worker,
            name="u1fa-update-check",
            daemon=True,
        )
        thread.start()
        return thread

    def download_available_update(self) -> Path:
        with self._update_lock:
            current = self._update
            if current.state != "available" or current.info is None:
                raise GUIError(
                    "Nessun aggiornamento disponibile / No update is available"
                )
            info = current.info
            self._update = UpdateSnapshot(
                "downloading",
                "Download e verifica SHA-256 in corso…",
                "Downloading and verifying SHA-256…",
                info=info,
            )
        try:
            path = download_update(info, self._update_dir)
        except UpdateError as exc:
            self._set_update(UpdateSnapshot(
                "error",
                f"Aggiornamento non scaricato: {exc}",
                f"Update was not downloaded: {exc}",
                info=info,
            ))
            raise GUIError(str(exc)) from exc
        self._set_update(UpdateSnapshot(
            "downloaded",
            "Pacchetto scaricato e SHA-256 verificato",
            "Package downloaded and SHA-256 verified",
            info=info,
            local_path=path,
        ))
        return path

    def open_downloaded_update(self) -> Path:
        with self._update_lock:
            current = self._update
        if current.state != "downloaded" or current.local_path is None:
            raise GUIError(
                "Nessun pacchetto verificato da aprire / No verified package to open"
            )
        try:
            open_update_package(current.local_path)
        except UpdateError as exc:
            raise GUIError(str(exc)) from exc
        return current.local_path

    def connection_config(self) -> ConnectionConfig | None:
        with self._lock:
            if not self.moonraker_url or not self.spoolman_url:
                return None
            return ConnectionConfig(self.moonraker_url, self.spoolman_url)

    def configure_connections(
        self,
        moonraker_address: str,
        spoolman_address: str,
    ) -> ConnectionConfig:
        """Verifica in sola lettura e salva gli endpoint scelti dall'utente."""
        try:
            moonraker_url = normalize_service_url(moonraker_address, "U1/Moonraker")
            MoonrakerClient(moonraker_url, timeout=self.timeout).safety_status()
            if self._spoolman_client_factory is not None:
                inventory = self._spoolman_client_factory().inventory()
                spoolman_url = normalize_service_url(inventory.url, "Spoolman")
            elif spoolman_address.strip() and spoolman_address.strip().lower() not in {
                "auto",
                "automatico",
                "automatic",
            }:
                spoolman_url = normalize_service_url(spoolman_address, "Spoolman")
                inventory = SpoolmanClient(spoolman_url, timeout=self.timeout).inventory()
            else:
                candidates = explicit_candidates()
                try:
                    discovered = candidates_from_moonraker(
                        moonraker_url,
                        timeout=self.timeout,
                    )
                except (ServiceError, ValueError):
                    discovered = []
                parsed_moonraker = urlsplit(moonraker_url)
                if parsed_moonraker.hostname:
                    host = parsed_moonraker.hostname
                    host_for_url = f"[{host}]" if ":" in host else host
                    discovered.append(f"http://{host_for_url}:7912")
                for candidate in discovered:
                    if candidate not in candidates:
                        candidates.append(candidate)
                inventory, errors = first_working_inventory(
                    candidates,
                    timeout=self.timeout,
                )
                if inventory is None:
                    detail = errors[-1] if errors else "nessun endpoint candidato"
                    raise ConfigError(
                        "Spoolman non rilevato automaticamente. "
                        "Inserire manualmente il suo indirizzo / "
                        f"Spoolman was not detected automatically. Enter its address manually: {detail}"
                    )
                spoolman_url = normalize_service_url(inventory.url, "Spoolman")
            parsed = urlsplit(moonraker_url)
            if not parsed.hostname:
                raise ConfigError("Impossibile ricavare l'host SSH / Cannot determine SSH host")
            config = ConnectionConfig(moonraker_url, spoolman_url)
            if self.connection_config_path is not None:
                save_connection_config(config, self.connection_config_path)
        except (ConfigError, PrinterInstallError, ServiceError, OSError) as exc:
            raise GUIError(str(exc)) from exc

        self.stop_profile_monitor()
        with self._lock:
            self.moonraker_url = moonraker_url
            self.spoolman_url = spoolman_url
            self.ssh_target = f"root@{parsed.hostname}"
        self._accept_inventory(inventory)
        self.start_profile_monitor()
        return config

    def sync_external_profiles(self):
        """Sincronizza anche le bobine create fuori dalla GUI, senza sovrascritture."""
        inventory = self._spoolman_client().inventory()
        self._accept_inventory(inventory)
        if self.real_orca_dir is None:
            return None
        report = sync_profiles(
            inventory,
            self.real_orca_dir,
            system_dir=self.system_dir,
            apply=True,
            ignored_profile_names=self._managed_profiles,
        )
        updated = self._managed_profiles | managed_profiles_from_report(report)
        if updated != self._managed_profiles and self._monitor_state_path is not None:
            save_managed_profiles(
                self._monitor_state_path,
                self.real_orca_dir,
                updated,
            )
        self._managed_profiles = updated
        created = tuple(
            action.profile_name for action in report.actions if action.status == "created"
        )
        now = time.strftime("%H:%M:%S")
        if created:
            names = ", ".join(created)
            self._set_monitor(ProfileMonitorSnapshot(
                "created",
                f"Creati automaticamente {len(created)} nuovi profili Orca: {names}",
                f"Automatically created {len(created)} new Orca profiles: {names}",
                created,
                now,
            ))
        else:
            self._set_monitor(ProfileMonitorSnapshot(
                "ready",
                "Spoolman sincronizzato; nessun nuovo profilo da creare",
                "Spoolman synchronized; no new profiles to create",
                (),
                now,
            ))
        return report

    def start_profile_monitor(self) -> None:
        if self.real_orca_dir is None or self._monitor_thread is not None:
            return
        if self.monitor_interval < 5:
            raise GUIError("Intervallo monitor minimo 5 secondi / Minimum monitor interval is 5 seconds")
        try:
            if self._monitor_state_path is not None:
                self._managed_profiles = load_managed_profiles(
                    self._monitor_state_path,
                    self.real_orca_dir,
                )
            self.sync_external_profiles()
        except (ServiceError, ValueError, PAProfileError, OSError, WatchStateError) as exc:
            raise GUIError(
                f"Avvio monitor Spoolman bloccato / Spoolman monitor startup blocked: {exc}"
            ) from exc
        self._monitor_stop.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="u1fa-spoolman-monitor",
            daemon=True,
        )
        self._monitor_thread.start()

    def _monitor_loop(self) -> None:
        while not self._monitor_stop.wait(self.monitor_interval):
            try:
                self.sync_external_profiles()
            except (ServiceError, ValueError, PAProfileError, OSError, WatchStateError) as exc:
                self._set_monitor(ProfileMonitorSnapshot(
                    "error",
                    f"Monitor temporaneamente non disponibile: {exc}",
                    f"Monitor temporarily unavailable: {exc}",
                    (),
                    time.strftime("%H:%M:%S"),
                ))

    def stop_profile_monitor(self) -> None:
        self._monitor_stop.set()
        thread = self._monitor_thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=min(2.0, self.monitor_interval))
        self._monitor_thread = None

    def _printer_target(self, password: str) -> SSHPrinterTarget:
        if not self.ssh_target:
            raise GUIError("Destinazione SSH U1 non configurata")
        use_password = bool(password)
        return SSHPrinterTarget(
            self.ssh_target,
            port=self.ssh_port,
            identity_file=self.identity_file,
            ask_password=use_password,
            password_provider=(lambda: password),
            timeout=self.timeout,
        )

    def prepare_printer_setup(self, password: str) -> PreparedPrinterSetup:
        with self._setup_lock:
            with self._lock:
                if self._job.state in {"checking", "running"}:
                    raise GUIError("Attendere la fine della calibrazione in corso")
            try:
                moonraker = MoonrakerClient(self.moonraker_url, timeout=self.timeout)
                require_safe_printer(moonraker)
                target = self._printer_target(password)
                loaded = moonraker.has_gcode_macro("APA_COIL_RUN_ULTRA")
                plan = plan_printer_setup(target, loaded_by_klipper=loaded)
            except PrinterInstallError as exc:
                raise GUIError(str(exc)) from exc
            prepared = PreparedPrinterSetup(
                ticket=secrets.token_urlsafe(32),
                plan=plan,
            )
            with self._lock:
                self._pending_setup = prepared
            return prepared

    def apply_printer_setup(
        self, ticket: str, password: str
    ) -> PrinterSetupReceipt:
        with self._setup_lock:
            with self._lock:
                prepared = self._pending_setup
                if prepared is None or not secrets.compare_digest(prepared.ticket, ticket):
                    raise GUIError("Conferma installazione scaduta o già usata")
                self._pending_setup = None
                if self._job.state in {"checking", "running"}:
                    raise GUIError("Attendere la fine della calibrazione in corso")
            try:
                moonraker = MoonrakerClient(self.moonraker_url, timeout=self.timeout)
                require_safe_printer(moonraker)
                target = self._printer_target(password)
                loaded = moonraker.has_gcode_macro("APA_COIL_RUN_ULTRA")
                current_plan = plan_printer_setup(target, loaded_by_klipper=loaded)
                if current_plan.to_dict() != prepared.plan.to_dict():
                    raise GUIError(
                        "I file o lo stato U1 sono cambiati dopo l'anteprima: operazione annullata"
                    )
                require_safe_printer(moonraker)
                result = install_printer_setup(
                    target,
                    loaded_by_klipper=loaded,
                    power_cycle_required=True,
                )
            except PrinterInstallError as exc:
                raise GUIError(str(exc)) from exc
            receipt = PrinterSetupReceipt(result=result)
            with self._lock:
                self._last_setup = receipt
            return receipt

    def last_setup(self) -> PrinterSetupReceipt | None:
        with self._lock:
            return self._last_setup

    def _spoolman_client(self) -> SpoolmanClient:
        if self._spoolman_client_factory is not None:
            return self._spoolman_client_factory()
        return SpoolmanClient(self.spoolman_url, timeout=self.timeout)

    def _accept_inventory(self, inventory: SpoolmanInventory) -> tuple[ProfileCandidate, ...]:
        sync_profiles(
            inventory,
            self.sandbox_dir,
            system_dir=self.system_dir,
            apply=True,
        )
        candidates = profile_candidates(inventory)
        with self._lock:
            self._inventory = inventory
            self._profiles = candidates
        return candidates

    def refresh_profiles(self) -> tuple[ProfileCandidate, ...]:
        inventory = self._spoolman_client().inventory()
        return self._accept_inventory(inventory)

    def prepare_spool_creation(
        self,
        request: NewSpoolRequest,
    ) -> PreparedSpoolCreation:
        with self._lock:
            if self._job.state in {"checking", "running"}:
                raise GUIError("Attendere la fine della calibrazione in corso")
        inventory = self._spoolman_client().inventory()
        try:
            plan = plan_spool_creation(inventory, request)
        except ValueError as exc:
            raise GUIError(str(exc)) from exc
        base_path = self.system_dir / f"{plan.base_profile}.json"
        if not base_path.is_file():
            raise GUIError(
                f"Profilo base Snapmaker non trovato: {plan.base_profile}. "
                "Nessun dato verrà scritto in Spoolman."
            )
        prepared = PreparedSpoolCreation(
            ticket=secrets.token_urlsafe(32),
            plan=plan,
        )
        with self._lock:
            self._pending_creation = prepared
        return prepared

    def create_prepared_spool(self, ticket: str) -> SpoolCreationReceipt:
        with self._creation_lock:
            with self._lock:
                prepared = self._pending_creation
                if prepared is None or not secrets.compare_digest(prepared.ticket, ticket):
                    raise GUIError(
                        "Conferma scaduta o già usata: nessuna bobina creata"
                    )
                self._pending_creation = None
                if self._job.state in {"checking", "running"}:
                    raise GUIError("Attendere la fine della calibrazione in corso")

            client = self._spoolman_client()
            inventory = client.inventory()
            try:
                current_plan = plan_spool_creation(inventory, prepared.plan.request)
            except ValueError as exc:
                raise GUIError(str(exc)) from exc
            base_path = self.system_dir / f"{current_plan.base_profile}.json"
            if not base_path.is_file():
                raise GUIError(
                    f"Profilo base Snapmaker non trovato: {current_plan.base_profile}. "
                    "Nessun dato scritto in Spoolman."
                )
            try:
                result = create_spool_from_plan(client, current_plan)
            except ServiceError as exc:
                raise GUIError(str(exc)) from exc
            try:
                updated_inventory = client.inventory()
                self._accept_inventory(updated_inventory)
                sandbox_profile_path = find_profile_path(
                    self.sandbox_dir,
                    result.plan.profile_name,
                )
                real_profile_path = None
                if self.real_orca_dir is not None:
                    sync_profiles(
                        updated_inventory,
                        self.real_orca_dir,
                        system_dir=self.system_dir,
                        apply=True,
                        only_profile_names={result.plan.profile_name},
                    )
                    real_profile_path = find_profile_path(
                        self.real_orca_dir,
                        result.plan.profile_name,
                    )
            except (ServiceError, PAProfileError, OSError, ValueError) as exc:
                raise GUIError(
                    f"La bobina Spoolman ID {result.spool_id} è già stata creata, "
                    f"ma la creazione del profilo Orca non è stata completata: {exc}. "
                    "Non creare di nuovo la bobina; aggiornare la pagina iniziale e riprovare la sincronizzazione."
                ) from exc
            receipt = SpoolCreationReceipt(
                result=result,
                sandbox_profile_path=sandbox_profile_path,
                real_profile_path=real_profile_path,
            )
            with self._lock:
                self._last_creation = receipt
            return receipt

    def last_creation(self) -> SpoolCreationReceipt | None:
        with self._lock:
            return self._last_creation

    def profiles(self) -> tuple[ProfileCandidate, ...]:
        with self._lock:
            return self._profiles

    def selection(
        self,
        profile_name: str,
        physical_slot: int,
        temperature: int,
    ) -> CalibrationSelection:
        normalized = profile_name.strip().casefold()
        with self._lock:
            matches = [
                item for item in self._profiles
                if item.profile_name.casefold() == normalized
            ]
        if len(matches) != 1:
            raise GUIError("Profilo non presente nell'inventario Spoolman corrente")
        find_profile_path(self.sandbox_dir, matches[0].profile_name)
        return CalibrationSelection(
            profile_name=matches[0].profile_name,
            physical_slot=physical_slot,
            internal_extruder=physical_to_internal(physical_slot),
            temperature=validate_temperature(temperature),
        )

    def snapshot(self) -> JobSnapshot:
        with self._lock:
            return self._job

    def _set_job(self, snapshot: JobSnapshot) -> None:
        with self._lock:
            self._job = snapshot

    def start(self, selection: CalibrationSelection) -> None:
        with self._lock:
            if self._job.state in {"checking", "running"}:
                raise GUIError("Una calibrazione è già in corso")
            self._job = JobSnapshot(
                "checking",
                "Controllo stato stampante e macro…",
                selection,
            )

        client = MoonrakerClient(
            self.moonraker_url,
            timeout=self.timeout,
        )
        try:
            status = require_safe_printer(client)
            if not client.has_gcode_macro("APA_COIL_SET_ENVELOPE"):
                raise GUIError("Macro APA_COIL_SET_ENVELOPE non caricata")
            if not client.has_gcode_macro("APA_COIL_RUN_ULTRA"):
                raise GUIError("Macro APA_COIL_RUN_ULTRA non caricata")
            baseline = parse_gcode_store(client.gcode_store(1000))
        except (PrinterInstallError, PACaptureError, GUIError) as exc:
            self._set_job(JobSnapshot("blocked", str(exc), selection))
            raise GUIError(str(exc)) from exc

        message = (
            "Calibrazione avviata: "
            f"slot fisico {selection.physical_slot} → "
            f"EXTRUDER={selection.internal_extruder}, "
            f"{selection.temperature} °C. "
            f"Stato iniziale: {status.print_state}/{status.idle_state}."
        )
        self._set_job(JobSnapshot("running", message, selection))
        worker = threading.Thread(
            target=self._run_job,
            args=(selection, baseline),
            name="u1fa-calibration",
            daemon=True,
        )
        worker.start()

    def _run_job(self, selection: CalibrationSelection, baseline) -> None:
        client = MoonrakerClient(
            self.moonraker_url,
            timeout=max(3 * 60 * 60 + 60.0, self.timeout),
        )
        started_at = time.time()
        previous = baseline
        captured = []
        try:
            envelope_command, run_command = selection.commands
            client.run_gcode(envelope_command)
            client.run_gcode(run_command)
            deadline = time.time() + 3 * 60 * 60
            while time.time() < deadline:
                current = parse_gcode_store(client.gcode_store(1000))
                try:
                    captured.extend(new_gcode_entries(previous, current))
                    previous = current
                    text = response_text(captured)
                    suite, _, suite_end = last_complete_suite_span(text)
                except PAParseError:
                    time.sleep(self.poll_interval)
                    continue
                except PACaptureError:
                    cached = latest_cached_suite(current)
                    if cached.completed_at < started_at - 5:
                        raise
                    suite = cached.suite
                    text = cached.text
                    suite_end = cached.suite_end

                sandbox_report = update_pa_profile(
                    self.sandbox_dir,
                    selection.profile_name,
                    CalibrationIdentity(),
                    suite,
                    apply=True,
                    manual_profile=True,
                )
                report = sandbox_report
                if self.real_orca_dir is not None:
                    report = update_pa_profile(
                        self.real_orca_dir,
                        selection.profile_name,
                        CalibrationIdentity(),
                        suite,
                        apply=True,
                        manual_profile=True,
                    )
                self._set_job(
                    JobSnapshot(
                        "completed",
                        "Calibrazione completata; profilo Snapmaker Orca aggiornato con backup.",
                        selection,
                        report.to_dict(),
                    )
                )
                return
            raise GUIError("Tempo massimo superato senza una suite ULTRA completa")
        except (GUIError, PrinterInstallError, PACaptureError, PAProfileError) as exc:
            self._set_job(
                JobSnapshot(
                    "error",
                    f"{exc}. Controllare Fluidd: non viene inviato alcun riavvio automatico.",
                    selection,
                )
            )


def _page(
    title: str,
    body: str,
    refresh: int | None = None,
    language: str = "it",
) -> str:
    refresh_tag = (
        "" if refresh is None
        else f'<meta http-equiv="refresh" content="{refresh}">'
    )
    return f"""<!doctype html>
<html lang="{language}"><head><meta charset="utf-8">{refresh_tag}
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/png" href="/assets/u1fa-logo.png">
<title>{html.escape(title)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#101318;color:#eef2f7;margin:0}}
main{{max-width:850px;margin:32px auto;padding:0 18px}}
.card{{background:#1a2029;border:1px solid #303a48;border-radius:16px;padding:22px;margin:16px 0}}
.brand{{display:flex;align-items:center;gap:16px;margin:0 0 22px}}
.brand-copy{{flex:1}}
.language{{display:flex;gap:6px;align-self:flex-start}} .language a{{padding:8px 10px;border-radius:8px;background:#273242;color:#eef2f7;text-decoration:none;font-weight:700}} .language a.active{{background:#35a7ff;color:#07111a}}
.brand img{{width:104px;height:104px;object-fit:contain;background:#fff;border-radius:50%;padding:4px;box-sizing:border-box}}
.brand strong{{display:block;font-size:21px}} .brand span{{color:#aeb9c8}}
h1{{font-size:28px}} label{{display:block;margin:14px 0 6px}}
select,input,textarea{{width:100%;box-sizing:border-box;padding:11px;border-radius:9px;border:1px solid #4a5667;background:#0f141b;color:#fff}}
input[type="color"]{{height:48px;padding:4px;cursor:pointer}}
input[type="color"]::-webkit-color-swatch-wrapper{{padding:0}}
input[type="color"]::-webkit-color-swatch{{border:0;border-radius:6px}}
.color-control{{display:grid;grid-template-columns:76px 1fr 48px;gap:10px;align-items:center}}
.color-sample{{display:block;width:48px;height:48px;border:2px solid #eef2f7;border-radius:9px;box-sizing:border-box}}
button,.button{{display:inline-block;background:#35a7ff;color:#07111a;border:0;border-radius:10px;padding:12px 18px;font-weight:700;text-decoration:none;cursor:pointer}}
.danger{{background:#ffb020}} .secondary{{background:#39485b;color:#eef2f7}} .ok{{color:#6ee7a8}} .warn{{color:#ffd166}} .muted{{color:#aeb9c8}}
pre{{white-space:pre-wrap;background:#0c1117;padding:14px;border-radius:10px;border:1px solid #303a48}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}} @media(max-width:620px){{.grid{{grid-template-columns:1fr}}.brand img{{width:82px;height:82px}}}}
</style></head><body><main><div class="brand"><img src="/assets/u1fa-logo.png" alt="Logo U1FA"><div class="brand-copy"><strong>U1 Filament Automation</strong><span>by Bottega3DLab · v{html.escape(__version__)}</span></div><div class="language"><a class="{'active' if language == 'it' else ''}" href="/language?lang=it">IT</a><a class="{'active' if language == 'en' else ''}" href="/language?lang=en">EN</a></div></div>{body}</main></body></html>"""


def _update_card(
    controller: CalibrationController,
    token: str,
    language: str,
) -> str:
    snapshot = controller.update_snapshot()
    message = snapshot.message_en if language == "en" else snapshot.message_it
    if snapshot.state == "available" and snapshot.info is not None:
        content = f"""<p class="warn"><strong>{html.escape(message)}</strong></p>
<p><a class="button danger" href="/updates">{_tr(language, 'Mostra aggiornamento', 'View update')}</a></p>"""
    elif snapshot.state == "downloaded":
        content = f"""<p class="ok"><strong>{html.escape(message)}</strong></p>
<p><a class="button" href="/updates">{_tr(language, 'Installa aggiornamento', 'Install update')}</a></p>"""
    elif snapshot.state == "checking":
        content = f'<p class="muted">{html.escape(message)}</p>'
    else:
        style = "ok" if snapshot.state == "current" else "muted"
        content = f"""<p class="{style}">{html.escape(message)}</p>
<form method="post" action="/updates/check"><input type="hidden" name="token" value="{token}">
<button class="secondary" type="submit">{_tr(language, 'Controlla ora', 'Check now')}</button></form>"""
    return f"""<div class="card"><h2>{_tr(language, 'Aggiornamenti U1FA', 'U1FA updates')}</h2>
{content}<p class="muted">{_tr(language, "Il controllo riguarda soltanto l’app sul computer: non aggiorna il firmware e non invia comandi alla U1.", "This check only concerns the computer app: it does not update firmware or send commands to the U1.")}</p></div>"""


def _updates_page(
    controller: CalibrationController,
    token: str,
    error: str = "",
    language: str = "it",
) -> str:
    snapshot = controller.update_snapshot()
    message = snapshot.message_en if language == "en" else snapshot.message_it
    error_box = "" if not error else f'<p class="warn">{html.escape(error)}</p>'
    content = f"<p>{html.escape(message)}</p>"
    if snapshot.info is not None:
        info = snapshot.info
        notes = html.escape(info.notes or _tr(
            language,
            "Nessuna nota di versione pubblicata.",
            "No release notes were published.",
        )).replace("\n", "<br>")
        size_mb = info.asset.size / (1024 * 1024)
        details = f"""<h2>{html.escape(info.title or info.tag)}</h2>
<p><strong>{_tr(language, 'Versione', 'Version')}:</strong> {html.escape(info.version)}<br>
<strong>{_tr(language, 'Pacchetto', 'Package')}:</strong> {html.escape(info.asset.name)} ({size_mb:.1f} MB)<br>
<strong>SHA-256:</strong> <code>{html.escape(info.asset.sha256)}</code></p>
<div class="card"><strong>{_tr(language, 'Novità', 'What is new')}</strong><p class="muted">{notes}</p></div>"""
        if snapshot.state == "available":
            action = f"""<form method="post" action="/updates/download">
<input type="hidden" name="token" value="{token}">
<label><input style="width:auto" type="checkbox" name="confirm" value="yes" required> {_tr(language, 'Confermo di voler scaricare il pacchetto per questo computer', 'I confirm that I want to download the package for this computer')}</label>
<p><button class="danger" type="submit">{_tr(language, 'Scarica e verifica aggiornamento', 'Download and verify update')}</button></p></form>"""
        elif snapshot.state == "downloaded" and snapshot.local_path is not None:
            action = f"""<p class="ok"><strong>{_tr(language, 'Download completato e SHA-256 verificato.', 'Download complete and SHA-256 verified.')}</strong><br><code>{html.escape(str(snapshot.local_path))}</code></p>
<form method="post" action="/updates/open"><input type="hidden" name="token" value="{token}">
<label><input style="width:auto" type="checkbox" name="confirm" value="yes" required> {_tr(language, 'Confermo di voler aprire il pacchetto di installazione', 'I confirm that I want to open the installation package')}</label>
<p><button class="danger" type="submit">{_tr(language, 'Apri installer verificato', 'Open verified installer')}</button></p></form>"""
        else:
            action = ""
        content += details + action
    content += f"""<p><a class="button secondary" href="/">{_tr(language, 'Torna alla schermata iniziale', 'Return to home')}</a></p>
<p class="muted">{_tr(language, "U1FA non si sostituisce mentre è in esecuzione. Su macOS si apre il DMG, su Windows l’installer e su Linux la cartella dell’AppImage; l’installazione resta sempre una scelta dell’utente.", "U1FA never replaces itself while it is running. On macOS it opens the DMG, on Windows the installer, and on Linux the AppImage folder; installation always remains the user's choice.")}</p>"""
    return _page(
        _tr(language, "Aggiornamenti U1FA", "U1FA updates"),
        f"<h1>{_tr(language, 'Aggiornamenti U1FA', 'U1FA updates')}</h1><div class=\"card\">{error_box}{content}</div>",
        refresh=2 if snapshot.state in {"checking", "downloading"} else None,
        language=language,
    )


def _home(
    controller: CalibrationController,
    token: str,
    error: str = "",
    language: str = "it",
) -> str:
    profiles = controller.profiles()
    beta_box = ""
    if "b" in __version__.casefold():
        beta_box = f"""<div class="card"><p class="warn"><strong>{_tr(language, 'Versione beta privata per collaudo.', 'Private beta for testing.')}</strong> {_tr(language, 'Usa prima i controlli in sola lettura. Non applicare modifiche alla stampante mentre è in stampa e interrompi il test se compare un file non riconosciuto.', 'Run the read-only checks first. Never modify the printer while it is printing, and stop testing if an unknown file is reported.')}</p></div>"""
    spool_word = _tr(language, "bobine", "spools")
    options = "".join(
        f'<option value="{html.escape(item.profile_name, quote=True)}">'
        f'{html.escape(item.profile_name)} — {spool_word} {html.escape(str(list(item.spool_ids)))}'
        "</option>"
        for item in profiles
    )
    error_box = "" if not error else f'<p class="warn">{html.escape(error)}</p>'
    monitor = controller.monitor_snapshot()
    monitor_message = monitor.message_en if language == "en" else monitor.message_it
    monitor_class = "warn" if monitor.state == "error" else "ok"
    monitor_time = (
        "" if not monitor.checked_at
        else f" · {_tr(language, 'ultimo controllo', 'last check')} {html.escape(monitor.checked_at)}"
    )
    connections = controller.connection_config()
    if connections is None:
        connection_box = f"""<div class="card"><h2>{_tr(language, 'Connessioni da configurare', 'Connections need setup')}</h2>
<p class="warn">{_tr(language, "Questa installazione non conosce ancora l'indirizzo della U1. Inseriscilo una sola volta e verrà verificato senza inviare comandi alla stampante.", "This installation does not know the U1 address yet. Enter it once; it will be verified without sending printer commands.")}</p>
<p><a class="button danger" href="/connections">{_tr(language, 'Configura U1 e Spoolman', 'Configure U1 and Spoolman')}</a></p></div>"""
    else:
        connection_box = f"""<div class="card"><h2>{_tr(language, 'Connessioni', 'Connections')}</h2>
<p><strong>U1 / Moonraker:</strong> <code>{html.escape(connections.moonraker_url)}</code><br>
<strong>Spoolman:</strong> <code>{html.escape(connections.spoolman_url)}</code></p>
<p><a class="button secondary" href="/connections">{_tr(language, 'Modifica indirizzi', 'Change addresses')}</a></p></div>"""
    calibration_form = f"""
<form method="post" action="/preview">
<input type="hidden" name="token" value="{token}">
<label>{_tr(language, 'Bobina / profilo Spoolman', 'Spoolman spool / profile')}</label><select name="profile_name" required>{options}</select>
<div class="grid"><div><label>{_tr(language, 'Estrusore fisico', 'Physical extruder')}</label><select name="physical_slot">
<option value="1">1 → {_tr(language, 'interno', 'internal')} 0</option><option value="2">2 → {_tr(language, 'interno', 'internal')} 1</option>
<option value="3">3 → {_tr(language, 'interno', 'internal')} 2</option><option value="4">4 → {_tr(language, 'interno', 'internal')} 3</option>
</select></div><div><label>{_tr(language, 'Temperatura', 'Temperature')} °C</label><input name="temperature" type="number" min="170" max="300" value="220" required></div></div>
<label>Envelope</label><input value="{_tr(language, 'U1 convalidato', 'Validated U1')}: 100 / 218 / 336 mm/s — 2000 / 6000 / 10000 mm/s²" disabled>
<p><button type="submit">{_tr(language, 'Controlla e mostra i comandi', 'Check and show commands')}</button></p>
</form>""" if profiles else f"""<p class="muted">{_tr(language, 'Non ci sono ancora bobine utilizzabili. Creane una con il pulsante qui sopra.', 'There are no usable spools yet. Create one with the button above.')}</p>"""
    body = f"""
<h1>U1 Filament Automation</h1>
<p class="muted">{_tr(language, 'Bobina Spoolman → profilo Snapmaker Orca → calibrazione Adaptive PA.', 'Spoolman spool → Snapmaker Orca profile → Adaptive PA calibration.')}</p>
{beta_box}
{_update_card(controller, token, language)}
{connection_box}
<div class="card"><h2>{_tr(language, '0. Configurazione o ripristino U1FA AutoPA Mod', '0. Set up or restore U1FA AutoPA Mod')}</h2>
<p>{_tr(language, "Controlla e, solo dopo due conferme, installa U1FA AutoPA Mod, la modifica Bottega3DLab per la calibrazione automatica dell’Adaptive Pressure Advance sulla Snapmaker U1. Dopo ogni aggiornamento firmware usa di nuovo questo controllo: ripristina calibratore, macro e include soltanto se l’originale Snapmaker è compatibile, crea backup verificati e blocca file sconosciuti.", "Checks and, only after two confirmations, installs U1FA AutoPA Mod, the Bottega3DLab modification for automatic Adaptive Pressure Advance calibration on the Snapmaker U1. Run this check again after every firmware update: it restores the calibrator, macro and include only when the Snapmaker original is compatible, creates verified backups and blocks unknown files.")}</p>
<p><a class="button secondary" href="/printer-setup">{_tr(language, 'Controlla configurazione stampante', 'Check printer setup')}</a></p></div>
<div class="card">{error_box}<h2>{_tr(language, '1. Nuova bobina', '1. New spool')}</h2>
<p>{_tr(language, "Inserisci i dati una volta sola: l'app crea o riusa vendor e filamento in Spoolman, crea la bobina e genera il nuovo profilo direttamente in Snapmaker Orca, mantenendo anche una copia nella sandbox.", "Enter the data once: the app creates or reuses the vendor and filament in Spoolman, creates the spool and generates the new profile directly in Snapmaker Orca, while keeping a sandbox copy.")}</p>
<p><a class="button danger" href="/new-spool">{_tr(language, 'Aggiungi nuova bobina', 'Add new spool')}</a></p></div>
<div class="card"><h2>{_tr(language, '2. Calibra una bobina già presente', '2. Calibrate an existing spool')}</h2><p class="muted">{_tr(language, 'Durata indicativa della calibrazione Adaptive PA: circa 10 minuti.', 'Estimated Adaptive PA calibration time: approximately 10 minutes.')}</p>{calibration_form}</div>
<div class="card"><p><strong>{_tr(language, 'Sincronizzazione automatica attiva', 'Automatic synchronization active')}</strong></p><p class="{monitor_class}">{html.escape(monitor_message)}{monitor_time}</p><p class="muted">{_tr(language, 'Anche le bobine aggiunte manualmente dal sito Spoolman vengono rilevate mentre l’app è aperta. I profili mancanti vengono creati in Orca senza sovrascrivere quelli esistenti; una cancellazione manuale viene rispettata.', 'Spools added manually from the Spoolman website are also detected while the app is open. Missing Orca profiles are created without overwriting existing ones; manual deletion is respected.')}</p></div>
<div class="card"><p><strong>{_tr(language, 'Protezione attiva', 'Active protection')}</strong></p><p class="muted">{_tr(language, "Il pulsante di avvio appare solo dopo l'anteprima. Prima dell'invio vengono verificati stampante inattiva, macro caricate, profilo esatto e mapping dello slot.", 'The start button appears only after the preview. Before sending commands, the app verifies that the printer is idle, the macros are loaded, the exact profile exists and the slot mapping is correct.')}</p></div>"""
    body += f"""<div class="card"><p><strong>{_tr(language, 'Applicazione', 'Application')}</strong></p>
<p class="muted">{_tr(language, "Chiude in sicurezza U1FA e il monitor Spoolman. L'operazione viene bloccata durante una calibrazione attiva.", 'Safely closes U1FA and the Spoolman monitor. Closing is blocked while a calibration is active.')}</p>
<p><a class="button secondary" href="/shutdown">{_tr(language, 'Chiudi applicazione', 'Close application')}</a></p></div>"""
    return _page("U1 Filament Automation", body, language=language)


def _connections_form(
    controller: CalibrationController,
    token: str,
    error: str = "",
    language: str = "it",
) -> str:
    current = controller.connection_config()
    moonraker_url = "" if current is None else current.moonraker_url
    spoolman_url = "" if current is None else current.spoolman_url
    error_box = "" if not error else f'<p class="warn">{html.escape(error)}</p>'
    body = f"""
<h1>{_tr(language, 'Connessioni U1 e Spoolman', 'U1 and Spoolman connections')}</h1>
<div class="card">{error_box}
<p>{_tr(language, "Inserisci l'indirizzo mostrato dalla tua U1. Puoi scrivere soltanto l'IP, per esempio 192.168.1.100: l'app aggiungerà automaticamente http:// e ricaverà l'accesso SSH root@IP.", "Enter the address shown by your U1. You may enter only the IP, for example 192.168.1.100: the app will add http:// automatically and derive root@IP for SSH.")}</p>
<form method="post" action="/connections/save">
<input type="hidden" name="token" value="{token}">
<label>{_tr(language, 'IP o hostname della Snapmaker U1', 'Snapmaker U1 IP or hostname')}</label>
<input name="moonraker_address" value="{html.escape(moonraker_url, quote=True)}" placeholder="192.168.1.100" required>
<label>{_tr(language, 'Indirizzo Spoolman', 'Spoolman address')}</label>
<input name="spoolman_address" value="{html.escape(spoolman_url, quote=True)}" placeholder="{_tr(language, 'Automatico (consigliato)', 'Automatic (recommended)')}">
<p class="muted">{_tr(language, "Lascia vuoto per il rilevamento automatico: l'app prova Spoolman su questo computer (127.0.0.1), l'indirizzo dichiarato da Moonraker/PAXX e infine la U1. Inserisci un indirizzo soltanto per forzarlo manualmente.", "Leave blank for automatic detection: the app tries Spoolman on this computer (127.0.0.1), the address reported by Moonraker/PAXX and finally the U1. Enter an address only to force it manually.")}</p>
<p class="warn">{_tr(language, 'Il controllo usa soltanto richieste di lettura. Non avvia stampe, calibrazioni o riavvii.', 'The check uses read-only requests. It does not start prints, calibrations or restarts.')}</p>
<p><button type="submit">{_tr(language, 'Verifica e salva', 'Verify and save')}</button> <a class="button secondary" href="/">{_tr(language, 'Annulla', 'Cancel')}</a></p>
</form></div>"""
    return _page(_tr(language, "Connessioni", "Connections"), body, language=language)


def _printer_setup_form(
    token: str,
    error: str = "",
    language: str = "it",
) -> str:
    error_box = "" if not error else f'<p class="warn">{html.escape(error)}</p>'
    body = f"""
<h1>{_tr(language, 'Configurazione U1 originale', 'Stock Snapmaker U1 setup')}</h1>
<div class="card"><p class="warn"><strong>{_tr(language, 'Aggiornamenti firmware:', 'Firmware updates:')}</strong> {_tr(language, 'un aggiornamento può rimuovere U1FA AutoPA Mod. Esegui prima questo controllo in sola lettura. Il firmware U1 1.6.0 è in attesa di convalida: se compare un hash sconosciuto non applicare nulla.', 'an update may remove U1FA AutoPA Mod. Run this read-only check first. U1 firmware 1.6.0 is pending validation: if an unknown hash appears, do not apply anything.')}</p></div>
<div class="card"><h2>{_tr(language, 'Prima di continuare: abilita due funzioni dal display U1', 'Before continuing: enable two features on the U1 touchscreen')}</h2>
<ol><li><strong>Fluidd:</strong> {_tr(language, 'Impostazioni → Manutenzione → Modalità avanzata → Accetto → Abilita', 'Settings → Maintenance → Advanced Mode → Agree → Enable')}.</li>
<li><strong>SSH:</strong> {_tr(language, 'Impostazioni → Manutenzione → Accesso Root → Accetto → Apri', 'Settings → Maintenance → Root Access → Agree → Open')}.</li></ol>
<p class="warn">{_tr(language, "Senza Modalità avanzata non puoi accedere a Fluidd. Senza Accesso Root/SSH l'app non può creare il backup né sostituire il file originale", "Without Advanced Mode you cannot access Fluidd. Without Root Access/SSH the app cannot back up or replace the original file")}:<br><code>/home/lava/klipper/klippy/extras/flow_calibrator.py</code></p></div>
<div class="card">{error_box}
<p>{_tr(language, 'Il primo controllo è in sola lettura. La stampante deve essere completamente inattiva.', 'The first check is read-only. The printer must be completely idle.')}</p>
<p class="muted">{_tr(language, 'La password resta in memoria soltanto durante questa richiesta locale e non viene salvata. Lascia il campo vuoto se hai già configurato una chiave SSH.', 'The password stays in memory only for this local request and is never saved. Leave it blank if you already configured an SSH key.')}</p>
<form method="post" action="/printer-setup/preview">
<input type="hidden" name="token" value="{token}">
<label><input style="width:auto" type="checkbox" name="printer_access_enabled" value="yes" required> {_tr(language, 'Confermo di aver abilitato Modalità avanzata e Accesso Root/SSH dal display', 'I confirm that I enabled Advanced Mode and Root Access/SSH on the touchscreen')}</label>
<label>{_tr(language, 'Password SSH U1 (facoltativa con chiave)', 'U1 SSH password (optional with a key)')}</label>
<input name="ssh_password" type="password" maxlength="256" autocomplete="current-password">
<p class="muted">{_tr(language, 'Se non hai modificato la password SSH, usa quella predefinita: ', 'If you have not changed the SSH password, use the default: ')}<code>snapmaker</code>.</p>
<p><button type="submit">{_tr(language, 'Controlla in sola lettura', 'Run read-only check')}</button> <a class="button secondary" href="/">{_tr(language, 'Annulla', 'Cancel')}</a></p>
</form></div>"""
    return _page(_tr(language, "Configurazione U1", "U1 setup"), body, language=language)


def _printer_setup_preview(
    prepared: PreparedPrinterSetup,
    token: str,
    language: str = "it",
) -> str:
    plan = prepared.plan
    has_writes = bool(
        plan.install_calibrator or plan.create_macro or plan.update_printer_cfg
    )
    actions = []
    if plan.install_calibrator:
        actions.append(_tr(
            language,
            "Installare o ripristinare U1FA AutoPA Mod sostituendo il flow_calibrator.py originale compatibile dopo averne creato il backup",
            "Install or restore U1FA AutoPA Mod by replacing the compatible original flow_calibrator.py after creating its backup",
        ))
    if plan.create_macro:
        actions.append(_tr(language, "Creare adaptive_pa_macro.cfg con lo SHA-256 validato", "Create adaptive_pa_macro.cfg with the validated SHA-256"))
    if plan.update_printer_cfg:
        actions.append(_tr(language, "Aggiungere l'include a printer.cfg dopo averne creato il backup", "Add the include to printer.cfg after creating its backup"))
    if not actions:
        actions.append(_tr(language, "Nessuna scrittura: U1FA AutoPA Mod risulta già installata e completa", "No write: U1FA AutoPA Mod is already installed and complete"))
    action_list = "".join(f"<li>{html.escape(item)}</li>" for item in actions)
    if has_writes:
        action_block = f"""
<p class="warn">{_tr(language, "Prima della scrittura lo stato macchina e gli SHA-256 vengono verificati di nuovo. L'app non invia RESTART né FIRMWARE_RESTART. Se vengono scritti file, al termine sarà richiesto spegnere completamente la U1 per 10–15 secondi.", "Before writing, the machine state and SHA-256 values are checked again. The app does not send RESTART or FIRMWARE_RESTART. If files are written, you will be asked to fully power off the U1 for 10–15 seconds afterward.")}</p>
<form method="post" action="/printer-setup/apply">
<input type="hidden" name="token" value="{token}"><input type="hidden" name="ticket" value="{prepared.ticket}">
<label>{_tr(language, 'Password SSH U1 (reinserirla; non viene memorizzata)', 'U1 SSH password (enter it again; it is not stored)')}</label>
<input name="ssh_password" type="password" maxlength="256" autocomplete="current-password">
<label><input style="width:auto" type="checkbox" name="confirm" value="yes" required> {_tr(language, 'Confermo di aver letto le operazioni e che la U1 è inattiva', 'I confirm that I read the operations and that the U1 is idle')}</label>
<p><button class="danger" type="submit">{_tr(language, 'Applica davvero la configurazione', 'Apply the setup')}</button> <a class="button secondary" href="/printer-setup">{_tr(language, 'Annulla', 'Cancel')}</a></p>
</form>"""
    else:
        action_block = f"""
<p class="ok"><strong>{_tr(language, 'Controllo completato: U1FA AutoPA Mod è pronta. Nessun file è stato modificato.', 'Check completed: U1FA AutoPA Mod is ready. No file was changed.')}</strong></p>
<p><a class="button" href="/">{_tr(language, 'Torna alla schermata iniziale', 'Return to home')}</a> <a class="button secondary" href="/printer-setup">{_tr(language, 'Ripeti controllo', 'Run check again')}</a></p>"""
    calibrator_label = _tr(
        language,
        "File del calibratore controllato" if not has_writes else "File originale da controllare e sostituire",
        "Checked calibrator file" if not has_writes else "Original file to check and replace",
    )
    body = f"""
<h1>{_tr(language, 'Conferma configurazione U1', 'Confirm U1 setup')}</h1><div class="card">
<p><strong>{calibrator_label}:</strong><br><code>{html.escape(plan.calibrator.path)}</code></p>
<p><strong>{_tr(language, 'Calibratore', 'Calibrator')}:</strong> {html.escape(plan.calibrator.state)}<br>
<span class="muted">SHA-256 {html.escape(plan.calibrator.sha256)}</span></p>
<p><strong>Macro Adaptive PA:</strong> {html.escape(plan.macro.state)}<br>
<span class="muted">SHA-256 {html.escape(plan.macro.sha256 or _tr(language, 'assente', 'missing'))}</span></p>
<p><strong>{_tr(language, 'Operazioni previste', 'Planned operations')}:</strong></p><ul>{action_list}</ul>
{action_block}</div>"""
    return _page(_tr(language, "Conferma configurazione U1", "Confirm U1 setup"), body, language=language)


def _printer_setup_result(
    receipt: PrinterSetupReceipt,
    language: str = "it",
) -> str:
    result = receipt.result
    if result.writes:
        items = "".join(
            "<li><strong>" + html.escape(item.action) + ":</strong> "
            + html.escape(item.path)
            + ("<br><span class=\"muted\">Backup: " + html.escape(item.backup_path) + "</span>" if item.backup_path else "")
            + "</li>"
            for item in result.writes
        )
        summary = f"<ul>{items}</ul>"
    else:
        summary = f'<p class="ok">{_tr(language, "Nessun file modificato: configurazione già presente.", "No file changed: the setup was already present.")}</p>'
    power = (
        f'<p class="warn"><strong>{_tr(language, "Ora spegni completamente la U1, attendi 10–15 secondi e riaccendila.", "Now fully power off the U1, wait 10–15 seconds, then turn it back on.")}</strong> {_tr(language, "Non usare un semplice RESTART.", "Do not use a simple RESTART.")}</p>'
        if result.power_cycle_required else ""
    )
    body = f"""
<h1>{_tr(language, 'Configurazione U1 completata', 'U1 setup completed')}</h1><div class="card">
<p class="ok"><strong>{_tr(language, 'Calibratore e macro verificati.', 'Calibrator and macro verified.')}</strong></p>{summary}{power}
<p><a class="button" href="/">{_tr(language, 'Torna alla schermata iniziale', 'Return to home')}</a></p>
</div>"""
    return _page(_tr(language, "Configurazione completata", "Setup completed"), body, language=language)


def _new_spool_form(
    token: str,
    error: str = "",
    language: str = "it",
) -> str:
    error_box = "" if not error else f'<p class="warn">{html.escape(error)}</p>'
    body = f"""
<h1>{_tr(language, 'Nuova bobina Spoolman', 'New Spoolman spool')}</h1><div class="card">{error_box}
<p class="muted">{_tr(language, 'Per PLA+ o PLA veloce inserisci RAPID, HYPER, HS o HF nel nome: verrà usato il profilo SnapSpeed. Per PLA normale scrivi soltanto PLA: verrà usato PLA Basic.', 'For PLA+ or high-speed PLA include RAPID, HYPER, HS or HF in the name: the SnapSpeed profile will be used. For standard PLA use only PLA: PLA Basic will be used.')}</p>
<form method="post" action="/new-spool/preview">
<input type="hidden" name="token" value="{token}">
<div class="grid"><div><label>{_tr(language, 'Marca / vendor', 'Brand / vendor')}</label><input name="vendor" maxlength="64" placeholder="{_tr(language, 'es. Deeplee', 'e.g. Deeplee')}" required></div>
<div><label>{_tr(language, 'Materiale', 'Material')}</label><select name="material" id="material"><option value="PLA">PLA</option><option value="PETG">PETG</option></select></div></div>
<label>{_tr(language, 'Nome tecnico del filamento', 'Technical filament name')}</label><input name="name" maxlength="64" placeholder="{_tr(language, 'es. PLA PRO RAPID BLUE', 'e.g. PLA PRO RAPID BLUE')}" required>
<div class="grid"><div><label>{_tr(language, 'Colore', 'Color')}</label><div class="color-control"><input id="color-picker" type="color" value="#2563eb" aria-label="{_tr(language, 'Selettore colore', 'Color picker')}">
<input id="color-hex" name="color_hex" value="#2563EB" pattern="#?[0-9A-Fa-f]{{6}}" maxlength="7" aria-label="HEX" required>
<span id="color-sample" class="color-sample" aria-hidden="true"></span></div><p class="muted">{_tr(language, 'Il codice HEX salvato in Spoolman è sempre visibile.', 'The HEX code saved in Spoolman is always visible.')}</p></div>
<div><label>{_tr(language, 'Temperatura ugello', 'Nozzle temperature')} °C</label><input name="nozzle_temperature" id="nozzle-temp" type="number" min="170" max="300" value="220" required></div></div>
<div class="grid"><div><label>{_tr(language, 'Temperatura piano', 'Bed temperature')} °C</label><input name="bed_temperature" id="bed-temp" type="number" min="0" max="150" value="60" required></div>
<div><label>{_tr(language, 'Densità', 'Density')} g/cm³</label><input name="density" id="density" type="number" min="0.1" max="10" step="0.01" value="1.24" required></div></div>
<div class="grid"><div><label>{_tr(language, 'Diametro', 'Diameter')} mm</label><input name="diameter" type="number" min="1" max="4" step="0.01" value="1.75" required></div>
<div><label>{_tr(language, 'Peso nominale filamento', 'Nominal filament weight')} g</label><input name="filament_weight" type="number" min="1" max="50000" step="0.1" value="1000" required></div></div>
<div class="grid"><div><label>{_tr(language, 'Filamento rimasto', 'Remaining filament')} g</label><input name="remaining_weight" type="number" min="0" max="50000" step="0.1" value="1000" required></div>
<div><label>{_tr(language, 'Tara bobina vuota', 'Empty spool weight')} g</label><input name="empty_spool_weight" type="number" min="0" max="10000" step="0.1" value="0" required></div></div>
<div class="grid"><div><label>{_tr(language, 'Posizione (facoltativa)', 'Location (optional)')}</label><input name="location" maxlength="64"></div>
<div><label>{_tr(language, 'Lotto (facoltativo)', 'Lot number (optional)')}</label><input name="lot_nr" maxlength="64"></div></div>
<label>{_tr(language, 'Commento', 'Comment')}</label><textarea name="comment" maxlength="1024" rows="2">{_tr(language, 'Creato con U1 Filament Automation', 'Created with U1 Filament Automation')}</textarea>
<p><button type="submit">{_tr(language, 'Mostra anteprima completa', 'Show full preview')}</button> <a class="button secondary" href="/">{_tr(language, 'Annulla', 'Cancel')}</a></p>
</form></div>
<script>
var picker=document.getElementById('color-picker'),hexField=document.getElementById('color-hex'),sample=document.getElementById('color-sample');
function showColor(value){{var normalized=value.trim().toUpperCase();if(normalized.charAt(0)!=='#')normalized='#'+normalized;if(/^#[0-9A-F]{{6}}$/.test(normalized)){{picker.value=normalized;hexField.value=normalized;sample.style.backgroundColor=normalized;}}}}
picker.addEventListener('input',function(){{showColor(this.value);}});hexField.addEventListener('input',function(){{showColor(this.value);}});showColor(picker.value);
document.getElementById('material').addEventListener('change',function(){{var p=this.value==='PETG'?['1.27','240','75']:['1.24','220','60'];document.getElementById('density').value=p[0];document.getElementById('nozzle-temp').value=p[1];document.getElementById('bed-temp').value=p[2];}});
</script>"""
    return _page(_tr(language, "Nuova bobina", "New spool"), body, language=language)


def _new_spool_request(values: dict[str, str]) -> NewSpoolRequest:
    try:
        request = NewSpoolRequest(
            vendor=values.get("vendor", ""),
            material=values.get("material", ""),
            name=values.get("name", ""),
            color_hex=values.get("color_hex", ""),
            density=float(values.get("density", "nan")),
            diameter=float(values.get("diameter", "nan")),
            filament_weight=float(values.get("filament_weight", "nan")),
            empty_spool_weight=float(values.get("empty_spool_weight", "nan")),
            remaining_weight=float(values.get("remaining_weight", "nan")),
            nozzle_temperature=int(values.get("nozzle_temperature", "0")),
            bed_temperature=int(values.get("bed_temperature", "-1")),
            location=values.get("location", ""),
            lot_nr=values.get("lot_nr", ""),
            comment=values.get("comment", ""),
        )
        return request.validated()
    except (TypeError, ValueError, OverflowError) as exc:
        raise GUIError(str(exc)) from exc


def _new_spool_preview(
    prepared: PreparedSpoolCreation,
    token: str,
    language: str = "it",
) -> str:
    plan = prepared.plan
    item = plan.request
    vendor_action = _tr(language, "riutilizza quello esistente", "reuse existing") if plan.vendor_id is not None else _tr(language, "crea nuovo", "create new")
    filament_action = _tr(language, "riutilizza quello esistente", "reuse existing") if plan.filament_id is not None else _tr(language, "crea nuovo", "create new")
    body = f"""
<h1>{_tr(language, 'Conferma nuova bobina', 'Confirm new spool')}</h1><div class="card">
<p><strong>Vendor:</strong> {html.escape(item.vendor)} — {vendor_action}</p>
<p><strong>{_tr(language, 'Filamento', 'Filament')}:</strong> {html.escape(item.material)} · {html.escape(item.name)} · #{item.color_hex} — {filament_action}</p>
<p><strong>{_tr(language, 'Bobina', 'Spool')}:</strong> {_tr(language, 'crea nuova', 'create new')} · {_tr(language, 'nominale', 'nominal')} {item.filament_weight:g} g · {_tr(language, 'rimasto', 'remaining')} {item.remaining_weight:g} g · {_tr(language, 'usato', 'used')} {item.used_weight:g} g · {_tr(language, 'tara', 'empty spool')} {item.empty_spool_weight:g} g</p>
<p><strong>{_tr(language, 'Profilo Snapmaker Orca', 'Snapmaker Orca profile')}:</strong> {html.escape(plan.profile_name)}</p>
<p><strong>Base Snapmaker:</strong> {html.escape(plan.base_profile)}</p>
<p><strong>{_tr(language, 'Calibrazione proposta', 'Proposed calibration')}:</strong> {item.nozzle_temperature} °C, {_tr(language, 'envelope U1 convalidato', 'validated U1 envelope')}</p>
<p class="warn">{_tr(language, 'La conferma scrive in Spoolman, crea una copia di prova nella sandbox e crea lo stesso nuovo profilo in Snapmaker Orca. Un profilo Orca già esistente non viene mai sovrascritto. Non invia ancora alcun comando alla stampante.', 'Confirmation writes to Spoolman, creates a test copy in the sandbox and creates the same new profile in Snapmaker Orca. An existing Orca profile is never overwritten. No command is sent to the printer yet.')}</p>
<form method="post" action="/new-spool/create">
<input type="hidden" name="token" value="{token}"><input type="hidden" name="ticket" value="{prepared.ticket}">
<label><input style="width:auto" type="checkbox" name="confirm" value="yes" required> {_tr(language, 'Confermo i dati e voglio creare la bobina in Spoolman', 'I confirm the data and want to create the spool in Spoolman')}</label>
<p><button class="danger" type="submit">{_tr(language, 'Crea bobina e profilo Orca', 'Create spool and Orca profile')}</button> <a class="button secondary" href="/new-spool">{_tr(language, 'Modifica dati', 'Edit data')}</a></p>
</form></div>"""
    return _page(_tr(language, "Conferma nuova bobina", "Confirm new spool"), body, language=language)


def _spool_created(
    receipt: SpoolCreationReceipt,
    token: str,
    language: str = "it",
) -> str:
    result = receipt.result
    item = result.plan.request
    vendor_note = _tr(language, "creato", "created") if result.vendor_created else _tr(language, "riutilizzato", "reused")
    filament_note = _tr(language, "creato", "created") if result.filament_created else _tr(language, "riutilizzato", "reused")
    body = f"""
<h1>{_tr(language, 'Bobina e profilo pronti', 'Spool and profile ready')}</h1><div class="card">
<p class="ok"><strong>{_tr(language, 'Catena completata fino a Orca.', 'Workflow completed through Orca.')}</strong></p>
<p>Vendor ID {html.escape(str(result.vendor_id))}: {vendor_note}<br>
{_tr(language, 'Filamento', 'Filament')} ID {html.escape(str(result.filament_id))}: {filament_note}<br>
{_tr(language, 'Bobina Spoolman', 'Spoolman spool')} ID <strong>{html.escape(str(result.spool_id))}</strong>: {_tr(language, 'creata', 'created')}</p>
<p><strong>{_tr(language, 'Profilo Snapmaker Orca', 'Snapmaker Orca profile')}:</strong> {html.escape(result.plan.profile_name)}<br>
<span class="muted">{html.escape(str(receipt.real_profile_path or _tr(language, 'non configurato', 'not configured')))}</span></p>
<p><strong>{_tr(language, 'Copia di sicurezza sandbox', 'Sandbox safety copy')}:</strong><br>
<span class="muted">{html.escape(str(receipt.sandbox_profile_path))}</span></p></div>
<div class="card"><h2>{_tr(language, 'Procedi con la calibrazione PA', 'Continue with PA calibration')}</h2>
<form method="post" action="/preview"><input type="hidden" name="token" value="{token}">
<input type="hidden" name="profile_name" value="{html.escape(result.plan.profile_name, quote=True)}">
<div class="grid"><div><label>{_tr(language, 'Estrusore fisico', 'Physical extruder')}</label><select name="physical_slot">
<option value="1">1 → {_tr(language, 'interno', 'internal')} 0</option><option value="2">2 → {_tr(language, 'interno', 'internal')} 1</option>
<option value="3">3 → {_tr(language, 'interno', 'internal')} 2</option><option value="4">4 → {_tr(language, 'interno', 'internal')} 3</option></select></div>
<div><label>{_tr(language, 'Temperatura', 'Temperature')} °C</label><input name="temperature" type="number" min="170" max="300" value="{item.nozzle_temperature}" required></div></div>
<p><button type="submit">{_tr(language, 'Controlla e mostra i comandi PA', 'Check and show PA commands')}</button></p></form>
<p class="muted">{_tr(language, 'La stampante non è stata ancora avviata. Il comando partirà soltanto dopo la successiva conferma.', 'The printer has not been started yet. The command will run only after the next confirmation.')}</p></div>"""
    return _page(_tr(language, "Bobina pronta", "Spool ready"), body, language=language)


def _preview(
    selection: CalibrationSelection,
    token: str,
    language: str = "it",
) -> str:
    envelope_command, run_command = selection.commands
    body = f"""
<h1>{_tr(language, 'Conferma calibrazione', 'Confirm calibration')}</h1><div class="card">
<p><strong>{_tr(language, 'Profilo', 'Profile')}:</strong> {html.escape(selection.profile_name)}</p>
<p><strong>{_tr(language, 'Estrusore', 'Extruder')}:</strong> {_tr(language, 'slot fisico', 'physical slot')} {selection.physical_slot} → <strong>EXTRUDER={selection.internal_extruder}</strong></p>
<p><strong>{_tr(language, 'Temperatura', 'Temperature')}:</strong> {selection.temperature} °C</p>
<pre>{html.escape(envelope_command)}\n{html.escape(run_command)}</pre>
<p class="warn">{_tr(language, "Avviando, la stampante selezionerà l'utensile indicato e scalderà l'ugello. Al termine l'app crea i backup e aggiorna la copia sandbox e il profilo Snapmaker Orca selezionato.", 'When started, the printer selects the specified tool and heats the nozzle. When complete, the app creates backups and updates both the sandbox copy and the selected Snapmaker Orca profile.')}</p>
<p class="warn"><strong>{_tr(language, 'Durata indicativa: circa 10 minuti.', 'Estimated duration: approximately 10 minutes.')}</strong> {_tr(language, 'Il tempo può variare leggermente. Durante il test non spegnere o riavviare la U1 e non inviare altri comandi da Fluidd o dal display.', 'The time may vary slightly. During the test, do not power off or restart the U1 and do not send other commands from Fluidd or the touchscreen.')}</p>
<form method="post" action="/start">
<input type="hidden" name="token" value="{token}">
<input type="hidden" name="profile_name" value="{html.escape(selection.profile_name, quote=True)}">
<input type="hidden" name="physical_slot" value="{selection.physical_slot}">
<input type="hidden" name="temperature" value="{selection.temperature}">
<button class="danger" type="submit">{_tr(language, 'Avvia davvero la calibrazione', 'Start calibration')}</button>
</form><p><a class="button" href="/">{_tr(language, 'Indietro', 'Back')}</a></p></div>"""
    return _page(_tr(language, "Conferma calibrazione", "Confirm calibration"), body, language=language)


def _status(controller: CalibrationController, language: str = "it") -> str:
    job = controller.snapshot()
    refresh = 3 if job.state in {"checking", "running"} else None
    selection = job.selection
    details = ""
    if selection is not None:
        details = (
            f"<p><strong>{html.escape(selection.profile_name)}</strong><br>"
            f"{_tr(language, 'Slot fisico', 'Physical slot')} {selection.physical_slot} → EXTRUDER={selection.internal_extruder}; "
            f"{selection.temperature} °C</p>"
        )
    report = ""
    if job.report:
        report = (
            f"<p class=\"ok\">{_tr(language, 'PA statico', 'Static PA')}: {html.escape(str(job.report.get('static_fallback', '')))}<br>"
            f"Backup: {html.escape(str(job.report.get('backup_path', '')))}</p>"
        )
    message = job.message
    if language == "en":
        if job.state == "idle":
            message = "Ready"
        elif job.state == "checking":
            message = "Checking printer state and macros…"
        elif job.state == "running" and selection is not None:
            message = (
                f"Calibration started: physical slot {selection.physical_slot} → "
                f"EXTRUDER={selection.internal_extruder}, {selection.temperature} °C."
            )
        elif job.state == "completed":
            message = "Calibration completed; the Snapmaker Orca profile was updated after creating a backup."
        elif job.state in {"blocked", "error"}:
            message = f"Calibration blocked or failed. Technical detail: {job.message}"
    body = f"""<h1>{_tr(language, 'Stato calibrazione', 'Calibration status')}</h1><div class="card">
<p><strong>{_tr(language, 'Stato', 'Status')}:</strong> {html.escape(job.state)}</p>{details}
<p>{html.escape(message)}</p>{report}
<p class="muted">{_tr(language, "Chiudere questa pagina non ferma una calibrazione già avviata. Per un'emergenza usare i controlli fisici/Fluidd della U1.", 'Closing this page does not stop a calibration that has already started. In an emergency, use the U1 physical controls or Fluidd.')}</p>
<p><a class="button" href="/">{_tr(language, 'Torna alla schermata iniziale', 'Return to home')}</a></p></div>"""
    return _page(_tr(language, "Stato calibrazione", "Calibration status"), body, refresh=refresh, language=language)


def _shutdown_page(
    controller: CalibrationController,
    token: str,
    error: str = "",
    language: str = "it",
) -> str:
    job = controller.snapshot()
    error_box = "" if not error else f'<p class="warn">{html.escape(error)}</p>'
    if job.state in {"checking", "running"}:
        content = f"""{error_box}<p class="warn"><strong>{_tr(language, 'Chiusura bloccata: è in corso una calibrazione. Attendi il completamento per non perdere l’applicazione del risultato PA.', 'Closing blocked: a calibration is running. Wait for completion so the PA result can be applied.')}</strong></p>
<p><a class="button" href="/status">{_tr(language, 'Mostra stato calibrazione', 'Show calibration status')}</a></p>"""
    else:
        content = f"""{error_box}<p>{_tr(language, "Verranno arrestati l'interfaccia locale e il monitor Spoolman. Non viene inviato alcun comando alla U1.", 'The local interface and Spoolman monitor will stop. No command is sent to the U1.')}</p>
<form method="post" action="/shutdown"><input type="hidden" name="token" value="{token}">
<p><button class="danger" type="submit">{_tr(language, 'Chiudi davvero U1FA', 'Close U1FA')}</button> <a class="button secondary" href="/">{_tr(language, 'Annulla', 'Cancel')}</a></p></form>"""
    body = f"<h1>{_tr(language, 'Chiudi applicazione', 'Close application')}</h1><div class=\"card\">{content}</div>"
    return _page(_tr(language, "Chiudi applicazione", "Close application"), body, language=language)


def _shutdown_result(language: str = "it") -> str:
    body = f"""<h1>{_tr(language, 'U1FA chiusa', 'U1FA closed')}</h1><div class="card">
<p class="ok"><strong>{_tr(language, "Applicazione e monitor Spoolman arrestati. Puoi chiudere questa scheda; nessun comando è stato inviato alla U1.", 'Application and Spoolman monitor stopped. You can close this tab; no command was sent to the U1.')}</strong></p></div>"""
    return _page(_tr(language, "U1FA chiusa", "U1FA closed"), body, language=language)


def _form(handler: BaseHTTPRequestHandler) -> dict[str, str]:
    try:
        length = int(handler.headers.get("Content-Length", "0"))
    except ValueError as exc:
        raise GUIError("Richiesta non valida") from exc
    if length < 1 or length > 16384:
        raise GUIError("Dimensione richiesta non valida")
    raw = handler.rfile.read(length).decode("utf-8", errors="strict")
    values = parse_qs(raw, keep_blank_values=True)
    return {key: items[-1] for key, items in values.items() if items}


def _handler(controller: CalibrationController, token: str):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, content: str, status: int = 200) -> None:
            data = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self' 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(data)

        def _send_logo(self) -> None:
            try:
                data = LOGO_ASSET.read_bytes()
            except OSError:
                language = controller.language()
                message = _tr(language, "Logo non disponibile", "Logo unavailable")
                self._send(_page(message, f"<h1>{message}</h1>", language=language), 404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "public, max-age=3600")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802
            request = urlsplit(self.path)
            path = request.path
            if path == "/language":
                language = (parse_qs(request.query).get("lang") or ["it"])[-1]
                try:
                    controller.set_language(language)
                except GUIError:
                    controller.set_language("it")
                self.send_response(303)
                self.send_header("Location", "/")
                self.end_headers()
                return
            language = controller.language()
            if path == "/":
                self._send(_home(controller, token, language=language))
            elif path == "/connections":
                self._send(_connections_form(controller, token, language=language))
            elif path == "/new-spool":
                self._send(_new_spool_form(token, language=language))
            elif path == "/printer-setup":
                self._send(_printer_setup_form(token, language=language))
            elif path == "/updates":
                self._send(_updates_page(controller, token, language=language))
            elif path == "/printer-setup/result":
                receipt = controller.last_setup()
                if receipt is None:
                    message = _tr(language, "Nessuna configurazione appena eseguita", "No setup was just completed")
                    self._send(_printer_setup_form(token, message, language), 404)
                else:
                    self._send(_printer_setup_result(receipt, language))
            elif path == "/spool-created":
                receipt = controller.last_creation()
                if receipt is None:
                    title = _tr(language, "Nessuna creazione", "No creation")
                    message = _tr(language, "Nessuna bobina appena creata", "No spool was just created")
                    back = _tr(language, "Torna indietro", "Go back")
                    self._send(
                        _page(
                            title,
                            f'<h1>{message}</h1><p><a class="button" href="/">{back}</a></p>',
                            language=language,
                        ),
                        404,
                    )
                else:
                    self._send(_spool_created(receipt, token, language))
            elif path == "/status":
                self._send(_status(controller, language))
            elif path == "/shutdown":
                self._send(_shutdown_page(controller, token, language=language))
            elif path == "/assets/u1fa-logo.png":
                self._send_logo()
            else:
                title = _tr(language, "Non trovato", "Not found")
                message = _tr(language, "Pagina non trovata", "Page not found")
                self._send(_page(title, f"<h1>{message}</h1>", language=language), 404)

        def do_POST(self) -> None:  # noqa: N802
            path = urlsplit(self.path).path
            language = controller.language()
            try:
                values = _form(self)
                if not secrets.compare_digest(values.get("token", ""), token):
                    raise GUIError(_tr(language, "Sessione non valida: operazione bloccata", "Invalid session: operation blocked"))
                if path == "/connections/save":
                    controller.configure_connections(
                        values.get("moonraker_address", ""),
                        values.get("spoolman_address", ""),
                    )
                    self.send_response(303)
                    self.send_header("Location", "/")
                    self.end_headers()
                    return
                if path == "/shutdown":
                    if controller.snapshot().state in {"checking", "running"}:
                        raise GUIError(_tr(
                            language,
                            "Chiusura bloccata durante la calibrazione",
                            "Closing is blocked during calibration",
                        ))
                    self._send(_shutdown_result(language))
                    threading.Thread(
                        target=self.server.shutdown,
                        name="u1fa-safe-shutdown",
                        daemon=True,
                    ).start()
                    return
                if path == "/updates/check":
                    controller.start_update_check()
                    self.send_response(303)
                    self.send_header("Location", "/updates")
                    self.end_headers()
                    return
                if path == "/updates/download":
                    if values.get("confirm") != "yes":
                        raise GUIError(_tr(
                            language,
                            "Conferma download mancante",
                            "Download confirmation is missing",
                        ))
                    controller.download_available_update()
                    self.send_response(303)
                    self.send_header("Location", "/updates")
                    self.end_headers()
                    return
                if path == "/updates/open":
                    if values.get("confirm") != "yes":
                        raise GUIError(_tr(
                            language,
                            "Conferma installazione mancante",
                            "Installation confirmation is missing",
                        ))
                    controller.open_downloaded_update()
                    self.send_response(303)
                    self.send_header("Location", "/updates")
                    self.end_headers()
                    return
                if path == "/new-spool/preview":
                    request = _new_spool_request(values)
                    prepared = controller.prepare_spool_creation(request)
                    self._send(_new_spool_preview(prepared, token, language))
                    return
                if path == "/printer-setup/preview":
                    if values.get("printer_access_enabled") != "yes":
                        raise GUIError(_tr(
                            language,
                            "Prima abilita Modalità avanzata e Accesso Root/SSH dal display U1",
                            "First enable Advanced Mode and Root Access/SSH on the U1 touchscreen",
                        ))
                    prepared = controller.prepare_printer_setup(
                        values.get("ssh_password", "")
                    )
                    self._send(_printer_setup_preview(prepared, token, language))
                    return
                if path == "/printer-setup/apply":
                    if values.get("confirm") != "yes":
                        raise GUIError(_tr(language, "Conferma esplicita mancante: nessun file modificato", "Explicit confirmation missing: no file changed"))
                    controller.apply_printer_setup(
                        values.get("ticket", ""),
                        values.get("ssh_password", ""),
                    )
                    self.send_response(303)
                    self.send_header("Location", "/printer-setup/result")
                    self.end_headers()
                    return
                if path == "/new-spool/create":
                    if values.get("confirm") != "yes":
                        raise GUIError(_tr(language, "Conferma esplicita mancante: nessuna bobina creata", "Explicit confirmation missing: no spool created"))
                    controller.create_prepared_spool(values.get("ticket", ""))
                    self.send_response(303)
                    self.send_header("Location", "/spool-created")
                    self.end_headers()
                    return

                selection = controller.selection(
                    values.get("profile_name", ""),
                    int(values.get("physical_slot", "0")),
                    int(values.get("temperature", "0")),
                )
                if path == "/preview":
                    self._send(_preview(selection, token, language))
                elif path == "/start":
                    controller.start(selection)
                    self.send_response(303)
                    self.send_header("Location", "/status")
                    self.end_headers()
                else:
                    title = _tr(language, "Non trovato", "Not found")
                    message = _tr(language, "Pagina non trovata", "Page not found")
                    self._send(_page(title, f"<h1>{message}</h1>", language=language), 404)
            except (ValueError, UnicodeError, GUIError, PAProfileError) as exc:
                if path.startswith("/connections"):
                    self._send(_connections_form(controller, token, str(exc), language), 400)
                elif path.startswith("/shutdown"):
                    self._send(_shutdown_page(controller, token, str(exc), language), 400)
                elif path.startswith("/new-spool"):
                    self._send(_new_spool_form(token, str(exc), language), 400)
                elif path.startswith("/printer-setup"):
                    self._send(_printer_setup_form(token, str(exc), language), 400)
                elif path.startswith("/updates"):
                    self._send(_updates_page(controller, token, str(exc), language), 400)
                else:
                    self._send(_home(controller, token, str(exc), language), 400)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def run_gui(
    moonraker_url: str,
    spoolman_url: str,
    sandbox_dir: Path,
    orca_dir: str | None = None,
    bind: str = "127.0.0.1",
    port: int = 8765,
    timeout: float = 5.0,
    open_browser: bool = True,
    ssh_target: str | None = None,
    ssh_port: int = 22,
    identity_file: str | None = None,
    monitor_interval: float = 10.0,
    connection_config_path: Path | None = None,
) -> int:
    if bind not in {"127.0.0.1", "localhost"}:
        raise GUIError("Per sicurezza l'interfaccia può ascoltare solo su localhost")
    if port < 1024 or port > 65535:
        raise GUIError("La porta deve essere compresa tra 1024 e 65535")
    installations = discover_orca(explicit_dir=orca_dir)
    if not installations:
        raise GUIError("Cartella filamenti Snapmaker Orca non trovata")
    if len(installations) > 1 and not orca_dir:
        raise GUIError("Trovate più cartelle Orca: indicare --orca-dir")
    real_user_dir = installations[0].path.resolve()
    sandbox_dir = sandbox_dir.expanduser().resolve()
    if (
        sandbox_dir == real_user_dir
        or sandbox_dir in real_user_dir.parents
        or real_user_dir in sandbox_dir.parents
    ):
        raise GUIError("La sandbox coincide o si sovrappone ai profili Orca reali")

    controller = CalibrationController(
        moonraker_url=moonraker_url,
        spoolman_url=spoolman_url,
        sandbox_dir=sandbox_dir,
        system_dir=default_system_dir(real_user_dir),
        timeout=timeout,
        real_orca_dir=real_user_dir,
        ssh_target=ssh_target,
        ssh_port=ssh_port,
        identity_file=identity_file,
        monitor_interval=monitor_interval,
        connection_config_path=connection_config_path,
    )
    controller.start_update_check()
    if moonraker_url and spoolman_url:
        try:
            controller.configure_connections(moonraker_url, spoolman_url)
        except GUIError as exc:
            controller._set_monitor(ProfileMonitorSnapshot(
                "error",
                f"Connessioni da verificare: {exc}",
                f"Connections need verification: {exc}",
            ))
    elif spoolman_url:
        try:
            controller.refresh_profiles()
            controller.start_profile_monitor()
        except (ServiceError, ValueError, PAProfileError, GUIError) as exc:
            controller._set_monitor(ProfileMonitorSnapshot(
                "error",
                f"Spoolman da configurare: {exc}",
                f"Spoolman needs setup: {exc}",
            ))

    token = secrets.token_urlsafe(32)
    server = ThreadingHTTPServer((bind, port), _handler(controller, token))
    url = f"http://127.0.0.1:{port}/"
    print("U1 Filament Automation — interfaccia locale")
    print(f"Aprire: {url}")
    print(f"Nuovi profili Orca: {real_user_dir} (nessuna sovrascrittura)")
    print(f"Copia di prova: {sandbox_dir}")
    print("Per chiudere l'interfaccia: Ctrl-C")
    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\nInterfaccia chiusa. Nessun riavvio inviato alla stampante.")
    finally:
        controller.stop_profile_monitor()
        server.server_close()
    return 0
