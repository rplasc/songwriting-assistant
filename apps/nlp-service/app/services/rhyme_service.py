from dataclasses import dataclass
from functools import lru_cache

from app.domain.languages.base import LanguageEngine
from app.domain.rhyme.diversity_rules import diversify
from app.domain.rhyme.ending_span_rules import extract_ending_span
from app.domain.rhyme.multisyllabic_rules import multisyllabic_rhyme_key
from app.domain.rhyme.rhyme_family import classify_rhyme_family
from app.repositories.pronunciation_repository import PronunciationRepository
from app.schemas.responses import RhymeCandidate
from app.services.pronunciation_service import PronunciationService
from app.services.ranking_service import score_entries
from app.services.rhyme_index import RhymeIndex
from app.services.syllable_service import SyllableService

_CACHE_SIZE = 1024


def _multisyllabic_len(phonemes: tuple[str, ...] | None) -> int:
    """Length (in phonemes) of the multisyllabic-key tail, or 0 if none.

    Pairs with the ``multisyllabic_tail_phonemes`` value cached per
    RhymeEntry at index build, so the ranking signal compares like with
    like.
    """
    if not phonemes:
        return 0
    key = multisyllabic_rhyme_key(phonemes)
    return len(key.split("_")) if key else 0


@dataclass(frozen=True, slots=True)
class _RankedEntry:
    """Scored, ranked candidate stored in the LRU cache.

    Kept separate from RhymeCandidate so include_metadata and family
    classification (both per-request, not per-cache-entry) stay outside
    the cache key.
    """

    word: str
    syllables: int
    rhyme_type: str
    score: float


