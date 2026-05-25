"""Rhyme-family classification table tests."""

from __future__ import annotations

from app.domain.rhyme.rhyme_family import classify_rhyme_family


def test_multisyllabic_tier_classifies_as_multisyllabic() -> None:
    assert (
        classify_rhyme_family(tier_name="multisyllabic", language="en")
        == "multisyllabic"
    )
    assert (
        classify_rhyme_family(tier_name="multisyllabic", language="es")
        == "multisyllabic"
    )


def test_english_perfect_tier_short_query_is_perfect() -> None:
    # "cat" / "hat" — perfect tier, but no multisyllabic key on either.
    fam = classify_rhyme_family(
        tier_name="perfect",
        language="en",
        query_phonemes=("K", "AE1", "T"),
        candidate_phonemes=("HH", "AE1", "T"),
    )
    assert fam == "perfect"


def test_english_perfect_tier_long_match_is_multisyllabic() -> None:
    # "ridiculous" / "meticulous" — both have multisyllabic keys and they
    # match.
    q = ("R", "IH0", "D", "IH1", "K", "Y", "AH0", "L", "AH0", "S")
    c = ("M", "AH0", "T", "IH1", "K", "Y", "AH0", "L", "AH0", "S")
    fam = classify_rhyme_family(
        tier_name="perfect",
        language="en",
        query_phonemes=q,
        candidate_phonemes=c,
    )
    assert fam == "multisyllabic"


def test_english_family_tier_is_multisyllabic() -> None:
    fam = classify_rhyme_family(tier_name="family", language="en")
    assert fam == "multisyllabic"


def test_english_near_tier_is_near() -> None:
    fam = classify_rhyme_family(tier_name="near", language="en")
    assert fam == "near"


def test_spanish_consonant_short_is_consonant() -> None:
    fam = classify_rhyme_family(
        tier_name="consonant",
        language="es",
        query_phonemes=("S", "O", "L"),  # no stress digit in test data is fine
        candidate_phonemes=("R", "O", "L"),
    )
    assert fam == "consonant"


def test_spanish_consonant_long_is_multisyllabic() -> None:
    # "ventana" vs "mañana" — share a multisyllabic stressed tail.
    q = ("B", "E0", "N", "T", "A1", "N", "A0")
    c = ("M", "A0", "N", "Y", "A1", "N", "A0")
    fam = classify_rhyme_family(
        tier_name="consonant",
        language="es",
        query_phonemes=q,
        candidate_phonemes=c,
    )
    assert fam == "multisyllabic"


def test_spanish_assonant_is_assonant() -> None:
    fam = classify_rhyme_family(tier_name="assonant", language="es")
    assert fam == "assonant"


def test_unknown_tier_falls_back_to_near() -> None:
    fam = classify_rhyme_family(tier_name="bogus", language="en")
    assert fam == "near"
