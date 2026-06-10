from fastapi import APIRouter, Request

from app.core.logging import get_logger, timed
from app.domain.rhyme.inner_rhyme_rules import (
    find_inner_rhyme_groups,
    phonemes_for_context,
)
from app.schemas.requests import LineAnalysisRequest
from app.schemas.responses import LastWord, LineAnalysisResponse, TokenAnalysis
from app.services.language_router import LanguageRouter

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.analysis")


def _language_router(request: Request) -> LanguageRouter:
    return request.app.state.language_router


def _source(found: bool) -> str:
    return "dictionary" if found else "heuristic"


@router.post("/analyze-line")
def post_analyze_line(
    payload: LineAnalysisRequest, request: Request
) -> LineAnalysisResponse:
    router_ = _language_router(request)
    ctx = router_.get(payload.language)
    with timed(
        logger,
        "analyze_line.request",
        length=len(payload.line),
        language=payload.language,
    ):
        tokens = ctx.engine.tokenize_line(payload.line)
        total, per_token = ctx.syllable_service.count_tokens(tokens)

    token_payloads = [
        TokenAnalysis(
            text=tok.text,
            normalized=tok.normalized,
            syllables=count,
            pronunciation_found=found,
            source=_source(found),
            low_confidence=not found,
        )
        for tok, count, found in per_token
    ]

    last_word: LastWord | None = None
    if per_token:
        tok, count, found = per_token[-1]
        last_word = LastWord(
            text=tok.text,
            normalized=tok.normalized,
            pronunciation_found=found,
            syllables=count,
            source=_source(found),
            low_confidence=not found,
        )

    inner_rhymes = find_inner_rhyme_groups(
        [(0, tokens)],
        phonemes_for_context(ctx, {}),
        payload.language,
    )

    normalized_line = " ".join(t.normalized for t in tokens)
    return LineAnalysisResponse(
        line=payload.line,
        normalized_line=normalized_line,
        language=payload.language,
        total_syllables=total,
        tokens=token_payloads,
        last_word=last_word,
        inner_rhymes=inner_rhymes,
    )
