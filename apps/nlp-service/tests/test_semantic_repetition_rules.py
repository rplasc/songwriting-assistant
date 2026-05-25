from app.domain.draft_analysis.semantic_repetition_rules import (
    detect_semantic_repetition,
)
from app.domain.nlp.phrase_clustering import PhraseCluster, PhraseRef


def _phrase(sid: str, line: int, text: str, lemmas: tuple[str, ...]) -> PhraseRef:
    return PhraseRef(section_id=sid, line_index=line, text=text, lemmas=lemmas)


def test_singleton_cluster_yields_no_insight() -> None:
    cluster = PhraseCluster(
        signature=("hear", "shadow"),
        members=[_phrase("s1", 1, "I hear your shadow", ("hear", "shadow"))],
    )
    assert detect_semantic_repetition([cluster]) == []


def test_pair_in_same_section_is_medium_confidence_section_scope() -> None:
    members = [
        _phrase("s1", 1, "I hear your shadow", ("hear", "shadow")),
        _phrase("s1", 2, "I hear your footsteps", ("hear", "footstep")),
    ]
    cluster = PhraseCluster(signature=("footstep", "hear", "shadow"), members=members)
    out = detect_semantic_repetition([cluster])
    assert len(out) == 1
    insight = out[0]
    assert insight.scope == "section"
    assert insight.target == "s1"
    assert insight.confidence == "medium"
    assert insight.severity == "low"
    assert insight.evidence["phrases"] == [
        "I hear your shadow",
        "I hear your footsteps",
    ]


def test_three_or_more_same_section_is_high_confidence() -> None:
    members = [
        _phrase("s1", i, f"hear thing {i}", ("hear", f"thing{i}"))
        for i in range(1, 4)
    ]
    cluster = PhraseCluster(
        signature=tuple(sorted({"hear", "thing1", "thing2", "thing3"})),
        members=members,
    )
    out = detect_semantic_repetition([cluster])
    assert out[0].confidence == "high"
    assert out[0].severity == "medium"


def test_cross_section_is_draft_scope_low_confidence() -> None:
    members = [
        _phrase("s1", 1, "fire on the hill", ("fire", "hill")),
        _phrase("s2", 5, "fire in the chest", ("fire", "chest")),
    ]
    cluster = PhraseCluster(signature=("chest", "fire", "hill"), members=members)
    out = detect_semantic_repetition([cluster])
    assert out[0].scope == "draft"
    assert out[0].target is None
    assert out[0].confidence == "low"
