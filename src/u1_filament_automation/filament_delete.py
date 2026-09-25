from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .models import SpoolmanInventory
from .spoolman import ServiceError, SpoolmanClient
from .sync import make_profile_name
from .watch import WatchStateError, save_managed_profiles


class FilamentDeletionError(ServiceError):
    """Errore distruttivo con stato parziale esplicito."""

    def __init__(
        self,
        message: str,
        *,
        deleted_spool_ids: Iterable[int | str] = (),
        filament_deleted: bool = False,
    ) -> None:
        super().__init__(message)
        self.deleted_spool_ids = tuple(deleted_spool_ids)
        self.filament_deleted = filament_deleted


@dataclass(frozen=True)
class FilamentDeletionCandidate:
    filament_id: int | str
    vendor: str
    material: str
    name: str
    spool_ids: tuple[int | str, ...]
    archived_spool_ids: tuple[int | str, ...]

    @property
    def display_name(self) -> str:
        parts = [self.vendor, self.material, self.name]
        return " ".join(item for item in parts if item).strip() or f"Filamento {self.filament_id}"


@dataclass(frozen=True)
class FilamentDeletionPlan:
    filament_id: int | str
    vendor: str
    material: str
    name: str
    profile_name: str
    spool_ids: tuple[int | str, ...]
    archived_spool_ids: tuple[int | str, ...]
    profile_managed: bool
    delete_orca_profile: bool

    @property
    def display_name(self) -> str:
        parts = [self.vendor, self.material, self.name]
        return " ".join(item for item in parts if item).strip() or f"Filamento {self.filament_id}"

    @property
    def signature(self) -> tuple[str, str, str, str, tuple[str, ...]]:
        return (
            str(self.filament_id),
            self.vendor,
            self.material,
            self.name,
            tuple(sorted(str(item) for item in self.spool_ids)),
        )


@dataclass(frozen=True)
class FilamentDeletionResult:
    plan: FilamentDeletionPlan
    deleted_spool_ids: tuple[int | str, ...]
    filament_deleted: bool
    orca_files_deleted: tuple[str, ...]
    managed_profiles_after: frozenset[str]
    warnings: tuple[str, ...] = ()


