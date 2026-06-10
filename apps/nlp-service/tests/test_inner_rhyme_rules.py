"""Unit tests for inner-rhyme detection over positioned tokens."""

from app.domain.rhyme.inner_rhyme_rules import find_inner_rhyme_groups
from app.models.token import Token


def _tok(index: int, text: str, char_start: int) -> Token:
    return Token(
        text=text,
        normalized=text.lower(),
        index=index,
        char_start=char_start,
        char_end=char_start + len(text),
    )


def _line(words: list[str], line_index: int = 0) -> tuple[int, list[Token]]:
    tokens: list[Token] = []
    cursor = 0
    for i, w in enumerate(words):
        tokens.append(_tok(i, w, cursor))
        cursor += len(w) + 1
    return line_index, tokens


# Phoneme map covering the test vocabulary. Keys are normalized words.
_PHONEMES: dict[str, tuple[str, ...]] = {
    "the": ("DH", "AH0"),
    "cat": ("K", "AE1", "T"),
    "sat": ("S", "AE1", "T"),
    "mat": ("M", "AE1", "T"),
    "on": ("AA1", "N"),
    "cad": ("K", "AE1", "D"),
    "feet": ("F", "IY1", "T"),
    "heat": ("HH", "IY1", "T"),
    "dog": ("D", "AO1", "G"),
}


def _phonemes_for(token: Token):
    return _PHONEMES.get(token.normalized)


def test_same_line_perfect_group() -> None:
    groups = find_inner_rhyme_groups(
        [_line(["the", "cat", "sat", "on", "the", "mat"])],
        _phonemes_for,
        "en",
    )
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    g = perfect[0]
    assert g.confidence == "high"
    assert [o.normalized for o in g.occurrences] == ["cat", "sat", "mat"]
    # word indices and char offsets are carried through for highlighting
    assert [o.word_index for o in g.occurrences] == [1, 2, 5]
    assert all(o.line_index == 0 for o in g.occurrences)
    first = g.occurrences[0]
    assert (first.char_start, first.char_end) == (4, 7)


def test_cross_line_perfect_group() -> None:
    groups = find_inner_rhyme_groups(
        [_line(["the", "cat"], 1), _line(["on", "the", "mat"], 2)],
        _phonemes_for,
        "en",
    )
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    occ = perfect[0].occurrences
    assert {(o.line_index, o.normalized) for o in occ} == {(1, "cat"), (2, "mat")}


def test_near_group_when_not_perfect() -> None:
    # cat (…AE1 T) and cad (…AE1 D) are not perfect but are near rhymes.
    groups = find_inner_rhyme_groups(
        [_line(["cat", "cad", "dog"])],
        _phonemes_for,
        "en",
    )
    near = [g for g in groups if g.rhyme_type == "near"]
    assert len(near) == 1
    assert {o.normalized for o in near[0].occurrences} == {"cat", "cad"}
    assert near[0].confidence == "medium"
    # dog rhymes with nothing here -> no group includes it
    assert all("dog" not in {o.normalized for o in g.occurrences} for g in groups)


def test_perfect_takes_precedence_over_near() -> None:
    # cat/sat/mat are perfect; cad would only be near with them. cad should not
    # pull the perfect members into a near group.
    groups = find_inner_rhyme_groups(
        [_line(["cat", "sat", "mat", "cad"])],
        _phonemes_for,
        "en",
    )
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    assert {o.normalized for o in perfect[0].occurrences} == {"cat", "sat", "mat"}
    # cad is alone on its near key now (its only partners were claimed) -> no near group
    assert [g for g in groups if g.rhyme_type == "near"] == []


def test_pure_repetition_is_not_a_rhyme_group() -> None:
    # "the ... the" repeats but is a single distinct word -> excluded.
    groups = find_inner_rhyme_groups(
        [_line(["the", "dog", "the"])],
        _phonemes_for,
        "en",
    )
    assert groups == []


def test_word_without_phonemes_is_skipped() -> None:
    def sparse(token: Token):
        return _PHONEMES.get(token.normalized) if token.normalized != "mat" else None

    groups = find_inner_rhyme_groups(
        [_line(["cat", "sat", "mat"])],
        sparse,
        "en",
    )
    # mat dropped; cat/sat still form a perfect group
    occ = groups[0].occurrences
    assert {o.normalized for o in occ} == {"cat", "sat"}


def test_single_letter_words_skipped() -> None:
    def phon(token: Token):
        return {"a": ("AH0",), "i": ("AY1",)}.get(token.normalized)

    groups = find_inner_rhyme_groups([_line(["a", "i", "a"])], phon, "en")
    assert groups == []


def test_deterministic_ids() -> None:
    line = _line(["cat", "sat", "mat"])
    g1 = find_inner_rhyme_groups([line], _phonemes_for, "en")
    g2 = find_inner_rhyme_groups([line], _phonemes_for, "en")
    assert [g.id for g in g1] == [g.id for g in g2]
    assert all(g.id.startswith("irh_") for g in g1)
