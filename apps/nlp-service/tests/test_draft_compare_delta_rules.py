"""Unit tests for the four delta-rule modules.

Builds synthetic ``DraftAnalysisResponse`` objects directly (rather
than going through the full analysis pipeline) so each rule can be
exercised in isolation.
"""

from __future__ import annotations

from app.domain.draft_compare.consistency_delta_rules import (
    compute_consistency_deltas,
)
from app.domain.draft_compare.motif_delta_rules import compute_motif_deltas
from app.domain.draft_compare.repetition_delta_rules import (
    compute_repetition_deltas,
)
from app.domain.draft_compare.section_delta_rules import compute_section_deltas
from app.domain.draft_compare.section_matcher import match_sections
from app.domain.response_contracts.capability_reason_mapper import (
    base_capabilities,
)
from app.schemas.anchors import InsightAnchor
from app.schemas.draft_analysis import (
    DraftAnalysisResponse,
    DraftDetail,
    DraftSummary,
    Insight,
    RepetitionSignal,
    SectionAnalysis,
)
from app.schemas.evidence import (
    MotifConcentrationEvidence,
    PerspectiveDriftEvidence,
)


def _sec(
    sid: str,
    label: str | None,
    *,
    scheme: str = "AA",
    cadence: str = "consistent",
    pattern: list[int] | None = None,
    signals: list[tuple[str, str]] | None = None,
) -> SectionAnalysis:
    return SectionAnalysis(
        id=sid,
        label=label,
        line_start=1,
        line_end=2,
        line_count=2,
        rhyme_scheme=scheme,
        rhyme_scheme_confidence="full",
        syllable_pattern=pattern or [8, 8],
        syllable_variance=0.0,
        cadence_class=cadence,  # type: ignore[arg-type]
        repetition_signals=[
            RepetitionSignal(type=t, value=v) for t, v in (signals or [])
        ],
    )


def _response(
    *,
    sections: list[SectionAnalysis],
    motifs: list[str] | None = None,
    insights: list[Insight] | None = None,
) -> DraftAnalysisResponse:
    return DraftAnalysisResponse(
        language="en",
        title=None,
        capabilities=base_capabilities("en"),
        summary=DraftSummary(
            section_count=len(sections),
            line_count=sum(s.line_count for s in sections),
            total_syllables=0,
            notable_patterns=[],
            motifs=motifs or [],
        ),
        insights=insights or [],
        detail=DraftDetail(sections=sections),
    )


# --- motif deltas ---


def test_motif_added_when_new_motif_appears() -> None:
    prev = _response(sections=[_sec("a", "verse")])
    cur = _response(sections=[_sec("a", "verse")], motifs=["fire"])
    out = compute_motif_deltas(prev, cur)
    assert [i.type for i in out] == ["motif_added"]
    assert out[0].evidence.kind == "motif_added"
    assert out[0].evidence.motif == "fire"


def test_motif_removed_when_motif_disappears() -> None:
    prev = _response(sections=[_sec("a", "verse")], motifs=["fire"])
    cur = _response(sections=[_sec("a", "verse")])
    out = compute_motif_deltas(prev, cur)
    assert [i.type for i in out] == ["motif_removed"]


def test_motif_strengthened_uses_concentration_evidence() -> None:
    section = _sec("a", "verse")
    motif_insight_prev = Insight(
        id="ins_a",
        type="motif_concentration",
        scope="section",
        target="a",
        severity="low",
        message="x",
        evidence=MotifConcentrationEvidence(motif="fire", section_count=3),
        anchor=InsightAnchor(scope="section", section_id="a", line_start=1, line_end=2),
        confidence="medium",
    )
    motif_insight_cur = motif_insight_prev.model_copy(
        update={"evidence": MotifConcentrationEvidence(motif="fire", section_count=5)}
    )
    prev = _response(
        sections=[section], motifs=["fire"], insights=[motif_insight_prev]
    )
    cur = _response(
        sections=[section], motifs=["fire"], insights=[motif_insight_cur]
    )
    out = compute_motif_deltas(prev, cur)
    assert [i.type for i in out] == ["motif_strengthened"]
    assert out[0].evidence.previous == 3
    assert out[0].evidence.current == 5


