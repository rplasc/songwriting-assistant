from app.repositories.pronunciation_repository import PronunciationRepository
from app.schemas.responses import RhymeCandidate
from app.services.pronunciation_service import PronunciationService
from app.services.ranking_service import rank_candidates
from app.services.rhyme_index import RhymeIndex
from app.services.syllable_service import SyllableService


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
    ) -> tuple[str | None, bool, list[RhymeCandidate]]:
        """Return (normalized_word, pronunciations_found, top-N exact rhyme candidates)."""
        normalized, prons = self._pronunciation.lookup(word)
        if not normalized or not prons:
            return normalized, False, []

        keys = self._index.keys_for_phonemes([p.phonemes for p in prons])
        candidate_words = self._index.words_for_keys(keys, exclude=normalized)
        ranked = rank_candidates(list(candidate_words))[:limit]

        results: list[RhymeCandidate] = []
        for cand in ranked:
            syllables, _ = self._syllables.count_word(cand)
            results.append(
                RhymeCandidate(
                    word=cand,
                    syllables=syllables,
                    rhyme_type="perfect",
                    score=1.0,
                )
            )
        return normalized, True, results
