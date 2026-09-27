from __future__ import annotations

import os

from .models import DoctorReport
from .orca import discover_orca
from .profile_audit import compare_previews, scan_profile_names
from .profiles import build_previews
from .spoolman import (
    ServiceError,
    candidates_from_moonraker,
    explicit_candidates,
    first_working_inventory,
)


def run_doctor(
    spoolman_url: str | None = None,
    moonraker_url: str | None = None,
    orca_dir: str | None = None,
    nozzle: float = 0.4,
    timeout: float = 2.0,
) -> DoctorReport:
    report = DoctorReport()
    report.orca = discover_orca(explicit_dir=orca_dir)
    if not report.orca:
        report.warnings.append("Cartella profili Snapmaker Orca non trovata.")

    candidates = explicit_candidates(spoolman_url=spoolman_url)
    effective_moonraker = moonraker_url or os.environ.get("U1FA_MOONRAKER_URL")
    if effective_moonraker:
        try:
            for candidate in candidates_from_moonraker(effective_moonraker, timeout):
                if candidate not in candidates:
                    candidates.append(candidate)
        except (ServiceError, ValueError) as exc:
            report.warnings.append(f"Moonraker non raggiungibile o non leggibile: {exc}")

    report.spoolman_candidates = candidates
    report.spoolman, errors = first_working_inventory(candidates, timeout=timeout)
    if report.spoolman is None:
        report.warnings.append("Nessuna istanza Spoolman raggiungibile.")
        if errors:
            report.warnings.append(f"Tentativi falliti: {len(errors)}")
    else:
        report.previews = build_previews(report.spoolman, nozzle=nozzle)
        if report.orca:
            existing_names, audit_warnings = scan_profile_names(
                item.path for item in report.orca
            )
            report.warnings.extend(audit_warnings)
            report.comparisons = compare_previews(report.previews, existing_names)
    return report
