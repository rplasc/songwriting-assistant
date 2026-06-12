from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.logging import get_logger, timed
from app.domain.rhyme.inner_rhyme_rules import (
    find_inner_rhyme_groups,
    phonemes_for_context,
)
from app.schemas.requests import LineAnalysisRequest
from app.schemas.responses import LastWord, LineAnalysisResponse, TokenAnalysis
from app.services.language_router import LanguageContext, LanguageRouter
from app.services.response_cache import ResponseCache

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.analysis")

_CACHE_NAMESPACE = "analyze-line"


def _language_router(request: Request) -> LanguageRouter:
    return request.app.state.language_router


def _cache(request: Request) -> ResponseCache:
    return request.app.state.rhyme_response_cache


def _source(found: bool) -> str:
    return "dictionary" if found else "heuristic"


def _compute_analyze_line(
    payload: LineAnalysisRequest, ctx: LanguageContext
) -> LineAnalysisResponse:
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


@router.post("/analyze-line")
async def post_analyze_line(
    payload: LineAnalysisRequest, request: Request
) -> LineAnalysisResponse:
    router_ = _language_router(request)
    ctx = router_.get(payload.language)
    cache = _cache(request)
    cache_key = ResponseCache.make_key(
        f"{settings.cache_key_prefix}:{_CACHE_NAMESPACE}", payload
    )

    if cache.enabled:
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.info(
                "analyze_line.cache_hit", extra={"extras": {"key": cache_key}}
            )
            return LineAnalysisResponse.model_validate(cached)

    response = await run_in_threadpool(_compute_analyze_line, payload, ctx)

    if cache.enabled:
        await cache.set(cache_key, response.model_dump(mode="json"))
    return response
