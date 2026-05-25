"""Multisyllabic rhyme-key behavior."""

from __future__ import annotations

import pytest

from app.domain.rhyme.multisyllabic_rules import multisyllabic_rhyme_key


def test_empty_phonemes_returns_none() -> None:
    assert multisyllabic_rhyme_key(()) is None


def test_no_stressed_vowel_returns_none() -> None:
    # All vowels unstressed (stress digit 0) -> no anchor.
    assert multisyllabic_rhyme_key(("AH0", "L")) is None


def test_single_vowel_in_tail_returns_none() -> None:
    # "cat": K AE1 T -> tail = AE1 T -> only 1 vowel -> None.
    assert multisyllabic_rhyme_key(("K", "AE1", "T")) is None


def test_two_vowel_tail_returns_joined_key() -> None:
    # "wonderful": W AH1 N D ER0 F AH0 L
    # tail from AH1 onward has 3 vowels -> qualifies.
    key = multisyllabic_rhyme_key(
        ("W", "AH1", "N", "D", "ER0", "F", "AH0", "L")
    )
    assert key == "AH1_N_D_ER0_F_AH0_L"


def test_phrase_concatenation_produces_long_key() -> None:
    # "hold me": HH OW1 L D + M IY0 -> 2 vowels in stressed-tail.
    key = multisyllabic_rhyme_key(
        ("HH", "OW1", "L", "D", "M", "IY0")
    )
    assert key == "OW1_L_D_M_IY0"


def test_min_vowels_parameter_is_honored() -> None:
    # With min_vowels=3, "hold me" (2 vowels) should drop out.
    assert (
        multisyllabic_rhyme_key(
            ("HH", "OW1", "L", "D", "M", "IY0"), min_vowels=3
        )
        is None
    )


@pytest.mark.parametrize(
    "phonemes,expected_match",
    [
        # "ridiculous" and "meticulous" share the same multisyllabic tail.
        (("R", "IH0", "D", "IH1", "K", "Y", "AH0", "L", "AH0", "S"), True),
        (("M", "AH0", "T", "IH1", "K", "Y", "AH0", "L", "AH0", "S"), True),
    ],
)
def test_multisyllabic_pairs_share_key(
    phonemes: tuple[str, ...], expected_match: bool
) -> None:
    reference = multisyllabic_rhyme_key(
        ("R", "IH0", "D", "IH1", "K", "Y", "AH0", "L", "AH0", "S")
    )
    assert reference is not None
    actual = multisyllabic_rhyme_key(phonemes)
    if expected_match:
        assert actual == reference
