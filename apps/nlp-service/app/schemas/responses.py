from typing import Any, Literal

from pydantic import BaseModel

TokenSource = Literal["dictionary", "heuristic"]
Language = Literal["en", "es"]
RhymeFamily = Literal["perfect", "multisyllabic", "near", "assonant", "consonant"]
RhymeTargetType = Literal["word", "phrase_ending"]
Capability = Literal["full", "partial", "unsupported"]


class HealthResponse(BaseModel):
    status: str


class RhymeCandidate(BaseModel):
    word: str
    syllables: int
    rhyme_type: str
    score: float
    # New in Phase 5: editorial family label. Null only when the engine
    # couldn't classify (e.g. legacy or unknown tier). Existing clients
    # ignore the field.
    rhyme_family: RhymeFamily | None = None
    # The matched ending span the candidate represents. For single-word
    # candidates this is just the candidate word; phrase-ending candidate
    # support arrives in a later milestone, but the field is reserved now
    # so the contract is stable.
    matched_span: str | None = None
    match_reason: str | None = None


class RhymeMeta(BaseModel):
    limit: int
    mode: str
    # Deprecated alongside the request flag; mirrored so Phase 1 clients see the
    # same shape they expect. Only meaningful for English (mode="near").
    include_near: bool
    # New in Phase 5 — additive optional fields. ``target_type`` echoes the
    # request; ``query_span`` carries the extracted phrase-ending text when
    # the request used ``target_type="phrase_ending"``; ``capabilities``
    # exposes per-feature availability so clients can hide controls for
    # features the engine has not implemented for a given language.
    target_type: RhymeTargetType = "word"
    query_span: str | None = None
    capabilities: dict[str, Capability] = {}


class RhymeResponse(BaseModel):
    word: str
    normalized_word: str | None
    language: Language
    pronunciations_found: bool
    rhymes: list[RhymeCandidate]
    meta: RhymeMeta


class TokenAnalysis(BaseModel):
    text: str
    normalized: str
    syllables: int
    pronunciation_found: bool
    source: TokenSource = "dictionary"
    # True when the engine fell back to a non-dictionary heuristic for this
    # token. Mirrors ``source == "heuristic"`` but is explicit in the contract
    # so clients can surface uncertainty without coupling to source strings.
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
