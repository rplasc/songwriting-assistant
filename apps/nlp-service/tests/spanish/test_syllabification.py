import json
from pathlib import Path

import pytest

from app.domain.languages.spanish.syllabification import syllabify

_GOLDEN = Path(__file__).resolve().parents[2] / "app" / "evaluation" / "golden_sets" / "spanish" / "syllables.json"


@pytest.mark.parametrize("case", json.loads(_GOLDEN.read_text(encoding="utf-8")))
def test_syllables_match_golden(case: dict) -> None:
    word = case["word"]
    expected_syllables = case["syllables"]
    expected_stress = case["stress_index"]
    syllables, stress_index = syllabify(word)
    assert syllables == expected_syllables, (
        f"syllabify({word!r}) = {syllables} (expected {expected_syllables})"
    )
    assert stress_index == expected_stress, (
        f"stress index for {word!r} = {stress_index} (expected {expected_stress})"
    )


def test_diphthong_ia() -> None:
    assert syllabify("piano")[0] == ["pia", "no"]


def test_hiatus_when_weak_vowel_accented() -> None:
    # The accent on í forces a syllable split between p-a-í-s.
    assert syllabify("país")[0] == ["pa", "ís"]


def test_valid_onset_keeps_cluster_together() -> None:
    assert syllabify("otro")[0] == ["o", "tro"]


def test_invalid_cluster_splits() -> None:
    assert syllabify("perla")[0] == ["per", "la"]


def test_silent_u_in_qu() -> None:
    assert syllabify("queso")[0] == ["que", "so"]


def test_silent_u_in_gu_before_e() -> None:
    assert syllabify("guerra")[0] == ["gue", "rra"]
