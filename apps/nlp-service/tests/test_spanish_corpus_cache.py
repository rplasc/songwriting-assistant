"""Tests for SpanishCorpus's on-disk wordfreq index cache (P6)."""

from pathlib import Path

import pytest

from app.models.pronunciation import Pronunciation
from app.repositories import spanish_corpus_cache


@pytest.fixture(autouse=True)
def _isolated_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    cache_dir = tmp_path / "spanish_corpus"
    monkeypatch.setattr(spanish_corpus_cache, "_CACHE_DIR", cache_dir)
    return cache_dir


def test_load_returns_none_when_missing() -> None:
    assert spanish_corpus_cache.load(123) is None


def test_save_and_load_round_trip() -> None:
    index = {
        "amor": (Pronunciation(phonemes=("A1", "M", "O0", "R"), syllables=2),),
        "vida": (Pronunciation(phonemes=("B1", "I0", "D", "A0"), syllables=2),),
    }
    spanish_corpus_cache.save(123, index)
    loaded = spanish_corpus_cache.load(123)
    assert loaded == index


def test_load_returns_none_on_corrupt_file(_isolated_cache_dir: Path) -> None:
    _isolated_cache_dir.mkdir(parents=True, exist_ok=True)
    path = spanish_corpus_cache._cache_path(123)
    path.write_bytes(b"not json")
    assert spanish_corpus_cache.load(123) is None


def test_cache_keyed_by_top_n() -> None:
    index = {"amor": (Pronunciation(phonemes=("A1", "M", "O0", "R"), syllables=2),)}
    spanish_corpus_cache.save(100, index)
    assert spanish_corpus_cache.load(200) is None
    assert spanish_corpus_cache.load(100) == index


def test_spanish_corpus_reuses_cache_on_second_build(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.repositories import spanish_corpus as spanish_corpus_module

    first = spanish_corpus_module.SpanishCorpus(top_n=200)
    assert len(first) > 0

    call_count = 0
    real_g2p = spanish_corpus_module.g2p

    def counting_g2p(word: str):
        nonlocal call_count
        call_count += 1
        return real_g2p(word)

    monkeypatch.setattr(spanish_corpus_module, "g2p", counting_g2p)

    second = spanish_corpus_module.SpanishCorpus(top_n=200)
    assert len(second) == len(first)
    # Only PR_SLANG entries (not already covered by the cached wordfreq
    # index) should hit g2p on the second build.
    assert call_count < len(spanish_corpus_module.PR_SLANG) + 1
