from app.domain.draft_analysis.section_contrast_rules import detect_section_contrast
from app.domain.draft_analysis.section_parser import ParsedLine, ParsedSection


def _sec(sid: str, label: str | None, start: int, n: int) -> ParsedSection:
    lines = tuple(ParsedLine(start + i, f"line {start + i}") for i in range(n))
    return ParsedSection(
        id=sid, label=label, line_start=start, line_end=start + n - 1, lines=lines
    )


def test_over_similarity_between_verses() -> None:
    sections = [_sec("v1", "verse", 1, 2), _sec("v2", "verse", 5, 2)]
    bag = {"sky", "blue", "road", "long"}
    bags = {"v1": bag, "v2": set(bag)}
    out = detect_section_contrast(sections, bags, {"v1": [], "v2": []})
    assert len(out) == 1
    insight = out[0]
    assert insight.evidence["contrast_kind"] == "over_similarity"
    assert insight.severity == "medium"
    assert insight.target is None  # scope draft


def test_low_variation_between_same_label_sections() -> None:
    sections = [_sec("v1", "verse", 1, 2), _sec("v2", "verse", 5, 2)]
    bags = {"v1": {"sky", "blue", "road"}, "v2": {"fire", "rain", "ash"}}
    out = detect_section_contrast(sections, bags, {"v1": [], "v2": []})
    assert len(out) == 1
    assert out[0].evidence["contrast_kind"] == "low_variation"
    assert out[0].severity == "low"


def test_verse_chorus_pair_only_flags_over_similarity() -> None:
    sections = [_sec("v1", "verse", 1, 2), _sec("c1", "chorus", 5, 2)]
    # disjoint bags would emit low_variation for same-label pairs but not here
    bags = {"v1": {"sky", "blue"}, "c1": {"fire", "rain"}}
    out = detect_section_contrast(sections, bags, {"v1": [], "v2": []})
    assert out == []


def test_skips_bridge() -> None:
    sections = [_sec("v1", "verse", 1, 2), _sec("b1", "bridge", 5, 2)]
    bag = {"sky", "blue", "road"}
    bags = {"v1": bag, "b1": set(bag)}
    out = detect_section_contrast(sections, bags, {"v1": [], "b1": []})
    assert out == []


def test_ending_overlap_attached_when_high() -> None:
    sections = [_sec("v1", "verse", 1, 2), _sec("v2", "verse", 5, 2)]
    bag = {"sky", "blue", "road", "long"}
    bags = {"v1": bag, "v2": set(bag)}
    endings = {"v1": ["night", "light"], "v2": ["night", "light"]}
    out = detect_section_contrast(sections, bags, endings)
    assert "ending_overlap" in out[0].evidence
