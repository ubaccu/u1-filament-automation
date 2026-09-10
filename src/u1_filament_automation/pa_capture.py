from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .pa import PASuite, last_complete_suite_span


class PACaptureError(RuntimeError):
    pass


@dataclass(frozen=True)
class GCodeStoreEntry:
    message: str
    time: float
    type: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CachedPASuite:
    suite: PASuite
    text: str
    suite_end: int
    completed_at: float


def parse_gcode_store(items: Any) -> tuple[GCodeStoreEntry, ...]:
    if not isinstance(items, list):
        raise PACaptureError("Risposta gcode_store non valida: elenco atteso")
    result: list[GCodeStoreEntry] = []
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise PACaptureError(
                f"Risposta gcode_store non valida alla posizione {index}"
            )
        message = item.get("message")
        timestamp = item.get("time")
        message_type = item.get("type", "response")
        if not isinstance(message, str) or not isinstance(
            timestamp, (int, float)
        ):
            raise PACaptureError(
                f"Messaggio gcode_store incompleto alla posizione {index}"
            )
        if message_type not in {"command", "response"}:
            raise PACaptureError(
                f"Tipo gcode_store sconosciuto alla posizione {index}: "
                f"{message_type!r}"
            )
        result.append(
            GCodeStoreEntry(
                message=message,
                time=float(timestamp),
                type=message_type,
            )
        )
    return tuple(result)


def new_gcode_entries(
    previous: tuple[GCodeStoreEntry, ...],
    current: tuple[GCodeStoreEntry, ...],
) -> tuple[GCodeStoreEntry, ...]:
    """Restituisce solo la coda aggiunta, tollerando lo scorrimento FIFO."""
    if current == previous:
        return ()
    if not previous:
        return current
    if not current:
        raise PACaptureError(
            "La cache G-code è stata azzerata durante il monitoraggio; "
            "riavviare il comando prima della prossima calibrazione"
        )

    maximum = min(len(previous), len(current))
    for overlap in range(maximum, 0, -1):
        if previous[-overlap:] == current[:overlap]:
            return current[overlap:]
    raise PACaptureError(
        "Continuità della cache G-code persa: nessun risultato viene applicato"
    )


def response_text(entries: Iterable[GCodeStoreEntry]) -> str:
    return "\n".join(
        entry.message for entry in entries if entry.type == "response"
    )


def latest_cached_suite(entries: Iterable[GCodeStoreEntry]) -> CachedPASuite:
    responses = tuple(entry for entry in entries if entry.type == "response")
    text = response_text(responses)
    suite, _, suite_end = last_complete_suite_span(text)

    position = 0
    completed_at: float | None = None
    for index, entry in enumerate(responses):
        if index:
            position += 1
        position += len(entry.message)
        if position >= suite_end:
            completed_at = entry.time
            break
    if completed_at is None:
        raise PACaptureError(
            "Impossibile determinare l'orario della suite PA in cache"
        )
    return CachedPASuite(
        suite=suite,
        text=text,
        suite_end=suite_end,
        completed_at=completed_at,
    )
