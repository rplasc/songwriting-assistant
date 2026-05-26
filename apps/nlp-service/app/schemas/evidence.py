"""Phase 5.5 typed evidence.

Each insight family carries a typed evidence variant discriminated by
``kind``. Replaces the Phase 5 ``evidence: dict[str, Any]`` so consumers
can rely on stable, validated shapes per insight family.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

CadenceClass = Literal["consistent", "mixed", "varied"]
ContrastKind = Literal["over_similarity", "low_variation"]


class SyllableVarianceEvidence(BaseModel):
    kind: Literal["syllable_variance"] = "syllable_variance"
    variance: float
    cadence_class: CadenceClass


class RepetitionOpeningEvidence(BaseModel):
    kind: Literal["repetition_opening"] = "repetition_opening"
    phrase: str


class RepetitionEndingEvidence(BaseModel):
    kind: Literal["repetition_ending"] = "repetition_ending"
    word: str


class WordOveruseEvidence(BaseModel):
    kind: Literal["word_overuse"] = "word_overuse"
    word: str
    line_count: int


class SemanticRepetitionEvidence(BaseModel):
    kind: Literal["semantic_repetition"] = "semantic_repetition"
    lemmas: list[str]
    phrases: list[str]


class MotifConcentrationEvidence(BaseModel):
    kind: Literal["motif_concentration"] = "motif_concentration"
    motif: str
    section_count: int


class SectionContrastEvidence(BaseModel):
    kind: Literal["section_contrast"] = "section_contrast"
    section_pair: tuple[str, str]
    jaccard: float
    shared_lemmas: list[str]
    contrast_kind: ContrastKind
    ending_overlap: float | None = None


class PerspectiveDriftEvidence(BaseModel):
    kind: Literal["perspective_drift"] = "perspective_drift"
    from_section: str | None = None
    to_section: str | None = None
    from_value: str | None = None
    to_value: str | None = None
    counts: dict[str, int] | None = None
    section_id: str | None = None


class TenseDriftEvidence(BaseModel):
    kind: Literal["tense_drift"] = "tense_drift"
    from_section: str | None = None
    to_section: str | None = None
    from_value: str | None = None
    to_value: str | None = None
    counts: dict[str, int] | None = None
    section_id: str | None = None


# --- Phase 5.5 M2: compare evidence variants ---


class MotifAddedEvidence(BaseModel):
    kind: Literal["motif_added"] = "motif_added"
    motif: str
    occurrences: int


class MotifRemovedEvidence(BaseModel):
    kind: Literal["motif_removed"] = "motif_removed"
    motif: str
    previous_occurrences: int


class MotifStrengthenedEvidence(BaseModel):
    kind: Literal["motif_strengthened"] = "motif_strengthened"
    motif: str
    previous: int
    current: int


class MotifWeakenedEvidence(BaseModel):
    kind: Literal["motif_weakened"] = "motif_weakened"
    motif: str
    previous: int
    current: int


class RepetitionSignalAddedEvidence(BaseModel):
    kind: Literal["repetition_signal_added"] = "repetition_signal_added"
    signal_type: str
    value: str
    section_id: str


class RepetitionSignalRemovedEvidence(BaseModel):
    kind: Literal["repetition_signal_removed"] = "repetition_signal_removed"
    signal_type: str
    value: str
    section_id: str


class SectionRhymeSchemeShiftEvidence(BaseModel):
    kind: Literal["section_rhyme_scheme_shift"] = "section_rhyme_scheme_shift"
    section_id: str
    previous: str
    current: str


class SectionCadenceShiftEvidence(BaseModel):
    kind: Literal["section_cadence_shift"] = "section_cadence_shift"
    section_id: str
    previous: str
    current: str


class SectionSyllablePatternShiftEvidence(BaseModel):
    kind: Literal["section_syllable_pattern_shift"] = (
        "section_syllable_pattern_shift"
    )
    section_id: str
    previous: list[int]
    current: list[int]
    delta: list[int]


class ConsistencyDriftResolvedEvidence(BaseModel):
    kind: Literal["consistency_drift_resolved"] = "consistency_drift_resolved"
    drift_type: str
    section_id: str | None = None


class ConsistencyDriftIntroducedEvidence(BaseModel):
    kind: Literal["consistency_drift_introduced"] = (
        "consistency_drift_introduced"
    )
    drift_type: str
    section_id: str | None = None


TypedEvidence = Annotated[
    SyllableVarianceEvidence
    | RepetitionOpeningEvidence
    | RepetitionEndingEvidence
    | WordOveruseEvidence
    | SemanticRepetitionEvidence
    | MotifConcentrationEvidence
    | SectionContrastEvidence
    | PerspectiveDriftEvidence
    | TenseDriftEvidence
    | MotifAddedEvidence
    | MotifRemovedEvidence
    | MotifStrengthenedEvidence
    | MotifWeakenedEvidence
    | RepetitionSignalAddedEvidence
    | RepetitionSignalRemovedEvidence
    | SectionRhymeSchemeShiftEvidence
    | SectionCadenceShiftEvidence
    | SectionSyllablePatternShiftEvidence
    | ConsistencyDriftResolvedEvidence
    | ConsistencyDriftIntroducedEvidence,
    Field(discriminator="kind"),
]


__all__ = [
    "ConsistencyDriftIntroducedEvidence",
    "ConsistencyDriftResolvedEvidence",
    "MotifAddedEvidence",
    "MotifConcentrationEvidence",
    "MotifRemovedEvidence",
    "MotifStrengthenedEvidence",
    "MotifWeakenedEvidence",
    "PerspectiveDriftEvidence",
    "RepetitionEndingEvidence",
    "RepetitionOpeningEvidence",
    "RepetitionSignalAddedEvidence",
    "RepetitionSignalRemovedEvidence",
    "SectionCadenceShiftEvidence",
    "SectionContrastEvidence",
    "SectionRhymeSchemeShiftEvidence",
    "SectionSyllablePatternShiftEvidence",
    "SemanticRepetitionEvidence",
    "SyllableVarianceEvidence",
    "TenseDriftEvidence",
    "TypedEvidence",
    "WordOveruseEvidence",
]
