"""Pair sections across two draft revisions for delta computation.

The matcher walks the two section lists and emits (previous, current)
pairs:

1. Explicit ids in both sides take priority (a caller-supplied id that
   appears on both sides always pairs).
2. Otherwise, sections pair by their (label, ordinal_within_label)
   key — "verse 2" pairs to "verse 2" even when a bridge was inserted
   between verses.
3. Sections that don't pair land in ``unmatched_previous`` /
   ``unmatched_current`` so the orchestrator can surface them as
   structural notes in ``CompareSummary``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.draft_analysis import SectionAnalysis


@dataclass(frozen=True, slots=True)
class SectionMatchResult:
    pairs: list[tuple[SectionAnalysis, SectionAnalysis]] = field(default_factory=list)
    unmatched_previous: list[SectionAnalysis] = field(default_factory=list)
    unmatched_current: list[SectionAnalysis] = field(default_factory=list)


def _label_ordinal_keys(sections: list[SectionAnalysis]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    out: list[tuple[str, int]] = []
    for s in sections:
        label = s.label or "_unlabeled"
        counts[label] = counts.get(label, 0) + 1
        out.append((label, counts[label]))
    return out


def match_sections(
    previous: list[SectionAnalysis],
    current: list[SectionAnalysis],
    *,
    previous_had_explicit_ids: bool = False,
    current_had_explicit_ids: bool = False,
) -> SectionMatchResult:
    pairs: list[tuple[SectionAnalysis, SectionAnalysis]] = []
    used_prev: set[int] = set()
    used_cur: set[int] = set()

    # Step 1: explicit-id matching. Only safe when both sides supplied
    # explicit section input — otherwise positional auto-ids would
    # produce false pairings (sec_1 in one structure is rarely the
    # same section as sec_1 in a restructured draft).
    if previous_had_explicit_ids and current_had_explicit_ids:
        prev_by_id = {s.id: (i, s) for i, s in enumerate(previous)}
        for j, cur_s in enumerate(current):
            hit = prev_by_id.get(cur_s.id)
            if hit is not None:
                i, prev_s = hit
                pairs.append((prev_s, cur_s))
                used_prev.add(i)
                used_cur.add(j)

    # Step 2: label-ordinal pairing for remaining sections.
    prev_keys = _label_ordinal_keys(previous)
    cur_keys = _label_ordinal_keys(current)
    prev_by_key: dict[tuple[str, int], int] = {}
    for i, key in enumerate(prev_keys):
        if i in used_prev:
            continue
        prev_by_key.setdefault(key, i)
    for j, cur_s in enumerate(current):
        if j in used_cur:
            continue
        key = cur_keys[j]
        i = prev_by_key.pop(key, None)
        if i is not None:
            pairs.append((previous[i], cur_s))
            used_prev.add(i)
            used_cur.add(j)

    unmatched_previous = [s for i, s in enumerate(previous) if i not in used_prev]
    unmatched_current = [s for j, s in enumerate(current) if j not in used_cur]
    return SectionMatchResult(
        pairs=pairs,
        unmatched_previous=unmatched_previous,
        unmatched_current=unmatched_current,
    )


__all__ = ["SectionMatchResult", "match_sections"]
