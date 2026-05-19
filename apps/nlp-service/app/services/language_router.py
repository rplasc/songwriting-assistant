from dataclasses import dataclass

from app.domain.languages.base import LanguageEngine
from app.repositories.pronunciation_repository import PronunciationRepository
from app.services.pronunciation_service import PronunciationService
from app.services.rhyme_index import RhymeIndex
from app.services.rhyme_service import RhymeService
from app.services.syllable_service import SyllableService


class UnsupportedLanguageError(Exception):
    """Raised when a request specifies a language that is not registered."""

    def __init__(self, code: str, supported: tuple[str, ...]):
        self.code = code
        self.supported = supported
        super().__init__(
            f"language '{code}' is not supported. "
            f"Supported languages: {', '.join(supported)}"
        )


@dataclass(frozen=True, slots=True)
class LanguageContext:
    engine: LanguageEngine
    repository: PronunciationRepository
    index: RhymeIndex
    pronunciation_service: PronunciationService
    syllable_service: SyllableService
    rhyme_service: RhymeService


class LanguageRouter:
    """Holds one LanguageContext per supported language code.

    A request's ``language`` field selects the context; everything downstream
    (rhyme lookup, syllable counting, normalization) is then language-specific
    without any branching in the route handlers themselves.
    """

    def __init__(self, contexts: dict[str, LanguageContext]) -> None:
        if not contexts:
            raise ValueError("LanguageRouter requires at least one context")
        self._contexts = dict(contexts)
        self._supported = tuple(self._contexts.keys())

    def get(self, code: str) -> LanguageContext:
        ctx = self._contexts.get(code)
        if ctx is None:
            raise UnsupportedLanguageError(code, self._supported)
        return ctx

    @property
    def supported(self) -> tuple[str, ...]:
        return self._supported
