"""Aggregate motif lemmas across the draft and emit summary + insights.

A motif is a single content lemma that recurs (rules in
``app.domain.nlp.motif_rules``). The tracker:

- returns the ordered motif lemma list for ``DraftSummary.motifs``,
- optionally emits a ``motif_concentration`` insight when a single
  motif dominates one section (>= 3 occurrences) — a soft signal that
  the hook image may be over-leaned-on in that part.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.domain.nlp.motif_rules import LemmaLocation, extract_motifs


@dataclass(frozen=True, slots=True)
class MotifInsight:
    type: str  # "motif_concentration"
    scope: str  # "section"
    target: str | None
    severity: str  # "info" | "low"
    confidence: str  # "low" | "medium"
    message: str
    evidence: dict[str, list[str] | str]


_SECTION_CONCENTRATION_MIN = 3


def track_motifs(
    locations: list[LemmaLocation],
    function_words: frozenset[str],
) -> tuple[list[str], list[MotifInsight]]:
    motifs = extract_motifs(locations, function_words)
    if not motifs:
        return [], []

    by_lemma_section: dict[str, dict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )
    for loc in locations:
        if loc.lemma not in motifs:
            continue
        by_lemma_section[loc.lemma][loc.section_id] += 1

    insights: list[MotifInsight] = []
    for lemma in motifs:
        section_counts = by_lemma_section.get(lemma, {})
        for section_id, count in section_counts.items():
            if count >= _SECTION_CONCENTRATION_MIN:
                insights.append(
                    MotifInsight(
                        type="motif_concentration",
                        scope="section",
                        target=section_id,
                        severity="low",
                        confidence="medium",
                        message=(
                            f'Motif "{lemma}" appears on {count} lines '
                            f"in this section."
                        ),
                        evidence={"motif": lemma, "section_count": str(count)},
                    )
                )
    return motifs, insights


__all__ = ["MotifInsight", "track_motifs"]
