"""Identify motif lemmas — content words that recur across the draft.

A motif is a single content lemma that appears:
- on at least ``_MIN_LINES`` distinct lines, OR
- in at least ``_MIN_SECTIONS`` distinct sections.

Lemmas are filtered through the language's function-word set before
counting so closed-class words (articles, pronouns, auxiliaries) never
qualify as motifs. The output is intentionally a flat list of lemma
strings so it can drop straight into ``DraftSummary.motifs``.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LemmaLocation:
    section_id: str
    line_index: int
    lemma: str


_MIN_LINES = 3
_MIN_SECTIONS = 2
_MAX_MOTIFS = 6


def extract_motifs(
    locations: list[LemmaLocation],
    function_words: frozenset[str],
) -> list[str]:
    by_lemma: dict[str, set[tuple[str, int]]] = defaultdict(set)
    sections_by_lemma: dict[str, set[str]] = defaultdict(set)
    for loc in locations:
        if loc.lemma in function_words or len(loc.lemma) < 3:
            continue
        by_lemma[loc.lemma].add((loc.section_id, loc.line_index))
        sections_by_lemma[loc.lemma].add(loc.section_id)

    scored: list[tuple[str, int, int]] = []
    for lemma, occurrences in by_lemma.items():
        line_count = len(occurrences)
        section_count = len(sections_by_lemma[lemma])
        if line_count >= _MIN_LINES or section_count >= _MIN_SECTIONS:
            # Sort key: cross-section reach first, then raw frequency.
            scored.append((lemma, section_count, line_count))

    scored.sort(key=lambda x: (-x[1], -x[2], x[0]))
    return [lemma for lemma, _sc, _lc in scored[:_MAX_MOTIFS]]


__all__ = ["LemmaLocation", "extract_motifs"]
