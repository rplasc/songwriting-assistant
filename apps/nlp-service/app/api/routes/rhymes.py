from collections import Counter

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.logging import get_logger, timed
from app.domain.response_contracts.capability_reason_mapper import (
    rhyme_capabilities,
)
from app.domain.response_contracts.rhyme_evidence_tagger import tag_candidate
from app.schemas.requests import RhymeRequest
from app.schemas.responses import RhymeResponse, RhymeSummary
from app.services.language_router import LanguageContext, LanguageRouter
from app.services.response_cache import ResponseCache

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.rhymes")

_CACHE_NAMESPACE = "rhymes"


def _language_router(request: Request) -> LanguageRouter:
    return request.app.state.language_router


def _cache(request: Request) -> ResponseCache:
    return request.app.state.rhyme_response_cache


def _compute_rhymes(payload: RhymeRequest, ctx: LanguageContext) -> RhymeResponse:
    with timed(
        logger,
        "rhymes.request",
        word=payload.word,
        limit=payload.limit,
        mode=payload.mode,
        language=payload.language,
        target_type=payload.target_type,
    ):
        lookup = ctx.rhyme_service.find_rhymes(
            payload.word,
            payload.limit,
            mode=payload.mode,
            target_type=payload.target_type,
            include_metadata=payload.include_metadata,
        )
    tagged = [
        tag_candidate(
            c,
            query=payload.word,
            language=payload.language,
            target_type=payload.target_type,
            pronunciations_found=lookup.pronunciations_found,
        )
        for c in lookup.candidates
    ]
    family_counts: Counter[str] = Counter()
    for c in tagged:
        if c.rhyme_family is not None:
            family_counts[c.rhyme_family] += 1
    capabilities = rhyme_capabilities(
        multisyllabic_supported=bool(
            getattr(ctx.engine, "multisyllabic_supported", False)
        )
    )
    return RhymeResponse(
        query=payload.word,
        normalized_query=lookup.normalized,
        language=payload.language,
        target_type=payload.target_type,
        mode=lookup.resolved_mode,
        pronunciations_found=lookup.pronunciations_found,
        partial_pronunciation=lookup.partial_pronunciation,
        summary=RhymeSummary(
            family_counts=dict(family_counts),
            returned=len(tagged),
            requested_limit=payload.limit,
        ),
        rhymes=tagged,
        capabilities=capabilities,
    )


@router.post("/rhymes")
async def post_rhymes(payload: RhymeRequest, request: Request) -> RhymeResponse:
    router_ = _language_router(request)
    ctx = router_.get(payload.language)
    cache = _cache(request)
    cache_key = ResponseCache.make_key(
        f"{settings.cache_key_prefix}:{_CACHE_NAMESPACE}", payload
    )

    if cache.enabled:
        cached = await cache.get(cache_key)
        if cached is not None:
            logger.info("rhymes.cache_hit", extra={"extras": {"key": cache_key}})
            return RhymeResponse.model_validate(cached)

    response = await run_in_threadpool(_compute_rhymes, payload, ctx)

    if cache.enabled:
        await cache.set(cache_key, response.model_dump(mode="json"))
    return response
