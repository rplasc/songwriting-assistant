"""Multisyllabic cadence matching.

The perfect tail key demands exact phonemes and the inner near key demands a
matching stressed rime, so multisyllabic endings that rhyme *rhythmically* —
"sandwiches" / "allowances" / "analysts" / "countin' this", where the delivery
lands the same even though the stressed vowels differ — connect through
neither. What those endings share is cadence: the same number of syllables
from the last primary stress plus a matching reduced final rime.

``ending_cadence_key`` captures exactly that. It is deliberately looser than
the other keys and is only safe because it demands a long tail
(``_MIN_CADENCE_VOWELS`` syllables from the stress): monosyllables and
two-beat endings — the bulk of a lyric — can never produce a key, so the
detector can run this pass over words anywhere in a line, and over line-ending
compound spans ("countin' this"), without flooding the highlight.
"""

from collections.abc import Sequence

from app.domain.near_rhyme_rules import (
    _MANNER_CLASS,
    _last_primary_or_secondary_vowel,
)

# A cadence needs at least three syllables from (and including) the last
# primary stress; shorter tails are the perfect/near tiers' territory. Three
# beats is also what makes the key safe to apply mid-line: only long
# multisyllabic deliveries qualify.
_MIN_CADENCE_VOWELS = 3

# Non-primary final vowels that reduce toward schwa in sung/spoken delivery.
# They collapse to one symbol so "sandwiches" (…IH0 CH AH0 Z), "allowances"
# (…N S AH0 Z), and "counterfeits" (…F IH2 T S) agree on their final rime.
_REDUCED_VOWELS = frozenset({"AH", "IH", "ER"})


def _is_vowel(phoneme: str) -> bool:
    """ARPABET vowels carry a stress digit at the end (0, 1, or 2)."""
    return bool(phoneme) and phoneme[-1].isdigit()


def _vowel_base(phoneme: str) -> str:
    return phoneme[:-1] if _is_vowel(phoneme) else phoneme


def vowel_count(phonemes: Sequence[str]) -> int:
    """Number of vowel phonemes — the syllable count for ARPABET sequences."""
    return sum(1 for p in phonemes if _is_vowel(p))


def destress(phonemes: Sequence[str]) -> tuple[str, ...]:
    """Zero out stress digits — for function words joined into a compound
    span ("countin' *this*"), whose dictionary stress ("this" DH IH1 S) would
    otherwise hijack the span's anchor even though the word is unstressed in
    connected speech."""
    return tuple(p[:-1] + "0" if _is_vowel(p) else p for p in phonemes)


def ending_cadence_key(phonemes: Sequence[str]) -> str | None:
    """Key describing the rhythmic shape of a multisyllabic ending.

    Anchored on the last *primary*-stressed vowel (falling back to the last
    secondary — cadence hinges on where the stress lands), the key joins:

      - the syllable count of the tail, so endings only match when the
        delivery spans the same number of beats
      - the final vowel's base, reduced to ``"x"`` when it is a non-primary
        schwa-family vowel (see ``_REDUCED_VOWELS``)
      - the manner class of the final consonant, if any — the closing sound
        the ear checks; interior consonants are delivery-flexible

    "sandwiches" (S AE1 N W IH0 CH AH0 Z) -> ``3_x_fric``
    "allowances" (AH0 L AW1 AH0 N S AH0 Z) -> ``3_x_fric``
    "analysts" (AE1 N AH0 L IH0 S T S) -> ``3_x_fric``
    "counterfeits" (K AW1 N T ER0 F IH2 T S) -> ``3_x_fric``
    "melody" (M EH1 L AH0 D IY0) -> ``3_IY``
    "syrup" (S IH1 R AH0 P) -> ``None`` (two-beat tail)
    "crime" (K R AY1 M) -> ``None`` (monosyllabic tail)
    """
    start = _last_primary_or_secondary_vowel(phonemes)
    if start < 0:
        return None
    tail = phonemes[start:]
    vowel_positions = [i for i, p in enumerate(tail) if _is_vowel(p)]
    if len(vowel_positions) < _MIN_CADENCE_VOWELS:
        return None
    final_idx = vowel_positions[-1]
    final_vowel = tail[final_idx]
    base = _vowel_base(final_vowel)
    final_part = "x" if final_vowel[-1] != "1" and base in _REDUCED_VOWELS else base
    parts = [str(len(vowel_positions)), final_part]
    coda = tail[final_idx + 1 :]
    if coda:
        parts.append(_MANNER_CLASS.get(coda[-1], coda[-1]))
    return "_".join(parts)


__all__ = ["ending_cadence_key", "destress", "vowel_count"]
