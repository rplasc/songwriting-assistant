from app.domain.languages.base import LanguageEngine
from app.models.token import Token
from app.repositories.pronunciation_repository import PronunciationRepository


class SyllableService:
    def __init__(
        self,
        repository: PronunciationRepository,
        engine: LanguageEngine,
    ) -> None:
        self._repository = repository
        self._engine = engine

    def count_word(self, normalized_word: str) -> tuple[int, bool]:
        """Return (count, pronunciation_found). Falls back to the engine's
        language-specific heuristic if the dictionary has nothing."""
        prons = self._repository.lookup(normalized_word)
        if prons:
            return prons[0].syllables, True
        return self._engine.heuristic_syllable_count(normalized_word), False

    def count_tokens(self, tokens: list[Token]) -> tuple[int, list[tuple[Token, int, bool]]]:
        per_token: list[tuple[Token, int, bool]] = []
        total = 0
        for tok in tokens:
            count, found = self.count_word(tok.normalized)
            per_token.append((tok, count, found))
            total += count
        return total, per_token
