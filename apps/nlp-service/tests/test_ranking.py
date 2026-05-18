from app.services.ranking_service import (
    _is_same_stem_inflection,
    _shares_stem,
    score_entries,
)
from app.services.rhyme_index import RhymeEntry


def _entry(word: str, syllables: int = 1, frequency: float = 1e-4) -> RhymeEntry:
    return RhymeEntry(word=word, syllables=syllables, frequency=frequency)


def test_inflection_detected() -> None:
    assert _is_same_stem_inflection("run", "runs")
    assert _is_same_stem_inflection("run", "running")
    assert _is_same_stem_inflection("walk", "walked")
    assert _is_same_stem_inflection("make", "making")
    assert _is_same_stem_inflection("try", "tries")
    assert not _is_same_stem_inflection("run", "rain")
    assert not _is_same_stem_inflection("run", "run")


def test_shares_stem_for_related_words() -> None:
    assert _shares_stem("fire", "fires")
    assert not _shares_stem("fire", "higher")


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
        query_syllables=1,
    )
    words = [c.word for c in ranked]
    assert "fires" in words
    assert words.index("fires") == len(words) - 1


def test_near_score_lower_than_perfect_at_equal_inputs() -> None:
    perfect = score_entries([_entry("higher")], query="fire", rhyme_type="perfect")
    near = score_entries([_entry("higher")], query="fire", rhyme_type="near")
    assert perfect[0].score > near[0].score


def test_syllable_match_bonus_applied() -> None:
    matched = score_entries(
        [_entry("higher", syllables=1)],
        query="fire",
        rhyme_type="perfect",
        query_syllables=1,
    )
    unmatched = score_entries(
        [_entry("higher", syllables=2)],
        query="fire",
        rhyme_type="perfect",
        query_syllables=1,
    )
    assert matched[0].score > unmatched[0].score
