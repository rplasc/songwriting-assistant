"""Build typed evidence + anchors from Phase 5 domain dataclasses.

Each function takes the raw domain insight (and any context the
section provides) and returns a fully-formed ``Insight`` ready for the
response. The service layer dispatches by family.
"""

from __future__ import annotations

from app.domain.draft_analysis.consistency_rules import ConsistencyDriftInsight
from app.domain.draft_analysis.motif_tracker import MotifInsight
from app.domain.draft_analysis.section_contrast_rules import SectionContrastInsight
from app.domain.draft_analysis.section_parser import ParsedSection
from app.domain.draft_analysis.semantic_repetition_rules import (
    SemanticRepetitionInsight,
)
from app.domain.response_contracts.insight_id import make_insight_id
from app.schemas.anchors import InsightAnchor
from app.schemas.draft_analysis import Insight
from app.schemas.evidence import (
    MotifConcentrationEvidence,
    PerspectiveDriftEvidence,
    RepetitionEndingEvidence,
    RepetitionOpeningEvidence,
    SectionContrastEvidence,
    SemanticRepetitionEvidence,
    SyllableVarianceEvidence,
    TenseDriftEvidence,
    TypedEvidence,
    WordOveruseEvidence,
)


def _section_anchor(section: ParsedSection) -> InsightAnchor:
    return InsightAnchor(
        scope="section",
        section_id=section.id,
        line_start=section.line_start,
        line_end=section.line_end,
    )


def _draft_anchor() -> InsightAnchor:
    return InsightAnchor(scope="draft")


def _finalize(
    *,
    insight_type: str,
    scope: str,
    target: str | None,
    severity: str,
    message: str,
    evidence: TypedEvidence | None,
    anchor: InsightAnchor | None,
    confidence: str | None = None,
) -> Insight:
    return Insight(
        id=make_insight_id(
            insight_type=insight_type,
            scope=scope,
            target=target,
            evidence=evidence,
        ),
        type=insight_type,
        scope=scope,  # type: ignore[arg-type]
        target=target,
        severity=severity,  # type: ignore[arg-type]
        message=message,
        evidence=evidence,
        anchor=anchor,
        confidence=confidence,  # type: ignore[arg-type]
    )


def build_syllable_variance_insight(
    section: ParsedSection,
    *,
    variance: float,
    cadence_class: str,
    severity: str,
    message: str,
) -> Insight:
    evidence = SyllableVarianceEvidence(
        variance=round(variance, 4),
        cadence_class=cadence_class,  # type: ignore[arg-type]
    )
    return _finalize(
        insight_type="syllable_variance",
        scope="section",
        target=section.id,
        severity=severity,
        message=message,
        evidence=evidence,
        anchor=_section_anchor(section),
    )


def build_repetition_opening_insight(
    section: ParsedSection,
    *,
    phrase: str,
    severity: str,
    message: str,
) -> Insight:
    evidence = RepetitionOpeningEvidence(phrase=phrase)
    return _finalize(
        insight_type="repetition_opening",
        scope="section",
        target=section.id,
        severity=severity,
        message=message,
        evidence=evidence,
        anchor=_section_anchor(section),
    )


def build_repetition_ending_insight(
    section: ParsedSection,
    *,
    word: str,
    severity: str,
    message: str,
) -> Insight:
    evidence = RepetitionEndingEvidence(word=word)
    return _finalize(
        insight_type="repetition_ending",
        scope="section",
        target=section.id,
        severity=severity,
        message=message,
        evidence=evidence,
        anchor=_section_anchor(section),
    )


def build_word_overuse_insight(
    *,
    word: str,
    line_count: int,
    severity: str,
    message: str,
) -> Insight:
    evidence = WordOveruseEvidence(word=word, line_count=line_count)
    return _finalize(
        insight_type="word_overuse",
        scope="draft",
        target=None,
        severity=severity,
        message=message,
        evidence=evidence,
        anchor=_draft_anchor(),
    )


