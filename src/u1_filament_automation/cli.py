from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from typing import Sequence
from urllib.parse import urlparse

from .config import (
    ConfigError,
    default_connection_config_path,
    load_connection_config,
    normalize_service_url,
)
from .doctor import run_doctor
from .gui import GUIError, run_gui
from .models import SpoolmanInventory
from .orca import discover_orca
from .pa import PAParseError, last_complete_suite, last_complete_suite_span
from .pa_capture import (
    PACaptureError,
    latest_cached_suite,
    new_gcode_entries,
    parse_gcode_store,
    response_text,
)
from .pa_profile import (
    PAProfileError,
    calibration_identity,
    resolve_profile_name,
    update_pa_profile,
)
from .printer import (
    STOCK_SHA256,
    V6_SHA256,
    LocalPrinterTarget,
    MoonrakerClient,
    PrinterInstallError,
    SSHPrinterTarget,
    install_printer_setup,
    inspect_adaptive_pa_macro,
    inspect_calibrator,
    plan_printer_setup,
    require_safe_printer,
    validated_asset,
)
from .spoolman import (
    ServiceError,
    candidates_from_moonraker,
    explicit_candidates,
    first_working_inventory,
)
from .sync import default_system_dir, sync_profiles
from .watch import (
    WatchStateError,
    default_watch_state_path,
    load_managed_profiles,
    managed_profiles_from_report,
    save_managed_profiles,
)


def _add_printer_target_arguments(parser: argparse.ArgumentParser) -> None:
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--sandbox-root",
        help="Replica locale isolata della U1; non contatta la stampante",
    )
    target.add_argument(
        "--ssh-target",
        help="Destinazione SSH, per esempio root@192.168.1.100",
    )
    parser.add_argument("--moonraker-url")
    parser.add_argument("--moonraker-api-key")
    parser.add_argument("--ssh-port", type=int, default=22)
    authentication = parser.add_mutually_exclusive_group()
    authentication.add_argument("--identity-file")
    authentication.add_argument(
        "--ask-ssh-password",
        action="store_true",
        help="Chiede la password SSH senza salvarla; alternativa alla chiave",
    )
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--json", action="store_true", dest="as_json")


