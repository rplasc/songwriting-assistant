from app.domain.response_contracts.insight_id import (
    evidence_signature,
    make_insight_id,
    make_rhyme_id,
)
from app.schemas.evidence import (
    SemanticRepetitionEvidence,
    SyllableVarianceEvidence,
    WordOveruseEvidence,
)


def test_insight_id_is_deterministic() -> None:
    ev = WordOveruseEvidence(word="fire", line_count=4)
    a = make_insight_id(
        insight_type="word_overuse", scope="draft", target=None, evidence=ev
    )
    b = make_insight_id(
        insight_type="word_overuse", scope="draft", target=None, evidence=ev
    )
    assert a == b
    assert a.startswith("ins_")


def test_insight_id_changes_with_evidence() -> None:
    a = make_insight_id(
        insight_type="word_overuse",
        scope="draft",
        target=None,
        evidence=WordOveruseEvidence(word="fire", line_count=4),
    )
    b = make_insight_id(
        insight_type="word_overuse",
        scope="draft",
        target=None,
        evidence=WordOveruseEvidence(word="rain", line_count=4),
    )
    assert a != b


def test_evidence_signature_for_syllable_variance() -> None:
    sig = evidence_signature(
        SyllableVarianceEvidence(variance=1.25, cadence_class="mixed")
    )
    assert "syllable_variance" in sig
    assert "mixed" in sig


def test_evidence_signature_semantic_repetition_is_lemma_order_stable() -> None:
    a = evidence_signature(
        SemanticRepetitionEvidence(lemmas=["b", "a"], phrases=["x", "y"])
    )
    b = evidence_signature(
        SemanticRepetitionEvidence(lemmas=["a", "b"], phrases=["x", "y"])
    )
    assert a == b


def test_rhyme_id_is_stable() -> None:
    a = make_rhyme_id(query="fire", language="en", word="wire")
    b = make_rhyme_id(query="fire", language="en", word="wire")
    assert a == b
    assert a.startswith("rhy_")
    c = make_rhyme_id(query="fire", language="en", word="liar")
    assert a != c
