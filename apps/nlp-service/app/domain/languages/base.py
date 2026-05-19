from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.models.token import Token

if TYPE_CHECKING:
    from app.services.rhyme_index import RhymeIndex


KeyFn = Callable[[Sequence[str]], "str | None"]


@dataclass(frozen=True, slots=True)
class KeySpec:
    """One named rhyme-key slot exposed by a LanguageEngine.

    The name is reused as: the slot label inside RhymeIndex and the
    rhyme_type tag attached to ranked candidates.
    """

    name: str
    fn: KeyFn


@dataclass(frozen=True, slots=True)
class CandidateTier:
    """Ordered tier returned by an engine's mode strategy.

    Words have already been deduped against higher tiers — RhymeService
    consumes the tuple in order and scores per tier.
    """

    name: str
    words: set[str]


class UnsupportedModeError(ValueError):
    """Raised when a mode is not valid for the engine's language."""


class LanguageEngine(ABC):
    """Per-language analysis surface.

    The engine owns normalization, tokenization, syllable fallback, rhyme-key
    derivation, and the per-mode candidate strategy. RhymeIndex and the
    services depend only on this interface — adding a language adds a new
    engine, not new branches in shared code.
    """

    code: str
    supported_modes: tuple[str, ...]
    default_mode: str
    key_specs: tuple[KeySpec, ...]
    match_reasons: dict[str, str]

    @abstractmethod
    def normalize_word(self, text: str | None) -> str | None: ...

    @abstractmethod
    def tokenize_line(self, line: str) -> list[Token]: ...

    @abstractmethod
    def heuristic_syllable_count(self, word: str) -> int:
        """Syllable count for words missing from the language's dictionary."""

    @abstractmethod
    def frequency(self, word: str) -> float:
        """Corpus frequency lookup; used by the rhyme index to filter and rank."""

    @abstractmethod
    def is_corpus_eligible_word(self, word: str) -> bool:
        """Cheap shape filter run before frequency lookup at index-build time."""

    @abstractmethod
    def candidate_tiers(
        self,
        index: "RhymeIndex",
        normalized: str,
        phonemes_list: list[tuple[str, ...]],
        mode: str,
        query_syllables: int,
    ) -> list[CandidateTier]: ...

    def heuristic_candidates(
        self,
        index: "RhymeIndex",
        normalized: str,
    ) -> list[CandidateTier]:
        """Fallback path when no dictionary pronunciation exists.

        Default: no fallback. English overrides this with spelling-derived tails.
        """
        return []

    def validate_mode(self, mode: str) -> str:
        if mode not in self.supported_modes:
            raise UnsupportedModeError(
                f"mode '{mode}' is not supported for language '{self.code}'. "
                f"Supported: {', '.join(self.supported_modes)}"
            )
        return mode
