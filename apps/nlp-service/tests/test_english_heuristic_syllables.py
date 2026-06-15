import pytest

from app.domain.languages.english.engine import _english_heuristic_syllable_count


@pytest.mark.parametrize(
    "word, expected",
    [
        ("cat", 1),
        ("wonderful", 3),
        # Hiatus cases (Q6): vowel pairs split across syllables.
        ("create", 2),  # cre-ate
        ("idea", 3),  # i-de-a
        ("being", 2),  # be-ing
        ("video", 3),  # vi-de-o
        ("boa", 2),  # bo-a
        ("poem", 2),  # po-em
        ("duo", 2),  # du-o
        ("fluent", 2),  # flu-ent
        ("radio", 3),  # ra-di-o
        ("media", 3),  # me-di-a
        # Silent-e and -le handling, unaffected by the hiatus fix.
        ("table", 2),
        ("able", 2),
    ],
)
def test_english_heuristic_syllable_count(word: str, expected: int) -> None:
    assert _english_heuristic_syllable_count(word) == expected
