"""Spanish pronunciation source.

There is no CMU equivalent for Spanish; we synthesize the corpus at startup
from ``wordfreq``'s top-N most-frequent Spanish tokens by running each
through the rule-based G2P. The result conforms to PronunciationRepository
so the same RhymeIndex builds it.
"""

from __future__ import annotations

from collections.abc import Iterable

from wordfreq import top_n_list

from app.domain.languages.spanish.data.pr_slang import PR_SLANG
from app.domain.languages.spanish.g2p import g2p
from app.domain.languages.spanish.normalization import normalize_word
from app.models.pronunciation import Pronunciation
from app.repositories import spanish_corpus_cache
from app.repositories.pronunciation_repository import PronunciationRepository


class SpanishCorpus(PronunciationRepository):
    def __init__(self, top_n: int = 80_000) -> None:
        index = spanish_corpus_cache.load(top_n)
        if index is None:
            index = self._build_wordfreq_index(top_n)
            spanish_corpus_cache.save(top_n, index)
        else:
            index = dict(index)

        # Merge PR/Reggaetón slang not already covered by the wordfreq top-N.
        # Words already indexed are skipped — wordfreq is the authoritative
        # source for their frequency; the slang map only fills gaps.
        for raw_slang in PR_SLANG:
            norm = normalize_word(raw_slang)
            if norm is None or norm in index:
                continue
            pron = g2p(norm)
            if not pron.phonemes:
                continue
            index[norm] = (pron,)
        self._index = index

    @staticmethod
    def _build_wordfreq_index(top_n: int) -> dict[str, tuple[Pronunciation, ...]]:
        index: dict[str, tuple[Pronunciation, ...]] = {}
        seen: set[str] = set()
        for raw in top_n_list("es", top_n):
            norm = normalize_word(raw)
            if norm is None or norm in seen:
                continue
            seen.add(norm)
            pron = g2p(norm)
            if not pron.phonemes:
                continue
            index[norm] = (pron,)
        return index

    def lookup(self, normalized_word: str) -> tuple[Pronunciation, ...]:
        return self._index.get(normalized_word, ())

    def iter_entries(self) -> Iterable[tuple[str, Pronunciation]]:
        for word, prons in self._index.items():
            for p in prons:
                yield word, p

    def __len__(self) -> int:
        return len(self._index)
