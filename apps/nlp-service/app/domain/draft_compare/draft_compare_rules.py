"""Orchestrator that runs each enabled delta rule module and bundles
the result for the compare service.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.domain.draft_compare.consistency_delta_rules import (
    compute_consistency_deltas,
)
from app.domain.draft_compare.motif_delta_rules import compute_motif_deltas
from app.domain.draft_compare.repetition_delta_rules import (
    compute_repetition_deltas,
)
from app.domain.draft_compare.section_delta_rules import compute_section_deltas
from app.domain.draft_compare.section_matcher import (
    SectionMatchResult,
    match_sections,
)
from app.schemas.draft_analysis import DraftAnalysisResponse, Insight


_COMPARE_FAMILY_FOR_TYPE: dict[str, str] = {
    "motif_added": "added",
    "motif_removed": "removed",
    "motif_strengthened": "strengthened",
    "motif_weakened": "weakened",
    "repetition_signal_added": "added",
    "repetition_signal_removed": "removed",
    "section_rhyme_scheme_shift": "shifted",
    "section_cadence_shift": "shifted",
    "section_syllable_pattern_shift": "shifted",
    "consistency_drift_introduced": "added",
    "consistency_drift_resolved": "removed",
}

_MOTIF_TYPES: frozenset[str] = frozenset(
    {"motif_added", "motif_removed", "motif_strengthened", "motif_weakened"}
)
_REPETITION_TYPES: frozenset[str] = frozenset(
    {"repetition_signal_added", "repetition_signal_removed"}
)
_SECTION_TYPES: frozenset[str] = frozenset(
    {
        "section_rhyme_scheme_shift",
        "section_cadence_shift",
        "section_syllable_pattern_shift",
    }
)
_CONSISTENCY_TYPES: frozenset[str] = frozenset(
    {"consistency_drift_introduced", "consistency_drift_resolved"}
)


@dataclass(frozen=True, slots=True)
class CompareResult:
    insights: list[Insight]
    match: SectionMatchResult
    motif_delta_count: int
    repetition_delta_count: int
    section_delta_count: int
    consistency_delta_count: int
    family_counts: dict[str, int]


def compute_compare(
    previous: DraftAnalysisResponse,
    current: DraftAnalysisResponse,
    *,
    compare_motifs: bool,
    compare_repetition: bool,
    compare_sections: bool,
    compare_consistency: bool,
    previous_had_explicit_ids: bool,
    current_had_explicit_ids: bool,
) -> CompareResult:
    match = match_sections(
        previous.detail.sections,
        current.detail.sections,
        previous_had_explicit_ids=previous_had_explicit_ids,
        current_had_explicit_ids=current_had_explicit_ids,
    )

    insights: list[Insight] = []
    if compare_motifs:
        insights.extend(compute_motif_deltas(previous, current))
    if compare_repetition:
        insights.extend(compute_repetition_deltas(match))
    if compare_sections:
        insights.extend(compute_section_deltas(match))
    if compare_consistency:
        insights.extend(compute_consistency_deltas(previous, current))

    family_counts: Counter[str] = Counter()
    motif_count = 0
    repetition_count = 0
    section_count = 0
    consistency_count = 0
    for ins in insights:
        family = _COMPARE_FAMILY_FOR_TYPE.get(ins.type)
        if family:
            family_counts[family] += 1
        if ins.type in _MOTIF_TYPES:
            motif_count += 1
        elif ins.type in _REPETITION_TYPES:
            repetition_count += 1
        elif ins.type in _SECTION_TYPES:
            section_count += 1
        elif ins.type in _CONSISTENCY_TYPES:
            consistency_count += 1

    return CompareResult(
        insights=insights,
        match=match,
        motif_delta_count=motif_count,
        repetition_delta_count=repetition_count,
        section_delta_count=section_count,
        consistency_delta_count=consistency_count,
        family_counts=dict(family_counts),
    )


__all__ = ["CompareResult", "compute_compare"]
