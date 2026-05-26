from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.schemas.anchors import InsightAnchor
from app.schemas.capability import Capabilities
from app.schemas.evidence import TypedEvidence

Language = Literal["en", "es"]
CadenceClass = Literal["consistent", "mixed", "varied"]
InsightSeverity = Literal["info", "low", "medium", "high"]
InsightConfidence = Literal["low", "medium", "high"]
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


class DraftAnalysisOptions(BaseModel):
    include_semantic_repetition: bool = False
    include_motif_tracking: bool = False
    include_section_contrast: bool = False
    include_consistency_hints: bool = False


class DraftAnalysisRequest(BaseModel):
    language: Language = "en"
    title: str | None = Field(default=None, max_length=200)
    content: str = Field(min_length=1, max_length=_MAX_DRAFT_CHARS)
    sections: list[SectionInput] | None = Field(default=None, max_length=_MAX_SECTIONS)
    options: DraftAnalysisOptions | None = None

    @field_validator("content")
    @classmethod
    def _content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be blank")
        return v


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
    motifs: list[str] = []
    insight_count: int = 0
    family_counts: dict[str, int] = {}


class Insight(BaseModel):
    id: str
    type: str
    scope: Literal["draft", "section"]
    target: str | None
    severity: InsightSeverity
    message: str
    evidence: TypedEvidence | None = None
    anchor: InsightAnchor | None = None
    confidence: InsightConfidence | None = None
    hook_context: bool = False


class DraftDetail(BaseModel):
    sections: list[SectionAnalysis]


class DraftAnalysisResponse(BaseModel):
    language: Language
    title: str | None
    capabilities: Capabilities
    summary: DraftSummary
    insights: list[Insight]
    detail: DraftDetail
