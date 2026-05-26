from fastapi import APIRouter, Request

from app.core.logging import get_logger, timed
from app.schemas.draft_compare import DraftCompareRequest, DraftCompareResponse
from app.services.draft_compare_service import DraftCompareService
from app.services.language_router import LanguageRouter

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.draft_compare")


def _language_router(request: Request) -> LanguageRouter:
    return request.app.state.language_router


def _service(request: Request) -> DraftCompareService:
    return request.app.state.draft_compare_service


@router.post("/analyze-draft-compare")
def post_analyze_draft_compare(
    payload: DraftCompareRequest, request: Request
) -> DraftCompareResponse:
    router_ = _language_router(request)
    ctx = router_.get(payload.language)
    service = _service(request)
    with timed(
        logger,
        "analyze_draft_compare.request",
        language=payload.language,
        previous_chars=len(payload.previous.content),
        current_chars=len(payload.current.content),
    ):
        return service.compare(payload, ctx)
