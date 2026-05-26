"""Phase 5.5 Milestone 2 draft-compare schemas.

The compare endpoint takes two embedded drafts (previous + current) and
returns per-side single-draft analyses plus a flat list of compare
insights derived from delta rules. Insight reuses the M0/M1 model.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.core.config import settings
from app.schemas.capability import Capability
from app.schemas.draft_analysis import (
    DraftAnalysisResponse,
    Insight,
    SectionInput,
)

Language = Literal["en", "es"]

_MAX_DRAFT_CHARS = max(settings.max_line_length * 80, 20_000)
_MAX_SECTIONS = 64


class DraftSide(BaseModel):
    content: str = Field(min_length=1, max_length=_MAX_DRAFT_CHARS)
    sections: list[SectionInput] | None = Field(default=None, max_length=_MAX_SECTIONS)

    @field_validator("content")
    @classmethod
    def _content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be blank")
        return v


class DraftCompareOptions(BaseModel):
    compare_motifs: bool = True
    compare_repetition: bool = True
    compare_sections: bool = True
    compare_consistency: bool = False


class DraftCompareRequest(BaseModel):
    language: Language = "en"
    title: str | None = Field(default=None, max_length=200)
    previous: DraftSide
    current: DraftSide
    options: DraftCompareOptions | None = None


class DraftRevision(BaseModel):
    revision_hash: str
    analysis: DraftAnalysisResponse


class CompareSummary(BaseModel):
    motif_delta_count: int = 0
    repetition_delta_count: int = 0
    section_delta_count: int = 0
    consistency_delta_count: int = 0
    family_counts: dict[str, int] = {}
    # Structural notes — sections in one side that didn't pair with the other.
    unmatched_previous_section_ids: list[str] = []
    unmatched_current_section_ids: list[str] = []


class CompareCapabilities(BaseModel):
    compare_motifs: Capability
    compare_repetition: Capability
    compare_sections: Capability
    compare_consistency: Capability


class DraftCompareResponse(BaseModel):
    analysis_id: str
    language: Language
    title: str | None
    previous: DraftRevision
    current: DraftRevision
    summary: CompareSummary
    insights: list[Insight]
    capabilities: CompareCapabilities
