from typing import Literal

from pydantic import BaseModel

TokenSource = Literal["dictionary", "heuristic"]


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
    # same shape they expect.
    include_near: bool


class RhymeResponse(BaseModel):
    word: str
    normalized_word: str | None
    pronunciations_found: bool
    rhymes: list[RhymeCandidate]
    meta: RhymeMeta


class TokenAnalysis(BaseModel):
    text: str
    normalized: str
    syllables: int
    pronunciation_found: bool
    source: TokenSource = "dictionary"


class LastWord(BaseModel):
    text: str
    normalized: str
    pronunciation_found: bool
    syllables: int | None = None
    source: TokenSource | None = None


class LineAnalysisResponse(BaseModel):
    line: str
    normalized_line: str
    total_syllables: int
    tokens: list[TokenAnalysis]
    last_word: LastWord | None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list = []


class ErrorResponse(BaseModel):
    error: ErrorDetail