@dataclass(frozen=True, slots=True)
class RhymeLookup:
    """Result of a rhyme lookup.

    ``normalized`` is the lower-cased single-token query for
    ``target_type="word"``, or the joined normalized span (e.g.
    ``"hold me"``) for ``target_type="phrase_ending"``. ``query_span`` is
    the original-casing span text for phrase-ending requests, ``None``
    otherwise.
    """

    normalized: str | None
    pronunciations_found: bool
    resolved_mode: str
    query_span: str | None
    candidates: list[RhymeCandidate]


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
        # lru_cache on a closure binds to this instance; one cache per language
        # singleton, garbage-collected with it. The corpus is read-only after
        # startup, so no invalidation is needed. include_metadata, family
        # labels, and matched_span are intentionally excluded from the key —
        # they're applied per-request after retrieval.
        self._cached_candidates = lru_cache(maxsize=_CACHE_SIZE)(
            self._compute_candidates
        )

    def find_rhymes(
        self,
        word: str,
        limit: int,
        *,
        mode: str | None = None,
        target_type: str = "word",
        include_metadata: bool = False,
    ) -> RhymeLookup:
        """Look up rhymes for ``word`` (single token or phrase ending).

        For ``target_type="word"`` the existing fast path runs unchanged
        and each result is annotated with a ``rhyme_family`` label.

        For ``target_type="phrase_ending"`` the input is tokenized, its
        ending span extracted, and phonemes are concatenated across the
        span tokens that have a dictionary pronunciation. Heuristic
        fallback is deliberately skipped on the phrase-ending path in
        M1 — phrase requests with non-dictionary words return empty.
        """
        resolved_mode = self._engine.validate_mode(
            mode or self._engine.default_mode
        )
        if target_type == "phrase_ending":
            return self._find_phrase_ending(
                word, limit, resolved_mode, include_metadata
            )
        return self._find_word(word, limit, resolved_mode, include_metadata)

    # --- single-token path ---

    def _find_word(
        self,
        word: str,
        limit: int,
        resolved_mode: str,
        include_metadata: bool,
    ) -> RhymeLookup:
        normalized, prons = self._pronunciation.lookup(word)
        if not normalized:
            return RhymeLookup(
                normalized=None,
                pronunciations_found=False,
                resolved_mode=resolved_mode,
                query_span=None,
                candidates=[],
            )
        cached = self._cached_candidates(normalized, limit, resolved_mode)
        # pronunciations_found is True for two distinct cases: (a) the word is
        # in the dictionary, or (b) the heuristic fallback produced usable
        # candidates. Clients that need to distinguish these quality levels
        # should inspect the token-level ``source`` field on
        # LineAnalysisResponse, which already carries ``dictionary`` |
        # ``heuristic``.
        found = bool(prons) or bool(cached)
        query_phonemes = prons[0].phonemes if prons else None
        candidates = self._annotate(
            cached,
            query_phonemes=query_phonemes,
            include_metadata=include_metadata,
        )
        return RhymeLookup(
            normalized=normalized,
            pronunciations_found=found,
            resolved_mode=resolved_mode,
            query_span=None,
            candidates=candidates,
        )

    # --- phrase-ending path ---

    def _find_phrase_ending(
        self,
        text: str,
        limit: int,
        resolved_mode: str,
        include_metadata: bool,
    ) -> RhymeLookup:
        tokens = self._engine.tokenize_line(text)
        span = extract_ending_span(tokens, self._engine.function_words)
        if span is None or not span.normalized:
            return RhymeLookup(
                normalized=None,
                pronunciations_found=False,
                resolved_mode=resolved_mode,
                query_span=None,
                candidates=[],
            )

        # Concatenate phonemes across span tokens that have a dictionary
        # pronunciation. Tokens without one are dropped on the assumption
        # that they contribute no reliable phonetic information (heuristic
        # G2P for English is single-token-shaped; mixing dictionary +
        # heuristic phonemes in one tail would be noisy).
        concatenated: list[str] = []
        any_pron = False
        for norm in span.normalized:
            _, prons = self._pronunciation.lookup(norm)
            if prons:
                concatenated.extend(prons[0].phonemes)
                any_pron = True
        normalized_span = " ".join(span.normalized)
        if not any_pron:
            return RhymeLookup(
                normalized=normalized_span,
                pronunciations_found=False,
                resolved_mode=resolved_mode,
                query_span=span.span_text,
                candidates=[],
            )

        # The last span token is the strongest single-word exclusion target
        # used by the engine when building the tier sets. We additionally
        # filter the FULL span set after ranking so other span tokens
        # ("hold" in "hold me") can't survive as candidates either.
        exclude_word = span.normalized[-1]
        span_set = set(span.normalized)
        query_phonemes = tuple(concatenated)
        query_syllables = sum(
            self._engine.heuristic_syllable_count(n) for n in span.normalized
        )
        tiers = self._engine.candidate_tiers(
            self._index,
            exclude_word,
            [query_phonemes],
            resolved_mode,
            query_syllables,
        )
        # Pull extra candidates to keep top-N stable after span-set filtering.
        overscan = limit + len(span_set)
        ranked = self._score_tiers(
            tiers,
            exclude_word,
            query_syllables,
            overscan,
            query_multisyllabic_len=_multisyllabic_len(query_phonemes),
        )
        ranked = tuple(e for e in ranked if e.word not in span_set)
        ranked = diversify(ranked, engine=self._engine)[:limit]
        candidates = self._annotate(
            ranked,
            query_phonemes=query_phonemes,
            include_metadata=include_metadata,
        )
        return RhymeLookup(
            normalized=normalized_span,
            pronunciations_found=True,
            resolved_mode=resolved_mode,
            query_span=span.span_text,
            candidates=candidates,
        )

    # --- shared helpers ---

    def _compute_candidates(
        self,
        normalized: str,
        limit: int,
        mode: str,
    ) -> tuple[_RankedEntry, ...]:
        # Word-path only; phrase-ending lookups are not cached in M1
        # because their pronunciation step iterates over span tokens.
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
            ranked = self._score_tiers(
                tiers,
                normalized,
                query_syllables,
                limit,
                query_multisyllabic_len=0,
            )
            return diversify(ranked, engine=self._engine)

        phonemes_list = [p.phonemes for p in prons]
        query_syllables = prons[0].syllables
        query_multi_len = _multisyllabic_len(phonemes_list[0])
        tiers = self._engine.candidate_tiers(
            self._index, normalized, phonemes_list, mode, query_syllables
        )
        ranked = self._score_tiers(
            tiers,
            normalized,
            query_syllables,
            limit,
            query_multisyllabic_len=query_multi_len,
        )
        return diversify(ranked, engine=self._engine)

    def _score_tiers(
        self,
        tiers,
        normalized: str,
        query_syllables: int,
        limit: int,
        *,
        query_multisyllabic_len: int = 0,
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
                query_multisyllabic_len=query_multisyllabic_len or None,
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

    def _annotate(
        self,
        ranked: tuple[_RankedEntry, ...],
        *,
        query_phonemes: tuple[str, ...] | None,
        include_metadata: bool,
    ) -> list[RhymeCandidate]:
        """Wrap ranked entries in RhymeCandidate, filling family and span."""
        reasons = self._engine.match_reasons
        out: list[RhymeCandidate] = []
        for e in ranked:
            cand_phonemes = self._candidate_phonemes(e.word)
            family = classify_rhyme_family(
                tier_name=e.rhyme_type,
                language=self._engine.code,
                query_phonemes=query_phonemes,
                candidate_phonemes=cand_phonemes,
            )
            out.append(
                RhymeCandidate(
                    word=e.word,
                    syllables=e.syllables,
                    rhyme_type=e.rhyme_type,
                    score=e.score,
                    rhyme_family=family,
                    matched_span=e.word,
                    match_reason=(
                        reasons.get(e.rhyme_type) if include_metadata else None
                    ),
                )
            )
        return out

    def _candidate_phonemes(self, word: str) -> tuple[str, ...] | None:
        prons = self._repository.lookup(word)
        if not prons:
            return None
        return prons[0].phonemes
