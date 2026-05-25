from app.domain.draft_analysis.hook_demotion import demote_inside_hooks
from app.domain.draft_analysis.section_parser import ParsedLine, ParsedSection
from app.schemas.draft_analysis import Insight


def _sec(sid: str, label: str | None) -> ParsedSection:
    line = ParsedLine(1, "x")
    return ParsedSection(id=sid, label=label, line_start=1, line_end=1, lines=(line,))


def _insight(
    type_: str, target: str | None, severity: str, scope: str = "section"
) -> Insight:
    return Insight(
        type=type_, scope=scope, target=target, severity=severity, message="m"
    )


def test_semantic_repetition_in_chorus_demoted() -> None:
    sections = [_sec("v1", "verse"), _sec("c1", "chorus")]
    ins = [_insight("semantic_repetition", "c1", "medium")]
    out = demote_inside_hooks(ins, sections)
    assert out[0].severity == "low"
    assert out[0].evidence == {"hook_context": True}


def test_semantic_repetition_in_verse_left_alone() -> None:
    sections = [_sec("v1", "verse"), _sec("c1", "chorus")]
    ins = [_insight("semantic_repetition", "v1", "medium")]
    out = demote_inside_hooks(ins, sections)
    assert out[0].severity == "medium"
    assert out[0].evidence is None


def test_word_overuse_demoted_only_when_words_hook_only() -> None:
    sections = [_sec("c1", "chorus"), _sec("v1", "verse")]
    overuse = Insight(
        type="word_overuse",
        scope="draft",
        target=None,
        severity="medium",
        message='"fire" appears on 4 lines.',
    )
    # No hook-only set: stays at medium.
    out = demote_inside_hooks([overuse], sections, hook_only_overuse_words=frozenset())
    assert out[0].severity == "medium"
    # With hook-only: demoted.
    out = demote_inside_hooks(
        [overuse], sections, hook_only_overuse_words=frozenset({"fire"})
    )
    assert out[0].severity == "low"
    assert out[0].evidence == {"hook_context": True}


def test_unrelated_type_untouched() -> None:
    sections = [_sec("c1", "chorus")]
    ins = [_insight("syllable_variance", "c1", "high")]
    out = demote_inside_hooks(ins, sections)
    assert out[0].severity == "high"


def test_severity_floor_at_info() -> None:
    sections = [_sec("c1", "chorus")]
    ins = [_insight("repetition_ending", "c1", "low")]
    out = demote_inside_hooks(ins, sections)
    assert out[0].severity == "info"
