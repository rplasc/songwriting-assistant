"""Tests for Spanish morphological inflection detection."""

import pytest

from app.domain.languages.spanish.inflection import is_same_stem_inflection


# ---------------------------------------------------------------------------
# -ar verb conjugation families
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,candidate", [
    ("canto", "cantaba"),
    ("canto", "cantamos"),
    ("canto", "cantarán"),
    ("canto", "cantaría"),
    ("canto", "cantando"),
    ("canto", "cantado"),
    ("cantar", "canto"),
    ("cantar", "cantabais"),
    ("hablar", "hablaba"),
    ("hablar", "hablaré"),
    ("hablar", "hablando"),
])
def test_ar_verb_inflections_detected(query: str, candidate: str) -> None:
    assert is_same_stem_inflection(query, candidate), (
        f"Expected {query!r} + {candidate!r} to be same-stem inflection"
    )


# ---------------------------------------------------------------------------
# -er verb conjugation families
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,candidate", [
    ("comer", "comía"),
    ("comer", "comiendo"),
    ("comer", "comido"),
    ("comer", "comeré"),
    ("comer", "comería"),
    ("tener", "tenía"),
    ("tener", "teniendo"),
])
def test_er_verb_inflections_detected(query: str, candidate: str) -> None:
    assert is_same_stem_inflection(query, candidate), (
        f"Expected {query!r} + {candidate!r} to be same-stem inflection"
    )


# ---------------------------------------------------------------------------
# -ir verb conjugation families
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,candidate", [
    ("vivir", "vivía"),
    ("vivir", "viviendo"),
    ("vivir", "vivido"),
    ("vivir", "viviré"),
    ("sentir", "sentía"),
    # Note: sentir->sintiendo involves a stem vowel change (e→i), which requires
    # a full morphological analyser — not handled by suffix-stripping.
])
def test_ir_verb_inflections_detected(query: str, candidate: str) -> None:
    assert is_same_stem_inflection(query, candidate), (
        f"Expected {query!r} + {candidate!r} to be same-stem inflection"
    )


# ---------------------------------------------------------------------------
# Noun/adjective gender and plural pairs
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,candidate", [
    ("niño", "niña"),
    ("niña", "niño"),
    ("libro", "libros"),
    ("libro", "libras"),
    ("casa", "casas"),
    ("ciudad", "ciudades"),
])
def test_noun_adj_pairs_detected(query: str, candidate: str) -> None:
    assert is_same_stem_inflection(query, candidate), (
        f"Expected {query!r} + {candidate!r} to be same-stem inflection"
    )


# ---------------------------------------------------------------------------
# Negative cases: unrelated words should NOT trigger the penalty
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("query,candidate", [
    ("amor", "dolor"),
    ("vida", "nada"),
    ("corazón", "razón"),
    ("canto", "manto"),
    ("flor", "color"),
    ("sol", "vol"),
    ("run", "run"),           # same word
    ("", "algo"),             # empty query
])
def test_unrelated_words_not_flagged(query: str, candidate: str) -> None:
    assert not is_same_stem_inflection(query, candidate), (
        f"Expected {query!r} + {candidate!r} NOT to be same-stem inflection"
    )