def _add_sync_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--spoolman-url")
    parser.add_argument("--moonraker-url")
    parser.add_argument("--orca-dir")
    parser.add_argument("--system-dir")
    parser.add_argument(
        "--sandbox-dir",
        help="Cartella di prova separata; non scrive nei profili reali di Orca",
    )
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--confirm-orca-write",
        action="store_true",
        help="Conferma esplicita richiesta per scrivere nella cartella reale",
    )
    parser.add_argument("--json", action="store_true", dest="as_json")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="u1fa")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor = subparsers.add_parser("doctor", help="Diagnosi in sola lettura")
    doctor.add_argument("--spoolman-url")
    doctor.add_argument("--moonraker-url")
    doctor.add_argument("--orca-dir")
    doctor.add_argument("--nozzle", type=float, default=0.4)
    doctor.add_argument("--timeout", type=float, default=2.0)
    doctor.add_argument("--json", action="store_true", dest="as_json")
    doctor.add_argument("--preview-limit", type=int, default=10)

    pa_parse = subparsers.add_parser(
        "pa-parse",
        help="Estrae la tabella PA da un log ULTRA v6 senza collegarsi alla stampante",
    )
    pa_parse.add_argument("logfile", help="File di log già salvato")
    pa_parse.add_argument("--json", action="store_true", dest="as_json")

    sync = subparsers.add_parser(
        "sync", help="Crea i profili Orca dalle bobine Spoolman"
    )
    _add_sync_arguments(sync)

    pa_profile = subparsers.add_parser(
        "pa-profile",
        help="Associa un log PA al filamento Spoolman e prepara il profilo Orca",
    )
    pa_profile.add_argument("logfile", help="File di log ULTRA v6 già salvato")
    pa_profile.add_argument("--spoolman-url")
    pa_profile.add_argument("--moonraker-url")
    pa_profile.add_argument("--orca-dir")
    pa_profile.add_argument(
        "--sandbox-dir",
        help="Cartella di prova separata; non scrive nei profili reali di Orca",
    )
    pa_profile.add_argument(
        "--profile-name",
        help="Profilo Orca esatto; ripiego manuale se il log non identifica la bobina",
    )
    pa_profile.add_argument("--timeout", type=float, default=2.0)
    pa_profile.add_argument("--apply", action="store_true")
    pa_profile.add_argument(
        "--confirm-orca-write",
        action="store_true",
        help="Conferma esplicita richiesta per scrivere nella cartella reale",
    )
    pa_profile.add_argument("--json", action="store_true", dest="as_json")

    pa_auto = subparsers.add_parser(
        "pa-auto",
        help="Attende una nuova calibrazione PA tramite Moonraker e aggiorna Orca",
    )
    pa_auto.add_argument("--moonraker-url", required=True)
    pa_auto.add_argument("--moonraker-api-key")
    pa_auto.add_argument("--spoolman-url")
    pa_auto.add_argument("--orca-dir")
    pa_auto.add_argument(
        "--sandbox-dir",
        help="Cartella di prova separata; non scrive nei profili reali di Orca",
    )
    pa_auto.add_argument(
        "--profile-name",
        help="Profilo Orca esatto; ripiego manuale se il log non identifica la bobina",
    )
    pa_auto.add_argument("--timeout", type=float, default=2.0)
    pa_auto.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Secondi tra le letture della cache Moonraker (minimo 0.5)",
    )
    pa_auto.add_argument(
        "--cycles",
        type=int,
        default=0,
        help="Numero di controlli; 0 attende fino al risultato o a Ctrl-C",
    )
    pa_auto.add_argument(
        "--store-count",
        type=int,
        default=1000,
        help="Numero di risposte recenti richieste a Moonraker",
    )
    pa_auto.add_argument("--apply", action="store_true")
    pa_auto.add_argument(
        "--confirm-orca-write",
        action="store_true",
        help="Conferma esplicita richiesta per scrivere nella cartella reale",
    )
    pa_auto.add_argument("--json", action="store_true", dest="as_json")

    pa_latest = subparsers.add_parser(
        "pa-latest",
        help="Recupera l'ultima suite PA completa ancora nella cache Moonraker",
    )
    pa_latest.add_argument("--moonraker-url", required=True)
    pa_latest.add_argument("--moonraker-api-key")
    pa_latest.add_argument("--spoolman-url")
    pa_latest.add_argument("--orca-dir")
    pa_latest.add_argument(
        "--sandbox-dir",
        help="Cartella di prova separata; non scrive nei profili reali di Orca",
    )
    pa_latest.add_argument(
        "--profile-name",
        help="Profilo Orca esatto a cui assegnare il risultato recuperato",
    )
    pa_latest.add_argument("--timeout", type=float, default=2.0)
    pa_latest.add_argument("--store-count", type=int, default=1000)
    pa_latest.add_argument(
        "--max-age",
        type=float,
        default=7200.0,
        help="Età massima accettata della calibrazione, in secondi",
    )
    pa_latest.add_argument("--apply", action="store_true")
    pa_latest.add_argument(
        "--confirm-orca-write",
        action="store_true",
        help="Conferma esplicita richiesta per scrivere nella cartella reale",
    )
    pa_latest.add_argument("--json", action="store_true", dest="as_json")

    gui = subparsers.add_parser(
        "gui",
        help="Crea bobine/profili e guida la calibrazione Adaptive PA",
    )
    gui.add_argument(
        "--moonraker-url",
        help="Facoltativo: se omesso viene usata la configurazione salvata o la GUI iniziale",
    )
    gui.add_argument(
        "--spoolman-url",
        help="Facoltativo: predefinito locale http://127.0.0.1:7912",
    )
    gui.add_argument("--sandbox-dir", required=True)
    gui.add_argument("--orca-dir")
    gui.add_argument(
        "--ssh-target",
        help="Destinazione SSH U1; predefinita root@HOST ricavata da Moonraker",
    )
    gui.add_argument("--ssh-port", type=int, default=22)
    gui.add_argument("--identity-file")
    gui.add_argument(
        "--config-file",
        help="Percorso alternativo del file locale con gli indirizzi (nessuna password)",
    )
    gui.add_argument("--bind", default="127.0.0.1")
    gui.add_argument("--port", type=int, default=8765)
    gui.add_argument("--timeout", type=float, default=5.0)
    gui.add_argument(
        "--sync-interval",
        type=float,
        default=10.0,
        help="Secondi tra i controlli automatici delle bobine aggiunte in Spoolman (minimo 5)",
    )
    gui.add_argument("--no-browser", action="store_true")

    watch = subparsers.add_parser(
        "watch",
        help="Sorveglia Spoolman e crea i nuovi profili Orca automaticamente",
    )
    _add_sync_arguments(watch)
    watch.add_argument(
        "--interval",
        type=float,
        default=30.0,
        help="Secondi tra i controlli Spoolman (minimo 5)",
    )
    watch.add_argument(
        "--cycles",
        type=int,
        default=0,
        help="Numero di controlli; 0 continua fino a Ctrl-C",
    )
    watch.add_argument(
        "--state-file",
        help="File locale che ricorda i profili già gestiti dal monitor",
    )

    printer_check = subparsers.add_parser(
        "printer-check",
        help="Controlla in sola lettura il calibratore della U1",
    )
    _add_printer_target_arguments(printer_check)

    printer_install = subparsers.add_parser(
        "printer-install",
        help="Installa calibratore, macro e include Adaptive PA in sicurezza",
    )
    _add_printer_target_arguments(printer_install)
    printer_install.add_argument("--apply", action="store_true")
    printer_install.add_argument(
        "--confirm-printer-write",
        action="store_true",
        help="Conferma distinta richiesta per modificare la U1 reale",
    )

    printer_restore = subparsers.add_parser(
        "printer-restore",
        help="Ripristina un backup originale creato dall'app",
    )
    _add_printer_target_arguments(printer_restore)
    printer_restore.add_argument("--backup-path", required=True)
    printer_restore.add_argument("--apply", action="store_true")
    printer_restore.add_argument(
        "--confirm-printer-write",
        action="store_true",
        help="Conferma distinta richiesta per modificare la U1 reale",
    )
    return parser


