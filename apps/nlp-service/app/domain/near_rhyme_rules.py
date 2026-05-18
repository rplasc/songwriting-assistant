from collections.abc import Sequence

# ARPABET consonant -> manner-of-articulation class. Voicing pairs share a class,
# so "cat"/"cad" become candidate near rhymes through their final consonant.
_MANNER_CLASS: dict[str, str] = {
    "P": "stop", "B": "stop", "T": "stop", "D": "stop", "K": "stop", "G": "stop",
    "CH": "affr", "JH": "affr",
    "F": "fric", "V": "fric", "S": "fric", "Z": "fric",
    "SH": "fric", "ZH": "fric", "TH": "fric", "DH": "fric", "HH": "fric",
    "M": "nas", "N": "nas", "NG": "nas",
    "L": "liq", "R": "liq",
    "W": "glide", "Y": "glide",
}


def _is_vowel(phoneme: str) -> bool:
    return bool(phoneme) and phoneme[-1].isdigit()


def _vowel_base(phoneme: str) -> str:
    return phoneme[:-1] if _is_vowel(phoneme) else phoneme


def _stressed_or_last_vowel(phonemes: Sequence[str]) -> int:
    last_stressed = -1
    last_vowel = -1
    for i, p in enumerate(phonemes):
        if _is_vowel(p):
            last_vowel = i
            if p[-1] in ("1", "2"):
                last_stressed = i
    return last_stressed if last_stressed >= 0 else last_vowel


def near_rhyme_key(phonemes: Sequence[str]) -> str | None:
    """A coarser key intended for slant/near rhymes.

    Strategy:
      - anchor on the last stressed (or last) vowel
      - keep the vowel identity (ignoring stress level)
      - replace each following consonant with its manner-of-articulation class

    This collapses voicing pairs (cat/cad), and groups consonants that share
    articulation so endings like "-ack" / "-ock" remain distinct (different
    vowels) while "-it" / "-id" merge.
    """
    start = _stressed_or_last_vowel(phonemes)
    if start < 0:
        return None
    parts: list[str] = [_vowel_base(phonemes[start])]
    for p in phonemes[start + 1 :]:
        if _is_vowel(p):
            parts.append(_vowel_base(p))
        else:
            parts.append(_MANNER_CLASS.get(p, p))
    return "_".join(parts)


