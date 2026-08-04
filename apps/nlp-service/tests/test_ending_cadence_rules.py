"""Unit tests for the multisyllabic cadence key."""

from app.domain.rhyme.ending_cadence_rules import (
    destress,
    ending_cadence_key,
    vowel_count,
)

_SANDWICHES = ("S", "AE1", "N", "W", "IH0", "CH", "AH0", "Z")
_ALLOWANCES = ("AH0", "L", "AW1", "AH0", "N", "S", "AH0", "Z")
_ANALYSTS = ("AE1", "N", "AH0", "L", "IH0", "S", "T", "S")
_COUNTERFEITS = ("K", "AW1", "N", "T", "ER0", "F", "IH2", "T", "S")


def test_cadence_family_shares_key() -> None:
    # Different stressed vowels, exact tails, and interior consonants — but
    # the same delivery shape: three beats from the primary stress, reduced
    # final vowel, fricative close.
    assert ending_cadence_key(_SANDWICHES) == "3_x_fric"
    assert ending_cadence_key(_ALLOWANCES) == "3_x_fric"
    assert ending_cadence_key(_ANALYSTS) == "3_x_fric"
    assert ending_cadence_key(_COUNTERFEITS) == "3_x_fric"


def test_anchor_prefers_primary_stress() -> None:
    # "counterfeits" ends on a secondary-stressed syllable (IH2); the cadence
    # must anchor on the primary (AW1) or the tail is one syllable and dies.
    assert ending_cadence_key(_COUNTERFEITS) is not None


def test_secondary_stressed_final_vowel_reduces() -> None:
    # The IH2 in "counterfeits" reduces to "x" like an unstressed IH0 —
    # that's what lets it join the sandwiches/allowances family above.
    assert ending_cadence_key(_COUNTERFEITS) == ending_cadence_key(_SANDWICHES)


def test_short_tails_have_no_cadence() -> None:
    # "crime" (one beat) and "syrup" (two beats): the perfect/near tiers'
    # job. The 3-beat minimum is what makes mid-line candidacy safe.
    assert ending_cadence_key(("K", "R", "AY1", "M")) is None
    assert ending_cadence_key(("S", "IH1", "R", "AH0", "P")) is None
    assert ending_cadence_key(("P", "EY1", "S", "T", "AH2", "B")) is None


def test_no_stressed_vowel_has_no_cadence() -> None:
    assert ending_cadence_key(("DH", "AH0")) is None
    assert ending_cadence_key(("SH",)) is None


def test_non_reduced_final_vowel_keeps_its_base() -> None:
    # "melody": final IY0 is unstressed but not schwa-family, so it stays IY —
    # "melody" must not cadence-match "sandwiches".
    assert ending_cadence_key(("M", "EH1", "L", "AH0", "D", "IY0")) == "3_IY"


def test_syllable_count_distinguishes_cadences() -> None:
    # Four beats from the stress cannot match three.
    four = ("K", "AA1", "M", "P", "L", "IH0", "K", "EY0", "T", "IH0", "D")
    assert ending_cadence_key(four) is not None
    assert ending_cadence_key(four) != ending_cadence_key(_SANDWICHES)


def test_destress_zeroes_vowel_digits_only() -> None:
    assert destress(("DH", "IH1", "S")) == ("DH", "IH0", "S")
    assert destress(("K", "T")) == ("K", "T")


def test_vowel_count() -> None:
    assert vowel_count(_SANDWICHES) == 3
    assert vowel_count(("K", "R", "AY1", "M")) == 1
    assert vowel_count(("SH",)) == 0
