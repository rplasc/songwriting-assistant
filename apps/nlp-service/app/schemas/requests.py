from pydantic import BaseModel, Field, field_validator

from app.core.config import settings


class RhymeRequest(BaseModel):
    word: str = Field(min_length=1, max_length=64)
    limit: int = Field(default=settings.default_rhyme_limit, ge=1)
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


class LineAnalysisRequest(BaseModel):
    line: str = Field(min_length=1, max_length=settings.max_line_length)

    @field_validator("line")
    @classmethod
    def _line_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("line must not be blank")
        return v
