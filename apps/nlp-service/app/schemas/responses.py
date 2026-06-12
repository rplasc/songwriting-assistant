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
    # True only for target_type="phrase_ending" when at least one span token
    # had no dictionary pronunciation and was dropped from the rhyme
    # phonemes -- the match reflects part of the phrase, not all of it.
    partial_pronunciation: bool = False
    summary: RhymeSummary
    rhymes: list[RhymeCandidate]
    capabilities: dict[str, Capability]


class RhymeOccurrence(BaseModel):
    """One rhyming word's position, so the UI can highlight it.

    ``line_index`` is 1-based and global within a draft; the single-line
    endpoint emits 0 since there is only one line. ``word_index`` is the
    0-based position of the word within its line, and ``char_start``/
    ``char_end`` are offsets into that line (``char_end`` exclusive).
    """

    line_index: int
    word_index: int
    char_start: int
    char_end: int
    text: str
    normalized: str


class InnerRhymeGroup(BaseModel):
    """A set of words that rhyme with each other, anywhere in the text.

    Covers interior and ending words alike, on the same line or across lines.
    """

    id: str
    rhyme_type: Literal["perfect", "near"]
    confidence: RhymeConfidence
    rhyme_key: str
    occurrences: list[RhymeOccurrence]


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
    inner_rhymes: list[InnerRhymeGroup] = []


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: list[Any] = []


class ErrorResponse(BaseModel):
    error: ErrorDetail
