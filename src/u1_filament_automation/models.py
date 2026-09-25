from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OrcaInstallation:
    path: Path
    profile_count: int
    source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "profile_count": self.profile_count,
            "source": self.source,
        }


@dataclass(frozen=True)
class SpoolmanInventory:
    url: str
    vendors: list[dict[str, Any]] = field(default_factory=list)
    filaments: list[dict[str, Any]] = field(default_factory=list)
    spools: list[dict[str, Any]] = field(default_factory=list)

    def counts(self) -> dict[str, int]:
        return {
            "vendors": len(self.vendors),
            "filaments": len(self.filaments),
            "spools": len(self.spools),
        }


@dataclass(frozen=True)
class ProfilePreview:
    identity: str
    base_profile: str
    nozzle_profile: str
    spool_ids: tuple[int | str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProfileComparison:
    target: str
    status: str
    exact_matches: tuple[str, ...] = ()
    equivalent_matches: tuple[str, ...] = ()
    similar_matches: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DoctorReport:
    orca: list[OrcaInstallation] = field(default_factory=list)
    spoolman_candidates: list[str] = field(default_factory=list)
    spoolman: SpoolmanInventory | None = None
    previews: list[ProfilePreview] = field(default_factory=list)
    comparisons: list[ProfileComparison] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.orca and self.spoolman)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "safety": {
                "mode": "read-only",
                "orca_writes": 0,
                "spoolman_writes": 0,
                "printer_writes": 0,
            },
            "orca": [item.to_dict() for item in self.orca],
            "spoolman_candidates": self.spoolman_candidates,
            "spoolman": None
            if self.spoolman is None
            else {"url": self.spoolman.url, **self.spoolman.counts()},
            "previews": [item.to_dict() for item in self.previews],
            "comparisons": [item.to_dict() for item in self.comparisons],
            "warnings": self.warnings,
        }
