from fastapi import APIRouter, Request

from app.core.logging import get_logger, timed
from app.schemas.requests import RhymeRequest
from app.schemas.responses import RhymeMeta, RhymeResponse
from app.services.language_router import LanguageRouter

router = APIRouter(prefix="/v1")
logger = get_logger("nlp.rhymes")


def _language_router(request: Request) -> LanguageRouter:
    return request.app.state.language_router


@router.post("/rhymes")
def post_rhymes(payload: RhymeRequest, request: Request) -> RhymeResponse:
    router_ = _language_router(request)
    ctx = router_.get(payload.language)
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
    multi_cap = (
        "full" if getattr(ctx.engine, "multisyllabic_supported", False) else "unsupported"
    )
    return RhymeResponse(
        word=payload.word,
        normalized_word=lookup.normalized,
        language=payload.language,
        pronunciations_found=lookup.pronunciations_found,
        rhymes=lookup.candidates,
        meta=RhymeMeta(
            limit=payload.limit,
            mode=lookup.resolved_mode,
            include_near=lookup.resolved_mode == "near",
            target_type=payload.target_type,
            query_span=lookup.query_span,
            capabilities={
                "multisyllabic": multi_cap,
                "phrase_ending": "full",
            },
        ),
    )