def _safe_sandbox_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    broad_roots = {Path(root.anchor).resolve(), Path.home().resolve()}
    if root in broad_roots:
        raise PrinterInstallError(
            "La sandbox non può essere la root del disco o la cartella home"
        )
    return root


def _printer_target(args):
    if args.sandbox_root:
        return LocalPrinterTarget(_safe_sandbox_root(args.sandbox_root)), None
    if not args.moonraker_url:
        raise PrinterInstallError(
            "Per una U1 reale è obbligatorio indicare --moonraker-url"
        )
    target = SSHPrinterTarget(
        args.ssh_target,
        port=args.ssh_port,
        identity_file=args.identity_file,
        ask_password=args.ask_ssh_password,
        timeout=args.timeout,
    )
    moonraker = MoonrakerClient(
        args.moonraker_url,
        timeout=args.timeout,
        api_key=args.moonraker_api_key,
    )
    return target, moonraker


def _printer_report(
    title: str,
    status,
    safety=None,
    action: str | None = None,
    macro_status=None,
    write_result=None,
    setup_result=None,
    power_cycle_required: bool = False,
    as_json: bool = False,
) -> None:
    payload = {
        "title": title,
        "calibrator": status.to_dict(),
        "adaptive_pa_macro": (
            None if macro_status is None else macro_status.to_dict()
        ),
        "safety": None if safety is None else safety.to_dict(),
        "action": action,
        "write": None if write_result is None else write_result.to_dict(),
        "setup": None if setup_result is None else setup_result.to_dict(),
        "power_cycle_required": power_cycle_required,
    }
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return
    print(title)
    if safety is None:
        print("Modalità SANDBOX locale — nessuna connessione alla stampante")
    else:
        print(
            "Stato U1: "
            f"Klipper={safety.klippy_state}, stampa={safety.print_state}, "
            f"virtual_sd_active={safety.virtual_sd_active}, "
            f"idle={safety.idle_state}, machine={safety.machine_state}"
        )
    print(f"File: {status.path}")
    print(f"SHA-256: {status.sha256}")
    print(f"Stato calibratore: {status.state}")
    if macro_status is not None:
        print(f"Macro: {macro_status.path}")
        print(f"SHA-256 macro: {macro_status.sha256 or 'assente'}")
        print(f"Stato macro: {macro_status.state}")
        loaded = {
            True: "sì",
            False: "no",
            None: "non verificato",
        }[macro_status.loaded_by_klipper]
        print(f"Macro caricata da Klipper: {loaded}")
        print(
            "Catena Adaptive PA: "
            + ("completa e validata" if macro_status.complete else "incompleta/bloccata")
        )
    if action:
        print(f"Azione: {action}")
    if write_result is not None:
        print(f"Backup: {write_result.backup_path}")
    if setup_result is not None:
        if not setup_result.writes:
            print("Scritture: nessuna; catena già installata")
        for item in setup_result.writes:
            print(f"{item.action.upper()}: {item.path}")
            if item.backup_path:
                print(f"  Backup: {item.backup_path}")
    if power_cycle_required:
        print("[RICHIESTO] Spegnere completamente la U1 per 10–15 secondi e riaccenderla.")
        print("Il semplice RESTART di Klipper non ricarica questo modulo Python sulla U1.")


