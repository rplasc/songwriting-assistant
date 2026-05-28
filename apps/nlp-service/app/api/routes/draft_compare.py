from fastapi import APIRouter, Request

from app.core.config import settings
from app.core.logging import get_logger, timed
from app.schemas.draft_compare import DraftCompareRequest, DraftCompareResponse
from app.services.draft_compare_service import DraftCompareService
from app.services.language_router import LanguageRouter
from app.services.response_cache import ResponseCache

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.draft_compare")

_CACHE_NAMESPACE = "analyze-draft-compare"


def _language_router(request: Request) -> LanguageRouter:
    return request.app.state.language_router


def _service(request: Request) -> DraftCompareService:
    return request.app.state.draft_compare_service


def _cache(request: Request) -> ResponseCache:
    return request.app.state.response_cache


@router.post("/analyze-draft-compare")
async def post_analyze_draft_compare(
    payload: DraftCompareRequest, request: Request
) -> DraftCompareResponse:
    router_ = _language_router(request)
    ctx = router_.get(payload.language)
    service = _service(request)
    cache = _cache(request)
    cache_key = ResponseCache.make_key(
        f"{settings.cache_key_prefix}:{_CACHE_NAMESPACE}", payload
    )

    with timed(
        logger,
        "analyze_draft_compare.request",
        language=payload.language,
        previous_chars=len(payload.previous.content),
        current_chars=len(payload.current.content),
    ):
        if cache.enabled:
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.info(
                    "analyze_draft_compare.cache_hit",
                    extra={"extras": {"key": cache_key}},
                )
                return DraftCompareResponse.model_validate(cached)

        response = service.compare(payload, ctx)

        if cache.enabled:
            await cache.set(cache_key, response.model_dump(mode="json"))
        return response
