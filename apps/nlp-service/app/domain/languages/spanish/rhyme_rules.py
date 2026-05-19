"""Spanish rhyme-key functions.

Two modes:

  - ``consonant_rhyme_key`` — phonemes from the last stressed vowel onward.
    Identical algorithm to English's ``rhyme_key`` (and reused from it),
    expressing the analog of "perfect rhyme" in Spanish poetry.

  - ``assonant_rhyme_key`` — vowels only from the last stressed vowel
    onward, stress digit stripped. Spanish assonant rhyme matches vowel
    sequences regardless of intervening consonants. It's a legitimate and
    common rhyme type in Spanish lyric tradition, not slant rhyme.
"""

from __future__ import annotations

from collections.abc import Sequence

from app.domain.rhyme_rules import rhyme_key as _english_rhyme_key

# Spanish consonant rhyme has the same shape as English perfect rhyme: take
# the phoneme tail starting at the last stressed vowel. Reusing the English
# function avoids drift between the two implementations.
consonant_rhyme_key = _english_rhyme_key


def _is_vowel(phoneme: str) -> bool:
    return bool(phoneme) and phoneme[-1].isdigit()


def _vowel_base(phoneme: str) -> str:
    return phoneme[:-1]


def assonant_rhyme_key(phonemes: Sequence[str]) -> str | None:
    """Vowel-only key from the last stressed vowel onward.

    Spanish assonant rhyme: ``ventana`` and ``mañana`` share ``A_A``;
    ``corazón`` and ``razón`` share ``O``. Stress digit is dropped so the
    key represents only vowel identity.
    """
    if not phonemes:
        return None
    last_stressed = -1
    last_vowel = -1
    for i, p in enumerate(phonemes):
        if _is_vowel(p):
            last_vowel = i
            if p[-1] in ("1", "2"):
                last_stressed = i
    start = last_stressed if last_stressed >= 0 else last_vowel
    if start < 0:
        return None
    vowels = [_vowel_base(p) for p in phonemes[start:] if _is_vowel(p)]
    if not vowels:
        return None
    return "_".join(vowels)
