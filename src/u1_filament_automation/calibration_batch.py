from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable


class CalibrationBatchError(ValueError):
    pass


@dataclass(frozen=True)
class CalibrationBatchItem:
    profile_name: str
    physical_slot: int
    temperature: int


@dataclass(frozen=True)
class CalibrationBatchPlan:
    items: tuple[CalibrationBatchItem, ...]

    @property
    def count(self) -> int:
        return len(self.items)


@dataclass(frozen=True)
class CalibrationBatchResult:
    completed: tuple[CalibrationBatchItem, ...]
    failed_item: CalibrationBatchItem | None = None
    error: str = ""

    @property
    def ok(self) -> bool:
        return self.failed_item is None


def _validate_item(item: CalibrationBatchItem) -> CalibrationBatchItem:
    profile = item.profile_name.strip()
    if not profile:
        raise CalibrationBatchError("Il profilo della bobina non può essere vuoto")
    if item.physical_slot not in {1, 2, 3, 4}:
        raise CalibrationBatchError("Lo slot fisico deve essere compreso tra 1 e 4")
    if item.temperature < 170 or item.temperature > 300:
        raise CalibrationBatchError("La temperatura deve essere compresa tra 170 e 300 °C")
    return CalibrationBatchItem(profile, item.physical_slot, item.temperature)


def build_calibration_batch(
    items: Iterable[CalibrationBatchItem],
) -> CalibrationBatchPlan:
    """Build a safe 1-4 spool sequential calibration plan.

    This module deliberately contains no Moonraker, G-code, Spoolman or slicer
    write operations. It only validates the queue foundation.
    """

    normalized = tuple(_validate_item(item) for item in items)
    if not normalized:
        raise CalibrationBatchError("Selezionare almeno una bobina")
    if len(normalized) > 4:
        raise CalibrationBatchError("La coda può contenere al massimo 4 bobine")

    slots = [item.physical_slot for item in normalized]
    if len(set(slots)) != len(slots):
        raise CalibrationBatchError("Ogni bobina deve usare uno slot fisico diverso")

    names = [item.profile_name.casefold() for item in normalized]
    if len(set(names)) != len(names):
        raise CalibrationBatchError("Ogni bobina deve usare un profilo diverso")

    return CalibrationBatchPlan(normalized)


def run_calibration_batch(
    plan: CalibrationBatchPlan,
    runner: Callable[[CalibrationBatchItem], None],
) -> CalibrationBatchResult:
    """Run items sequentially and stop immediately at the first failure."""

    completed: list[CalibrationBatchItem] = []
    for item in plan.items:
        try:
            runner(item)
        except Exception as exc:  # caller owns the concrete execution layer
            return CalibrationBatchResult(
                completed=tuple(completed),
                failed_item=item,
                error=str(exc),
            )
        completed.append(item)
    return CalibrationBatchResult(completed=tuple(completed))
