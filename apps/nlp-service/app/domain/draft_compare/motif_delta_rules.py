"""Motif delta rules.

Compares motif occurrences across two draft analyses. The motif list
lives on ``DraftSummary.motifs`` and per-motif section counts can be
recovered from ``motif_concentration`` insights' typed evidence
(``MotifConcentrationEvidence.section_count``). For motifs that don't
trigger the concentration threshold, we fall back to a count of 1 per
side so we still detect added/removed motifs.
"""

from __future__ import annotations

from app.domain.draft_compare._compare_insight import (
    build_compare_insight,
    draft_anchor,
)
from app.schemas.draft_analysis import DraftAnalysisResponse, Insight
from app.schemas.evidence import (
    MotifAddedEvidence,
    MotifConcentrationEvidence,
    MotifRemovedEvidence,
    MotifStrengthenedEvidence,
    MotifWeakenedEvidence,
)


def _motif_strength(analysis: DraftAnalysisResponse) -> dict[str, int]:
    strength: dict[str, int] = {m: 1 for m in analysis.summary.motifs}
    for ins in analysis.insights:
        if (
            ins.type == "motif_concentration"
            and isinstance(ins.evidence, MotifConcentrationEvidence)
        ):
            motif = ins.evidence.motif
            # Sum across sections in case the same motif concentrates in
            # multiple sections — the stronger signal wins.
            current = strength.get(motif, 0)
            strength[motif] = max(current, ins.evidence.section_count)
    return strength


def compute_motif_deltas(
    previous: DraftAnalysisResponse,
    current: DraftAnalysisResponse,
) -> list[Insight]:
    prev = _motif_strength(previous)
    cur = _motif_strength(current)
    out: list[Insight] = []
    for motif in sorted(set(prev) | set(cur)):
        p = prev.get(motif, 0)
        c = cur.get(motif, 0)
        if p == 0 and c > 0:
            out.append(
                build_compare_insight(
                    insight_type="motif_added",
                    scope="draft",
                    target=None,
                    severity="info",
                    message=f'New motif "{motif}" appears in this revision.',
                    evidence=MotifAddedEvidence(motif=motif, occurrences=c),
                    anchor=draft_anchor(),
                    confidence="medium",
                )
            )
        elif p > 0 and c == 0:
            out.append(
                build_compare_insight(
                    insight_type="motif_removed",
                    scope="draft",
                    target=None,
                    severity="info",
                    message=f'Motif "{motif}" no longer appears.',
                    evidence=MotifRemovedEvidence(
                        motif=motif, previous_occurrences=p
                    ),
                    anchor=draft_anchor(),
                    confidence="medium",
                )
            )
        elif c > p:
            out.append(
                build_compare_insight(
                    insight_type="motif_strengthened",
                    scope="draft",
                    target=None,
                    severity="low",
                    message=f'Motif "{motif}" is more prominent now.',
                    evidence=MotifStrengthenedEvidence(
                        motif=motif, previous=p, current=c
                    ),
                    anchor=draft_anchor(),
                    confidence="low",
                )
            )
        elif c < p:
            out.append(
                build_compare_insight(
                    insight_type="motif_weakened",
                    scope="draft",
                    target=None,
                    severity="low",
                    message=f'Motif "{motif}" is less prominent now.',
                    evidence=MotifWeakenedEvidence(
                        motif=motif, previous=p, current=c
                    ),
                    anchor=draft_anchor(),
                    confidence="low",
                )
            )
    return out


__all__ = ["compute_motif_deltas"]
