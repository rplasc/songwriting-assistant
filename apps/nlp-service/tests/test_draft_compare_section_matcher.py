from app.domain.draft_compare.section_matcher import match_sections
from app.schemas.draft_analysis import SectionAnalysis


def _sec(sid: str, label: str | None, scheme: str = "AA") -> SectionAnalysis:
    return SectionAnalysis(
        id=sid,
        label=label,
        line_start=1,
        line_end=2,
        line_count=2,
        rhyme_scheme=scheme,
        rhyme_scheme_confidence="full",
        syllable_pattern=[8, 8],
        syllable_variance=0.0,
        cadence_class="consistent",
        repetition_signals=[],
    )


def test_explicit_ids_pair_when_both_sides_supplied() -> None:
    prev = [_sec("v1", "verse"), _sec("c1", "chorus")]
    cur = [_sec("v1", "verse"), _sec("c1", "chorus", scheme="AB")]
    result = match_sections(
        prev,
        cur,
        previous_had_explicit_ids=True,
        current_had_explicit_ids=True,
    )
    assert [(p.id, c.id) for p, c in result.pairs] == [("v1", "v1"), ("c1", "c1")]
    assert not result.unmatched_previous
    assert not result.unmatched_current


def test_label_ordinal_pairing_aligns_through_insertion() -> None:
    prev = [_sec("sec_1", "verse"), _sec("sec_2", "verse")]
    cur = [
        _sec("sec_1", "verse"),
        _sec("sec_2", "bridge"),
        _sec("sec_3", "verse"),
    ]
    result = match_sections(prev, cur)
    paired_labels = {(p.label, c.label) for p, c in result.pairs}
    assert paired_labels == {("verse", "verse")}
    assert len(result.pairs) == 2
    assert [s.label for s in result.unmatched_current] == ["bridge"]
    assert not result.unmatched_previous


def test_unmatched_sections_surface_on_both_sides() -> None:
    prev = [_sec("a", "verse"), _sec("b", "outro")]
    cur = [_sec("a", "verse")]
    result = match_sections(prev, cur)
    assert len(result.pairs) == 1
    assert [s.label for s in result.unmatched_previous] == ["outro"]
    assert not result.unmatched_current
