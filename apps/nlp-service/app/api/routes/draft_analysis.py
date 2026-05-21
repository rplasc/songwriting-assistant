from fastapi import APIRouter, HTTPException, Request

from app.core.logging import get_logger, timed
from app.schemas.draft_analysis import DraftAnalysisRequest, DraftAnalysisResponse
from app.services.draft_analysis_service import DraftAnalysisService
from app.services.language_router import LanguageRouter

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.draft_analysis")


def _language_router(request: Request) -> LanguageRouter:
    return request.app.state.language_router


def _service(request: Request) -> DraftAnalysisService:
    return request.app.state.draft_analysis_service


@router.post("/analyze-draft")
def post_analyze_draft(
    payload: DraftAnalysisRequest, request: Request
) -> DraftAnalysisResponse:
    router_ = _language_router(request)
    ctx = router_.get(payload.language)
    service = _service(request)
    with timed(
        logger,
        "analyze_draft.request",
        language=payload.language,
        chars=len(payload.content),
        sections=len(payload.sections) if payload.sections else 0,
    ):
        try:
            return service.analyze(payload, ctx)
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
