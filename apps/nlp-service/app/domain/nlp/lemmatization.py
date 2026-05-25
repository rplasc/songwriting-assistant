"""Per-language lemmatization for draft semantic analysis.

Lemmatization here is deterministic: simplemma ships static word-form
dictionaries and falls back to suffix rules. We wrap that with a small
LRU-style per-instance cache so repeated forms across a draft don't pay
the dictionary-lookup cost twice. On a miss (proper nouns, made-up
lyric words), we return the input unchanged — never None — so callers
can always rely on a usable lemma for grouping.
"""

from __future__ import annotations

from typing import Protocol

import simplemma

from app.models.token import Token


class Lemmatizer(Protocol):
    """Interface for per-language lemmatization."""

    language: str

    def lemmatize_word(self, word: str) -> str: ...

    def lemmatize_tokens(self, tokens: list[Token]) -> list[str]: ...


class SimplemmaLemmatizer:
    """simplemma-backed lemmatizer with per-instance caching.

    Constructed once per language at app startup; one instance is safe
    to share across requests (cache is read-mostly after warmup).
    """

    __slots__ = ("language", "_cache")

    def __init__(self, language: str) -> None:
        self.language = language
        self._cache: dict[str, str] = {}

    def lemmatize_word(self, word: str) -> str:
        if not word:
            return word
        cached = self._cache.get(word)
        if cached is not None:
            return cached
        try:
            lemma = simplemma.lemmatize(word, lang=self.language)
        except Exception:
            lemma = word
        if not lemma:
            lemma = word
        self._cache[word] = lemma
        return lemma

    def lemmatize_tokens(self, tokens: list[Token]) -> list[str]:
        return [self.lemmatize_word(t.normalized) for t in tokens if t.normalized]


__all__ = ["Lemmatizer", "SimplemmaLemmatizer"]
