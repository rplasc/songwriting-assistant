"""Consistency drift delta rules.

Detects perspective/tense drifts that appeared or disappeared between
two revisions. A drift is keyed by (drift_type, section_id) so a drift
moving sections produces one resolved + one introduced insight.
"""

from __future__ import annotations

from app.domain.draft_compare._compare_insight import (
    build_compare_insight,
    draft_anchor,
)
from app.schemas.draft_analysis import DraftAnalysisResponse, Insight
from app.schemas.evidence import (
    ConsistencyDriftIntroducedEvidence,
    ConsistencyDriftResolvedEvidence,
)

_DRIFT_TYPES: frozenset[str] = frozenset({"perspective_drift", "tense_drift"})


def _drift_keys(analysis: DraftAnalysisResponse) -> set[tuple[str, str | None]]:
    return {
        (ins.type, ins.target)
        for ins in analysis.insights
        if ins.type in _DRIFT_TYPES
    }


def compute_consistency_deltas(
    previous: DraftAnalysisResponse,
    current: DraftAnalysisResponse,
) -> list[Insight]:
    prev_keys = _drift_keys(previous)
    cur_keys = _drift_keys(current)
    out: list[Insight] = []
    for drift_type, section_id in sorted(
        prev_keys - cur_keys, key=lambda x: (x[0], x[1] or "")
    ):
        out.append(
            build_compare_insight(
                insight_type="consistency_drift_resolved",
                scope="draft",
                target=None,
                severity="info",
                message=(
                    f'A {drift_type.replace("_", " ")} '
                    "is no longer present in this revision."
                ),
                evidence=ConsistencyDriftResolvedEvidence(
                    drift_type=drift_type, section_id=section_id
                ),
                anchor=draft_anchor(),
                confidence="medium",
            )
        )
    for drift_type, section_id in sorted(
        cur_keys - prev_keys, key=lambda x: (x[0], x[1] or "")
    ):
        out.append(
            build_compare_insight(
                insight_type="consistency_drift_introduced",
                scope="draft",
                target=None,
                severity="low",
                message=(
                    f'A new {drift_type.replace("_", " ")} '
                    "appeared in this revision."
                ),
                evidence=ConsistencyDriftIntroducedEvidence(
                    drift_type=drift_type, section_id=section_id
                ),
                anchor=draft_anchor(),
                confidence="medium",
            )
        )
    return out


__all__ = ["compute_consistency_deltas"]
