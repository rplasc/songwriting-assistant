"""Compare sections for over-similarity or low-variation.

Pair selection:
- every same-label pair (verse↔verse, chorus↔chorus, ...) excluding
  bridge/outro which are usually intentional one-offs,
- every verse↔chorus pair (one direction; reciprocal pairs are de-duped
  by always ordering by section index).

Similarity is Jaccard over content-lemma bags. Thresholds:
- >= 0.85 → over_similarity (medium severity, medium confidence)
- <= 0.15 (same-label pairs only) → low_variation (low severity,
  low confidence — easier to be wrong here)

Optional ending-overlap evidence: when two same-label sections share
>= half their line endings, ``ending_overlap`` lands in the insight
evidence dict.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.draft_analysis.section_parser import ParsedSection


@dataclass(frozen=True, slots=True)
class SectionContrastInsight:
    type: str  # "section_contrast"
    scope: str  # "draft"
    target: str | None
    severity: str
    confidence: str
    message: str
    evidence: dict[str, object]


_OVER_SIMILARITY_THRESHOLD = 0.85
_LOW_VARIATION_THRESHOLD = 0.15
_HOOK_LABELS: frozenset[str] = frozenset({"chorus", "hook", "refrain"})
_SKIP_LABELS: frozenset[str] = frozenset({"bridge", "outro", "intro"})


def detect_section_contrast(
    sections: list[ParsedSection],
    section_bags: dict[str, set[str]],
    section_endings: dict[str, list[str]],
) -> list[SectionContrastInsight]:
    if len(sections) < 2:
        return []

    out: list[SectionContrastInsight] = []
    for i in range(len(sections)):
        for j in range(i + 1, len(sections)):
            a, b = sections[i], sections[j]
            label_a, label_b = a.label, b.label
            if label_a in _SKIP_LABELS or label_b in _SKIP_LABELS:
                continue
            same_label = label_a is not None and label_a == label_b
            cross_verse_chorus = (
                {label_a, label_b} == {"verse", "chorus"}
                or (label_a in _HOOK_LABELS and label_b == "verse")
                or (label_b in _HOOK_LABELS and label_a == "verse")
            )
            if not (same_label or cross_verse_chorus):
                continue

            bag_a = section_bags.get(a.id, set())
            bag_b = section_bags.get(b.id, set())
            if not bag_a or not bag_b:
                continue
            jaccard = len(bag_a & bag_b) / len(bag_a | bag_b)
            ending_share = _ending_share(
                section_endings.get(a.id, []), section_endings.get(b.id, [])
            )
            evidence: dict[str, object] = {
                "section_pair": [a.id, b.id],
                "jaccard": round(jaccard, 3),
                "shared_lemmas": sorted(bag_a & bag_b)[:6],
            }
            if ending_share is not None and ending_share >= 0.5:
                evidence["ending_overlap"] = round(ending_share, 3)

            if jaccard >= _OVER_SIMILARITY_THRESHOLD:
                evidence["contrast_kind"] = "over_similarity"
                where = _pair_label(label_a, label_b, same_label)
                out.append(
                    SectionContrastInsight(
                        type="section_contrast",
                        scope="draft",
                        target=None,
                        severity="medium",
                        confidence="medium",
                        message=(
                            f"{where} share {int(jaccard * 100)}% of their "
                            "content words — consider varying one."
                        ),
                        evidence=evidence,
                    )
                )
            elif same_label and jaccard <= _LOW_VARIATION_THRESHOLD:
                evidence["contrast_kind"] = "low_variation"
                out.append(
                    SectionContrastInsight(
                        type="section_contrast",
                        scope="draft",
                        target=None,
                        severity="low",
                        confidence="low",
                        message=(
                            f"Two {label_a}s have almost no shared imagery — "
                            "is that intentional?"
                        ),
                        evidence=evidence,
                    )
                )
    return out


def _pair_label(a: str | None, b: str | None, same_label: bool) -> str:
    if same_label and a is not None:
        return f"Two {a}s"
    a_lbl = a or "section"
    b_lbl = b or "section"
    return f"The {a_lbl} and the {b_lbl}"


def _ending_share(a: list[str], b: list[str]) -> float | None:
    if not a or not b:
        return None
    set_a, set_b = set(a), set(b)
    overlap = len(set_a & set_b)
    return overlap / max(len(set_a), len(set_b))


__all__ = ["SectionContrastInsight", "detect_section_contrast"]
