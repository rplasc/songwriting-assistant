from app.domain.near_rhyme_rules import near_rhyme_key
from app.domain.rhyme_rules import rhyme_key


def test_near_rhyme_collapses_voicing_pair() -> None:
    # "cat":  K AE1 T   "cad": K AE1 D — both end in a stop, near rhymes.
    assert near_rhyme_key(["K", "AE1", "T"]) == near_rhyme_key(["K", "AE1", "D"])


def test_near_rhyme_does_not_collapse_distinct_manners() -> None:
    # "cat" (stop) vs "can" (nasal) — different manner, should NOT match.
    assert near_rhyme_key(["K", "AE1", "T"]) != near_rhyme_key(["K", "AE1", "N"])


def test_near_rhyme_preserves_vowel_identity() -> None:
    # Same coda manner, different vowel — different keys.
    assert near_rhyme_key(["K", "AE1", "T"]) != near_rhyme_key(["K", "IH1", "T"])


def test_near_rhyme_returns_none_without_vowel() -> None:
    assert near_rhyme_key([]) is None
    assert near_rhyme_key(["K", "T"]) is None


def test_perfect_rhyme_implies_near_rhyme_match() -> None:
    """Words that share a perfect rhyme key always share a near rhyme key too."""
    a = ["F", "AY1", "ER0"]
    b = ["HH", "AY1", "ER0"]
    assert rhyme_key(a) == rhyme_key(b)
    assert near_rhyme_key(a) == near_rhyme_key(b)


def test_near_rhyme_groups_across_consonant_cluster_extension() -> None:
    # "mind": M AY1 N D (nasal + stop coda)  "time": T AY1 M (nasal-only coda).
    # Slant-rhyme families commonly add/drop a trailing consonant.
    mind = ["M", "AY1", "N", "D"]
    time = ["T", "AY1", "M"]
    assert near_rhyme_key(mind) == near_rhyme_key(time)


def test_near_rhyme_groups_friend_and_again() -> None:
    # "friend": F R EH1 N D  "again": AH0 G EH1 N — same vowel + nasal onset coda,
    # "friend" extends with an extra stop.
    friend = ["F", "R", "EH1", "N", "D"]
    again = ["AH0", "G", "EH1", "N"]
    assert near_rhyme_key(friend) == near_rhyme_key(again)


def test_near_rhyme_keeps_unrelated_words_separate() -> None:
    # "cat": K AE1 T (stop coda)  "dog": D AO1 G (different vowel, stop coda).
    cat = ["K", "AE1", "T"]
    dog = ["D", "AO1", "G"]
    assert near_rhyme_key(cat) != near_rhyme_key(dog)
