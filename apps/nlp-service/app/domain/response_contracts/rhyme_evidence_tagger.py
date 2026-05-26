"""Tag a rhyme candidate with id, confidence, and evidence tags.

The service layer ranks candidates without product framing. This tagger
overlays the Phase 5.5 product fields onto each candidate at response
build time so the route stays the only place that knows about UI
contract decisions.
"""

from __future__ import annotations

from app.domain.response_contracts.insight_id import make_rhyme_id
from app.schemas.responses import EvidenceTag, RhymeCandidate, RhymeConfidence


def _confidence_for(rhyme_type: str, rhyme_family: str | None) -> RhymeConfidence:
    if rhyme_type == "perfect" or rhyme_family == "perfect":
        return "high"
    if rhyme_type == "multisyllabic" or rhyme_family == "multisyllabic":
        return "high"
    if rhyme_type == "family":
        return "medium"
    return "low"


def _evidence_tags(
    rhyme_type: str,
    rhyme_family: str | None,
    *,
    target_type: str,
    pronunciations_found: bool,
) -> list[EvidenceTag]:
    tags: list[EvidenceTag] = []
    if rhyme_family == "perfect" or rhyme_type == "perfect":
        tags.append("shared_stressed_ending")
    if rhyme_family == "multisyllabic" or rhyme_type == "multisyllabic":
        tags.append("multisyllabic_key_match")
    if rhyme_family == "assonant":
        tags.append("shared_vowel_pattern")
    if rhyme_family == "consonant":
        tags.append("shared_consonant_tail")
    if rhyme_family == "near" or rhyme_type == "near":
        tags.append("shared_vowel_pattern")
    if target_type == "phrase_ending":
        tags.append("phrase_ending_match")
    if not pronunciations_found:
        tags.append("heuristic_fallback")
    if rhyme_type == "family" and not tags:
        tags.append("shared_stressed_ending")
    # de-duplicate while preserving order
    seen: set[str] = set()
    deduped: list[EvidenceTag] = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            deduped.append(t)
    return deduped


def tag_candidate(
    candidate: RhymeCandidate,
    *,
    query: str,
    language: str,
    target_type: str,
    pronunciations_found: bool,
) -> RhymeCandidate:
    confidence = _confidence_for(candidate.rhyme_type, candidate.rhyme_family)
    tags = _evidence_tags(
        candidate.rhyme_type,
        candidate.rhyme_family,
        target_type=target_type,
        pronunciations_found=pronunciations_found,
    )
    return candidate.model_copy(
        update={
            "id": make_rhyme_id(query=query, language=language, word=candidate.word),
            "confidence": confidence,
            "evidence_tags": tags,
        }
    )


__all__ = ["tag_candidate"]