def _run_printer_command(args) -> int:
    try:
        if (
            args.command in {"printer-install", "printer-restore"}
            and args.apply
            and args.ssh_target
            and not args.confirm_printer_write
        ):
            print("[BLOCCATO] Scrittura sulla U1 reale non autorizzata.")
            print("Nessun collegamento e nessuna modifica eseguiti.")
            return 2

        target, moonraker = _printer_target(args)
        safety = None
        if moonraker is not None:
            safety = require_safe_printer(moonraker)

        if args.command == "printer-install" and args.apply and isinstance(
            target, LocalPrinterTarget
        ):
            target.seed_stock_if_missing()
            target.seed_config_if_missing()

        status = inspect_calibrator(target)

        if args.command == "printer-check":
            macro_loaded = (
                None
                if moonraker is None
                else moonraker.has_gcode_macro("APA_COIL_RUN_ULTRA")
            )
            macro_status = inspect_adaptive_pa_macro(
                target,
                loaded_by_klipper=macro_loaded,
            )
            _printer_report(
                "U1 Filament Automation — controllo calibratore in sola lettura",
                status,
                safety=safety,
                action="nessuna scrittura",
                macro_status=macro_status,
                as_json=args.as_json,
            )
            return (
                0
                if status.state != "unknown-blocked" and macro_status.complete
                else 2
            )

        if args.command == "printer-install":
            macro_loaded = (
                None
                if moonraker is None
                else moonraker.has_gcode_macro("APA_COIL_RUN_ULTRA")
            )
            plan = plan_printer_setup(
                target, loaded_by_klipper=macro_loaded
            )
            if not args.apply:
                planned = []
                if plan.install_calibrator:
                    planned.append("sostituirebbe il calibratore creando un backup")
                if plan.create_macro:
                    planned.append("creerebbe adaptive_pa_macro.cfg")
                if plan.update_printer_cfg:
                    planned.append("aggiungerebbe l'include a printer.cfg creando un backup")
                action = "; ".join(planned) or "catena già installata; nessuna scrittura"
                _printer_report(
                    "U1 Filament Automation — anteprima configurazione completa",
                    status,
                    safety=safety,
                    action=action,
                    macro_status=plan.macro,
                    as_json=args.as_json,
                )
                return 0

            if moonraker is not None:
                safety = require_safe_printer(moonraker)
            setup_result = install_printer_setup(
                target,
                loaded_by_klipper=macro_loaded,
                power_cycle_required=moonraker is not None,
            )
            _printer_report(
                "U1 Filament Automation — configurazione completa installata",
                setup_result.calibrator,
                safety=safety,
                action=(
                    "file configurati e verificati; caricamento runtime da controllare dopo la riaccensione"
                    if setup_result.power_cycle_required or moonraker is None
                    else "catena già installata e caricata; nessuna modifica"
                ),
                macro_status=setup_result.macro,
                setup_result=setup_result,
                power_cycle_required=setup_result.power_cycle_required,
                as_json=args.as_json,
            )
            return 0

        if status.state != "v6-installed":
            raise PrinterInstallError(
                "Il calibratore v6 non è installato: ripristino non necessario"
            )
        if not args.apply:
            _printer_report(
                "U1 Filament Automation — anteprima ripristino",
                status,
                safety=safety,
                action=f"ripristinerebbe {args.backup_path}",
                as_json=args.as_json,
            )
            return 0
        if moonraker is not None:
            safety = require_safe_printer(moonraker)
        write_result = target.restore_atomic(args.backup_path, V6_SHA256)
        restored = inspect_calibrator(target)
        _printer_report(
            "U1 Filament Automation — ripristino completato",
            restored,
            safety=safety,
            action="originale validato ripristinato",
            write_result=write_result,
            power_cycle_required=moonraker is not None,
            as_json=args.as_json,
        )
        return 0
    except PrinterInstallError as exc:
        print(f"[BLOCCATO] {exc}")
        return 2


def _print_report(report, preview_limit: int) -> None:
    print("U1 Filament Automation — diagnosi sola lettura")
    print("Modalità sicurezza: 0 scritture su Orca, Spoolman e stampante")
    print()
    if report.orca:
        for item in report.orca:
            print(f"[OK] Snapmaker Orca: {item.path} ({item.profile_count} profili JSON)")
    else:
        print("[--] Snapmaker Orca: non trovato")

    if report.spoolman:
        counts = report.spoolman.counts()
        print(f"[OK] Spoolman: {report.spoolman.url}")
        print(
            "     "
            f"vendor={counts['vendors']} filamenti={counts['filaments']} "
            f"bobine={counts['spools']}"
        )
    else:
        print("[--] Spoolman: non raggiungibile")

    if report.comparisons:
        print()
        print("Confronto profili tecnici (nessun file scritto):")
        preview_by_name = {item.nozzle_profile: item for item in report.previews}
        labels = {
            "existing": "ESISTE",
            "equivalent": "EQUIVALENTE",
            "ambiguous": "AMBIGUO",
            "similar": "SIMILE",
            "missing": "MANCANTE",
        }
        for comparison in report.comparisons[: max(0, preview_limit)]:
            preview = preview_by_name[comparison.target]
            print(
                f"[{labels[comparison.status]}] {comparison.target} "
                f"| bobine={list(preview.spool_ids)}"
            )
            if comparison.exact_matches:
                print(f"           corrispondenza: {', '.join(comparison.exact_matches)}")
            elif comparison.equivalent_matches:
                print(
                    "           stesso profilo: "
                    f"{', '.join(comparison.equivalent_matches)}"
                )
            elif comparison.similar_matches:
                description = (
                    "verifica richiesta"
                    if comparison.status == "ambiguous"
                    else "possibile simile"
                )
                print(f"           {description}: {', '.join(comparison.similar_matches)}")
        remaining = len(report.comparisons) - max(0, preview_limit)
        if remaining > 0:
            print(f"  ... altri {remaining}")

    if report.warnings:
        print()
        for warning in report.warnings:
            print(f"[ATTENZIONE] {warning}")


