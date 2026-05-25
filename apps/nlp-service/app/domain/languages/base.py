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
    # Closed-class words used by the phrase-ending extractor; default empty
    # so engines that don't ship phrase-ending support degrade gracefully.
    function_words: frozenset[str] = frozenset()
    # Engines with at least one stressed multi-syllable example in their
    # corpus set this True so the route handler can expose the capability.
    multisyllabic_supported: bool = False

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

    def is_same_stem_inflection(self, query: str, candidate: str) -> bool:
        """True if candidate is an inflected form of query (same stem, different ending).

        Default returns False — engines opt in by overriding with language-specific
        morphology. Returning True causes the inflection penalty to apply in ranking.
        """
        return False

    def inflection_forms(self, query: str) -> frozenset[str]:
        """All candidate words that should be penalised as same-stem inflections
        of ``query``. Built once per query so the ranking loop can do O(1)
        membership tests instead of calling :meth:`is_same_stem_inflection`
        per candidate. Default: empty set (no penalty).
        """
        return frozenset()

    def shares_stem(self, query: str, candidate: str, min_stem: int = 4) -> bool:
        """True if query and candidate share a long enough common prefix to suggest
        they derive from the same root (e.g. "fire"/"fireplace").

        Two conditions must both hold:
          - shared >= min_stem: absolute floor.
          - shared >= len(query) - 1: scales required overlap with query length so
            coincidental short-prefix matches don't penalise unrelated longer words.

        Inflected forms caught by is_same_stem_inflection are not re-checked here.
        """
        if len(query) < min_stem or len(candidate) < min_stem:
            return False
        shared = 0
        for a, b in zip(query, candidate):
            if a != b:
                break
            shared += 1
        return shared >= min_stem and shared >= len(query) - 1

    def stress_signature(self, word: str) -> str | None:
        """Return prosodic stress class of the word, or None if not applicable.

        Possible values: "aguda" (final stress), "llana" (penultimate), "esdrujula"
        (antepenultimate or earlier). Engines that don't use stress-position ranking
        return None (the default), which disables the bonus in score_entries.
        """
        return None

    def validate_mode(self, mode: str) -> str:
        if mode not in self.supported_modes:
            raise UnsupportedModeError(
                f"mode '{mode}' is not supported for language '{self.code}'. "
                f"Supported: {', '.join(self.supported_modes)}"
            )
        return mode
