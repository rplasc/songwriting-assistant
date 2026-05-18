from app.repositories.pronunciation_repository import PronunciationRepository
from app.schemas.responses import RhymeCandidate
from app.services.pronunciation_service import PronunciationService
from app.services.ranking_service import ScoredCandidate, score_entries
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

    def find_rhymes(
        self,
        word: str,
        limit: int,
        *,
        mode: str = "perfect",
        include_metadata: bool = False,
    ) -> tuple[str | None, bool, list[RhymeCandidate]]:
        """Return (normalized_word, pronunciations_found, ranked rhyme candidates).

        When mode == "perfect", cascades through tiers (perfect -> family -> near)
        until `limit` is reached, so dactylic words like "wonderful" — which have
        no true perfect rhymes — still surface useful suggestions. Each candidate
        is tagged with the tier it was actually matched from.
        """
        normalized, prons = self._pronunciation.lookup(word)
        if not normalized or not prons:
            return normalized, False, []

        phonemes_list = [p.phonemes for p in prons]
        query_syllables = prons[0].syllables

        if mode == "near":
            near_keys = self._index.near_keys_for_phonemes(phonemes_list)
            near_words = self._index.words_for_near_keys(near_keys, exclude=normalized)
            perfect_keys = self._index.perfect_keys_for_phonemes(phonemes_list)
            perfect_words = self._index.words_for_perfect_keys(
                perfect_keys, exclude=normalized
            )
            candidate_words = near_words - perfect_words
            scored = score_entries(
                self._index.entries_for(candidate_words),
                query=normalized,
                rhyme_type="near",
                query_syllables=query_syllables,
            )[:limit]
            return normalized, True, [
                self._candidate(c, "near", include_metadata) for c in scored
            ]

        # mode == "perfect" — tiered cascade.
        perfect_keys = self._index.perfect_keys_for_phonemes(phonemes_list)
        family_keys = self._index.family_keys_for_phonemes(phonemes_list)
        near_keys = self._index.near_keys_for_phonemes(phonemes_list)

        perfect_words = self._index.words_for_perfect_keys(
            perfect_keys, exclude=normalized
        )
        family_words = self._index.words_for_family_keys(
            family_keys, exclude=normalized
        ) - perfect_words
        near_words = (
            self._index.words_for_near_keys(near_keys, exclude=normalized)
            - perfect_words
            - family_words
        )

        results: list[RhymeCandidate] = []
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
                query_syllables=query_syllables,
            )[:remaining]
            results.extend(self._candidate(c, tier, include_metadata) for c in scored)

        return normalized, True, results

    @staticmethod
    def _candidate(
        scored: ScoredCandidate, tier: str, include_metadata: bool
    ) -> RhymeCandidate:
        return RhymeCandidate(
            word=scored.word,
            syllables=scored.syllables,
            rhyme_type=tier,
            score=round(scored.score, 4),
            match_reason=_REASON_BY_TYPE[tier] if include_metadata else None,
        )
