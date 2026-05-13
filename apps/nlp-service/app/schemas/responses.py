from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class RhymeCandidate(BaseModel):
    word: str
    syllables: int
    rhyme_type: str
    score: float


class RhymeMeta(BaseModel):
    limit: int
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


class LastWord(BaseModel):
    text: str
    normalized: str
    pronunciation_found: bool


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
