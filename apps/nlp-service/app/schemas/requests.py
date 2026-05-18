from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import settings

RhymeMode = Literal["perfect", "near"]


class RhymeRequest(BaseModel):
    word: str = Field(min_length=1, max_length=64)
    limit: int = Field(default=settings.default_rhyme_limit, ge=1)
    mode: RhymeMode = "perfect"
    include_metadata: bool = False
    # Deprecated: kept so Phase 1 clients keep working. If set true and `mode`
    # was not explicitly chosen, the request is treated as mode="near".
    include_near: bool = False

    @field_validator("word")
    @classmethod
    def _word_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("word must not be blank")
        if any(ch.isspace() for ch in v.strip()):
            raise ValueError("word must be a single token")
        return v

    @field_validator("limit")
    @classmethod
    def _clamp_limit(cls, v: int) -> int:
        return min(v, settings.max_rhyme_limit)

    @model_validator(mode="after")
    def _apply_legacy_near_flag(self) -> "RhymeRequest":
        if self.include_near and self.mode == "perfect":
            self.mode = "near"
        return self


class LineAnalysisRequest(BaseModel):
    line: str = Field(min_length=1, max_length=settings.max_line_length)
    include_metadata: bool = False

    @field_validator("line")
    @classmethod
    def _line_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("line must not be blank")
        return v
