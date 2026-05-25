from app.domain.draft_analysis.consistency_rules import (
    detect_perspective_drift,
    detect_tense_drift,
)
from app.domain.draft_analysis.section_parser import ParsedLine, ParsedSection


def _sec(sid: str, label: str | None, n: int = 2) -> ParsedSection:
    lines = tuple(ParsedLine(i, f"line {i}") for i in range(1, n + 1))
    return ParsedSection(id=sid, label=label, line_start=1, line_end=n, lines=lines)


def test_perspective_flip_across_sections() -> None:
    sections = [_sec("v1", "verse"), _sec("c1", "chorus")]
    classifications = {
        "v1": [(1, "first"), (1, "first"), (2, "first"), (2, "first")],
        "c1": [(3, "second"), (3, "second"), (4, "second"), (4, "second")],
    }
    out = detect_perspective_drift(sections, classifications)
    assert len(out) == 1
    insight = out[0]
    assert insight.type == "perspective_drift"
    assert insight.scope == "draft"
    assert insight.evidence["from"] == "first"
    assert insight.evidence["to"] == "second"


def test_no_drift_when_dominance_consistent() -> None:
    sections = [_sec("v1", "verse"), _sec("v2", "verse")]
    same = [(1, "first")] * 4
    out = detect_perspective_drift(sections, {"v1": same, "v2": list(same)})
    assert out == []


def test_internal_mix_flagged() -> None:
    sections = [_sec("v1", "verse")]
    classifications = {
        "v1": [
            (1, "first"), (1, "first"),
            (2, "second"), (2, "second"),
            (3, "third"), (3, "third"),
        ]
    }
    out = detect_perspective_drift(sections, classifications)
    assert any(i.scope == "section" and i.target == "v1" for i in out)


def test_too_few_signals_no_insight() -> None:
    sections = [_sec("v1", "verse"), _sec("v2", "verse")]
    classifications = {
        "v1": [(1, "first")],  # below min
        "v2": [(3, "second"), (3, "second"), (4, "second"), (4, "second")],
    }
    out = detect_perspective_drift(sections, classifications)
    assert out == []  # v1 has no dominant due to insufficient signals


def test_tense_drift_spanish_low_confidence() -> None:
    sections = [_sec("v1", "verse"), _sec("v2", "verse")]
    classifications = {
        "v1": [(1, "present")] * 4,
        "v2": [(3, "past")] * 4,
    }
    out = detect_tense_drift(sections, classifications, language="es")
    assert len(out) == 1
    assert out[0].confidence == "low"


def test_tense_drift_english_medium_confidence() -> None:
    sections = [_sec("v1", "verse"), _sec("v2", "verse")]
    classifications = {
        "v1": [(1, "present")] * 4,
        "v2": [(3, "past")] * 4,
    }
    out = detect_tense_drift(sections, classifications, language="en")
    assert out[0].confidence == "medium"
