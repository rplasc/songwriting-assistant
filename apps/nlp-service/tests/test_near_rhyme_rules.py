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


def test_near_rhyme_groups_vowel_neighbors_again_and_thin() -> None:
    # "again": AH0 G EH1 N  "thin": TH IH1 N — EH/IH are both front,
    # non-low vowels and share a nasal coda.
    again = ["AH0", "G", "EH1", "N"]
    thin = ["TH", "IH1", "N"]
    assert near_rhyme_key(again) == near_rhyme_key(thin)


def test_near_rhyme_groups_vowel_neighbors_love_and_move() -> None:
    # "love": L AH1 V  "move": M UW1 V — AH/UW are both in the broad
    # central/back vowel class and share a fricative coda.
    love = ["L", "AH1", "V"]
    move = ["M", "UW1", "V"]
    assert near_rhyme_key(love) == near_rhyme_key(move)


def test_near_rhyme_vowel_classes_do_not_collapse_ae() -> None:
    # "cat": K AE1 T  "cut": K AH1 T — AE is deliberately excluded from both
    # vowel-neighborhood classes, so it must not merge with "back" (AH/UW/...)
    # any more than it merges with "front" (IH/EH/...).
    cat = ["K", "AE1", "T"]
    cut = ["K", "AH1", "T"]
    assert near_rhyme_key(cat) != near_rhyme_key(cut)


def test_near_rhyme_does_not_group_unrelated_diphthongs() -> None:
    # "boy": B OY1  "buy": B AY1 — closing diphthongs are left out of the
    # vowel-neighborhood classes and keep their own identity.
    boy = ["B", "OY1"]
    buy = ["B", "AY1"]
    assert near_rhyme_key(boy) != near_rhyme_key(buy)
