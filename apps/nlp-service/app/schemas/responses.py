from typing import Any, Literal

from pydantic import BaseModel

TokenSource = Literal["dictionary", "heuristic"]
Language = Literal["en", "es"]


class HealthResponse(BaseModel):
    status: str


class RhymeCandidate(BaseModel):
    word: str
    syllables: int
    rhyme_type: str
    score: float
    match_reason: str | None = None


class RhymeMeta(BaseModel):
    limit: int
    mode: str
    # Deprecated alongside the request flag; mirrored so Phase 1 clients see the
    # same shape they expect. Only meaningful for English (mode="near").
    include_near: bool


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
