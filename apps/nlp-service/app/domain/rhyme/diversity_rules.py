"""Soft diversity rules applied to a ranked rhyme list.

Two demotions are layered on top of the per-tier score so the result
list does not collapse onto a single trailing pattern (e.g. eight ``-ing``
words in the top ten) or onto candidates that are themselves morphological
variants of each other (``hurry`` / ``hurries`` / ``hurried``).

The pass is intentionally soft -- it nudges ordering, it does not delete.
Strong phonetic matches stay near the top; only redundant followers drift
down. Both demotions are deterministic functions of the input.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Protocol


# Last N chars define a "cluster". Long enough to capture meaningful
# suffix families (-ing, -tion, -ous, -ado, -ente, -ana) without being so
# long that every word is its own cluster.
_CLUSTER_SUFFIX_LEN: int = 3

# Two members of a cluster is fine. The third and subsequent each carry
# this much demotion times their position-within-cluster offset.
_MAX_PER_CLUSTER_BEFORE_DEMOTE: int = 2
_CLUSTER_DEMOTION_STEP: float = 0.05

# Stem-mate demotion (candidate-vs-candidate, complementing the existing
# query-vs-candidate _SAME_STEM_PENALTY in ranking_service).
_STEM_DEMOTION: float = 0.03


class _EngineProtocol(Protocol):
    def shares_stem(self, query: str, candidate: str, min_stem: int = 4) -> bool: ...


class _RankedEntryProtocol(Protocol):
    """Structural shape we operate on -- avoids importing the concrete
    _RankedEntry from rhyme_service (which would create a cycle)."""

    word: str
    syllables: int
    rhyme_type: str
    score: float


def diversify(
    ranked: tuple[_RankedEntryProtocol, ...],
    *,
    engine: _EngineProtocol,
) -> tuple[_RankedEntryProtocol, ...]:
    """Return a new tuple with cluster + stem demotions applied and re-sorted.

    The returned items are the same dataclass type as the input (the function
    uses :func:`dataclasses.replace` to copy with an adjusted score), so
    callers continue to receive ``_RankedEntry`` instances.
    """
    if len(ranked) < 2:
        return tuple(ranked)

    cluster_counts: dict[str, int] = {}
    kept_words: list[str] = []
    out: list[_RankedEntryProtocol] = []
    for entry in ranked:
        cluster = entry.word[-_CLUSTER_SUFFIX_LEN:] if len(entry.word) >= _CLUSTER_SUFFIX_LEN else entry.word
        seen = cluster_counts.get(cluster, 0)
        demote = 0.0
        if seen >= _MAX_PER_CLUSTER_BEFORE_DEMOTE:
            demote += _CLUSTER_DEMOTION_STEP * (seen - _MAX_PER_CLUSTER_BEFORE_DEMOTE + 1)
        # Candidate-vs-candidate stem dedup: penalise this entry once if any
        # earlier kept word shares its stem. We do not stack the penalty
        # across multiple stem-mates -- one signal is enough to bury a
        # redundant variant.
        for prev_word in kept_words:
            if engine.shares_stem(prev_word, entry.word) or engine.shares_stem(
                entry.word, prev_word
            ):
                demote += _STEM_DEMOTION
                break
        if demote:
            new_score = max(0.0, entry.score - demote)
            entry = replace(entry, score=round(new_score, 4))
        out.append(entry)
        cluster_counts[cluster] = seen + 1
        kept_words.append(entry.word)

    # Stable re-sort by descending score; preserves original order for
    # candidates with identical scores so callers see deterministic output.
    out.sort(key=lambda e: -e.score)
    return tuple(out)
