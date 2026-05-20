from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings

Language = Literal["en", "es"]
CapabilityLevel = Literal["full", "partial", "unsupported"]
CadenceClass = Literal["consistent", "mixed", "varied"]
InsightSeverity = Literal["info", "low", "medium", "high"]
RhymeConfidence = Literal["full", "partial"]


_MAX_DRAFT_CHARS = max(settings.max_line_length * 80, 20_000)
_MAX_SECTIONS = 64


class SectionInput(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    label: str | None = Field(default=None, max_length=32)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)

    @field_validator("label")
    @classmethod
    def _normalize_label(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip().lower()
        return s or None


class DraftAnalysisRequest(BaseModel):
    language: Language = "en"
    title: str | None = Field(default=None, max_length=200)
    content: str = Field(min_length=1, max_length=_MAX_DRAFT_CHARS)
    sections: list[SectionInput] | None = Field(default=None, max_length=_MAX_SECTIONS)

    @field_validator("content")
    @classmethod
    def _content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be blank")
        return v


class Capabilities(BaseModel):
    rhyme_scheme: CapabilityLevel
    cadence_patterns: CapabilityLevel
    stress_hints: CapabilityLevel
    repetition: CapabilityLevel
    mixed_language: CapabilityLevel


class RepetitionSignal(BaseModel):
    type: str
    value: str


class SectionAnalysis(BaseModel):
    id: str
    label: str | None
    line_start: int
    line_end: int
    line_count: int
    rhyme_scheme: str
    rhyme_scheme_confidence: RhymeConfidence
    syllable_pattern: list[int]
    syllable_variance: float
    cadence_class: CadenceClass
    repetition_signals: list[RepetitionSignal] = []


class DraftSummary(BaseModel):
    section_count: int
    line_count: int
    total_syllables: int
    notable_patterns: list[str]


class Insight(BaseModel):
    type: str
    scope: Literal["draft", "section"]
    target: str | None
    severity: InsightSeverity
    message: str


class DraftAnalysisResponse(BaseModel):
    language: Language
    title: str | None
    capabilities: Capabilities
    summary: DraftSummary
    sections: list[SectionAnalysis]
    insights: list[Insight]
