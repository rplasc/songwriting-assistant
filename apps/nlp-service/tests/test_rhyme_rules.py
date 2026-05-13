from app.domain.rhyme_rules import rhyme_key


def test_rhyme_key_uses_last_stressed_vowel() -> None:
    # cmudict pronunciation for "fire": F AY1 ER0
    assert rhyme_key(["F", "AY1", "ER0"]) == "AY1_ER0"


def test_rhyme_key_handles_unstressed_only() -> None:
    # Contrived: no stress markers; falls back to last vowel.
    assert rhyme_key(["P", "AH0", "T", "AH0"]) == "AH0"


def test_rhyme_key_returns_none_without_vowel() -> None:
    assert rhyme_key(["K", "T"]) is None
    assert rhyme_key([]) is None


def test_two_rhyming_words_share_key() -> None:
    # "higher": HH AY1 ER0  shares rhyme key with "fire".
    assert rhyme_key(["HH", "AY1", "ER0"]) == rhyme_key(["F", "AY1", "ER0"])
