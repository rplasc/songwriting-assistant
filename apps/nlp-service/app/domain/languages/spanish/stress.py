"""Spanish stress placement.

Rules (Real Academia Española):

  1. A written accent (á é í ó ú) pins stress on that syllable.
  2. Otherwise, words ending in a vowel, ``n``, or ``s`` carry stress on
     the penultimate syllable (palabras llanas).
  3. Otherwise, stress falls on the last syllable (palabras agudas).

This module exposes a single function used by syllabification.
"""

from __future__ import annotations

_ACCENTED_VOWELS: frozenset[str] = frozenset("áéíóú")
_PLAIN_VOWELS: frozenset[str] = frozenset("aeiouü")
_PENULT_END_LETTERS: frozenset[str] = _PLAIN_VOWELS | _ACCENTED_VOWELS | frozenset("ns")


def _syllable_has_accent(syllable: str) -> bool:
    return any(c in _ACCENTED_VOWELS for c in syllable)


def stressed_syllable_index(syllables: list[str], word: str) -> int:
    if not syllables:
        return 0
    for i, syl in enumerate(syllables):
        if _syllable_has_accent(syl):
            return i
    if len(syllables) == 1:
        return 0
    last = word[-1]
    if last in _PENULT_END_LETTERS:
        return len(syllables) - 2
    return len(syllables) - 1
