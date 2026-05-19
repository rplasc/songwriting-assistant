from dataclasses import dataclass
from functools import lru_cache

from app.domain.heuristic_g2p import heuristic_phoneme_tails
from app.repositories.pronunciation_repository import PronunciationRepository
from app.schemas.responses import RhymeCandidate
from app.services.pronunciation_service import PronunciationService
from app.services.ranking_service import score_entries
from app.services.rhyme_index import RhymeIndex
from app.services.syllable_service import SyllableService

_PERFECT_REASON = "shared stressed ending"
_FAMILY_REASON = "shared trailing syllable"
_NEAR_REASON = "shared vowel with similar consonants"

_REASON_BY_TYPE: dict[str, str] = {
    "perfect": _PERFECT_REASON,
    "family": _FAMILY_REASON,
    "near": _NEAR_REASON,
}

_CACHE_SIZE = 1024


@dataclass(frozen=True, slots=True)
class _RankedEntry:
    """Scored, ranked candidate stored in the LRU cache.

    Kept separate from RhymeCandidate so include_metadata (which only affects
    the match_reason field) is applied after retrieval rather than baked into
    the cache key.
    """

    word: str
    syllables: int
    rhyme_type: str
    score: float


class RhymeService:
    def __init__(
        self,
        repository: PronunciationRepository,
        index: RhymeIndex,
        pronunciation_service: PronunciationService,
        syllable_service: SyllableService,
    ) -> None:
        self._repository = repository
        self._index = index
        self._pronunciation = pronunciation_service
        self._syllables = syllable_service
        # lru_cache on a closure binds to this instance; one cache per service
        # singleton, garbage-collected with it. The corpus is read-only after
        # startup, so no invalidation is needed.
        # include_metadata is intentionally excluded from the key — it only
        # controls match_reason formatting, which is applied in find_rhymes.
        self._cached_candidates = lru_cache(maxsize=_CACHE_SIZE)(
            self._compute_candidates
        )

    def find_rhymes(
        self,
        word: str,
        limit: int,
        *,
        mode: str = "perfect",
        include_metadata: bool = False,
    ) -> tuple[str | None, bool, list[RhymeCandidate]]:
        """Return (normalized_word, pronunciations_found, ranked rhyme candidates).

        Cached on (normalized, limit, mode). Songwriting editing re-queries the
        same line-end word on every keystroke, so this is the dominant hot-path win.
        """
        normalized, prons = self._pronunciation.lookup(word)
        if not normalized:
            return None, False, []
        cached = self._cached_candidates(normalized, limit, mode)
        # pronunciations_found is True for two distinct cases: (a) the word is in
        # the CMU dictionary, or (b) the heuristic spelling rules produced usable
        # candidates. Clients that need to distinguish these quality levels should
        # inspect the token-level `source` field on LineAnalysisResponse instead,
        # which already carries "dictionary" | "heuristic".
        found = bool(prons) or bool(cached)
        return normalized, found, [
            RhymeCandidate(
                word=e.word,
                syllables=e.syllables,
                rhyme_type=e.rhyme_type,
                score=e.score,
                match_reason=_REASON_BY_TYPE[e.rhyme_type] if include_metadata else None,
            )
            for e in cached
        ]

    def _compute_candidates(
        self,
        normalized: str,
        limit: int,
        mode: str,
    ) -> tuple[_RankedEntry, ...]:
        # Pronunciations are re-looked-up here (vs threaded through from
        # find_rhymes) so this method's signature is fully hashable for the
        # LRU cache. The lookup is a dict access — negligible.
        prons = self._pronunciation.lookup(normalized)[1]
        if not prons:
            return self._heuristic_candidates(normalized, limit)
        phonemes_list = [p.phonemes for p in prons]
        query_syllables = prons[0].syllables

        if mode == "near":
            near_keys = self._index.near_keys_for_phonemes(phonemes_list)
            near_words = self._index.words_for_near_keys(near_keys, exclude=normalized)
            perfect_keys = self._index.perfect_keys_for_phonemes(phonemes_list)
            family_keys = self._index.family_keys_for_phonemes(phonemes_list)
            perfect_words = self._index.words_for_perfect_keys(
                perfect_keys, exclude=normalized
            )
            family_words = self._index.words_for_family_keys(
                family_keys, exclude=normalized
            )
            candidate_words = near_words - perfect_words - family_words
            scored = score_entries(
                self._index.entries_for(candidate_words),
                query=normalized,
                rhyme_type="near",
                limit=limit,
                query_syllables=query_syllables,
            )
            return tuple(
                _RankedEntry(
                    word=c.word,
                    syllables=c.syllables,
                    rhyme_type="near",
                    score=round(c.score, 4),
                )
                for c in scored
            )

        # mode == "perfect" — tiered cascade.
        perfect_keys = self._index.perfect_keys_for_phonemes(phonemes_list)
        family_keys = self._index.family_keys_for_phonemes(phonemes_list)
        near_keys = self._index.near_keys_for_phonemes(phonemes_list)

        perfect_words = self._index.words_for_perfect_keys(
            perfect_keys, exclude=normalized
        )
        family_words = (
            self._index.words_for_family_keys(family_keys, exclude=normalized)
            - perfect_words
        )
        near_words = (
            self._index.words_for_near_keys(near_keys, exclude=normalized)
            - perfect_words
            - family_words
        )

        results: list[_RankedEntry] = []
        for tier, words in (
            ("perfect", perfect_words),
            ("family", family_words),
            ("near", near_words),
        ):
            remaining = limit - len(results)
            if remaining <= 0:
                break
            if not words:
                continue
            scored = score_entries(
                self._index.entries_for(words),
                query=normalized,
                rhyme_type=tier,
                limit=remaining,
                query_syllables=query_syllables,
            )
            results.extend(
                _RankedEntry(
                    word=c.word,
                    syllables=c.syllables,
                    rhyme_type=tier,
                    score=round(c.score, 4),
                )
                for c in scored
            )

        return tuple(results)

    def _heuristic_candidates(
        self, normalized: str, limit: int
    ) -> tuple[_RankedEntry, ...]:
        """Fallback path for words missing from CMU dict.

        Derives candidate ARPABET tails from English spelling, queries the
        perfect and family phoneme indexes for any match, and tags every
        result as ``family`` to signal the approximate match. Mode is ignored.

        The near index is intentionally *not* consulted here — its manner-class
        keys are too coarse for spelling-derived tails and pollute results
        with words that share only a fricative or liquid in the same position.
        """
        tails = heuristic_phoneme_tails(normalized)
        if not tails:
            return ()
        perfect_keys = self._index.perfect_keys_for_phonemes(tails)
        family_keys = self._index.family_keys_for_phonemes(tails)
        words = self._index.words_for_perfect_keys(
            perfect_keys, exclude=normalized
        ) | self._index.words_for_family_keys(family_keys, exclude=normalized)
        if not words:
            return ()
        # Use the heuristic syllable count as the query length signal — pulls
        # multi-syllable matches like "beautiful" above 1-syllable matches
        # like "will" for inputs like "wundurful".
        heuristic_syllables, _ = self._syllables.count_word(normalized)
        scored = score_entries(
            self._index.entries_for(words),
            query=normalized,
            rhyme_type="family",
            limit=limit,
            query_syllables=heuristic_syllables,
        )
        return tuple(
            _RankedEntry(
                word=c.word,
                syllables=c.syllables,
                rhyme_type="family",
                score=round(c.score, 4),
            )
            for c in scored
        )
