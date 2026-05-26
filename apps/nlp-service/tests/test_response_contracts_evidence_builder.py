from app.domain.draft_analysis.motif_tracker import MotifInsight
from app.domain.draft_analysis.section_contrast_rules import SectionContrastInsight
from app.domain.draft_analysis.section_parser import ParsedLine, ParsedSection
from app.domain.draft_analysis.semantic_repetition_rules import (
    SemanticRepetitionInsight,
)
from app.domain.response_contracts.evidence_anchor_builder import (
    build_motif_insight,
    build_section_contrast_insight,
    build_semantic_repetition_insight,
    build_word_overuse_insight,
)


def _sec(sid: str, label: str | None = None) -> ParsedSection:
    line = ParsedLine(1, "x")
    return ParsedSection(id=sid, label=label, line_start=1, line_end=2, lines=(line,))


def test_word_overuse_insight_has_typed_evidence_and_draft_anchor() -> None:
    ins = build_word_overuse_insight(
        word="fire", line_count=4, severity="medium", message="m"
    )
    assert ins.evidence is not None and ins.evidence.kind == "word_overuse"
    assert ins.evidence.word == "fire"
    assert ins.anchor is not None
    assert ins.anchor.scope == "draft"
    assert ins.id.startswith("ins_")


def test_motif_insight_evidence_is_typed_and_anchor_is_sectional() -> None:
    raw = MotifInsight(
        type="motif_concentration",
        scope="section",
        target="v1",
        severity="low",
        confidence="medium",
        message="m",
        evidence={"motif": "fire", "section_count": "3"},
    )
    sections_by_id = {"v1": _sec("v1", "verse")}
    ins = build_motif_insight(raw, sections_by_id)
    assert ins.evidence is not None
    assert ins.evidence.kind == "motif_concentration"
    assert ins.evidence.motif == "fire"
    assert ins.evidence.section_count == 3
    assert ins.anchor is not None and ins.anchor.section_id == "v1"


def test_section_contrast_evidence_carries_typed_pair_and_kind() -> None:
    raw = SectionContrastInsight(
        type="section_contrast",
        scope="draft",
        target=None,
        severity="medium",
        confidence="medium",
        message="m",
        evidence={
            "section_pair": ["v1", "v2"],
            "jaccard": 0.9,
            "shared_lemmas": ["fire", "rain"],
            "contrast_kind": "over_similarity",
            "ending_overlap": 0.5,
        },
    )
    ins = build_section_contrast_insight(raw)
    assert ins.evidence is not None
    assert ins.evidence.kind == "section_contrast"
    assert ins.evidence.section_pair == ("v1", "v2")
    assert ins.evidence.contrast_kind == "over_similarity"
    assert ins.evidence.ending_overlap == 0.5


def test_semantic_repetition_anchor_is_draft_when_no_target() -> None:
    raw = SemanticRepetitionInsight(
        type="semantic_repetition",
        scope="draft",
        target=None,
        severity="low",
        confidence="low",
        message="m",
        evidence={"phrases": ["a", "b"], "lemmas": ["fire"]},
    )
    ins = build_semantic_repetition_insight(raw, {})
    assert ins.anchor is not None
    assert ins.anchor.scope == "draft"
    assert ins.evidence is not None
    assert ins.evidence.lemmas == ["fire"]
