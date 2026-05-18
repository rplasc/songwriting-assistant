from app.domain.rhyme_rules import family_rhyme_key, rhyme_key


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


def test_family_key_anchors_on_last_vowel_regardless_of_stress() -> None:
    # "wonderful": W AH1 N D ER0 F AH0 L  -> last vowel AH0 -> AH0_L
    assert family_rhyme_key(["W", "AH1", "N", "D", "ER0", "F", "AH0", "L"]) == "AH0_L"
    # "beautiful": B Y UW1 T AH0 F AH0 L  -> same tail.
    assert family_rhyme_key(["B", "Y", "UW1", "T", "AH0", "F", "AH0", "L"]) == "AH0_L"


def test_family_key_collapses_to_perfect_for_final_stressed_vowel() -> None:
    # When the last vowel IS the stressed vowel, family and perfect agree.
    phonemes = ["F", "AY1", "ER0"]
    # "fire"'s last vowel is ER0 (unstressed), so family key is just "ER0".
    assert family_rhyme_key(phonemes) == "ER0"
    # Single-vowel word: "cat" K AE1 T  -> last vowel is AE1, family == perfect.
    cat = ["K", "AE1", "T"]
    assert family_rhyme_key(cat) == rhyme_key(cat)


def test_family_key_returns_none_without_vowel() -> None:
    assert family_rhyme_key(["K", "T"]) is None
    assert family_rhyme_key([]) is None
