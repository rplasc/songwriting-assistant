"""Tail-only heuristic grapheme-to-phoneme for unknown words.

We don't need a full G2P — only enough to extract a rhyme tail that
`rhyme_key` / `family_rhyme_key` / `near_rhyme_key` can consume. Given an
unknown word, this module finds the last orthographic vowel cluster, applies
English orthography shortcuts (magic-e, syllabic-L, R-coloring, common
digraphs, silent trailing h), and returns a set of plausible ARPABET
phoneme tails. The caller turns those into index keys and unions the
matched words.

Returning multiple candidates is intentional. Beyond letter-cluster ambiguity
("ea" can be IY1 or EH1, "ou" can be AW1/OW1/UW1/AH1), each vowel candidate
is emitted at every stress level (0/1/2) because the corpus indexes preserve
stress: words like "wonderful" and "beautiful" carry their final-syllable
schwa as AH0, so a heuristic that only emits stress-1 vowels would miss the
family-tier `AH0_L` key that ties those words together.
"""

import re

_LAST_VOWEL_RE = re.compile(r"(?P<vowel>[aeiouy]+)(?P<tail>[^aeiouy]*)$")

_MAX_CANDIDATES = 30

_VOWEL_PHONEMES: dict[str, tuple[str, ...]] = {
    # Monographs — broad coverage of common readings.
    "a": ("AE1", "EY1", "AH1"),
    "e": ("EH1", "IY1"),
    "i": ("IH1", "AY1"),
    "o": ("AA1", "OW1", "AO1"),
    "u": ("AH1", "UW1"),
    "y": ("IH1", "AY1"),
    # Digraphs.
    "ee": ("IY1",),
    "ea": ("IY1", "EH1"),
    "ai": ("EY1",),
    "ay": ("EY1",),
    "ei": ("EY1", "IY1"),
    "ey": ("IY1", "EY1"),
    "oa": ("OW1",),
    "oo": ("UW1", "UH1"),
    "ou": ("AW1", "OW1", "UW1", "AH1"),
    "ow": ("AW1", "OW1"),
    "oi": ("OY1",),
    "oy": ("OY1",),
    "au": ("AO1",),
    "aw": ("AO1",),
    "ue": ("UW1",),
    "ui": ("UW1",),
    "ie": ("IY1", "AY1"),
    "eu": ("UW1",),
    # Triphthong-ish.
    "eau": ("OW1",),
}

# Magic-e long-vowel readings (single vowel + single consonant + silent 'e').
_MAGIC_E: dict[str, tuple[str, ...]] = {
    "a": ("EY1",),
    "i": ("AY1",),
    "o": ("OW1",),
    "u": ("UW1",),
    "e": ("IY1",),
}

# R-colored vowels: 'er' / 'ir' / 'ur' all map to ARPABET ER1.
_R_COLORED: frozenset[str] = frozenset(("e", "i", "u"))

_CONSONANT_PHONEMES: dict[str, tuple[str, ...]] = {
    "b": ("B",),
    "c": ("K",),
    "d": ("D",),
    "f": ("F",),
    "g": ("G",),
    "h": ("HH",),
    "j": ("JH",),
    "k": ("K",),
    "l": ("L",),
    "m": ("M",),
    "n": ("N",),
    "p": ("P",),
    "q": ("K",),
    "r": ("R",),
    "s": ("S",),
    "t": ("T",),
    "v": ("V",),
    "w": ("W",),
    "x": ("K", "S"),
    "z": ("Z",),
}

_CONSONANT_DIGRAPHS: dict[str, tuple[str, ...]] = {
    "tch": ("CH",),
    "ch": ("CH",),
    "sh": ("SH",),
    "th": ("TH",),
    "ph": ("F",),
    "ck": ("K",),
    "ng": ("NG",),
    "qu": ("K", "W"),
    "wh": ("W",),
    "gh": (),  # silent in tails ("light", "though")
}

_STRESS_LEVELS = ("0", "1", "2")


def _consonant_tail_phonemes(tail: str) -> list[str]:
    """Walk the consonant tail left-to-right, preferring digraphs, collapsing doubles.

    A tail of just ``"h"`` is treated as silent — covers "oh", "ah", "blah",
    "woah", "yeah", "bleh", where final-h has no phonetic content.
    """
    if tail == "h":
        return []
    out: list[str] = []
    i = 0
    n = len(tail)
    while i < n:
        matched = False
        for span in (3, 2):
            chunk = tail[i : i + span]
            if chunk in _CONSONANT_DIGRAPHS:
                out.extend(_CONSONANT_DIGRAPHS[chunk])
                i += span
                matched = True
                break
        if matched:
            continue
        ch = tail[i]
        # Soft-C and soft-G: c/g before e, i, y → S / JH.
        # The regex-derived tail never contains vowels, so this branch only fires
        # when the function is called directly (e.g. from tests or future callers).
        if ch in "cg" and i + 1 < n and tail[i + 1] in "eiy":
            out.append("S" if ch == "c" else "JH")
            i += 2  # consume the consonant and its following vowel diacritic
            continue
        if i + 1 < n and tail[i + 1] == ch:
            i += 1
        phs = _CONSONANT_PHONEMES.get(ch)
        if phs:
            out.extend(phs)
        i += 1
    return out


