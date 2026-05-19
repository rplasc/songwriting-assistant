from app.domain.languages.spanish.g2p import g2p
from app.domain.languages.spanish.rhyme_rules import (
    assonant_rhyme_key,
    consonant_rhyme_key,
)


def _ck(word: str) -> str | None:
    return consonant_rhyme_key(g2p(word).phonemes)


def _ak(word: str) -> str | None:
    return assonant_rhyme_key(g2p(word).phonemes)


def test_corazon_canclion_pair_share_consonant_key() -> None:
    assert _ck("corazón") == _ck("canción") == _ck("razón")


def test_amor_dolor_share_consonant_key() -> None:
    assert _ck("amor") == _ck("dolor")


def test_manana_ventana_share_assonant_key() -> None:
    # ventana and mañana both end with stressed A1 N A0 → assonant key "A_A".
    assert _ak("mañana") == _ak("ventana") == "A_A"


def test_consonant_implies_assonant() -> None:
    assert _ak("corazón") == _ak("razón")


def test_distinct_words_distinct_consonant_keys() -> None:
    assert _ck("amor") != _ck("corazón")
