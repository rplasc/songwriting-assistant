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


def _phonemes_for(token: Token) -> list[tuple[str, ...]]:
    phonemes = _PHONEMES.get(token.normalized)
    return [phonemes] if phonemes is not None else []


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
    def sparse(token: Token) -> list[tuple[str, ...]]:
        if token.normalized == "mat":
            return []
        return _phonemes_for(token)

    groups = find_inner_rhyme_groups(
        [_line(["cat", "sat", "mat"])],
        sparse,
        "en",
    )
    # mat dropped; cat/sat still form a perfect group
    occ = groups[0].occurrences
    assert {o.normalized for o in occ} == {"cat", "sat"}


def test_single_letter_words_skipped() -> None:
    def phon(token: Token) -> list[tuple[str, ...]]:
        phonemes = {"a": ("AH0",), "i": ("AY1",)}.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups([_line(["a", "i", "a"])], phon, "en")
    assert groups == []


def test_heteronym_joins_either_pronunciation_group() -> None:
    # "read" can be R IY1 D (present) or R EH1 D (past). It should be able to
    # join a "reed"-style group OR a "red"-style group via either variant.
    def phon(token: Token) -> list[tuple[str, ...]]:
        table: dict[str, list[tuple[str, ...]]] = {
            "read": [("R", "IY1", "D"), ("R", "EH1", "D")],
            "feed": [("F", "IY1", "D")],
            "fed": [("F", "EH1", "D")],
        }
        return table.get(token.normalized, [])

    groups = find_inner_rhyme_groups(
        [_line(["read", "feed", "fed"])], phon, "en"
    )
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    # Both the IY1_D and EH1_D buckets get merged because "read" sits in both,
    # producing one group with all three words.
    assert len(perfect) == 1
    assert {o.normalized for o in perfect[0].occurrences} == {"read", "feed", "fed"}


def test_unknown_word_heuristic_tail_can_match() -> None:
    # An unknown word's second heuristic tail (EH1_T) matches "set", even
    # though its first tail (IY1_T) doesn't match anything.
    def phon(token: Token) -> list[tuple[str, ...]]:
        if token.normalized == "zeb":
            return [("Z", "IY1", "T"), ("Z", "EH1", "T")]
        if token.normalized == "set":
            return [("S", "EH1", "T")]
        return []

    groups = find_inner_rhyme_groups([_line(["zeb", "set"])], phon, "en")
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    assert {o.normalized for o in perfect[0].occurrences} == {"zeb", "set"}


def test_function_words_do_not_seed_near_groups() -> None:
    # "them" (DH EH1 M) and "ten" (T EH1 N) share the inner near key
    # (EH + nasal coda), but "them" is a function word -> no near group.
    def phon(token: Token) -> list[tuple[str, ...]]:
        table = {
            "them": ("DH", "EH1", "M"),
            "ten": ("T", "EH1", "N"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups([_line(["them", "ten"])], phon, "en")
    assert groups == []
    # Sanity: the same sounds on content words DO form a near group.
    def phon_content(token: Token) -> list[tuple[str, ...]]:
        table = {
            "hem": ("HH", "EH1", "M"),
            "ten": ("T", "EH1", "N"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups([_line(["hem", "ten"])], phon_content, "en")
    assert [g.rhyme_type for g in groups] == ["near"]


def test_all_function_word_perfect_group_is_suppressed() -> None:
    # "you"/"do" rhyme perfectly but highlighting them is noise; adding a
    # content word ("true") anchors the group and lets them ride along.
    def phon(token: Token) -> list[tuple[str, ...]]:
        table = {
            "you": ("Y", "UW1"),
            "do": ("D", "UW1"),
            "true": ("T", "R", "UW1"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    assert find_inner_rhyme_groups([_line(["you", "do"])], phon, "en") == []
    groups = find_inner_rhyme_groups([_line(["you", "do", "true"])], phon, "en")
    assert len(groups) == 1
    assert {o.normalized for o in groups[0].occurrences} == {"you", "do", "true"}


def test_deterministic_ids() -> None:
    line = _line(["cat", "sat", "mat"])
    g1 = find_inner_rhyme_groups([line], _phonemes_for, "en")
    g2 = find_inner_rhyme_groups([line], _phonemes_for, "en")
    assert [g.id for g in g1] == [g.id for g in g2]
    assert all(g.id.startswith("irh_") for g in g1)
