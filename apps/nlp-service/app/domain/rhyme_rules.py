from collections.abc import Sequence


def _is_vowel(phoneme: str) -> bool:
    """ARPABET vowels carry a stress digit at the end (0, 1, or 2)."""
    return bool(phoneme) and phoneme[-1].isdigit()


def _is_stressed_vowel(phoneme: str) -> bool:
    return _is_vowel(phoneme) and phoneme[-1] in ("1", "2")


def rhyme_key(phonemes: Sequence[str]) -> str | None:
    """Return the phoneme sequence from the last stressed vowel to the end, joined with `_`.

    Falls back to the last vowel if no stressed vowel exists. Returns None when the
    sequence has no vowel at all.
    """
    if not phonemes:
        return None
    last_stressed = -1
    last_vowel = -1
    for i, p in enumerate(phonemes):
        if _is_vowel(p):
            last_vowel = i
            if _is_stressed_vowel(p):
                last_stressed = i
    start = last_stressed if last_stressed >= 0 else last_vowel
    if start < 0:
        return None
    return "_".join(phonemes[start:])
