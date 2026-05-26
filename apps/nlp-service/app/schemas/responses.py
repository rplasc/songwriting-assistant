from typing import Any, Literal

from pydantic import BaseModel

from app.schemas.capability import Capability

TokenSource = Literal["dictionary", "heuristic"]
Language = Literal["en", "es"]
RhymeFamily = Literal["perfect", "multisyllabic", "near", "assonant", "consonant"]
RhymeTargetType = Literal["word", "phrase_ending"]
RhymeConfidence = Literal["high", "medium", "low"]
EvidenceTag = Literal[
    "shared_stressed_ending",
    "shared_vowel_pattern",
    "shared_consonant_tail",
    "phrase_ending_match",
    "heuristic_fallback",
    "multisyllabic_key_match",
]


class HealthResponse(BaseModel):
    status: str


class RhymeCandidate(BaseModel):
    word: str
    syllables: int
    rhyme_type: str
    score: float
    rhyme_family: RhymeFamily | None = None
    matched_span: str | None = None
    match_reason: str | None = None
    # Phase 5.5 productization fields. Filled by the route layer via the
    # rhyme_evidence_tagger; defaults exist only so the service layer can
    # construct a candidate without knowing about UI framing.
    id: str = ""
    confidence: RhymeConfidence = "low"
    evidence_tags: list[EvidenceTag] = []


class RhymeSummary(BaseModel):
    family_counts: dict[str, int] = {}
    returned: int = 0
    requested_limit: int = 0


class RhymeResponse(BaseModel):
    query: str
    normalized_query: str | None
    language: Language
    target_type: RhymeTargetType
    mode: str
    pronunciations_found: bool
    summary: RhymeSummary
    rhymes: list[RhymeCandidate]
    capabilities: dict[str, Capability]


class TokenAnalysis(BaseModel):
    text: str
    normalized: str
    syllables: int
    pronunciation_found: bool
    source: TokenSource = "dictionary"
    low_confidence: bool = False


class LastWord(BaseModel):
    text: str
    normalized: str
    pronunciation_found: bool
    syllables: int | None = None
    source: TokenSource | None = None
    low_confidence: bool = False


class LineAnalysisResponse(BaseModel):
    line: str
    normalized_line: str
    language: Language
    total_syllables: int
    tokens: list[TokenAnalysis]
    last_word: LastWord | None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[Any] = []


class ErrorResponse(BaseModel):
    error: ErrorDetail
