from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.models.pronunciation import Pronunciation


class PronunciationRepository(ABC):
    @abstractmethod
    def lookup(self, normalized_word: str) -> tuple[Pronunciation, ...]:
        """Return all pronunciations for the normalized word, or () if unknown.

        Implementations return the corpus's own stored tuple directly, not a
        copy — callers must not mutate the result.
        """

    @abstractmethod
    def iter_entries(self) -> Iterable[tuple[str, Pronunciation]]:
        """Yield (normalized_word, pronunciation) for every pronunciation in the corpus."""
