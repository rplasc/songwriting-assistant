from fastapi import APIRouter, HTTPException, Request

from app.core.config import settings
from app.core.logging import get_logger, timed
from app.schemas.draft_analysis import DraftAnalysisRequest, DraftAnalysisResponse
from app.services.draft_analysis_service import DraftAnalysisService
from app.services.language_router import LanguageRouter
from app.services.response_cache import ResponseCache

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.draft_analysis")

_CACHE_NAMESPACE = "analyze-draft"


def _language_router(request: Request) -> LanguageRouter:
    return request.app.state.language_router


def _service(request: Request) -> DraftAnalysisService:
    return request.app.state.draft_analysis_service


def _cache(request: Request) -> ResponseCache:
    return request.app.state.response_cache


@router.post("/analyze-draft")
async def post_analyze_draft(
    payload: DraftAnalysisRequest, request: Request
) -> DraftAnalysisResponse:
    router_ = _language_router(request)
    ctx = router_.get(payload.language)
    service = _service(request)
    cache = _cache(request)
    cache_key = ResponseCache.make_key(
        f"{settings.cache_key_prefix}:{_CACHE_NAMESPACE}", payload
    )

    with timed(
        logger,
        "analyze_draft.request",
        language=payload.language,
        chars=len(payload.content),
        sections=len(payload.sections) if payload.sections else 0,
    ):
        if cache.enabled:
            cached = await cache.get(cache_key)
            if cached is not None:
                logger.info(
                    "analyze_draft.cache_hit",
                    extra={"extras": {"key": cache_key}},
                )
                return DraftAnalysisResponse.model_validate(cached)

        try:
            response = service.analyze(payload, ctx)
        except Exception:
            logger.exception(
                "analyze_draft.failed",
                extra={
                    "extras": {
                        "language": payload.language,
                        "chars": len(payload.content),
                    }
                },
            )
            raise HTTPException(
                status_code=500,
                detail={"error": "analysis_failed"},
            )

        if cache.enabled:
            await cache.set(cache_key, response.model_dump(mode="json"))
        return response
