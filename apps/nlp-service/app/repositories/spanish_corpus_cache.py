"""On-disk cache for SpanishCorpus's wordfreq-derived pronunciation index.

Running rule-based G2P over the wordfreq top-N (default 150k) is the
dominant cost of Spanish startup. That index is a pure function of
(top_n, wordfreq's version, G2P_VERSION), so cache it to disk and skip
recomputation when none of those have changed. Cache misses (including any
read/parse failure) fall back to rebuilding, so a missing or corrupt cache
file is never fatal.
"""

from __future__ import annotations

import importlib.metadata
from pathlib import Path

import orjson

from app.domain.languages.spanish.g2p import G2P_VERSION
from app.models.pronunciation import Pronunciation

_CACHE_DIR = Path(__file__).resolve().parents[2] / ".cache" / "spanish_corpus"


def _wordfreq_version() -> str:
    try:
        return importlib.metadata.version("wordfreq")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _cache_path(top_n: int) -> Path:
    return _CACHE_DIR / f"es_{top_n}_g2p{G2P_VERSION}_wf{_wordfreq_version()}.json"


def load(top_n: int) -> dict[str, tuple[Pronunciation, ...]] | None:
    try:
        raw = _cache_path(top_n).read_bytes()
        data: dict[str, list[list]] = orjson.loads(raw)
        return {
            word: tuple(
                Pronunciation(phonemes=tuple(phonemes), syllables=syllables)
                for phonemes, syllables in prons
            )
            for word, prons in data.items()
        }
    except (OSError, orjson.JSONDecodeError, TypeError, ValueError):
        return None


def save(top_n: int, index: dict[str, tuple[Pronunciation, ...]]) -> None:
    data = {
        word: [[list(p.phonemes), p.syllables] for p in prons]
        for word, prons in index.items()
    }
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _cache_path(top_n).write_bytes(orjson.dumps(data))
    except OSError:
        pass
