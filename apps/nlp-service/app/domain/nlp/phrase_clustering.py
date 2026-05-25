"""Group lyric phrases by overlapping content-word lemmas.

Used by semantic_repetition_rules and motif_tracker. Phrases that share
enough content-word lemmas land in the same cluster — that's the only
"semantic" signal in M3, deliberately surface-shallow and deterministic.

Matching rule (per pairwise comparison against an existing cluster):
- Jaccard over content lemmas >= 0.5, OR
- the phrase's anchor lemma (first content lemma) matches the anchor
  of at least one cluster member AND both phrases are small (<= 2
  content lemmas each), capturing the "hear your shadow / hear your
  footsteps" pattern where the verb head is the shared image.

When a phrase matches multiple clusters, the highest-Jaccard cluster
wins. Function-word filtering happens upstream — callers should pass
PhraseRefs whose ``lemmas`` already exclude closed-class tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PhraseRef:
    """A phrase candidate from a single lyric line."""

    section_id: str
    line_index: int  # 1-based line index in the draft
    text: str  # original lyric line text (for evidence display)
    lemmas: tuple[str, ...]  # content-word lemmas, position-preserving


@dataclass(slots=True)
class PhraseCluster:
    signature: tuple[str, ...]  # sorted unique lemmas defining the cluster
    members: list[PhraseRef] = field(default_factory=list)

    @property
    def section_ids(self) -> set[str]:
        return {m.section_id for m in self.members}


_JACCARD_THRESHOLD = 0.5
_ANCHOR_MAX_LEMMAS = 4
_ANCHOR_MIN_JACCARD = 0.15


def cluster_phrases(phrases: list[PhraseRef]) -> list[PhraseCluster]:
    clusters: list[PhraseCluster] = []
    for phrase in phrases:
        if not phrase.lemmas:
            continue
        target = _find_cluster(clusters, phrase)
        if target is None:
            clusters.append(
                PhraseCluster(signature=_signature(phrase.lemmas), members=[phrase])
            )
        else:
            target.members.append(phrase)
            target.signature = _signature(
                tuple(lemma for m in target.members for lemma in m.lemmas)
            )
    return clusters


def _signature(lemmas: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(set(lemmas)))


def _find_cluster(
    clusters: list[PhraseCluster], phrase: PhraseRef
) -> PhraseCluster | None:
    p_set = set(phrase.lemmas)
    p_anchor = phrase.lemmas[0]
    p_small = len(phrase.lemmas) <= _ANCHOR_MAX_LEMMAS
    best: PhraseCluster | None = None
    best_score = 0.0
    for cluster in clusters:
        c_set = set(cluster.signature)
        if not c_set:
            continue
        jaccard = len(p_set & c_set) / len(p_set | c_set)
        anchor_match = p_small and any(
            len(m.lemmas) <= _ANCHOR_MAX_LEMMAS and m.lemmas[0] == p_anchor
            for m in cluster.members
        )
        score = jaccard if jaccard >= _JACCARD_THRESHOLD else 0.0
        if anchor_match and jaccard >= _ANCHOR_MIN_JACCARD:
            score = max(score, _JACCARD_THRESHOLD)
        if score >= _JACCARD_THRESHOLD and score >= best_score:
            best = cluster
            best_score = score
    return best


__all__ = ["PhraseRef", "PhraseCluster", "cluster_phrases"]
