"""Spanish grapheme-to-phoneme.

Produces an ARPABET-shaped phoneme tuple (vowels carry a stress digit, just
like CMU English entries) so the index/key/ranking code can be shared
across languages. Defaults are Latin-American: ``c``/``z`` → S (seseo),
``ll``/``y`` → Y (yeísmo).

The mapping is intentionally narrow and rule-based. Spanish orthography is
near-phonetic, so a small ruleset covers the corpus; loanwords and
exceptions (``méxico`` etc.) are accepted with seseo-style readings rather
than dictionary lookups, since the result is still a usable rhyme key.
"""

from __future__ import annotations

from app.domain.languages.spanish.syllabification import syllabify
from app.models.pronunciation import Pronunciation

_VOWEL_BASE: dict[str, str] = {
    "a": "A",
    "á": "A",
    "e": "E",
    "é": "E",
    "i": "I",
    "í": "I",
    "o": "O",
    "ó": "O",
    "u": "U",
    "ú": "U",
    "ü": "U",
}

_FRONT_VOWELS: frozenset[str] = frozenset("eiéí")
_VOWEL_LETTERS: frozenset[str] = frozenset(_VOWEL_BASE.keys())
# Letters after which an intervocalic ``r`` becomes a trill (RR), not a tap (R).
_TRILL_TRIGGER_LETTERS: frozenset[str] = frozenset("nls")

# Letters with a stable 1:1 mapping.
_SIMPLE_CONSONANTS: dict[str, str] = {
    "b": "B",
    "d": "D",
    "f": "F",
    "j": "H",
    "k": "K",
    "l": "L",
    "m": "M",
    "n": "N",
    "p": "P",
    "s": "S",
    "t": "T",
    "w": "W",
}


def _letter_to_syllable(syllables: list[str]) -> list[int]:
    """For each character position in the joined word, the syllable index."""
    out: list[int] = []
    for s_idx, syl in enumerate(syllables):
        out.extend(s_idx for _ in syl)
    return out


_STRONG_LETTERS: frozenset[str] = frozenset("aeoáéó")
_ALL_VOWEL_LETTERS: frozenset[str] = frozenset("aeiouáéíóúü")
_ACCENTED_LETTERS: frozenset[str] = frozenset("áéíóú")


def _syllable_nucleus_local_index(syllable: str) -> int:
    """Index within ``syllable`` of the nucleus vowel (the one that carries
    stress when the syllable is stressed). Returns -1 if the syllable has
    no vowel.

    Rules:
      1. A written accent always wins (``ció``-n: ó is the nucleus).
      2. Otherwise the first strong vowel (a/e/o) is the nucleus
         (diphthongs like ``ie``, ``ue``, ``ai`` etc.).
      3. Otherwise (weak+weak diphthong like ``iu``/``ui``), the SECOND
         weak vowel carries stress in Spanish.
    """
    for i, c in enumerate(syllable):
        if c in _ACCENTED_LETTERS:
            return i
    vowel_positions = [i for i, c in enumerate(syllable) if c in _ALL_VOWEL_LETTERS]
    if not vowel_positions:
        return -1
    if len(vowel_positions) == 1:
        return vowel_positions[0]
    strong = [i for i in vowel_positions if syllable[i] in _STRONG_LETTERS]
    if strong:
        return strong[0]
    return vowel_positions[-1]


def _nucleus_mask(syllables: list[str]) -> list[bool]:
    """Parallel-to-word boolean: True at each character position that is the
    nucleus of its syllable."""
    mask: list[bool] = []
    for syl in syllables:
        local = _syllable_nucleus_local_index(syl)
        for j, _ in enumerate(syl):
            mask.append(j == local)
    return mask


def g2p(word: str) -> Pronunciation:
    """Convert a normalized Spanish word to a (Pronunciation,) tuple.

    Returns a single deterministic pronunciation. Empty / unparseable input
    returns an empty phoneme tuple with syllables=1 so downstream code can
    short-circuit safely.
    """
    if not word:
        return Pronunciation(phonemes=(), syllables=1)

    syllables, stress_idx = syllabify(word)
    letter_to_syl = _letter_to_syllable(syllables)
    is_nucleus = _nucleus_mask(syllables)

    phonemes: list[str] = []
    i = 0
    n = len(word)
    while i < n:
        ch = word[i]
        nxt = word[i + 1] if i + 1 < n else None
        nxt2 = word[i + 2] if i + 2 < n else None
        prev = word[i - 1] if i > 0 else None

        # Consonant digraphs and silent-u sequences first.
        if ch == "c" and nxt == "h":
            phonemes.append("CH")
            i += 2
            continue
        if ch == "l" and nxt == "l":
            phonemes.append("Y")
            i += 2
            continue
        if ch == "r" and nxt == "r":
            phonemes.append("RR")
            i += 2
            continue
        if ch == "q" and nxt == "u":
            # Spanish ``qu`` always before e/i; the u is silent.
            phonemes.append("K")
            i += 2
            continue
        if ch == "g" and nxt == "u" and nxt2 in _FRONT_VOWELS:
            # Silent-u ``gu`` before e/i (``guerra``, ``guitarra``).
            phonemes.append("G")
            i += 2
            continue

        # Vowels carry a stress digit. Only the syllable's nucleus vowel
        # gets the "1" when the syllable is stressed; non-nucleus vowels in
        # a diphthong / triphthong remain unstressed.
        if ch in _VOWEL_LETTERS:
            syl_idx = letter_to_syl[i] if i < len(letter_to_syl) else 0
            is_stressed = syl_idx == stress_idx and i < len(is_nucleus) and is_nucleus[i]
            phonemes.append(_VOWEL_BASE[ch] + ("1" if is_stressed else "0"))
            i += 1
            continue

        # Context-sensitive consonants.
        if ch == "c":
            phonemes.append("S" if nxt in _FRONT_VOWELS else "K")
            i += 1
            continue
        if ch == "g":
            phonemes.append("H" if nxt in _FRONT_VOWELS else "G")
            i += 1
            continue
        if ch == "r":
            # Word-initial OR after n/l/s → trill RR. Otherwise tap R.
            if prev is None or prev in _TRILL_TRIGGER_LETTERS:
                phonemes.append("RR")
            else:
                phonemes.append("R")
            i += 1
            continue
        if ch == "h":
            # Silent in Spanish.
            i += 1
            continue
        if ch == "x":
            # Intervocalic → KS (``examen``). Edge → S (``xilófono``).
            if (
                prev in _VOWEL_LETTERS
                and nxt is not None
                and nxt in _VOWEL_LETTERS
            ):
                phonemes.extend(("K", "S"))
            else:
                phonemes.append("S")
            i += 1
            continue
        if ch == "y":
            phonemes.append("Y")
            i += 1
            continue
        if ch == "ñ":
            phonemes.append("NY")
            i += 1
            continue
        if ch == "v":
            phonemes.append("B")
            i += 1
            continue
        if ch == "z":
            phonemes.append("S")
            i += 1
            continue

        mapped = _SIMPLE_CONSONANTS.get(ch)
        if mapped is not None:
            phonemes.append(mapped)
        i += 1

    return Pronunciation(phonemes=tuple(phonemes), syllables=len(syllables))
