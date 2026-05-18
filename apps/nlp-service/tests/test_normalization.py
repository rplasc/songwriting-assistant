from app.domain.normalization import expand_basic_contractions, normalize_word


def test_normalize_word_strips_punctuation() -> None:
    assert normalize_word("Fire!") == "fire"
    assert normalize_word("  Eyes,  ") == "eyes"
    assert normalize_word("(love)") == "love"


def test_normalize_word_handles_curly_quotes() -> None:
    assert normalize_word("don’t") == "don't"


def test_normalize_word_handles_em_dash() -> None:
    assert normalize_word("fire—") == "fire"


def test_normalize_word_rejects_empty_or_non_word() -> None:
    assert normalize_word("") is None
    assert normalize_word("   ") is None
    assert normalize_word("1234") is None
    assert normalize_word("!!!") is None


def test_expand_basic_contractions() -> None:
    assert expand_basic_contractions("I don't know") == "I do not know"
    assert expand_basic_contractions("we're here") == "we are here"
    assert expand_basic_contractions("nothing to expand") == "nothing to expand"


def test_expand_handles_lyric_style_contractions() -> None:
    assert expand_basic_contractions("y'all gonna see") == "you all going to see"
    assert expand_basic_contractions("I wanna fly") == "I want to fly"
    assert expand_basic_contractions("gimme that") == "give me that"


def test_expand_handles_leading_apostrophe() -> None:
    # 'cause / 'til shouldn't be left as-is.
    assert expand_basic_contractions("'cause I tried") == "because I tried"
    assert expand_basic_contractions("wait 'til dawn") == "wait until dawn"
