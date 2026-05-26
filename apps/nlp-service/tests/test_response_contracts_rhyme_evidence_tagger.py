from app.domain.response_contracts.rhyme_evidence_tagger import tag_candidate
from app.schemas.responses import RhymeCandidate


def _cand(**kwargs) -> RhymeCandidate:
    defaults = dict(
        word="wire",
        syllables=1,
        rhyme_type="perfect",
        score=0.9,
        rhyme_family="perfect",
        matched_span="wire",
    )
    defaults.update(kwargs)
    return RhymeCandidate(**defaults)


def test_perfect_candidate_high_confidence_and_stressed_ending_tag() -> None:
    tagged = tag_candidate(
        _cand(),
        query="fire",
        language="en",
        target_type="word",
        pronunciations_found=True,
    )
    assert tagged.confidence == "high"
    assert "shared_stressed_ending" in tagged.evidence_tags
    assert tagged.id.startswith("rhy_")


def test_multisyllabic_candidate_tagged_with_key_match() -> None:
    tagged = tag_candidate(
        _cand(rhyme_type="multisyllabic", rhyme_family="multisyllabic"),
        query="wonderful",
        language="en",
        target_type="word",
        pronunciations_found=True,
    )
    assert tagged.confidence == "high"
    assert "multisyllabic_key_match" in tagged.evidence_tags


def test_phrase_ending_adds_phrase_match_tag() -> None:
    tagged = tag_candidate(
        _cand(),
        query="hold me",
        language="en",
        target_type="phrase_ending",
        pronunciations_found=True,
    )
    assert "phrase_ending_match" in tagged.evidence_tags


def test_heuristic_fallback_tag_when_no_pronunciation_found() -> None:
    tagged = tag_candidate(
        _cand(rhyme_type="family", rhyme_family=None),
        query="wundurful",
        language="en",
        target_type="word",
        pronunciations_found=False,
    )
    assert "heuristic_fallback" in tagged.evidence_tags
