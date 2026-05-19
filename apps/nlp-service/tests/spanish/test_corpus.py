"""Tests that the Spanish corpus includes PR slang entries."""

import pytest

from app.domain.languages.spanish.data.pr_slang import PR_SLANG
from app.repositories.spanish_corpus import SpanishCorpus


@pytest.fixture(scope="module")
def small_corpus() -> SpanishCorpus:
    # Use a small top-N to keep the test fast; slang is merged separately.
    return SpanishCorpus(top_n=1_000)


_EXPECTED_SLANG = ["perreo", "dembow", "flow", "bregar", "guagua"]


@pytest.mark.parametrize("word", _EXPECTED_SLANG)
def test_slang_word_present_in_corpus(small_corpus: SpanishCorpus, word: str) -> None:
    entries = small_corpus.lookup(word)
    assert entries, f"Slang word {word!r} not found in corpus"
    assert entries[0].phonemes, f"Slang word {word!r} has empty phoneme tuple"


def test_slang_map_frequencies_above_floor() -> None:
    from app.services.rhyme_index import CORPUS_FREQ_FLOOR

    for word, freq in PR_SLANG.items():
        assert freq > CORPUS_FREQ_FLOOR, (
            f"{word!r} frequency {freq} is not above CORPUS_FREQ_FLOOR {CORPUS_FREQ_FLOOR}"
        )


def test_engine_frequency_uses_slang_floor() -> None:
    from app.domain.languages.spanish.engine import SpanishEngine

    engine = SpanishEngine()
    # "perreo" is unlikely to have a high wordfreq value; engine.frequency should
    # return at least the floor defined in PR_SLANG.
    freq = engine.frequency("perreo")
    assert freq >= PR_SLANG["perreo"], (
        f"engine.frequency('perreo') = {freq} is below PR_SLANG floor {PR_SLANG['perreo']}"
    )
