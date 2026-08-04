"""Unit tests for the line-ending cadence key."""

from app.domain.rhyme.ending_cadence_rules import ending_cadence_key, vowel_count

_SANDWICHES = ("S", "AE1", "N", "W", "IH0", "CH", "AH0", "Z")
_ALLOWANCES = ("AH0", "L", "AW1", "AH0", "N", "S", "AH0", "Z")


def test_cadence_pair_shares_key() -> None:
    # Different stressed vowels and exact tails, same delivery shape:
    # three syllables from the stress, reduced final vowel, fricative coda.
    assert ending_cadence_key(_SANDWICHES) == "3_x_fric"
    assert ending_cadence_key(_ALLOWANCES) == "3_x_fric"


def test_monosyllabic_tail_has_no_cadence() -> None:
    # "crime": one syllable after the stress -> the perfect/near tiers' job.
    assert ending_cadence_key(("K", "R", "AY1", "M")) is None


def test_no_stressed_vowel_has_no_cadence() -> None:
    assert ending_cadence_key(("DH", "AH0")) is None
    assert ending_cadence_key(("SH",)) is None


def test_non_reduced_final_vowel_keeps_its_base() -> None:
    # "melody": final IY0 is unstressed but not schwa-family, so it stays IY —
    # "melody" should not cadence-match "sandwiches".
    assert ending_cadence_key(("M", "EH1", "L", "AH0", "D", "IY0")) == "3_IY"


def test_syllable_count_distinguishes_cadences() -> None:
    # "syrup": two syllables from the stress -> 2_x_stop, which cannot match
    # the three-beat 3_x_fric endings.
    assert ending_cadence_key(("S", "IH1", "R", "AH0", "P")) == "2_x_stop"


def test_vowel_count() -> None:
    assert vowel_count(_SANDWICHES) == 3
    assert vowel_count(("K", "R", "AY1", "M")) == 1
    assert vowel_count(("SH",)) == 0
