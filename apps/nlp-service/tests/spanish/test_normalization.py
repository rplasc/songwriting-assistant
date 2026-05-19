from app.domain.languages.spanish.normalization import (
    expand_basic_contractions,
    normalize_word,
)


def test_preserves_accent_marks_and_n_tilde() -> None:
    assert normalize_word("corazón") == "corazón"
    assert normalize_word("niño") == "niño"
    assert normalize_word("país") == "país"
    assert normalize_word("pingüino") == "pingüino"


def test_lowercases() -> None:
    assert normalize_word("Corazón") == "corazón"
    assert normalize_word("MAÑANA") == "mañana"


def test_strips_spanish_inverted_punctuation() -> None:
    assert normalize_word("¡amor!") == "amor"
    assert normalize_word("¿corazón?") == "corazón"


def test_flattens_curly_quotes() -> None:
    assert normalize_word("“mañana”") == "mañana"


def test_rejects_blank_and_pure_punctuation() -> None:
    assert normalize_word("") is None
    assert normalize_word("   ") is None
    assert normalize_word("...") is None


def test_contraction_expansion_del_al() -> None:
    assert expand_basic_contractions("del cielo") == "de el cielo"
    assert expand_basic_contractions("al amanecer") == "a el amanecer"


def test_contraction_lyric_elisions() -> None:
    assert expand_basic_contractions("pa' siempre") == "para siempre"
    assert expand_basic_contractions("tó el día") == "todo el día"
