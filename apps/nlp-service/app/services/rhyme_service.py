from app.repositories.pronunciation_repository import PronunciationRepository
from app.schemas.responses import RhymeCandidate
from app.services.pronunciation_service import PronunciationService
from app.services.ranking_service import score_entries
from app.services.rhyme_index import RhymeIndex
from app.services.syllable_service import SyllableService

_PERFECT_REASON = "shared stressed ending"
_NEAR_REASON = "shared vowel with similar consonants"


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
        """Return (normalized_word, pronunciations_found, ranked rhyme candidates)."""
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
            rhyme_type = "near"
            reason = _NEAR_REASON
        else:
            perfect_keys = self._index.perfect_keys_for_phonemes(phonemes_list)
            candidate_words = self._index.words_for_perfect_keys(
                perfect_keys, exclude=normalized
            )
            rhyme_type = "perfect"
            reason = _PERFECT_REASON

        entries = self._index.entries_for(candidate_words)
        scored = score_entries(
            entries,
            query=normalized,
            rhyme_type=rhyme_type,
            query_syllables=query_syllables,
        )[:limit]

        return normalized, True, [
            RhymeCandidate(
                word=c.word,
                syllables=c.syllables,
                rhyme_type=rhyme_type,
                score=round(c.score, 4),
                match_reason=reason if include_metadata else None,
            )
            for c in scored
        ]
