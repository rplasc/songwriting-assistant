"""Shared content-lemma helper used by both M3 and M4 pipelines.

Filters function words and short tokens, then lemmatizes what's left.
The result is the per-line "content bag" both phrase clustering and
section contrast want to compare.
"""

from __future__ import annotations

from app.domain.nlp.lemmatization import Lemmatizer
from app.models.token import Token


def content_lemmas(
    tokens: list[Token],
    lemmatizer: Lemmatizer,
    function_words: frozenset[str],
) -> list[str]:
    out: list[str] = []
    for token in tokens:
        norm = token.normalized
        if not norm or norm in function_words or len(norm) < 2:
            continue
        lemma = lemmatizer.lemmatize_word(norm)
        if not lemma or lemma in function_words:
            continue
        out.append(lemma)
    return out


__all__ = ["content_lemmas"]
