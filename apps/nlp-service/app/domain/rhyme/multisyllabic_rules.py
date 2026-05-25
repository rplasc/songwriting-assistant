"""Multisyllabic rhyme key.

``multisyllabic_rhyme_key`` is a stricter variant of
:func:`app.domain.rhyme_rules.rhyme_key`: it returns the same phoneme
tail starting at the last stressed vowel, but only when that tail spans
at least ``min_vowels`` vowels. Otherwise it returns ``None`` so words
that cannot meaningfully participate in multisyllabic matching never
enter the multisyllabic-tier index.

For phrase-ending lookups, the caller concatenates phonemes across the
ending span before calling this function; the same single rule works
whether the input is one word ("ridiculous") or several ("hold me").
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.rhyme_rules import _is_stressed_vowel, _is_vowel


def multisyllabic_rhyme_key(
    phonemes: Sequence[str],
    min_vowels: int = 2,
) -> str | None:
    """Phoneme tail from the last stressed vowel onward, only if it spans
    ``min_vowels`` vowels or more.

    Returns ``None`` for sequences without a stressed vowel or whose
    stressed-tail covers fewer than ``min_vowels`` vowel phonemes.
    """
    if not phonemes:
        return None
    last_stressed = -1
    for i, p in enumerate(phonemes):
        if _is_stressed_vowel(p):
            last_stressed = i
    if last_stressed < 0:
        return None
    tail = phonemes[last_stressed:]
    vowel_count = sum(1 for p in tail if _is_vowel(p))
    if vowel_count < min_vowels:
        return None
    return "_".join(tail)
