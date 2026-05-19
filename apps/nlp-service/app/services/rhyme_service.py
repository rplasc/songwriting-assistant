from dataclasses import dataclass
from functools import lru_cache

from app.domain.languages.base import LanguageEngine
from app.repositories.pronunciation_repository import PronunciationRepository
from app.schemas.responses import RhymeCandidate
from app.services.pronunciation_service import PronunciationService
from app.services.ranking_service import score_entries
from app.services.rhyme_index import RhymeIndex
from app.services.syllable_service import SyllableService

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
        engine: LanguageEngine,
    ) -> None:
        self._repository = repository
        self._index = index
        self._pronunciation = pronunciation_service
        self._syllables = syllable_service
        self._engine = engine
        # lru_cache on a closure binds to this instance; one cache per service
        # singleton (and therefore per language), garbage-collected with it.
        # The corpus is read-only after startup, so no invalidation is needed.
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
        mode: str | None = None,
        include_metadata: bool = False,
    ) -> tuple[str | None, bool, str, list[RhymeCandidate]]:
        """Return (normalized_word, pronunciations_found, resolved_mode, candidates).

        Cached on (normalized, limit, mode). Songwriting editing re-queries the
        same line-end word on every keystroke, so this is the dominant hot-path win.
        """
        resolved_mode = self._engine.validate_mode(mode or self._engine.default_mode)
        normalized, prons = self._pronunciation.lookup(word)
        if not normalized:
            return None, False, resolved_mode, []
        cached = self._cached_candidates(normalized, limit, resolved_mode)
        # pronunciations_found is True for two distinct cases: (a) the word is
        # in the dictionary, or (b) the heuristic fallback produced usable
        # candidates. Clients that need to distinguish these quality levels
        # should inspect the token-level ``source`` field on
        # LineAnalysisResponse instead, which already carries
        # ``dictionary`` | ``heuristic``.
        found = bool(prons) or bool(cached)
        reasons = self._engine.match_reasons
        return (
            normalized,
            found,
            resolved_mode,
            [
                RhymeCandidate(
                    word=e.word,
                    syllables=e.syllables,
                    rhyme_type=e.rhyme_type,
                    score=e.score,
                    match_reason=reasons.get(e.rhyme_type) if include_metadata else None,
                )
                for e in cached
            ],
        )

    def _compute_candidates(
        self,
        normalized: str,
        limit: int,
        mode: str,
    ) -> tuple[_RankedEntry, ...]:
        prons = self._pronunciation.lookup(normalized)[1]
        if not prons:
            # Heuristic fallback path. The engine decides whether one exists
            # (English does; Spanish's rule-based G2P succeeds on every input,
            # so it returns no fallback). Use the engine's heuristic syllable
            # count as the query length signal so multi-syllable matches like
            # "beautiful" beat 1-syllable matches like "will" for "wundurful".
            tiers = self._engine.heuristic_candidates(self._index, normalized)
            if not tiers:
                return ()
            query_syllables = self._engine.heuristic_syllable_count(normalized)
            return self._score_tiers(tiers, normalized, query_syllables, limit)

        phonemes_list = [p.phonemes for p in prons]
        query_syllables = prons[0].syllables
        tiers = self._engine.candidate_tiers(
            self._index, normalized, phonemes_list, mode, query_syllables
        )
        return self._score_tiers(tiers, normalized, query_syllables, limit)

    def _score_tiers(
        self,
        tiers,
        normalized: str,
        query_syllables: int,
        limit: int,
    ) -> tuple[_RankedEntry, ...]:
        results: list[_RankedEntry] = []
        for tier in tiers:
            remaining = limit - len(results)
            if remaining <= 0:
                break
            if not tier.words:
                continue
            scored = score_entries(
                self._index.entries_for(tier.words),
                query=normalized,
                rhyme_type=tier.name,
                limit=remaining,
                query_syllables=query_syllables,
                engine=self._engine,
            )
            results.extend(
                _RankedEntry(
                    word=c.word,
                    syllables=c.syllables,
                    rhyme_type=tier.name,
                    score=round(c.score, 4),
                )
                for c in scored
            )
        return tuple(results)