def build_semantic_repetition_insight(
    raw: SemanticRepetitionInsight,
    sections_by_id: dict[str, ParsedSection],
) -> Insight:
    raw_ev = raw.evidence or {}
    evidence = SemanticRepetitionEvidence(
        lemmas=list(raw_ev.get("lemmas", [])),
        phrases=list(raw_ev.get("phrases", [])),
    )
    anchor: InsightAnchor
    if raw.scope == "section" and raw.target and raw.target in sections_by_id:
        anchor = _section_anchor(sections_by_id[raw.target])
    else:
        anchor = _draft_anchor()
    return _finalize(
        insight_type="semantic_repetition",
        scope=raw.scope,
        target=raw.target,
        severity=raw.severity,
        message=raw.message,
        evidence=evidence,
        anchor=anchor,
        confidence=raw.confidence,
    )


def build_motif_insight(
    raw: MotifInsight,
    sections_by_id: dict[str, ParsedSection],
) -> Insight:
    raw_ev = raw.evidence or {}
    motif = str(raw_ev.get("motif", ""))
    section_count = int(raw_ev.get("section_count", 0) or 0)
    evidence = MotifConcentrationEvidence(motif=motif, section_count=section_count)
    anchor = (
        _section_anchor(sections_by_id[raw.target])
        if raw.target and raw.target in sections_by_id
        else _draft_anchor()
    )
    return _finalize(
        insight_type="motif_concentration",
        scope=raw.scope,
        target=raw.target,
        severity=raw.severity,
        message=raw.message,
        evidence=evidence,
        anchor=anchor,
        confidence=raw.confidence,
    )


def build_section_contrast_insight(
    raw: SectionContrastInsight,
) -> Insight:
    raw_ev = raw.evidence or {}
    pair = raw_ev.get("section_pair") or ["", ""]
    a, b = str(pair[0]), str(pair[1]) if len(pair) > 1 else ""
    jaccard = float(raw_ev.get("jaccard", 0.0))
    shared = [str(x) for x in raw_ev.get("shared_lemmas", [])]
    contrast_kind = str(raw_ev.get("contrast_kind", "over_similarity"))
    ending_overlap = raw_ev.get("ending_overlap")
    evidence = SectionContrastEvidence(
        section_pair=(a, b),
        jaccard=jaccard,
        shared_lemmas=shared,
        contrast_kind=contrast_kind,  # type: ignore[arg-type]
        ending_overlap=float(ending_overlap) if ending_overlap is not None else None,
    )
    return _finalize(
        insight_type="section_contrast",
        scope=raw.scope,
        target=raw.target,
        severity=raw.severity,
        message=raw.message,
        evidence=evidence,
        anchor=_draft_anchor(),
        confidence=raw.confidence,
    )


def build_consistency_insight(
    raw: ConsistencyDriftInsight,
    sections_by_id: dict[str, ParsedSection],
) -> Insight:
    raw_ev = raw.evidence or {}
    counts_raw = raw_ev.get("counts")
    counts = (
        {str(k): int(v) for k, v in counts_raw.items()}
        if isinstance(counts_raw, dict)
        else None
    )
    common = {
        "from_section": (
            str(raw_ev["from_section"]) if "from_section" in raw_ev else None
        ),
        "to_section": (
            str(raw_ev["to_section"]) if "to_section" in raw_ev else None
        ),
        "from_value": str(raw_ev["from"]) if "from" in raw_ev else None,
        "to_value": str(raw_ev["to"]) if "to" in raw_ev else None,
        "counts": counts,
        "section_id": (
            str(raw_ev["section_id"]) if "section_id" in raw_ev else None
        ),
    }
    evidence: TypedEvidence
    if raw.type == "perspective_drift":
        evidence = PerspectiveDriftEvidence(**common)
    else:
        evidence = TenseDriftEvidence(**common)
    anchor = (
        _section_anchor(sections_by_id[raw.target])
        if raw.target and raw.target in sections_by_id
        else _draft_anchor()
    )
    return _finalize(
        insight_type=raw.type,
        scope=raw.scope,
        target=raw.target,
        severity=raw.severity,
        message=raw.message,
        evidence=evidence,
        anchor=anchor,
        confidence=raw.confidence,
    )


__all__ = [
    "build_consistency_insight",
    "build_motif_insight",
    "build_repetition_ending_insight",
    "build_repetition_opening_insight",
    "build_section_contrast_insight",
    "build_semantic_repetition_insight",
    "build_syllable_variance_insight",
    "build_word_overuse_insight",
]