def _vowel_candidates(vowel_cluster: str) -> tuple[str, ...]:
    if vowel_cluster in _VOWEL_PHONEMES:
        return _VOWEL_PHONEMES[vowel_cluster]
    return _VOWEL_PHONEMES.get(vowel_cluster[-1], ())


def _expand_stress(vowels: tuple[str, ...]) -> tuple[str, ...]:
    """For each stressed ARPABET vowel, emit the (0, 1, 2) family.

    The corpus stores final unstressed syllables (e.g. AH0 in "wonderful")
    and stressed nuclei (AH1 in "love") as distinct keys, so emitting all
    three stress levels broadens matching dramatically.
    """
    out: list[str] = []
    seen: set[str] = set()
    for v in vowels:
        if v and v[-1].isdigit():
            base = v[:-1]
            for s in _STRESS_LEVELS:
                cand = base + s
                if cand not in seen:
                    seen.add(cand)
                    out.append(cand)
        elif v not in seen:
            seen.add(v)
            out.append(v)
    return tuple(out)


def heuristic_phoneme_tails(word: str) -> list[tuple[str, ...]]:
    """Return up to ``_MAX_CANDIDATES`` ARPABET phoneme tails for ``word``.

    Empty list when the word has no vowel letter at all.
    """
    if not word:
        return []
    w = word.lower().replace("'", "")

    # Syllabic-L pattern (-Cle): "table", "fumble", "glimble". The orthographic
    # 'e' is silent and the 'l' carries its own syllable; CMU realises this as
    # [...vowel...consonant...AH0 L]. Re-anchor on the vowel *before* the
    # consonant cluster so the emitted tail looks like a real CMU tail.
    if (
        len(w) >= 4
        and w.endswith("le")
        and w[-3] not in "aeiouy"
    ):
        stem = w[:-2]
        inner = _LAST_VOWEL_RE.search(stem)
        if inner:
            v_cluster = inner.group("vowel")
            v_tail = inner.group("tail")
            vowels = _vowel_candidates(v_cluster)
            if vowels:
                vowels = _expand_stress(vowels)
                cons = _consonant_tail_phonemes(v_tail)
                tails = [(v, *cons, "AH0", "L") for v in vowels]
                return _dedupe(tails)[:_MAX_CANDIDATES]

    # Magic-e: vowel + single consonant + silent 'e' ("kite", "cute").
    if (
        len(w) >= 4
        and w.endswith("e")
        and w[-2] not in "aeiouy"
        and w[-3] in "aeiouy"
    ):
        magic_vowel = w[-3]
        vowels = _MAGIC_E.get(magic_vowel, _VOWEL_PHONEMES.get(magic_vowel, ()))
        if vowels:
            vowels = _expand_stress(vowels)
            cons_char = w[-2]
            # Soft-C and soft-G: before the silent 'e', c→S and g→JH.
            # Handles "-ace"/"-ice"/"-uce" (place, price,uce) and
            # "-age"/"-ege"/"-uge" (stage, huge).
            if cons_char == "c":
                cons_phonemes: list[str] = ["S"]
            elif cons_char == "g":
                cons_phonemes = ["JH"]
            else:
                cons_phonemes = _consonant_tail_phonemes(cons_char)
            tails = [(v, *cons_phonemes) for v in vowels]
            return _dedupe(tails)[:_MAX_CANDIDATES]

    match = _LAST_VOWEL_RE.search(w)
    if not match:
        return []
    vowel_cluster = match.group("vowel")
    tail = match.group("tail")

    vowels = _vowel_candidates(vowel_cluster)

    # R-coloring: 'er' / 'ir' / 'ur' at the end → ER1 (plus stress siblings).
    if tail == "r" and vowel_cluster in _R_COLORED:
        vowels = ("ER1",) + tuple(v for v in vowels if v != "ER1")
        cons_phonemes: list[str] = []
    else:
        cons_phonemes = _consonant_tail_phonemes(tail)

    if not vowels:
        return []

    vowels = _expand_stress(vowels)
    tails = [(v, *cons_phonemes) for v in vowels]
    return _dedupe(tails)[:_MAX_CANDIDATES]


def _dedupe(tails: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    seen: set[tuple[str, ...]] = set()
    out: list[tuple[str, ...]] = []
    for t in tails:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


__all__ = ["heuristic_phoneme_tails"]
