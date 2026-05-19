from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import settings

Language = Literal["en", "es"]
RhymeMode = Literal["perfect", "near", "consonant", "assonant"]


class RhymeRequest(BaseModel):
    word: str = Field(min_length=1, max_length=64)
    limit: int = Field(default=settings.default_rhyme_limit, ge=1)
    language: Language = "en"
    # ``mode`` defaults to None so the service can resolve the language's own
    # default. English defaults to ``perfect``, Spanish to ``consonant``.
    mode: RhymeMode | None = None
    include_metadata: bool = False
    # Deprecated: kept so Phase 1 clients keep working. If set true and ``mode``
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
        # Only fires when the caller did not supply an explicit ``mode``.
        if self.include_near and self.mode is None:
            self.mode = "near"
        return self


class LineAnalysisRequest(BaseModel):
    line: str = Field(min_length=1, max_length=settings.max_line_length)
    language: Language = "en"
    include_metadata: bool = False

    @field_validator("line")
    @classmethod
    def _line_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("line must not be blank")
        return v
