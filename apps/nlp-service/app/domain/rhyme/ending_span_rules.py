"""Phrase-ending span extraction.

The rhyme engine treats a line's "ending" as the last 1-3 trailing tokens
once leading function words have been stripped off. The rule is
deterministic:

1. Take the last ``max_tokens`` tokens of the input as the trailing window.
2. Walk the window from left to right and skip leading function words.
3. If the resulting span is empty (every token in the window was a
   function word), fall back to the trailing window's final token alone
   if it has at least one alphabetic character, else return ``None``.

This keeps phrase endings like "in the night" -> "night" while preserving
"hold me" -> "hold me" (the pronoun is trailing, not leading, so it
contributes phonetic material to the multisyllabic match).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.models.token import Token


@dataclass(frozen=True, slots=True)
class EndingSpan:
    """An extracted phrase-ending span.

    ``tokens`` preserves the original Token objects (with their raw text)
    so the API can echo the span back to the caller. ``normalized`` is the
    parallel tuple of normalized forms used for dictionary lookups.
    """

    tokens: tuple[Token, ...]
    normalized: tuple[str, ...]

    @property
    def span_text(self) -> str:
        return " ".join(t.text for t in self.tokens)


def extract_ending_span(
    tokens: Sequence[Token],
    function_words: frozenset[str],
    max_tokens: int = 3,
) -> EndingSpan | None:
    """Return the trailing rhyme-target span of ``tokens``.

    ``function_words`` is the language-specific closed-class set, looked
    up against each token's ``normalized`` form. See module docstring for
    the algorithm.
    """
    if not tokens:
        return None
    window = list(tokens[-max_tokens:])
    # Strip leading function words from the window.
    start = 0
    while start < len(window) and window[start].normalized in function_words:
        start += 1
    if start < len(window):
        chosen = window[start:]
    else:
        # Every token in the window was a function word. Keep the final
        # token as a last-resort anchor so the engine still has something
        # to look up; the rhyme service will return no candidates if even
        # that token has no pronunciation.
        chosen = window[-1:]
    span_tokens = tuple(chosen)
    return EndingSpan(
        tokens=span_tokens,
        normalized=tuple(t.normalized for t in span_tokens),
    )
