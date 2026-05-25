from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.config import settings

Language = Literal["en", "es"]
RhymeMode = Literal["perfect", "near", "consonant", "assonant", "multisyllabic"]
RhymeTargetType = Literal["word", "phrase_ending"]


class RhymeRequest(BaseModel):
    # Widened from 64 to fit short phrase endings (e.g. "hold me tonight").
    word: str = Field(min_length=1, max_length=128)
    limit: int = Field(default=settings.default_rhyme_limit, ge=1)
    language: Language = "en"
    # ``mode`` defaults to None so the service can resolve the language's own
    # default. English defaults to ``perfect``, Spanish to ``consonant``.
    # A phrase_ending request with no explicit mode defaults to
    # ``multisyllabic``.
    mode: RhymeMode | None = None
    # ``target_type`` selects between single-token rhyme lookup (default,
    # fast path) and phrase-ending rhyme lookup. Phrase-ending mode allows
    # whitespace inside ``word``.
    target_type: RhymeTargetType = "word"
    include_metadata: bool = False
    # Deprecated: kept so Phase 1 clients keep working. If set true and ``mode``
    # was not explicitly chosen, the request is treated as mode="near".
    include_near: bool = False

    @field_validator("word")
    @classmethod
    def _word_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("word must not be blank")
        return v

    @field_validator("limit")
    @classmethod
    def _clamp_limit(cls, v: int) -> int:
        return min(v, settings.max_rhyme_limit)

    @model_validator(mode="after")
    def _apply_post_field_rules(self) -> "RhymeRequest":
        # The single-token rule only applies to ``target_type="word"``.
        # Phrase-ending requests explicitly allow internal whitespace.
        if self.target_type == "word" and any(
            ch.isspace() for ch in self.word.strip()
        ):
            raise ValueError(
                "word must be a single token when target_type='word'"
            )
        # Phrase-ending requests fall through to the language's default
        # mode (perfect for English, consonant for Spanish). The concatenated
        # span phonemes make the rhyme_key tail naturally span word
        # boundaries when the final word's vowel is unstressed; for
        # stressed-final phrases the anchor lands on the last token.
        # Callers wanting strictly multi-syllable matches opt into
        # mode="multisyllabic" explicitly.
        # Legacy near flag.
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