def _sync_candidates(args) -> list[str]:
    candidates = explicit_candidates(args.spoolman_url)
    moonraker_url = args.moonraker_url or os.environ.get("U1FA_MOONRAKER_URL")
    if moonraker_url:
        try:
            discovered = candidates_from_moonraker(
                moonraker_url,
                timeout=args.timeout,
            )
        except (ServiceError, ValueError):
            discovered = []
        for candidate in discovered:
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


def _pa_profile_candidates(args) -> list[str]:
    """Evita Moonraker salvo richiesta esplicita nel comando corrente."""
    candidates = explicit_candidates(args.spoolman_url)
    if not args.moonraker_url:
        return candidates
    try:
        discovered = candidates_from_moonraker(
            args.moonraker_url,
            timeout=args.timeout,
        )
    except (ServiceError, ValueError):
        discovered = []
    for candidate in discovered:
        if candidate not in candidates:
            candidates.append(candidate)
    return candidates


def _print_sync_report(report, mode: str, cycle: int | None = None) -> None:
    suffix = "" if cycle is None else f" — controllo {cycle}"
    print(f"U1 Filament Automation — sincronizzazione {mode}{suffix}")
    print(f"Profili utente: {report.user_dir}")
    print(f"Profili base:   {report.system_dir}")
    print()
    labels = {
        "planned": "CREEREBBE",
        "created": "CREATO",
        "existing": "ESISTE",
        "merged": "UNIFICATO",
        "skipped": "SALTATO",
        "dismissed": "GESTITO",
    }
    for action in report.actions:
        print(f"[{labels[action.status]}] {action.profile_name}")
        if action.base:
            print(f"           Base: {action.base}")
        if action.message:
            print(f"           Nota: {action.message}")
    print()
    print("Riepilogo:", report.counts())


def _print_pa_profile_report(report, sandbox: bool, apply: bool) -> None:
    if apply and sandbox:
        mode = "SANDBOX — profili reali intatti"
    elif apply:
        mode = "APPLICAZIONE REALE CONFERMATA"
    else:
        mode = "ANTEPRIMA — nessun file scritto"
    print(f"U1 Filament Automation — Adaptive PA → profilo Orca — {mode}")
    print(f"Profilo: {report.profile_name}")
    print(f"File:    {report.profile_path}")
    if report.manual_profile:
        print("Associazione profilo: selezionata esplicitamente; ID cache ignorato")
    elif report.identity.spool_id is not None:
        print(f"Bobina Spoolman: ID {report.identity.spool_id}")
    elif report.identity.tracking_label or report.identity.flow_label:
        print(
            "Filamento dal log: "
            f"{report.identity.tracking_label or report.identity.flow_label}"
        )
    print(f"PA statica di sicurezza: {report.static_fallback}")
    print("Tabella Adaptive PA (PA, flusso, accelerazione):")
    for row in report.adaptive_model.splitlines():
        print(f"- {row}")
    if report.status == "planned":
        print(f"Campi che aggiornerebbe: {', '.join(report.changed_fields)}")
        print("Azione: nessuna scrittura")
    elif report.status == "updated":
        print(f"Campi aggiornati: {', '.join(report.changed_fields)}")
        print(f"Backup: {report.backup_path}")
    else:
        print("[INVARIATO] Il profilo contiene già esattamente questi valori PA.")


