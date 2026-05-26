"""Deterministic insight identifiers.

An insight id is a short, stable hash of the insight's identifying
fields: type, scope, target, and an evidence signature drawn from the
typed evidence variant's load-bearing fields. The same draft + options
re-analyzed must yield the same ids so the UI can match insights across
re-runs.
"""

from __future__ import annotations

import hashlib

from app.schemas.evidence import (
    ConsistencyDriftIntroducedEvidence,
    ConsistencyDriftResolvedEvidence,
    MotifAddedEvidence,
    MotifConcentrationEvidence,
    MotifRemovedEvidence,
    MotifStrengthenedEvidence,
    MotifWeakenedEvidence,
    PerspectiveDriftEvidence,
    RepetitionEndingEvidence,
    RepetitionOpeningEvidence,
    RepetitionSignalAddedEvidence,
    RepetitionSignalRemovedEvidence,
    SectionCadenceShiftEvidence,
    SectionContrastEvidence,
    SectionRhymeSchemeShiftEvidence,
    SectionSyllablePatternShiftEvidence,
    SemanticRepetitionEvidence,
    SyllableVarianceEvidence,
    TenseDriftEvidence,
    TypedEvidence,
    WordOveruseEvidence,
)


def evidence_signature(evidence: TypedEvidence | None) -> str:
    if evidence is None:
        return ""
    if isinstance(evidence, SyllableVarianceEvidence):
        return f"syllable_variance|{evidence.cadence_class}|{evidence.variance:.4f}"
    if isinstance(evidence, RepetitionOpeningEvidence):
        return f"repetition_opening|{evidence.phrase}"
    if isinstance(evidence, RepetitionEndingEvidence):
        return f"repetition_ending|{evidence.word}"
    if isinstance(evidence, WordOveruseEvidence):
        return f"word_overuse|{evidence.word}|{evidence.line_count}"
    if isinstance(evidence, SemanticRepetitionEvidence):
        return "semantic_repetition|" + ",".join(sorted(evidence.lemmas))
    if isinstance(evidence, MotifConcentrationEvidence):
        return f"motif|{evidence.motif}|{evidence.section_count}"
    if isinstance(evidence, SectionContrastEvidence):
        a, b = evidence.section_pair
        return (
            f"section_contrast|{a}|{b}|{evidence.contrast_kind}|"
            f"{evidence.jaccard:.3f}"
        )
    if isinstance(evidence, PerspectiveDriftEvidence):
        return (
            f"perspective_drift|{evidence.from_section or ''}|"
            f"{evidence.to_section or ''}|{evidence.section_id or ''}|"
            f"{evidence.from_value or ''}|{evidence.to_value or ''}"
        )
    if isinstance(evidence, TenseDriftEvidence):
        return (
            f"tense_drift|{evidence.from_section or ''}|"
            f"{evidence.to_section or ''}|{evidence.section_id or ''}|"
            f"{evidence.from_value or ''}|{evidence.to_value or ''}"
        )
    # --- M2 compare evidence variants ---
    if isinstance(evidence, MotifAddedEvidence):
        return f"motif_added|{evidence.motif}|{evidence.occurrences}"
    if isinstance(evidence, MotifRemovedEvidence):
        return f"motif_removed|{evidence.motif}|{evidence.previous_occurrences}"
    if isinstance(evidence, MotifStrengthenedEvidence):
        return (
            f"motif_strengthened|{evidence.motif}|"
            f"{evidence.previous}|{evidence.current}"
        )
    if isinstance(evidence, MotifWeakenedEvidence):
        return (
            f"motif_weakened|{evidence.motif}|"
            f"{evidence.previous}|{evidence.current}"
        )
    if isinstance(evidence, RepetitionSignalAddedEvidence):
        return (
            f"repetition_signal_added|{evidence.section_id}|"
            f"{evidence.signal_type}|{evidence.value}"
        )
    if isinstance(evidence, RepetitionSignalRemovedEvidence):
        return (
            f"repetition_signal_removed|{evidence.section_id}|"
            f"{evidence.signal_type}|{evidence.value}"
        )
    if isinstance(evidence, SectionRhymeSchemeShiftEvidence):
        return (
            f"section_rhyme_scheme_shift|{evidence.section_id}|"
            f"{evidence.previous}|{evidence.current}"
        )
    if isinstance(evidence, SectionCadenceShiftEvidence):
        return (
            f"section_cadence_shift|{evidence.section_id}|"
            f"{evidence.previous}|{evidence.current}"
        )
    if isinstance(evidence, SectionSyllablePatternShiftEvidence):
        return (
            f"section_syllable_pattern_shift|{evidence.section_id}|"
            f"{','.join(map(str, evidence.previous))}|"
            f"{','.join(map(str, evidence.current))}"
        )
    if isinstance(evidence, ConsistencyDriftResolvedEvidence):
        return (
            f"consistency_drift_resolved|{evidence.drift_type}|"
            f"{evidence.section_id or ''}"
        )
    if isinstance(evidence, ConsistencyDriftIntroducedEvidence):
        return (
            f"consistency_drift_introduced|{evidence.drift_type}|"
            f"{evidence.section_id or ''}"
        )
    return ""


def make_insight_id(
    *,
    insight_type: str,
    scope: str,
    target: str | None,
    evidence: TypedEvidence | None,
) -> str:
    raw = f"{insight_type}|{scope}|{target or ''}|{evidence_signature(evidence)}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"ins_{digest}"


def make_rhyme_id(*, query: str, language: str, word: str) -> str:
    raw = f"{language}|{query}|{word}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    return f"rhy_{digest}"


__all__ = ["evidence_signature", "make_insight_id", "make_rhyme_id"]
