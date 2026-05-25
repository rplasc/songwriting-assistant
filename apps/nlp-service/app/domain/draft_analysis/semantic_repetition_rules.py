"""Detect repeated semantic concepts across draft lines.

Runs after literal repetition. Uses phrase_clustering: clusters
of size >= 2 become "semantic_repetition" insights. Confidence reflects
how concentrated the cluster is:

- high   : >= 3 members all in the same section (heavy reuse)
- medium : 2+ members in the same section (clear pair)
- low    : members spread across sections (motif touch, not over-reuse)

Scope is "section" when all members share a section, else "draft".
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.nlp.phrase_clustering import PhraseCluster


@dataclass(frozen=True, slots=True)
class SemanticRepetitionInsight:
    type: str  # always "semantic_repetition"
    scope: str  # "section" | "draft"
    target: str | None
    severity: str  # "low" | "medium" | "high"
    confidence: str  # "low" | "medium" | "high"
    message: str
    evidence: dict[str, list[str]]


def detect_semantic_repetition(
    clusters: list[PhraseCluster],
) -> list[SemanticRepetitionInsight]:
    out: list[SemanticRepetitionInsight] = []
    for cluster in clusters:
        if len(cluster.members) < 2:
            continue
        section_ids = cluster.section_ids
        per_section_counts = _group_by_section(cluster)
        max_in_section = max(per_section_counts.values())

        if len(section_ids) == 1:
            target = next(iter(section_ids))
            scope = "section"
            if max_in_section >= 3:
                confidence = "high"
                severity = "medium"
            else:
                confidence = "medium"
                severity = "low"
        else:
            target = None
            scope = "draft"
            confidence = "low"
            severity = "info" if max_in_section < 2 else "low"

        phrases = [m.text.strip() for m in cluster.members]
        lemma_label = ", ".join(cluster.signature[:3])
        message = (
            f"Multiple lines reuse the same image ({lemma_label})."
            if scope == "draft"
            else f"This section reuses the same image ({lemma_label})."
        )
        out.append(
            SemanticRepetitionInsight(
                type="semantic_repetition",
                scope=scope,
                target=target,
                severity=severity,
                confidence=confidence,
                message=message,
                evidence={"phrases": phrases, "lemmas": list(cluster.signature)},
            )
        )
    return out


def _group_by_section(cluster: PhraseCluster) -> dict[str, int]:
    counts: dict[str, int] = {}
    for m in cluster.members:
        counts[m.section_id] = counts.get(m.section_id, 0) + 1
    return counts


__all__ = ["SemanticRepetitionInsight", "detect_semantic_repetition"]
