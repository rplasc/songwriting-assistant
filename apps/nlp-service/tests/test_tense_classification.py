import pytest

from app.domain.nlp.tense import classify_tense


@pytest.mark.parametrize(
    "token,expected",
    [
        ("walked", "past"),
        ("walking", "present"),
        ("ran", "past"),
        ("was", "past"),
        ("am", "present"),
        ("is", "present"),
        ("i'm", "present"),
        ("will", "future"),
        ("won't", "future"),
        ("i'll", "future"),
        ("bed", None),
        ("red", None),
        ("good", None),
        ("sky", None),
        ("a", None),
        ("", None),
    ],
)
def test_english_tense(token: str, expected: str | None) -> None:
    assert classify_tense(token, "en") == expected


@pytest.mark.parametrize(
    "token,expected",
    [
        ("cantaba", "past"),
        ("cantaron", "past"),
        ("cantamos", "past"),
        ("cantaré", "future"),
        ("cantaremos", "future"),
        ("cantarán", "future"),
        ("cantan", "present"),
        ("comemos", "present"),
        ("cantando", "present"),
        ("fui", "past"),
        ("soy", "present"),
        ("noche", None),
        ("a", None),
        ("", None),
    ],
)
def test_spanish_tense(token: str, expected: str | None) -> None:
    assert classify_tense(token, "es") == expected


def test_unknown_language_returns_none() -> None:
    assert classify_tense("walked", "fr") is None
