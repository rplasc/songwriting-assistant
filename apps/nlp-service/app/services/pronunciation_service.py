from app.domain.normalization import normalize_word
from app.models.pronunciation import Pronunciation
from app.repositories.pronunciation_repository import PronunciationRepository


class PronunciationService:
    def __init__(self, repository: PronunciationRepository) -> None:
        self._repository = repository

    def lookup(self, word: str) -> tuple[str | None, list[Pronunciation]]:
        normalized = normalize_word(word)
        if normalized is None:
            return None, []
        return normalized, self._repository.lookup(normalized)