def _run_pa_auto(args, target_user_dir: Path) -> int:
    if args.interval < 0.5:
        print("[ERRORE] --interval deve essere almeno 0.5 secondi.")
        return 2
    if args.cycles < 0:
        print("[ERRORE] --cycles non può essere negativo.")
        return 2
    try:
        client = MoonrakerClient(
            args.moonraker_url,
            timeout=args.timeout,
            api_key=args.moonraker_api_key,
        )
        previous = parse_gcode_store(client.gcode_store(args.store_count))
    except (PrinterInstallError, PACaptureError) as exc:
        print(f"[BLOCCATO] {exc}")
        return 2


    if not args.as_json:
        mode = (
            "SANDBOX — profili reali intatti"
            if args.sandbox_dir
            else "PROFILI REALI CON CONFERMA"
        )
        print(f"U1 Filament Automation — attesa nuova calibrazione PA — {mode}")
        print(
            "Moonraker: sola lettura GET /server/gcode_store; "
            "nessun G-code inviato"
        )
        print(f"Risposte già presenti ignorate: {len(previous)}")
        print("In attesa di una nuova suite ULTRA v6 completa…")

    captured = []
    cycle = 0
    try:
        while True:
            if args.cycles and cycle >= args.cycles:
                if args.as_json:
                    print(
                        json.dumps(
                            {
                                "status": "no-new-complete-suite",
                                "cycles": cycle,
                                "writes": 0,
                            },
                            ensure_ascii=False,
                        )
                    )
                else:
                    print(
                        "[NESSUN RISULTATO] Nessuna nuova suite completa; "
                        "nessun profilo modificato."
                    )
                return 0
            time.sleep(args.interval)
            cycle += 1
            current = parse_gcode_store(client.gcode_store(args.store_count))
            captured.extend(new_gcode_entries(previous, current))
            previous = current
            text = response_text(captured)
            try:
                suite, _, suite_end = last_complete_suite_span(text)
            except PAParseError:
                continue
            identity = calibration_identity(text, end_offset=suite_end)
            if args.profile_name:
                profile_name = resolve_profile_name(
                    identity,
                    SpoolmanInventory(url="manual"),
                    override=args.profile_name,
                )
            else:
                inventory, _ = first_working_inventory(
                    _pa_profile_candidates(args),
                    timeout=args.timeout,
                )
                if inventory is None:
                    raise PAProfileError("Spoolman non raggiungibile")
                profile_name = resolve_profile_name(identity, inventory)
            report = update_pa_profile(
                target_user_dir,
                profile_name,
                identity,
                suite,
                apply=args.apply,
                manual_profile=bool(args.profile_name),
            )
            if args.as_json:
                print(
                    json.dumps(
                        {
                            "capture": {
                                "status": "new-complete-suite",
                                "cycles": cycle,
                                "new_messages": len(captured),
                            },
                            **report.to_dict(),
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            else:
                print()
                print("[RILEVATA] Nuova suite ULTRA v6 completa.")
                _print_pa_profile_report(
                    report,
                    sandbox=bool(args.sandbox_dir),
                    apply=args.apply,
                )
            return 0
    except KeyboardInterrupt:
        print("\nMonitoraggio interrotto; nessun comando inviato alla stampante.")
        return 0
    except (PrinterInstallError, PACaptureError, PAProfileError) as exc:
        print(f"[BLOCCATO] {exc}")
        return 2


def _run_pa_latest(args, target_user_dir: Path) -> int:
    if args.max_age <= 0:
        print("[ERRORE] --max-age deve essere maggiore di zero.")
        return 2
    try:
        client = MoonrakerClient(
            args.moonraker_url,
            timeout=args.timeout,
            api_key=args.moonraker_api_key,
        )
        entries = parse_gcode_store(client.gcode_store(args.store_count))
        cached = latest_cached_suite(entries)
        age = time.time() - cached.completed_at
        if age < -300:
            raise PACaptureError(
                "L'orologio Moonraker risulta nel futuro: recupero bloccato"
            )
        if age > args.max_age:
            raise PACaptureError(
                f"L'ultima suite completa ha {age:.0f} secondi ed è troppo vecchia"
            )
        identity = calibration_identity(
            cached.text,
            end_offset=cached.suite_end,
        )
        if args.profile_name:
            profile_name = resolve_profile_name(
                identity,
                SpoolmanInventory(url="manual"),
                override=args.profile_name,
            )
        else:
            inventory, _ = first_working_inventory(
                _pa_profile_candidates(args),
                timeout=args.timeout,
            )
            if inventory is None:
                raise PAProfileError("Spoolman non raggiungibile")
            profile_name = resolve_profile_name(identity, inventory)
        report = update_pa_profile(
            target_user_dir,
            profile_name,
            identity,
            cached.suite,
            apply=args.apply,
            manual_profile=bool(args.profile_name),
        )
    except (PrinterInstallError, PACaptureError, PAParseError, PAProfileError) as exc:
        print(f"[BLOCCATO] {exc}")
        return 2

    if args.as_json:
        print(
            json.dumps(
                {
                    "cache": {
                        "completed_at": cached.completed_at,
                        "age_seconds": max(0.0, age),
                    },
                    **report.to_dict(),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        print(
            "U1 Filament Automation — recupero ultima suite PA "
            f"({max(0.0, age):.0f} secondi fa)"
        )
        print("Moonraker: sola lettura; nessun G-code inviato")
        print()
        _print_pa_profile_report(
            report,
            sandbox=bool(args.sandbox_dir),
            apply=args.apply,
        )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "doctor":
        report = run_doctor(
            spoolman_url=args.spoolman_url,
            moonraker_url=args.moonraker_url,
            orca_dir=args.orca_dir,
            nozzle=args.nozzle,
            timeout=args.timeout,
        )
        if args.as_json:
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        else:
            _print_report(report, args.preview_limit)
        return 0 if report.ok else 2

    if args.command == "pa-parse":
        logfile = Path(args.logfile).expanduser()
        try:
            log = logfile.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"[ERRORE] Impossibile leggere il log: {exc}")
            return 2
        try:
            suite = last_complete_suite(log)
        except PAParseError as exc:
            print(f"[ERRORE] {exc}")
            return 2

        if args.as_json:
            print(json.dumps(suite.to_dict(), indent=2, ensure_ascii=False))
            return 0

        print("U1 Filament Automation — lettura PA offline")
        print("Nessun collegamento a stampante, Spoolman o Snapmaker Orca")
        print()
        print("Righe Adaptive PA per Orca (PA, flusso, accelerazione):")
        for result in suite.results:
            print(f"- {result.point}: {result.orca_row()}")
        print()
        print(f"Fallback PA statico (mediana): {suite.static_fallback:.6f}")
        return 0

    if args.command == "gui":
        try:
            config_path = (
                Path(args.config_file).expanduser()
                if args.config_file
                else default_connection_config_path()
            )
            try:
                saved_connections = load_connection_config(config_path)
            except ConfigError as exc:
                print(f"[AVVISO] {exc}")
                print("Aprire la GUI e salvare nuovamente gli indirizzi.")
                saved_connections = None
            moonraker_url = args.moonraker_url or (
                "" if saved_connections is None else saved_connections.moonraker_url
            )
            spoolman_url = args.spoolman_url or (
                "http://127.0.0.1:7912"
                if saved_connections is None
                else saved_connections.spoolman_url
            )
            if moonraker_url:
                moonraker_url = normalize_service_url(moonraker_url, "U1/Moonraker")
            spoolman_url = normalize_service_url(spoolman_url, "Spoolman")
            parsed_moonraker = urlparse(moonraker_url)
            ssh_target = args.ssh_target
            if not ssh_target and parsed_moonraker.hostname:
                ssh_target = f"root@{parsed_moonraker.hostname}"
            return run_gui(
                moonraker_url=moonraker_url,
                spoolman_url=spoolman_url,
                sandbox_dir=Path(args.sandbox_dir),
                orca_dir=args.orca_dir,
                bind=args.bind,
                port=args.port,
                timeout=args.timeout,
                open_browser=not args.no_browser,
                ssh_target=ssh_target,
                ssh_port=args.ssh_port,
                identity_file=args.identity_file,
                monitor_interval=args.sync_interval,
                connection_config_path=config_path,
            )
        except (GUIError, ConfigError) as exc:
            print(f"[BLOCCATO] {exc}")
            return 2

    if args.command in {"printer-check", "printer-install", "printer-restore"}:
        return _run_printer_command(args)

    if args.apply and not args.sandbox_dir and not args.confirm_orca_write:
        print("[BLOCCATO] Scrittura nella cartella reale di Snapmaker Orca non autorizzata.")
        print("Per i test usare --sandbox-dir; nessun profilo reale è stato modificato.")
        return 2

    installations = discover_orca(explicit_dir=args.orca_dir)
    if not installations:
        print("[ERRORE] Cartella filamenti Snapmaker Orca non trovata.")
        return 2
    if len(installations) > 1 and not args.orca_dir:
        print("[ERRORE] Trovate più cartelle Orca; indicare quella desiderata con --orca-dir.")
        return 2

    real_user_dir = installations[0].path
    if args.sandbox_dir:
        sandbox_dir = Path(args.sandbox_dir).expanduser().resolve()
        resolved_real_dir = real_user_dir.resolve()
        overlaps_real_orca = (
            sandbox_dir == resolved_real_dir
            or sandbox_dir in resolved_real_dir.parents
            or resolved_real_dir in sandbox_dir.parents
        )
        if overlaps_real_orca:
            print("[BLOCCATO] La cartella sandbox coincide o si sovrappone a Orca reale.")
            print("Scegliere una cartella separata, per esempio in Downloads.")
            return 2
        target_user_dir = sandbox_dir
    else:
        target_user_dir = real_user_dir
    if args.command == "pa-profile":
        logfile = Path(args.logfile).expanduser()
        try:
            log = logfile.read_text(encoding="utf-8", errors="replace")
            suite, _, suite_end = last_complete_suite_span(log)
            identity = calibration_identity(log, end_offset=suite_end)
            if args.profile_name:
                profile_name = resolve_profile_name(
                    identity,
                    SpoolmanInventory(url="manual"),
                    override=args.profile_name,
                )
            else:
                inventory, _ = first_working_inventory(
                    _pa_profile_candidates(args),
                    timeout=args.timeout,
                )
                if inventory is None:
                    print("[ERRORE] Spoolman non raggiungibile.")
                    return 2
                profile_name = resolve_profile_name(identity, inventory)
            report = update_pa_profile(
                target_user_dir,
                profile_name,
                identity,
                suite,
                apply=args.apply,
                manual_profile=bool(args.profile_name),
            )
        except OSError as exc:
            print(f"[ERRORE] Impossibile leggere il log: {exc}")
            return 2
        except (PAParseError, PAProfileError) as exc:
            print(f"[BLOCCATO] {exc}")
            return 2
        if args.as_json:
            print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        else:
            _print_pa_profile_report(
                report,
                sandbox=bool(args.sandbox_dir),
                apply=args.apply,
            )
        return 0

    if args.command == "pa-auto":
        return _run_pa_auto(args, target_user_dir)

    if args.command == "pa-latest":
        return _run_pa_latest(args, target_user_dir)

    effective_system_dir = (
        Path(args.system_dir).expanduser()
        if args.system_dir
        else default_system_dir(real_user_dir)
    )
    candidates = _sync_candidates(args)

    if args.command == "watch":
        if args.interval < 5:
            print("[ERRORE] --interval deve essere almeno 5 secondi.")
            return 2
        if args.cycles < 0:
            print("[ERRORE] --cycles non può essere negativo.")
            return 2
        if args.as_json and args.cycles == 0:
            print("[ERRORE] Con --json indicare anche --cycles per terminare il comando.")
            return 2
        state_path = (
            Path(args.state_file).expanduser().resolve()
            if args.state_file
            else default_watch_state_path(
                target_user_dir,
                sandbox=bool(args.sandbox_dir),
            )
        )
        try:
            managed_profiles = load_managed_profiles(state_path, target_user_dir)
        except WatchStateError as exc:
            print(f"[BLOCCATO] {exc}")
            return 2
        cycle = 0
        try:
            while True:
                cycle += 1
                inventory, errors = first_working_inventory(
                    candidates,
                    timeout=args.timeout,
                )
                if inventory is None:
                    if args.as_json:
                        print(
                            json.dumps(
                                {"cycle": cycle, "error": "Spoolman non raggiungibile", "details": errors},
                                ensure_ascii=False,
                            )
                        )
                    else:
                        print(f"[ATTENZIONE] Controllo {cycle}: Spoolman non raggiungibile; riprovo.")
                else:
                    report = sync_profiles(
                        inventory,
                        target_user_dir,
                        effective_system_dir,
                        apply=args.apply,
                        ignored_profile_names=managed_profiles,
                    )
                    if args.apply:
                        updated_profiles = (
                            managed_profiles | managed_profiles_from_report(report)
                        )
                        if updated_profiles != managed_profiles:
                            try:
                                save_managed_profiles(
                                    state_path,
                                    target_user_dir,
                                    updated_profiles,
                                )
                            except WatchStateError as exc:
                                print(f"[BLOCCATO] {exc}")
                                return 2
                            managed_profiles = updated_profiles
                    if args.as_json:
                        print(
                            json.dumps(
                                {"cycle": cycle, **report.to_dict()},
                                ensure_ascii=False,
                            )
                        )
                    else:
                        mode = (
                            "AUTOMATICA SANDBOX — profili reali intatti"
                            if args.apply and args.sandbox_dir
                            else "AUTOMATICA REALE CONFERMATA"
                            if args.apply
                            else "AUTOMATICA IN ANTEPRIMA — nessun file scritto"
                        )
                        _print_sync_report(report, mode, cycle=cycle)
                if args.cycles and cycle >= args.cycles:
                    return 0
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nMonitoraggio interrotto; nessun file esistente è stato modificato.")
            return 0

    inventory, _ = first_working_inventory(candidates, timeout=args.timeout)
    if inventory is None:
        print("[ERRORE] Spoolman non raggiungibile.")
        return 2
    report = sync_profiles(
        inventory,
        target_user_dir,
        effective_system_dir,
        apply=args.apply,
    )
    if args.as_json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        return 0

    if args.apply and args.sandbox_dir:
        mode = "SANDBOX — profili reali intatti"
    elif args.apply:
        mode = "APPLICAZIONE REALE CONFERMATA"
    else:
        mode = "ANTEPRIMA — nessun file scritto"
    _print_sync_report(report, mode)
    if not args.apply:
        print("Anteprima completata: nessun file è stato creato o modificato.")
        print("Per un test isolato usare --sandbox-dir insieme a --apply.")
    return 0