def _items(payload: Any, key: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for candidate in ("items", "results", key):
            value = payload.get(candidate)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ServiceError(f"Risposta inattesa dall'endpoint {key}")


def inventory_with_archived_spools(client: SpoolmanClient) -> SpoolmanInventory:
    """Carica anche le bobine archiviate, che bloccano la cancellazione del filamento."""
    inventory = client.inventory()
    payload = client._request("GET", "spool?allow_archived=true")
    return SpoolmanInventory(
        url=inventory.url,
        vendors=inventory.vendors,
        filaments=inventory.filaments,
        spools=_items(payload, "spool"),
    )


def _filament_id_for_spool(spool: dict[str, Any]) -> int | str | None:
    nested = spool.get("filament")
    if isinstance(nested, dict) and nested.get("id") is not None:
        return nested.get("id")
    return spool.get("filament_id")


def _vendor_name(filament: dict[str, Any], inventory: SpoolmanInventory) -> str:
    nested = filament.get("vendor")
    if isinstance(nested, dict):
        return str(nested.get("name") or "").strip()
    vendor_id = filament.get("vendor_id")
    if vendor_id is None:
        return ""
    for vendor in inventory.vendors:
        if str(vendor.get("id")) == str(vendor_id):
            return str(vendor.get("name") or "").strip()
    return ""


def _candidate_from_filament(
    filament: dict[str, Any],
    inventory: SpoolmanInventory,
) -> FilamentDeletionCandidate:
    filament_id = filament.get("id")
    if filament_id is None:
        raise ValueError("Il filamento Spoolman selezionato non ha un ID valido")
    linked = [
        spool
        for spool in inventory.spools
        if str(_filament_id_for_spool(spool)) == str(filament_id)
    ]
    spool_ids = tuple(
        spool["id"] for spool in linked if spool.get("id") is not None
    )
    archived_ids = tuple(
        spool["id"]
        for spool in linked
        if spool.get("id") is not None and bool(spool.get("archived"))
    )
    return FilamentDeletionCandidate(
        filament_id=filament_id,
        vendor=_vendor_name(filament, inventory),
        material=str(filament.get("material") or "").strip(),
        name=str(filament.get("name") or "").strip(),
        spool_ids=spool_ids,
        archived_spool_ids=archived_ids,
    )


def deletion_candidates(inventory: SpoolmanInventory) -> tuple[FilamentDeletionCandidate, ...]:
    result: list[FilamentDeletionCandidate] = []
    for filament in inventory.filaments:
        if filament.get("id") is None:
            continue
        result.append(_candidate_from_filament(filament, inventory))
    result.sort(
        key=lambda item: (
            item.vendor.casefold(),
            item.material.casefold(),
            item.name.casefold(),
            str(item.filament_id),
        )
    )
    return tuple(result)


def plan_filament_deletion(
    inventory: SpoolmanInventory,
    filament_id: int | str,
    managed_profiles: Iterable[str],
    *,
    delete_orca_profile: bool,
) -> FilamentDeletionPlan:
    matches = [
        filament
        for filament in inventory.filaments
        if filament.get("id") is not None and str(filament.get("id")) == str(filament_id)
    ]
    if len(matches) != 1:
        raise ValueError("Filamento Spoolman non trovato o ID ambiguo")
    candidate = _candidate_from_filament(matches[0], inventory)
    profile_name = make_profile_name(candidate.vendor, candidate.material, candidate.name)
    managed = {str(item).casefold() for item in managed_profiles}
    return FilamentDeletionPlan(
        filament_id=candidate.filament_id,
        vendor=candidate.vendor,
        material=candidate.material,
        name=candidate.name,
        profile_name=profile_name,
        spool_ids=candidate.spool_ids,
        archived_spool_ids=candidate.archived_spool_ids,
        profile_managed=profile_name.casefold() in managed,
        delete_orca_profile=bool(delete_orca_profile),
    )


def _managed_orca_files(user_dir: Path, profile_name: str) -> tuple[Path, ...]:
    wanted = {
        f"{profile_name}.json".casefold(),
        f"{profile_name}.info".casefold(),
        f"{profile_name}.json.u1fa-pre181.bak".casefold(),
    }
    try:
        return tuple(
            path
            for path in user_dir.iterdir()
            if path.is_file() and path.name.casefold() in wanted
        )
    except OSError as exc:
        raise ServiceError(f"Cartella profili Orca non leggibile: {user_dir}") from exc


def execute_filament_deletion(
    client: SpoolmanClient,
    expected_plan: FilamentDeletionPlan,
    *,
    real_orca_dir: Path,
    watch_state_path: Path | None,
    managed_profiles: Iterable[str],
) -> FilamentDeletionResult:
    """Esegue bobine -> filamento -> pulizia Orca/watch-state, senza scrivere sulla U1."""
    managed_before = {str(item).casefold() for item in managed_profiles}
    current_inventory = inventory_with_archived_spools(client)
    current_plan = plan_filament_deletion(
        current_inventory,
        expected_plan.filament_id,
        managed_before,
        delete_orca_profile=expected_plan.delete_orca_profile,
    )
    if current_plan.signature != expected_plan.signature:
        raise FilamentDeletionError(
            "Spoolman è cambiato dopo l'anteprima: cancellazione annullata prima di qualsiasi modifica"
        )

    deleted_spools: list[int | str] = []
    for spool_id in current_plan.spool_ids:
        try:
            client._request("DELETE", f"spool/{spool_id}")
        except ServiceError as exc:
            raise FilamentDeletionError(
                f"Cancellazione interrotta eliminando la bobina Spoolman ID {spool_id}: {exc}",
                deleted_spool_ids=deleted_spools,
            ) from exc
        deleted_spools.append(spool_id)

    try:
        client._request("DELETE", f"filament/{current_plan.filament_id}")
    except ServiceError as exc:
        raise FilamentDeletionError(
            f"Le bobine collegate sono state eliminate, ma il filamento Spoolman ID {current_plan.filament_id} non è stato cancellato: {exc}",
            deleted_spool_ids=deleted_spools,
        ) from exc

    warnings: list[str] = []
    deleted_files: list[str] = []
    if current_plan.profile_managed and current_plan.delete_orca_profile:
        try:
            for path in _managed_orca_files(real_orca_dir, current_plan.profile_name):
                try:
                    path.unlink()
                    deleted_files.append(path.name)
                except OSError as exc:
                    warnings.append(f"Profilo Orca non eliminato ({path.name}): {exc}")
        except ServiceError as exc:
            warnings.append(str(exc))

    managed_after = set(managed_before)
    managed_after.discard(current_plan.profile_name.casefold())
    if watch_state_path is not None:
        try:
            save_managed_profiles(watch_state_path, real_orca_dir, managed_after)
        except (WatchStateError, OSError) as exc:
            warnings.append(f"Stato monitor non aggiornato: {exc}")

    return FilamentDeletionResult(
        plan=current_plan,
        deleted_spool_ids=tuple(deleted_spools),
        filament_deleted=True,
        orca_files_deleted=tuple(deleted_files),
        managed_profiles_after=frozenset(managed_after),
        warnings=tuple(warnings),
    )
