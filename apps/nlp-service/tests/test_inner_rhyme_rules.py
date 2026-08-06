"""Unit tests for inner-rhyme detection over positioned tokens."""

from app.domain.rhyme.inner_rhyme_rules import (
    HeuristicTailVariants,
    english_phonemes_for,
    find_inner_rhyme_groups,
)
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
    # cat (…AE1 T) and cad (…AE1 D) are not perfect but are near rhymes; the
    # line-final "cad" anchors the group.
    groups = find_inner_rhyme_groups(
        [_line(["cat", "dog", "cad"])],
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


def _function_word_phonemes(token: Token) -> list[tuple[str, ...]]:
    table = {
        "your": ("Y", "AO1", "R"),
        "for": ("F", "AO1", "R"),
        "you": ("Y", "UW1"),
        "do": ("D", "UW1"),
        "dog": ("D", "AO1", "G"),
        "cat": ("K", "AE1", "T"),
    }
    phonemes = table.get(token.normalized)
    return [phonemes] if phonemes is not None else []


def test_function_words_highlight_only_at_line_end() -> None:
    # Mid-line function-word matches ("your" earlier in the line) are exactly
    # the color-fatigue noise the highlighter must suppress — even on an exact
    # sound match.
    groups = find_inner_rhyme_groups(
        [_line(["your", "for"])], _function_word_phonemes, "en"
    )
    assert groups == []

    groups = find_inner_rhyme_groups(
        [_line(["you", "do"])], _function_word_phonemes, "en"
    )
    assert groups == []

    # But lines *ending* on function words carry a real end-rhyme.
    groups = find_inner_rhyme_groups(
        [_line(["dog", "your"], 1), _line(["cat", "for"], 2)],
        _function_word_phonemes,
        "en",
    )
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    assert {o.normalized for o in perfect[0].occurrences} == {"your", "for"}

    groups = find_inner_rhyme_groups(
        [_line(["dog", "you"], 1), _line(["cat", "do"], 2)],
        _function_word_phonemes,
        "en",
    )
    assert [g.rhyme_type for g in groups] == ["perfect"]


def test_deterministic_ids() -> None:
    line = _line(["cat", "sat", "mat"])
    g1 = find_inner_rhyme_groups([line], _phonemes_for, "en")
    g2 = find_inner_rhyme_groups([line], _phonemes_for, "en")
    assert [g.id for g in g1] == [g.id for g in g2]
    assert all(g.id.startswith("irh_") for g in g1)


def test_midline_pair_without_anchor_is_pruned() -> None:
    # feet/heat is a perfect pair, but both sit mid-line as unstressed-position
    # monosyllables with no third member -> incidental, not the scheme.
    groups = find_inner_rhyme_groups(
        [_line(["feet", "heat", "dog"])],
        _phonemes_for,
        "en",
    )
    assert groups == []


def test_line_final_occurrence_anchors_group() -> None:
    # The same pair survives once one member lands on the line ending.
    groups = find_inner_rhyme_groups(
        [_line(["feet", "dog", "heat"])],
        _phonemes_for,
        "en",
    )
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    assert {o.normalized for o in perfect[0].occurrences} == {"feet", "heat"}


def test_dense_midline_chain_survives() -> None:
    # Three or more perfect occurrences mid-line are deliberate craft, not
    # coincidence, even without a line-final or multisyllabic anchor.
    groups = find_inner_rhyme_groups(
        [_line(["cat", "sat", "mat", "dog"])],
        _phonemes_for,
        "en",
    )
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    assert {o.normalized for o in perfect[0].occurrences} == {"cat", "sat", "mat"}


def test_multisyllabic_occurrence_anchors_group() -> None:
    # A multisyllabic member anchors a mid-line pair: the stress landing on a
    # longer word reads as intentional.
    def phon(token: Token) -> list[tuple[str, ...]]:
        table = {
            "delay": ("D", "IH0", "L", "EY1"),
            "play": ("P", "L", "EY1"),
            "dog": ("D", "AO1", "G"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups([_line(["delay", "play", "dog"])], phon, "en")
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    assert {o.normalized for o in perfect[0].occurrences} == {"delay", "play"}


def test_midline_near_pair_is_pruned_without_dense_escape() -> None:
    # Near groups get no dense-chain escape hatch: mid-line monosyllable slant
    # matches are the dominant highlight noise. (Same words as
    # test_near_group_when_not_perfect, but with the anchor position lost.)
    groups = find_inner_rhyme_groups(
        [_line(["cat", "cad", "dog"])],
        _phonemes_for,
        "en",
    )
    assert groups == []


def test_multisyllabic_occurrence_anchors_near_group() -> None:
    # "attack" and "cat" share the inner near key (AE1 + stop coda); the
    # two-syllable "attack" anchors the group even mid-line.
    def phon(token: Token) -> list[tuple[str, ...]]:
        table = {
            "attack": ("AH0", "T", "AE1", "K"),
            "cat": ("K", "AE1", "T"),
            "dog": ("D", "AO1", "G"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups([_line(["cat", "attack", "dog"])], phon, "en")
    near = [g for g in groups if g.rhyme_type == "near"]
    assert len(near) == 1
    assert {o.normalized for o in near[0].occurrences} == {"cat", "attack"}


_CADENCE_PHONEMES: dict[str, tuple[str, ...]] = {
    "sandwiches": ("S", "AE1", "N", "W", "IH0", "CH", "AH0", "Z"),
    "allowances": ("AH0", "L", "AW1", "AH0", "N", "S", "AH0", "Z"),
    "crime": ("K", "R", "AY1", "M"),
    "dog": ("D", "AO1", "G"),
    "feet": ("F", "IY1", "T"),
}


def _cadence_phonemes_for(token: Token) -> list[tuple[str, ...]]:
    phonemes = _CADENCE_PHONEMES.get(token.normalized)
    return [phonemes] if phonemes is not None else []


def test_cadence_connects_multisyllabic_line_endings() -> None:
    # "sandwiches"/"allowances" share no perfect tail and no near key, but the
    # line endings carry the same cadence -> one de-emphasized (near) group.
    groups = find_inner_rhyme_groups(
        [_line(["crime", "sandwiches"], 1), _line(["dog", "allowances"], 2)],
        _cadence_phonemes_for,
        "en",
    )
    assert len(groups) == 1
    g = groups[0]
    assert g.rhyme_type == "near"
    assert g.confidence == "medium"
    assert {o.normalized for o in g.occurrences} == {"sandwiches", "allowances"}


def test_cadence_matches_multisyllabic_words_midline() -> None:
    # Cadence candidacy is position-independent: the 3-beat minimum already
    # limits it to long deliveries, so "sandwiches" mid-line still joins the
    # family ("syrup sandwiches and crime allowances" puts it mid-line).
    groups = find_inner_rhyme_groups(
        [_line(["sandwiches", "dog"], 1), _line(["allowances", "feet"], 2)],
        _cadence_phonemes_for,
        "en",
    )
    assert len(groups) == 1
    assert {o.normalized for o in groups[0].occurrences} == {
        "sandwiches",
        "allowances",
    }


def test_compound_line_ending_spans_rhyme_as_units() -> None:
    # "countin' this" / "downin' this": the trailing function word joins its
    # stress anchor so the compound endings rhyme as units — all four words
    # land in one cadence group.
    def phon(token: Token) -> list[tuple[str, ...]]:
        table = {
            "countin'": ("K", "AW1", "N", "T", "IH0", "N"),
            "downin'": ("D", "AW1", "N", "IH0", "N"),
            "this": ("DH", "IH1", "S"),
            "i'm": ("AY1", "M"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups(
        [_line(["i'm", "countin'", "this"], 1), _line(["i'm", "downin'", "this"], 2)],
        phon,
        "en",
    )
    assert len(groups) == 1
    g = groups[0]
    assert g.rhyme_type == "near"
    assert [(o.line_index, o.normalized) for o in g.occurrences] == [
        (1, "countin'"),
        (1, "this"),
        (2, "downin'"),
        (2, "this"),
    ]


def test_end_refrain_repetition_is_highlighted() -> None:
    # The same content word ending several lines ("…funk" / "…funk") is the
    # bars' structural anchor — highlighted despite being a repetition.
    def phon(token: Token) -> list[tuple[str, ...]]:
        table = {
            "funk": ("F", "AH1", "NG", "K"),
            "cat": ("K", "AE1", "T"),
            "dog": ("D", "AO1", "G"),
            "you": ("Y", "UW1"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups(
        [_line(["cat", "funk"], 1), _line(["dog", "funk"], 2)],
        phon,
        "en",
    )
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    assert [o.normalized for o in perfect[0].occurrences] == ["funk", "funk"]

    # A repeated line-final *function* word is not a refrain worth showing.
    groups = find_inner_rhyme_groups(
        [_line(["cat", "you"], 1), _line(["dog", "you"], 2)],
        phon,
        "en",
    )
    assert groups == []


def test_dense_chain_requires_distinct_words() -> None:
    # sit/quit/quit: three occurrences but only two distinct mid-line
    # monosyllables — repeats padding the count don't make a chain.
    def phon(token: Token) -> list[tuple[str, ...]]:
        table = {
            "sit": ("S", "IH1", "T"),
            "quit": ("K", "W", "IH1", "T"),
            "dog": ("D", "AO1", "G"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups(
        [_line(["sit", "quit", "quit", "dog"])], phon, "en"
    )
    assert groups == []


def test_identical_function_tails_join_their_anchors_group() -> None:
    # When members of a group are each followed by the same function word at
    # line end ("delay this" / "play this"), the tails join the group so the
    # phrases highlight as compound units.
    def phon(token: Token) -> list[tuple[str, ...]]:
        table = {
            "delay": ("D", "IH0", "L", "EY1"),
            "play": ("P", "L", "EY1"),
            "this": ("DH", "IH1", "S"),
            "dog": ("D", "AO1", "G"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups(
        [_line(["dog", "delay", "this"], 1), _line(["dog", "play", "this"], 2)],
        phon,
        "en",
    )
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    assert [(o.line_index, o.normalized) for o in perfect[0].occurrences] == [
        (1, "delay"),
        (1, "this"),
        (2, "play"),
        (2, "this"),
    ]


def test_asymmetric_function_tails_do_not_extend() -> None:
    # Only one member has the trailing function word -> no compound pattern,
    # the group keeps its original occurrences.
    def phon(token: Token) -> list[tuple[str, ...]]:
        table = {
            "delay": ("D", "IH0", "L", "EY1"),
            "play": ("P", "L", "EY1"),
            "this": ("DH", "IH1", "S"),
            "dog": ("D", "AO1", "G"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups(
        [_line(["dog", "delay", "this"], 1), _line(["dog", "play"], 2)],
        phon,
        "en",
    )
    perfect = [g for g in groups if g.rhyme_type == "perfect"]
    assert len(perfect) == 1
    assert {o.normalized for o in perfect[0].occurrences} == {"delay", "play"}


def test_heuristic_tail_variants_never_perfect_match() -> None:
    # Tail guesses carry fabricated stress readings; an unknown word must not
    # claim a *perfect* rhyme with a function word through one ("tetris" /
    # "this" was the real-world failure).
    def phon_wrapped(token: Token) -> list[tuple[str, ...]]:
        if token.normalized == "zorbis":
            return HeuristicTailVariants([("IH0", "S"), ("IH1", "S")])
        if token.normalized == "this":
            return [("DH", "IH1", "S"), ("DH", "IH0", "S")]
        if token.normalized in ("dog", "cat"):
            return [_PHONEMES[token.normalized]]
        return []

    groups = find_inner_rhyme_groups(
        [_line(["dog", "this"], 1), _line(["cat", "zorbis"], 2)],
        phon_wrapped,
        "en",
    )
    assert groups == []

    # Control: the same variants as a plain list (a real multi-pronunciation
    # word) do perfect-match.
    def phon_plain(token: Token) -> list[tuple[str, ...]]:
        if token.normalized == "zorbis":
            return [("IH0", "S"), ("IH1", "S")]
        return phon_wrapped(token)

    groups = find_inner_rhyme_groups(
        [_line(["dog", "this"], 1), _line(["cat", "zorbis"], 2)],
        phon_plain,
        "en",
    )
    assert [g.rhyme_type for g in groups] == ["perfect"]


def test_dense_chain_must_sit_on_one_line() -> None:
    # cat/sat/mat scattered mid-line across three lines is coincidence, not a
    # deliberate run; only the anchored feet/heat end-rhyme survives.
    groups = find_inner_rhyme_groups(
        [
            _line(["cat", "dog"], 1),
            _line(["sat", "feet"], 2),
            _line(["mat", "heat"], 3),
        ],
        _phonemes_for,
        "en",
    )
    assert len(groups) == 1
    assert {o.normalized for o in groups[0].occurrences} == {"feet", "heat"}


class _FakePronunciationService:
    def __init__(self, table: dict[str, list[tuple[str, ...]]]) -> None:
        self._table = table

    def lookup(self, word: str):
        class _Pron:
            def __init__(self, phonemes: tuple[str, ...]) -> None:
                self.phonemes = list(phonemes)

        prons = [_Pron(p) for p in self._table.get(word.lower(), [])]
        return bool(prons), prons


def _token(text: str, normalized: str) -> Token:
    return Token(
        text=text, normalized=normalized, index=0, char_start=0, char_end=len(text)
    )


def test_english_lookup_recovers_dropped_g() -> None:
    svc = _FakePronunciationService(
        {"counting": [("K", "AW1", "N", "T", "IH0", "NG")]}
    )
    lookup = english_phonemes_for(svc, {})
    variants = lookup(_token("countin'", "countin"))
    assert variants == [("K", "AW1", "N", "T", "IH0", "NG")]
    assert not isinstance(variants, HeuristicTailVariants)


def test_english_lookup_splits_oov_compounds() -> None:
    svc = _FakePronunciationService(
        {"pay": [("P", "EY1")], "stub": [("S", "T", "AH1", "B")]}
    )
    lookup = english_phonemes_for(svc, {})
    variants = lookup(_token("paystub", "paystub"))
    # Right half's primary stress demoted to secondary, as CMU compounds do.
    assert variants == [("P", "EY1", "S", "T", "AH2", "B")]
    assert not isinstance(variants, HeuristicTailVariants)


def test_english_lookup_wraps_heuristic_guesses() -> None:
    lookup = english_phonemes_for(_FakePronunciationService({}), {})
    variants = lookup(_token("tetris", "tetris"))
    assert isinstance(variants, HeuristicTailVariants)
    # Full-word reading first (used for spans/syllables), tails after.
    assert variants[0] == ("T", "EH1", "T", "R", "IH0", "S")
    assert len(variants) > 1


def test_near_key_anchors_on_primary_stress_for_compounds() -> None:
    # "paystub" (P EY1 S T AH2 B) must slant-match the long-A family
    # ("waist"/"taste"), not anchor on its secondary "-stub".
    def phon(token: Token) -> list[tuple[str, ...]]:
        table = {
            "taste": ("T", "EY1", "S", "T"),
            "waist": ("W", "EY1", "S", "T"),
            "paystub": ("P", "EY1", "S", "T", "AH2", "B"),
            "dog": ("D", "AO1", "G"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups(
        [_line(["taste", "dog", "waist", "paystub"])], phon, "en"
    )
    near = [g for g in groups if g.rhyme_type == "near"]
    assert len(near) == 1
    assert {o.normalized for o in near[0].occurrences} == {
        "taste",
        "waist",
        "paystub",
    }


def test_function_heavy_draft_highlights_only_the_scheme() -> None:
    # Regression for feedback.md: a draft dense with mid-line function words
    # (the HUMBLE. failure mode) must highlight only the end-rhyme scheme —
    # no group may contain a mid-line function word.
    def phon(token: Token) -> list[tuple[str, ...]]:
        table = {
            "my": ("M", "AY1"),
            "by": ("B", "AY1"),
            "to": ("T", "UW1"),
            "the": ("DH", "AH0"),
            "we": ("W", "IY1"),
            "give": ("G", "IH1", "V"),
            "dog": ("D", "AO1", "G"),
            "sat": ("S", "AE1", "T"),
            "feet": ("F", "IY1", "T"),
            "heat": ("HH", "IY1", "T"),
        }
        phonemes = table.get(token.normalized)
        return [phonemes] if phonemes is not None else []

    groups = find_inner_rhyme_groups(
        [
            _line(["my", "dog", "sat", "by", "my", "feet"], 1),
            _line(["to", "the", "dog", "we", "give", "heat"], 2),
        ],
        phon,
        "en",
    )
    # Only the feet/heat end-rhyme survives; the mid-line "my"/"by" perfect
    # match and every other function-word match are suppressed.
    assert len(groups) == 1
    assert {o.normalized for o in groups[0].occurrences} == {"feet", "heat"}
    function_words = {"my", "by", "to", "the", "we"}
    for g in groups:
        assert not {o.normalized for o in g.occurrences} & function_words
