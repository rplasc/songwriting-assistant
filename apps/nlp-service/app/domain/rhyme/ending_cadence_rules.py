"""Line-ending cadence matching.

The perfect tail key demands exact phonemes and the inner near key demands a
matching stressed rime, so multisyllabic line endings that rhyme *rhythmically*
— "sandwiches" / "allowances", where the delivery lands the same even though
the stressed vowels differ — connect through neither. What those endings share
is cadence: the same number of syllables from the last stress plus a matching
reduced final rime.

``ending_cadence_key`` captures exactly that. It is deliberately looser than
the other keys and is only safe because the inner-rhyme detector restricts it
to line-final words (see ``inner_rhyme_rules``): at a line ending the cadence
IS the rhyme delivery, while mid-line the same key would flood the highlight
with false positives.
"""

from collections.abc import Sequence

from app.domain.near_rhyme_rules import _MANNER_CLASS

# A cadence needs at least two syllables after (and including) the last stress;
# monosyllabic tails are the perfect/near tiers' territory.
_MIN_CADENCE_VOWELS = 2

# Unstressed-final vowels that reduce toward schwa in sung/spoken delivery.
# They collapse to one symbol so "sandwiches" (…IH0 CH AH0 Z) and
# "allowances" (…AH0 N S AH0 Z) agree on their final rime.
_REDUCED_VOWELS = frozenset({"AH", "IH", "ER"})


def _is_vowel(phoneme: str) -> bool:
    """ARPABET vowels carry a stress digit at the end (0, 1, or 2)."""
    return bool(phoneme) and phoneme[-1].isdigit()


def _vowel_base(phoneme: str) -> str:
    return phoneme[:-1] if _is_vowel(phoneme) else phoneme


def vowel_count(phonemes: Sequence[str]) -> int:
    """Number of vowel phonemes — the syllable count for ARPABET sequences."""
    return sum(1 for p in phonemes if _is_vowel(p))


def ending_cadence_key(phonemes: Sequence[str]) -> str | None:
    """Key describing the rhythmic shape of a word's ending.

    Anchored on the last *stressed* vowel (no fallback — cadence hinges on a
    stress landing), the key joins:

      - the syllable count of the tail, so endings only match when the
        delivery spans the same number of beats
      - the final vowel's base, reduced to ``"x"`` when it is an unstressed
        schwa-family vowel (see ``_REDUCED_VOWELS``)
      - the manner class of each consonant after the final vowel

    "sandwiches" (S AE1 N W IH0 CH AH0 Z) -> ``3_x_fric``
    "allowances" (AH0 L AW1 AH0 N S AH0 Z) -> ``3_x_fric``
    "melody" (M EH1 L AH0 D IY0) -> ``3_IY``
    "crime" (K R AY1 M) -> ``None`` (monosyllabic tail)
    """
    last_stressed = -1
    for i, p in enumerate(phonemes):
        if _is_vowel(p) and p[-1] in ("1", "2"):
            last_stressed = i
    if last_stressed < 0:
        return None
    tail = phonemes[last_stressed:]
    vowel_positions = [i for i, p in enumerate(tail) if _is_vowel(p)]
    if len(vowel_positions) < _MIN_CADENCE_VOWELS:
        return None
    final_idx = vowel_positions[-1]
    final_vowel = tail[final_idx]
    base = _vowel_base(final_vowel)
    final_part = "x" if final_vowel[-1] == "0" and base in _REDUCED_VOWELS else base
    parts = [str(len(vowel_positions)), final_part]
    for consonant in tail[final_idx + 1 :]:
        parts.append(_MANNER_CLASS.get(consonant, consonant))
    return "_".join(parts)


__all__ = ["ending_cadence_key", "vowel_count"]
