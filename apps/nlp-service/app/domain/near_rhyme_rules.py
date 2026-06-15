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


# Vowel-neighborhood classes for near-rhyme grouping. Within a class, vowels
# are treated as interchangeable when building the near-rhyme key — they're
# close enough that lyricists routinely slant-rhyme across them ("again"/
# "thin", "love"/"move"). AE and the closing diphthongs (AW, AY, OY) are
# deliberately left out: AE sits between the two classes below, and merging
# it into either would collapse otherwise-distinct families (e.g. "cat"
# would land in the same bucket as both "cit" and "dog").
_VOWEL_CLASS: dict[str, str] = {
    # Front, non-low: fleece/kit/face/dress.
    "IY": "front", "IH": "front", "EY": "front", "EH": "front",
    # Central/back: strut/lot/thought/goat/foot/goose/nurse.
    "AH": "back", "AA": "back", "AO": "back", "OW": "back",
    "UH": "back", "UW": "back", "ER": "back",
}


def _vowel_class(vowel_base: str) -> str:
    return _VOWEL_CLASS.get(vowel_base, vowel_base)


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
      - reduce the vowel to its neighborhood class (ignoring stress level),
        so close vowels like the IH/EY/EH family or the AH/UW/AO/... family
        become interchangeable (see ``_VOWEL_CLASS``)
      - reduce the coda to just its first phoneme: a following vowel keeps its
        class, a following consonant becomes its manner-of-articulation class

    This collapses voicing pairs (cat/cad), and groups consonants that share
    articulation so endings like "-ack" / "-ock" remain distinct (different
    vowels) while "-it" / "-id" merge. Reducing the coda to a single unit also
    lets codas of different lengths still match (mind/time, friend/again),
    since slant-rhyme families commonly add or drop a trailing consonant.
    Reducing the vowel to a neighborhood class additionally groups slant pairs
    that differ only by vowel (again/thin, love/move).
    """
    start = _stressed_or_last_vowel(phonemes)
    if start < 0:
        return None
    parts: list[str] = [_vowel_class(_vowel_base(phonemes[start]))]
    coda = phonemes[start + 1 :]
    if coda:
        first = coda[0]
        if _is_vowel(first):
            parts.append(_vowel_class(_vowel_base(first)))
        else:
            # Unknown phoneme falls through verbatim, creating a singleton bucket
            # that only matches itself. All standard ARPABET consonants are covered
            # above; this path only fires for non-standard or future phonemes.
            parts.append(_MANNER_CLASS.get(first, first))
    return "_".join(parts)


def inner_near_rhyme_key(phonemes: Sequence[str]) -> str | None:
    """Stricter near key for in-editor inner-rhyme highlighting.

    ``near_rhyme_key`` trades precision for recall (vowel neighborhoods,
    unstressed anchors) because the suggestion path re-scores its candidates
    afterwards. The inner-rhyme detector has no scoring pass — bucket
    membership *is* the highlight group — so this key:

      - requires a stressed anchor vowel (slant rhyme hinges on stressed
        syllables; schwa-only function words never anchor a group)
      - keeps the exact vowel, so "you"/"so"/"world" no longer share a
        vowel-class mega-bucket
      - requires a coda: open syllables ("you" UW1, "so" OW1) carry no
        consonant to slant-match on, and pooling every open syllable with the
        same vowel produces mega-buckets of false positives (true open-syllable
        rhymes are still caught by the perfect tier)
      - tags the coda length (single consonant vs cluster) so a bare ending
        doesn't merge with a cluster ending — "cat"/"cad" stay together but
        "time" no longer slant-merges with "mind"

    The coda manner stays fuzzy (manner-of-articulation classes), preserving
    classic same-length slant pairs like cat/cad and mind/find.
    """
    start = _stressed_or_last_vowel(phonemes)
    if start < 0 or phonemes[start][-1] not in ("1", "2"):
        return None
    coda = phonemes[start + 1 :]
    if not coda:
        return None
    parts: list[str] = [_vowel_base(phonemes[start])]
    first = coda[0]
    if _is_vowel(first):
        parts.append(_vowel_base(first))
    else:
        parts.append(_MANNER_CLASS.get(first, first))
    # Cluster vs single-consonant coda: narrows "add/drop a trailing consonant"
    # merges that over-group the highlight tier.
    parts.append("c" if len(coda) > 1 else "s")
    return "_".join(parts)


