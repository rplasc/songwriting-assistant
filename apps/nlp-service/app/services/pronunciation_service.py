from app.domain.languages.base import LanguageEngine
from app.models.pronunciation import Pronunciation
from app.repositories.pronunciation_repository import PronunciationRepository


class PronunciationService:
    def __init__(
        self,
        repository: PronunciationRepository,
        engine: LanguageEngine,
    ) -> None:
        self._repository = repository
        self._engine = engine

    def lookup(self, word: str) -> tuple[str | None, list[Pronunciation]]:
        normalized = self._engine.normalize_word(word)
        if normalized is None:
            return None, []
        return normalized, self._repository.lookup(normalized)
