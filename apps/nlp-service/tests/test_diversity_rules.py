"""Soft diversity pass over the ranked rhyme list."""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.languages.english.engine import EnglishEngine
from app.domain.rhyme.diversity_rules import diversify


_engine = EnglishEngine()


@dataclass(frozen=True, slots=True)
class _FakeRanked:
    """Mirror of the private _RankedEntry shape used by RhymeService.

    Kept local so this test does not depend on internal service types.
    """

    word: str
    syllables: int
    rhyme_type: str
    score: float


def _e(word: str, score: float, syllables: int = 1) -> _FakeRanked:
    return _FakeRanked(word=word, syllables=syllables, rhyme_type="perfect", score=score)


def test_empty_input_returns_empty() -> None:
    assert diversify((), engine=_engine) == ()


def test_single_candidate_returned_unchanged() -> None:
    only = (_e("fire", 0.90),)
    out = diversify(only, engine=_engine)
    assert out == only


def test_two_cluster_members_are_not_demoted() -> None:
    # The first two members of a cluster pay no penalty.
    ranked = (_e("running", 0.90), _e("stunning", 0.85))
    out = diversify(ranked, engine=_engine)
    assert out[0].score == 0.90
    assert out[1].score == 0.85


def test_third_cluster_member_gets_demoted() -> None:
    ranked = (
        _e("running", 0.90),
        _e("stunning", 0.85),
        _e("sunning", 0.80),
    )
    out = diversify(ranked, engine=_engine)
    scores = {e.word: e.score for e in out}
    assert scores["running"] == 0.90
    assert scores["stunning"] == 0.85
    # third member of -ing cluster loses 0.05.
    assert scores["sunning"] == 0.75


def test_cluster_demotion_compounds_with_position() -> None:
    ranked = tuple(_e(w, 0.90 - 0.001 * i) for i, w in enumerate(
        ["running", "stunning", "sunning", "punning", "gunning"]
    ))
    out = diversify(ranked, engine=_engine)
    by_word = {e.word: e.score for e in out}
    # Positions 0,1 untouched.
    assert by_word["running"] == 0.90
    assert by_word["stunning"] == 0.899
    # Position 2 -> -0.05; position 3 -> -0.10; position 4 -> -0.15.
    assert by_word["sunning"] == round(0.898 - 0.05, 4)
    assert by_word["punning"] == round(0.897 - 0.10, 4)
    assert by_word["gunning"] == round(0.896 - 0.15, 4)


def test_unrelated_clusters_are_independent() -> None:
    ranked = (
        _e("running", 0.90),
        _e("stunning", 0.85),
        _e("ocean", 0.82),
        _e("station", 0.81),
        _e("sunning", 0.80),
    )
    out = diversify(ranked, engine=_engine)
    by_word = {e.word: e.score for e in out}
    # "ocean" and "station" are different clusters; neither demoted by -ing.
    assert by_word["ocean"] == 0.82
    assert by_word["station"] == 0.81
    # Three -ing members now; the third (sunning) is demoted by 0.05.
    assert by_word["sunning"] == 0.75


def test_stem_dedup_demotes_candidate_vs_candidate() -> None:
    # "hurry" / "hurries" share a stem. The first survives clean; the
    # second pays the candidate-vs-candidate stem demotion. The cluster
    # check does not fire (suffixes differ: "rry" vs "ies").
    ranked = (_e("hurry", 0.80), _e("hurries", 0.78))
    out = diversify(ranked, engine=_engine)
    scores = {e.word: e.score for e in out}
    assert scores["hurry"] == 0.80
    # Stem demotion is 0.03.
    assert scores["hurries"] == 0.75


def test_results_are_resorted_by_score() -> None:
    # Pre-demotion order has "sunning" above an unrelated higher-quality
    # rhyme that would benefit from being elevated. After diversify the
    # demoted "sunning" should drop below it.
    ranked = (
        _e("running", 0.90),
        _e("stunning", 0.85),
        _e("sunning", 0.80),  # 3rd -ing; demoted by 0.05 -> 0.75
        _e("ocean", 0.78),    # unaffected
    )
    out = diversify(ranked, engine=_engine)
    words = [e.word for e in out]
    assert words.index("ocean") < words.index("sunning")
