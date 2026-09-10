from __future__ import annotations

import re
import statistics
from dataclasses import asdict, dataclass
from typing import Any


POINT_ORDER = ("low_anchor", "high_flow", "high_force", "stress", "center")
_POINT_RE = re.compile(r"Point:\s*([a-z_]+)\b", re.IGNORECASE)
_XY_RE = re.compile(
    r"accel=([0-9]+(?:\.[0-9]+)?)\s+.*?Q=([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE,
)
_PA_RE = re.compile(
    r"Got pressure advance:\s*([0-9]+(?:\.[0-9]+)?)",
    re.IGNORECASE,
)


class PAParseError(ValueError):
    pass


@dataclass(frozen=True)
class PAResult:
    point: str
    pressure_advance: float
    flow: float
    acceleration: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def orca_row(self) -> str:
        return ",".join(
            (
                _format_number(self.pressure_advance, 6),
                _format_number(self.flow, 6),
                _format_number(self.acceleration, 3),
            )
        )


@dataclass(frozen=True)
class PASuite:
    results: tuple[PAResult, ...]

    @property
    def static_fallback(self) -> float:
        return float(statistics.median(item.pressure_advance for item in self.results))

    def to_dict(self) -> dict[str, Any]:
        return {
            "complete": True,
            "results": [item.to_dict() for item in self.results],
            "orca_rows": [item.orca_row() for item in self.results],
            "static_fallback": self.static_fallback,
        }


@dataclass(frozen=True)
class _LocatedPAResult:
    result: PAResult
    start: int
    end: int


def _format_number(value: float, decimals: int) -> str:
    text = f"{value:.{decimals}f}".rstrip("0").rstrip(".")
    return text if text else "0"


def _parse_pa_results_located(text: str) -> list[_LocatedPAResult]:
    results: list[_LocatedPAResult] = []
    point: str | None = None
    point_start: int | None = None
    flow: float | None = None
    acceleration: float | None = None
    offset = 0

    for line in text.splitlines(keepends=True):
        line_start = offset
        offset += len(line)
        point_match = _POINT_RE.search(line)
        if point_match:
            candidate = point_match.group(1).casefold()
            if candidate in POINT_ORDER:
                point = candidate
                point_start = line_start
                flow = None
                acceleration = None
            continue

        xy_match = _XY_RE.search(line)
        if xy_match and point is not None:
            acceleration = float(xy_match.group(1))
            flow = float(xy_match.group(2))
            continue

        pa_match = _PA_RE.search(line)
        if pa_match:
            if (
                point is None
                or point_start is None
                or flow is None
                or acceleration is None
            ):
                continue
            results.append(
                _LocatedPAResult(
                    result=PAResult(
                        point=point,
                        pressure_advance=float(pa_match.group(1)),
                        flow=flow,
                        acceleration=acceleration,
                    ),
                    start=point_start,
                    end=offset,
                )
            )
            point = None
            point_start = None
            flow = None
            acceleration = None

    return results


def parse_pa_results(text: str) -> list[PAResult]:
    return [item.result for item in _parse_pa_results_located(text)]


def last_complete_suite_span(text: str) -> tuple[PASuite, int, int]:
    parsed = _parse_pa_results_located(text)
    width = len(POINT_ORDER)
    for start in range(len(parsed) - width, -1, -1):
        candidate = parsed[start : start + width]
        if tuple(item.result.point for item in candidate) == POINT_ORDER:
            return (
                PASuite(tuple(item.result for item in candidate)),
                candidate[0].start,
                candidate[-1].end,
            )
    raise PAParseError(
        "Suite PA completa non trovata: servono i cinque punti "
        + ", ".join(POINT_ORDER)
    )


def last_complete_suite(text: str) -> PASuite:
    suite, _, _ = last_complete_suite_span(text)
    return suite
