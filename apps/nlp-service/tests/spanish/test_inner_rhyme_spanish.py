"""Spanish inner-rhyme highlighting.

Spanish runs the same detector as English but with a stricter hand, because the
English thresholds are vacuous under Spanish phonology: five vowels make
mid-line assonance close to coincidence, and nearly every word clears two
syllables. These tests pin the Spanish-specific rules.

Lines are invented for the tests — never lyrics from a real song.
"""

from __future__ import annotations

from app.domain.languages.spanish.engine import SpanishEngine
from app.domain.rhyme.inner_rhyme_rules import (
    find_inner_rhyme_groups,
    spanish_phonemes_for,
    spanish_syllables_for,
)
from app.schemas.responses import InnerRhymeGroup

_engine = SpanishEngine()


def _groups(*lines: str) -> list[InnerRhymeGroup]:
    tokenized = [(i + 1, _engine.tokenize_line(line)) for i, line in enumerate(lines)]
    return find_inner_rhyme_groups(
        tokenized,
        spanish_phonemes_for({}),
        "es",
        spanish_syllables_for({}),
    )


def _words(group: InnerRhymeGroup) -> set[str]:
    return {o.normalized for o in group.occurrences}


def _all_highlighted(groups: list[InnerRhymeGroup]) -> set[str]:
    return {o.normalized for g in groups for o in g.occurrences}


# ── Function words ────────────────────────────────────────────────────────


def test_mid_line_function_words_never_highlight() -> None:
    # "no", "hasta" and "más" were missing from a stale hand-rolled list and
    # highlighted as content words all over the page.
    groups = _groups(
        "Que no me falte hasta el final",
        "Y no me pidas más silencio",
        "Pero no quiero mas distancia",
    )
    highlighted = _all_highlighted(groups)
    assert not highlighted & {"no", "hasta", "más", "mas"}


def test_accented_function_words_are_recognized() -> None:
    # The Spanish normalizer keeps accents, so an accented function word only
    # matches the list if the list has the accented spelling.
    groups = _groups("Tú sabes que él vino", "Tú sientes que él espera")
    assert not _all_highlighted(groups) & {"tú", "él"}


# ── Assonance is a line-ending phenomenon ─────────────────────────────────


def test_mid_line_assonance_is_not_a_group() -> None:
    # "sueño"/"vuelvo" share the assonant key E_O. Mid-line that is a
    # coincidence of a five-vowel inventory, not craft.
    groups = _groups(
        "Un sueño roto en la manana",
        "Y vuelvo lento por la tarde",
    )
    assert not _all_highlighted(groups) & {"sueño", "vuelvo"}


def test_line_final_assonance_is_a_group() -> None:
    groups = _groups("Camino contra el viento", "La noche enciende el fuego")
    assert len(groups) == 1
    assert _words(groups[0]) == {"viento", "fuego"}
    assert groups[0].rhyme_type == "near"


def test_line_final_assonance_survives_accented_endings() -> None:
    # murió / ardor both reduce to the assonant key "O"; guards the
    # accent-preserving tokenizer as much as the key function.
    groups = _groups("Y en rezos nunca murió", "Por donde no hay ardor")
    assert len(groups) == 1
    assert _words(groups[0]) == {"murió", "ardor"}


# ── Consonant (perfect) tier ──────────────────────────────────────────────


def test_consonant_end_rhyme_family_groups_as_perfect() -> None:
    groups = _groups(
        "El viento del invierno me ha llamado",
        "La sombra de tu nombre se ha borrado",
        "Y vuelvo a levantar lo que he dejado",
        "Un pajaro dormido en el tejado",
    )
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    assert _words(perfect[0]) == {"llamado", "borrado", "dejado", "tejado"}


def test_two_syllable_mid_line_match_does_not_anchor() -> None:
    # Spanish words are overwhelmingly 2+ syllables, so at the English
    # threshold this pair would anchor itself and survive. The Spanish bar is
    # three syllables.
    groups = _groups(
        "La casa vieja guarda polvo",
        "Su casa nueva guarda humo",
    )
    assert not _all_highlighted(groups) & {"casa"}


def test_diphthong_monosyllables_do_not_anchor() -> None:
    # Spanish G2P emits one vowel phoneme per vowel *letter*, so counting
    # vowels makes "bien" and "dios" look like two syllables. They are one.
    groups = _groups(
        "Yo canto bien temprano",
        "Le pido a dios paciencia",
    )
    assert not _all_highlighted(groups) & {"bien", "dios"}


# ── Repetition is not rhyme ───────────────────────────────────────────────


def test_repeated_stanza_produces_no_groups_by_itself() -> None:
    # A repeated chorus otherwise makes every one of its words rhyme with its
    # own echo, painting the refrain in as many colors as it has words.
    stanza = [
        "Que limpie el polvo de mi frente",
        "Que guarde el fuego con tu nombre",
        "Que sea un rio de piedra",
    ]
    assert _groups(*stanza, *stanza) == []


def test_repeated_line_does_not_block_a_real_rhyme() -> None:
    # The repeat contributes nothing, but the genuine end-rhyme between two
    # *different* lines still forms — and both copies of the repeated line
    # keep their highlight.
    groups = _groups(
        "Camino contra el viento",
        "La noche enciende el fuego",
        "Camino contra el viento",
    )
    assert len(groups) == 1
    assert _words(groups[0]) == {"viento", "fuego"}
    assert sorted(o.line_index for o in groups[0].occurrences) == [1, 2, 3]
