"""Shared helper to build a compare insight with id + anchor."""

from __future__ import annotations

from app.domain.response_contracts.insight_id import make_insight_id
from app.schemas.anchors import InsightAnchor
from app.schemas.draft_analysis import Insight, SectionAnalysis
from app.schemas.evidence import TypedEvidence


def section_anchor(section: SectionAnalysis) -> InsightAnchor:
    return InsightAnchor(
        scope="section",
        section_id=section.id,
        line_start=section.line_start,
        line_end=section.line_end,
    )


def draft_anchor() -> InsightAnchor:
    return InsightAnchor(scope="draft")


def build_compare_insight(
    *,
    insight_type: str,
    scope: str,
    target: str | None,
    severity: str,
    message: str,
    evidence: TypedEvidence,
    anchor: InsightAnchor,
    confidence: str | None = None,
) -> Insight:
    return Insight(
        id=make_insight_id(
            insight_type=insight_type,
            scope=scope,
            target=target,
            evidence=evidence,
        ),
        type=insight_type,
        scope=scope,  # type: ignore[arg-type]
        target=target,
        severity=severity,  # type: ignore[arg-type]
        message=message,
        evidence=evidence,
        anchor=anchor,
        confidence=confidence,  # type: ignore[arg-type]
    )


__all__ = ["build_compare_insight", "draft_anchor", "section_anchor"]
