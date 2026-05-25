import pytest

from app.domain.nlp.perspective import classify_person


@pytest.mark.parametrize(
    "token,language,expected",
    [
        ("i", "en", "first"),
        ("me", "en", "first"),
        ("we", "en", "first"),
        ("i'm", "en", "first"),
        ("you", "en", "second"),
        ("your", "en", "second"),
        ("you're", "en", "second"),
        ("he", "en", "third"),
        ("they", "en", "third"),
        ("their", "en", "third"),
        ("sky", "en", None),
        ("", "en", None),
        ("yo", "es", "first"),
        ("nuestra", "es", "first"),
        ("tú", "es", "second"),
        ("tu", "es", "second"),
        ("ustedes", "es", "second"),
        ("él", "es", "third"),
        ("sus", "es", "third"),
        ("noche", "es", None),
        ("yo", "fr", None),
    ],
)
def test_classify_person(token: str, language: str, expected: str | None) -> None:
    assert classify_person(token, language) == expected
