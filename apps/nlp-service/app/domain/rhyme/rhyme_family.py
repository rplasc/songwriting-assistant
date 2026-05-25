"""Rhyme-family classification.

Maps the engine-internal tier name (``perfect``/``family``/``near`` for
English, ``consonant``/``assonant`` for Spanish, plus the new
``multisyllabic`` tier) to a small, editorially meaningful family that
clients can render. The taxonomy is kept narrow on purpose -- only
families that the Phase 5 golden sets demonstrate explicitly.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

from app.domain.rhyme.multisyllabic_rules import multisyllabic_rhyme_key

RhymeFamily = Literal[
    "perfect", "multisyllabic", "near", "assonant", "consonant"
]


def classify_rhyme_family(
    *,
    tier_name: str,
    language: str,
    query_phonemes: Sequence[str] | None = None,
    candidate_phonemes: Sequence[str] | None = None,
) -> RhymeFamily:
    """Return the family label for a ranked candidate.

    Decision rules:

    * ``multisyllabic`` tier (explicit) -> ``"multisyllabic"``.
    * English ``perfect``: ``"multisyllabic"`` when both query and
      candidate share a multisyllabic-key tail; ``"perfect"`` otherwise.
    * English ``family``: ``"multisyllabic"`` -- the family tier in
      English only fires for multi-vowel queries (dactylic words like
      "wonderful"/"beautiful") which the user perceives as multi-syllable
      tail rhymes.
    * English ``near`` -> ``"near"``.
    * Spanish ``consonant``: ``"multisyllabic"`` when both share a
      multisyllabic-key tail; ``"consonant"`` otherwise.
    * Spanish ``assonant`` -> ``"assonant"``.

    Falls back to ``"near"`` for any unknown tier so the response is
    never missing the field.
    """
    if tier_name == "multisyllabic":
        return "multisyllabic"
    if language == "en":
        if tier_name == "perfect":
            if _shares_multisyllabic_tail(query_phonemes, candidate_phonemes):
                return "multisyllabic"
            return "perfect"
        if tier_name == "family":
            return "multisyllabic"
        if tier_name == "near":
            return "near"
    elif language == "es":
        if tier_name == "consonant":
            if _shares_multisyllabic_tail(query_phonemes, candidate_phonemes):
                return "multisyllabic"
            return "consonant"
        if tier_name == "assonant":
            return "assonant"
    return "near"


def _shares_multisyllabic_tail(
    query_phonemes: Sequence[str] | None,
    candidate_phonemes: Sequence[str] | None,
) -> bool:
    if query_phonemes is None or candidate_phonemes is None:
        return False
    qk = multisyllabic_rhyme_key(query_phonemes)
    if qk is None:
        return False
    ck = multisyllabic_rhyme_key(candidate_phonemes)
    return ck is not None and qk == ck
