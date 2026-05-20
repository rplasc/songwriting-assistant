"""Compare line syllable counts within a section.

The thresholds are deliberately coarse — Phase 4 cadence guidance is
pattern-visibility, not musical-meter detection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

CadenceClass = Literal["consistent", "mixed", "varied"]
Severity = Literal["info", "low", "medium"]


@dataclass(frozen=True, slots=True)
class CadenceSummary:
    counts: tuple[int, ...]
    variance: float  # population stdev rounded to 1 dp
    cadence_class: CadenceClass
    severity: Severity
    message: str


def classify_pattern(counts: list[int], label: str | None = None) -> CadenceSummary:
    counts_t = tuple(counts)
    if len(counts_t) <= 1:
        return CadenceSummary(
            counts=counts_t,
            variance=0.0,
            cadence_class="consistent",
            severity="low",
            message=_message_for("consistent", label),
        )

    mean = sum(counts_t) / len(counts_t)
    stdev = math.sqrt(sum((c - mean) ** 2 for c in counts_t) / len(counts_t))
    variance = round(stdev, 1)
    spread = max(counts_t) - min(counts_t)

    if stdev <= 1.0 and spread <= 2:
        klass: CadenceClass = "consistent"
        severity: Severity = "low"
    elif stdev >= 2.5:
        klass = "varied"
        severity = "medium"
    else:
        klass = "mixed"
        severity = "info"

    return CadenceSummary(
        counts=counts_t,
        variance=variance,
        cadence_class=klass,
        severity=severity,
        message=_message_for(klass, label),
    )


def _message_for(klass: CadenceClass, label: str | None) -> str:
    where = f"{label.capitalize()} " if label else "Section "
    if klass == "consistent":
        return f"{where}line lengths are consistent."
    if klass == "varied":
        return f"{where}line lengths vary widely."
    return f"{where}line lengths are mixed."


__all__ = ["CadenceSummary", "classify_pattern"]
