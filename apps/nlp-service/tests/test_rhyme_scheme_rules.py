from app.domain.draft_analysis.rhyme_scheme_rules import assign_scheme


def test_empty_returns_empty_string_full_confidence() -> None:
    assert assign_scheme([]) == ("", "full")


def test_aabb_pattern() -> None:
    scheme, conf = assign_scheme(["k1", "k1", "k2", "k2"])
    assert scheme == "AABB"
    assert conf == "full"


def test_abab_pattern() -> None:
    scheme, conf = assign_scheme(["k1", "k2", "k1", "k2"])
    assert scheme == "ABAB"
    assert conf == "full"


def test_abcb_pattern() -> None:
    scheme, _ = assign_scheme(["k1", "k2", "k3", "k2"])
    assert scheme == "ABCB"


def test_all_different() -> None:
    scheme, _ = assign_scheme(["a", "b", "c", "d"])
    assert scheme == "ABCD"


def test_none_key_renders_question_mark_and_partial_confidence() -> None:
    scheme, conf = assign_scheme(["k1", None, "k1"])
    assert scheme == "A?A"
    assert conf == "partial"


def test_multi_key_transitive_bridge() -> None:
    # Line 0 is a heteronym with two candidate keys; lines 1 and 2 each match
    # one of them and should end up in the same group as each other, even
    # though they share no key directly.
    scheme, conf = assign_scheme(
        [
            frozenset({"k1", "k2"}),
            frozenset({"k1"}),
            frozenset({"k2"}),
            frozenset({"k3"}),
        ]
    )
    assert scheme == "AAAB"
    assert conf == "full"