# --- repetition deltas ---


def test_repetition_signal_added_emits_per_signal() -> None:
    prev = _response(sections=[_sec("a", "verse")])
    cur = _response(
        sections=[
            _sec("a", "verse", signals=[("opening_phrase_repeat", "hold me")])
        ]
    )
    match = match_sections(prev.detail.sections, cur.detail.sections)
    out = compute_repetition_deltas(match)
    assert [i.type for i in out] == ["repetition_signal_added"]
    assert out[0].evidence.signal_type == "opening_phrase_repeat"
    assert out[0].evidence.value == "hold me"
    assert out[0].anchor.scope == "section"


def test_repetition_signal_removed_emits_per_signal() -> None:
    prev = _response(
        sections=[
            _sec("a", "verse", signals=[("ending_word_repeat", "tonight")])
        ]
    )
    cur = _response(sections=[_sec("a", "verse")])
    match = match_sections(prev.detail.sections, cur.detail.sections)
    out = compute_repetition_deltas(match)
    assert [i.type for i in out] == ["repetition_signal_removed"]


# --- section deltas ---


def test_section_rhyme_scheme_shift_detected() -> None:
    prev = _response(sections=[_sec("a", "verse", scheme="AA")])
    cur = _response(sections=[_sec("a", "verse", scheme="AB")])
    match = match_sections(prev.detail.sections, cur.detail.sections)
    out = compute_section_deltas(match)
    types = {i.type for i in out}
    assert "section_rhyme_scheme_shift" in types


def test_section_cadence_shift_detected() -> None:
    prev = _response(sections=[_sec("a", "verse", cadence="consistent")])
    cur = _response(sections=[_sec("a", "verse", cadence="mixed")])
    match = match_sections(prev.detail.sections, cur.detail.sections)
    out = compute_section_deltas(match)
    assert any(i.type == "section_cadence_shift" for i in out)


def test_syllable_pattern_shift_suppressed_for_one_syllable_wobble() -> None:
    prev = _response(sections=[_sec("a", "verse", pattern=[8, 8])])
    cur = _response(sections=[_sec("a", "verse", pattern=[8, 9])])
    match = match_sections(prev.detail.sections, cur.detail.sections)
    out = compute_section_deltas(match)
    assert not any(i.type == "section_syllable_pattern_shift" for i in out)


def test_syllable_pattern_shift_emitted_for_large_delta() -> None:
    prev = _response(sections=[_sec("a", "verse", pattern=[8, 8])])
    cur = _response(sections=[_sec("a", "verse", pattern=[8, 12])])
    match = match_sections(prev.detail.sections, cur.detail.sections)
    out = compute_section_deltas(match)
    pattern_shifts = [i for i in out if i.type == "section_syllable_pattern_shift"]
    assert len(pattern_shifts) == 1
    assert pattern_shifts[0].evidence.delta == [0, 4]


# --- consistency deltas ---


def _drift_insight(target: str | None = None) -> Insight:
    return Insight(
        id="ins_drift",
        type="perspective_drift",
        scope="section" if target else "draft",
        target=target,
        severity="low",
        message="x",
        evidence=PerspectiveDriftEvidence(section_id=target),
        anchor=InsightAnchor(scope="draft"),
        confidence="medium",
    )


def test_consistency_drift_resolved_when_drift_disappears() -> None:
    prev = _response(sections=[], insights=[_drift_insight("a")])
    cur = _response(sections=[])
    out = compute_consistency_deltas(prev, cur)
    assert [i.type for i in out] == ["consistency_drift_resolved"]


def test_consistency_drift_introduced_when_drift_appears() -> None:
    prev = _response(sections=[])
    cur = _response(sections=[], insights=[_drift_insight("a")])
    out = compute_consistency_deltas(prev, cur)
    assert [i.type for i in out] == ["consistency_drift_introduced"]
