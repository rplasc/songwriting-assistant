import pytest

from app.domain.languages.english.engine import (
    EnglishEngine,
    _en_is_same_stem_inflection,
)
from app.domain.languages.base import LanguageEngine
from app.services.ranking_service import score_entries
from app.services.rhyme_index import RhymeEntry

_engine = EnglishEngine()


def _entry(
    word: str,
    syllables: int = 1,
    frequency: float = 1e-4,
    multisyllabic_tail_phonemes: int = 0,
) -> RhymeEntry:
    return RhymeEntry(
        word=word,
        syllables=syllables,
        frequency=frequency,
        multisyllabic_tail_phonemes=multisyllabic_tail_phonemes,
    )


def test_inflection_detected() -> None:
    assert _en_is_same_stem_inflection("run", "runs")
    assert _en_is_same_stem_inflection("run", "running")
    assert _en_is_same_stem_inflection("walk", "walked")
    assert _en_is_same_stem_inflection("make", "making")
    assert _en_is_same_stem_inflection("try", "tries")
    assert not _en_is_same_stem_inflection("run", "rain")
    assert not _en_is_same_stem_inflection("run", "run")


def test_engine_inflection_detection_matches_helper() -> None:
    assert _engine.is_same_stem_inflection("run", "runs")
    assert not _engine.is_same_stem_inflection("run", "rain")


def test_shares_stem_for_related_words() -> None:
    assert _engine.shares_stem("fire", "fires")
    assert not _engine.shares_stem("fire", "higher")


def test_english_inflection_forms_cover_common_suffixes() -> None:
    forms = _engine.inflection_forms("walk")
    assert "walked" in forms
    assert "walks" in forms
    assert "walking" in forms
    assert "walk" not in forms


def test_inflection_penalty_applies_to_walked_and_walking() -> None:
    # "talk" is an unrelated perfect rhyme for "walk" and should not be
    # penalised; "walked"/"walking" are inflections and should take the
    # full -0.20 penalty rather than the weaker -0.10 same-stem penalty.
    ranked = score_entries(
        [
            _entry("talk", frequency=1e-4),
            _entry("walked", frequency=1e-4),
            _entry("walking", frequency=1e-4),
        ],
        query="walk",
        rhyme_type="perfect",
        limit=10,
        engine=_engine,
    )
    scores = {c.word: c.score for c in ranked}
    assert scores["talk"] - scores["walked"] == pytest.approx(0.20)
    assert scores["talk"] - scores["walking"] == pytest.approx(0.20)


def test_score_entries_orders_by_score_then_frequency() -> None:
    # "higher" and "buyer" rhyme perfectly with "fire" and aren't related;
    # "fires" is the inflection and should rank last under the penalty.
    ranked = score_entries(
        [
            _entry("higher", syllables=2, frequency=1e-4),
            _entry("buyer", syllables=2, frequency=1e-4),
            _entry("fires", syllables=1, frequency=1e-4),
        ],
        query="fire",
        rhyme_type="perfect",
        limit=10,
        query_syllables=1,
        engine=_engine,
    )
    words = [c.word for c in ranked]
    assert "fires" in words
    assert words.index("fires") == len(words) - 1


def test_near_score_lower_than_perfect_at_equal_inputs() -> None:
    perfect = score_entries(
        [_entry("higher")], query="fire", rhyme_type="perfect", limit=10, engine=_engine
    )
    near = score_entries(
        [_entry("higher")], query="fire", rhyme_type="near", limit=10, engine=_engine
    )
    assert perfect[0].score > near[0].score


def test_family_score_between_perfect_and_near() -> None:
    perfect = score_entries(
        [_entry("higher")], query="fire", rhyme_type="perfect", limit=10, engine=_engine
    )
    family = score_entries(
        [_entry("higher")], query="fire", rhyme_type="family", limit=10, engine=_engine
    )
    near = score_entries(
        [_entry("higher")], query="fire", rhyme_type="near", limit=10, engine=_engine
    )
    assert perfect[0].score > family[0].score > near[0].score


def test_multisyllabic_length_bonus_applied() -> None:
    """A candidate with a long shared stressed tail scores above one
    without when both query and candidate have multisyllabic keys."""
    with_tail = score_entries(
        [_entry("meticulous", syllables=4, multisyllabic_tail_phonemes=7)],
        query="ridiculous",
        rhyme_type="perfect",
        limit=10,
        query_syllables=4,
        query_multisyllabic_len=7,
        engine=_engine,
    )
    without_tail = score_entries(
        [_entry("meticulous", syllables=4, multisyllabic_tail_phonemes=0)],
        query="ridiculous",
        rhyme_type="perfect",
        limit=10,
        query_syllables=4,
        query_multisyllabic_len=7,
        engine=_engine,
    )
    assert with_tail[0].score > without_tail[0].score


def test_multisyllabic_bonus_inert_for_short_queries() -> None:
    """When the query has no multisyllabic key, the bonus must not fire
    even if the candidate has a long tail (otherwise a 'cat' lookup would
    drift toward unrelated multisyllabic candidates)."""
    no_query_len = score_entries(
        [_entry("hat", syllables=1, multisyllabic_tail_phonemes=0)],
        query="cat",
        rhyme_type="perfect",
        limit=10,
        query_syllables=1,
        query_multisyllabic_len=None,
        engine=_engine,
    )
    baseline = score_entries(
        [_entry("hat", syllables=1, multisyllabic_tail_phonemes=0)],
        query="cat",
        rhyme_type="perfect",
        limit=10,
        query_syllables=1,
        engine=_engine,
    )
    assert no_query_len[0].score == baseline[0].score


def test_syllable_match_bonus_applied() -> None:
    matched = score_entries(
        [_entry("higher", syllables=1)],
        query="fire",
        rhyme_type="perfect",
        limit=10,
        query_syllables=1,
        engine=_engine,
    )
    unmatched = score_entries(
        [_entry("higher", syllables=2)],
        query="fire",
        rhyme_type="perfect",
        limit=10,
        query_syllables=1,
        engine=_engine,
    )
    assert matched[0].score > unmatched[0].score
