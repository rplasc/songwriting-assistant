"""Detect perspective and tense drift across (and within) sections.

Conservative by design — we only emit when the evidence is concrete:
- a section needs >= ``_MIN_PERSON_SIGNALS`` person-bearing tokens
  before we'll claim a "dominant" person, and a flip only counts when
  the next section also has a dominant person that disagrees, OR a
  single section mixes >= 3 persons without one crossing 50%.
- tense drift uses the same dominance logic over past/present/future
  classifications.

ES tense detection ships at lower confidence than EN because simplemma
mishandles common irregular verbs (ser/ir/haber); see tense.py.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.domain.draft_analysis.section_parser import ParsedSection


@dataclass(frozen=True, slots=True)
class ConsistencyDriftInsight:
    type: str  # "perspective_drift" | "tense_drift"
    scope: str  # "section" | "draft"
    target: str | None
    severity: str
    confidence: str
    message: str
    evidence: dict[str, object]


# Per-section classification: lists of (line_index, label) tuples.
SectionClassifications = dict[str, list[tuple[int, str]]]


_MIN_PERSON_SIGNALS = 3
_MIN_TENSE_SIGNALS = 3
_DOMINANCE_RATIO = 0.6
_INTERNAL_MIX_RATIO = 0.5


def _dominant(items: list[tuple[int, str]]) -> tuple[str | None, float, Counter[str]]:
    counts: Counter[str] = Counter(label for _, label in items)
    total = sum(counts.values())
    if total == 0:
        return None, 0.0, counts
    top, top_count = counts.most_common(1)[0]
    share = top_count / total
    return top, share, counts


def detect_perspective_drift(
    sections: list[ParsedSection],
    classifications: SectionClassifications,
) -> list[ConsistencyDriftInsight]:
    return _detect_drift(
        sections,
        classifications,
        kind="perspective_drift",
        min_signals=_MIN_PERSON_SIGNALS,
        confidence="medium",
        label_noun="person",
    )


def detect_tense_drift(
    sections: list[ParsedSection],
    classifications: SectionClassifications,
    language: str,
) -> list[ConsistencyDriftInsight]:
    # Spanish tense classifier leans on suffix heuristics plus a tiny
    # irregular whitelist; downgrade reported confidence accordingly.
    confidence = "low" if language == "es" else "medium"
    return _detect_drift(
        sections,
        classifications,
        kind="tense_drift",
        min_signals=_MIN_TENSE_SIGNALS,
        confidence=confidence,
        label_noun="tense",
    )


def _detect_drift(
    sections: list[ParsedSection],
    classifications: SectionClassifications,
    *,
    kind: str,
    min_signals: int,
    confidence: str,
    label_noun: str,
) -> list[ConsistencyDriftInsight]:
    out: list[ConsistencyDriftInsight] = []
    section_dominants: list[tuple[ParsedSection, str | None, Counter[str]]] = []
    for section in sections:
        items = classifications.get(section.id, [])
        dom, share, counts = _dominant(items)
        if sum(counts.values()) < min_signals:
            section_dominants.append((section, None, counts))
            continue
        if share >= _DOMINANCE_RATIO:
            section_dominants.append((section, dom, counts))
        else:
            section_dominants.append((section, None, counts))
            if len(counts) >= 3 and sum(counts.values()) >= min_signals + 1:
                # Internal mix: three or more distinct values with no dominant.
                out.append(
                    ConsistencyDriftInsight(
                        type=kind,
                        scope="section",
                        target=section.id,
                        severity="low",
                        confidence=confidence,
                        message=(
                            f"This section mixes {len(counts)} {label_noun}s "
                            "without a clear dominant one."
                        ),
                        evidence={
                            "counts": dict(counts),
                            "section_id": section.id,
                        },
                    )
                )

    # Cross-section flips between adjacent dominant sections.
    prev: tuple[ParsedSection, str] | None = None
    for section, dom, _ in section_dominants:
        if dom is None:
            continue
        if prev is not None and prev[1] != dom:
            out.append(
                ConsistencyDriftInsight(
                    type=kind,
                    scope="draft",
                    target=None,
                    severity="low",
                    confidence=confidence,
                    message=(
                        f"{label_noun.capitalize()} shifts from "
                        f"{prev[1]} ({prev[0].id}) to {dom} ({section.id})."
                    ),
                    evidence={
                        "from_section": prev[0].id,
                        "to_section": section.id,
                        "from": prev[1],
                        "to": dom,
                    },
                )
            )
        prev = (section, dom)

    return out


__all__ = [
    "ConsistencyDriftInsight",
    "SectionClassifications",
    "detect_perspective_drift",
    "detect_tense_drift",
]
